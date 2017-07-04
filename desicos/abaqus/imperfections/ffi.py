from __future__ import absolute_import

import numpy as np

from desicos.logger import warn
from .imperfection import Imperfection

class FFI(Imperfection):
    r"""Fiber Fraction Imperfection

    Thickness variations are generally caused by a varying amount of matrix,
    while the amount of fibers remains constant. Thus, the actual fiber volume
    fraction is higher in thinner sections of the material. This imperfection
    aims to include that effect in the model, by adjusting the material
    properties.

    =====================  ==================================================
    Attributes             Description
    =====================  ==================================================
    nominal_vf             ``float``, nominal fiber volume fraction
    E_matrix               ``float``, Young's modulus of the matrix material
    nu_matrix              ``float``, Poisson's ratio of the matrix material
    use_ti                 ``bool``, if ``True``, create varying material
                           properties according to the thickness imperfection
                           data (if present).
    global_sf              ``float`` or ``None``, global scaling factor to
                           apply to the material thickness. Set to ``None``
                           to disable. The global scaling may be overridden
                           by a thickness imperfection, if ``use_ti`` (see
                           above) is ``True``.
    created                ``bool``, ``True`` after the imperfection has been
                           created.
    =====================  ==================================================

    """
    def __init__(self, nominal_vf, E_matrix, nu_matrix, use_ti, global_sf=None):
        super(FFI, self).__init__()
        self.nominal_vf = nominal_vf
        self.E_matrix = E_matrix
        self.nu_matrix = nu_matrix
        self.use_ti = use_ti
        self.global_sf = global_sf
        self.name = 'FFI'
        self.xaxis = 'scaling_factor'
        self.xaxis_label = 'Global thickness scaling factor, -'
        self.created = False


    @property
    def scaling_factor(self):
        return 1.0 if self.global_sf is None else self.global_sf


    def rebuild(self):
        if self.global_sf is not None:
            self.name = 'FFI_SF_%05d' % (int(round(100*self.global_sf)))


    def calc_amplitude(self):
        """Calculates the imperfection amplitude

        Amplitude measured as the biggest thickness difference between
        the actual and nominal layup thickness of the Cone/Cylinder,
        considering only the layups that have this imperfection applied.

        .. note:: Must be called from Abaqus.

        Returns
        -------
        max_amp : float
            Maximum absolute imperfection amplitude.

        """
        cc = self.impconf.conecyl
        max_amp = 0
        cc_total_t = sum(cc.plyts)
        if self.global_sf is not None:
            max_amp = abs(self.global_sf - 1.0) * cc_total_t
        if self.use_ti:
            from abaqus import mdb

            part = mdb.models[cc.model_name].parts[cc.part_name_shell]
            for layup in part.compositeLayups.values():
                if not layup.suppressed:
                    layup_t = sum(p.thickness for p in layup.plies.values())
                    max_amp = max(max_amp, abs(layup_t - cc_total_t))
        self.amplitude = max_amp
        return self.amplitude


    def calc_scaled_laminaprop(self, laminaprop, scaling_factor):
        """Calculate material properties of a lamina with a scaled thickness.

        Calculates the new lamina properties, if a given material (lamina)
        is scaled in thickness by a given factor. The new material properties
        are calculated from the properties of the fiber and the matrix, using
        the composition rule (for E11 and nu12) and the corrected composition
        rule (for E22, G12, G13 and G23).

        The matrix properties are to be supplied by the user. The fiber
        properties are calculated based on the original (nominal) lamina
        properties, using the inverse of the respective composition rule.

        Parameters
        ----------
        laminaprop : tuple
            Material properties (E11, E12, nu12, G12, G13, G23) of the lamina
            at the nominal thickness
        scaling_factor : float
            Scaling factor that is to be applied to the ply thickness. The
            total amount of fibers is assumed to remain constant, thus the
            actual fiber volume fraction is inversely proportional to this
            scaling factor.

        Returns
        -------
        new_laminaprop : tuple
            Lamina properties of the lamina with a scaled thickness

        """
        assert len(laminaprop) == 6
        E_m = float(self.E_matrix)
        nu_m = float(self.nu_matrix)
        G_m = E_m / (2.*(1.+nu_m))
        vf_nom = float(self.nominal_vf)
        vf = vf_nom / scaling_factor
        if not (0. < vf < 1.):
            raise ValueError(('Invalid scaling factor {0:.2f} for Fiber' +
                'Fraction Imperfection, resulting fiber volume fraction' +
                ' ({1:.2f}) is out of range 0..1)').format(scaling_factor, vf))

        # Composition rule to obtain material properties,
        # based on fiber and matrix data
        # There are two different rules, one for longitudinal properties
        # (E11, nu12) and one for transversal props (E22, G12, G13, G23)
        def compL(X_f, X_m):
            return vf*X_f + (1 - vf)*X_m
        def compT(X_f, X_m):
            return X_m / (1 - np.sqrt(vf)*(1 - X_m/X_f))
        comp_rule = (compL, compT, compL, compT, compT, compT)

        # Inverse composition rule to obtain fiber properties,
        # based on nominal laminate properties and matrix data
        def invL(X_nom, X_m):
            return (X_nom - (1 - vf_nom)*X_m) / vf_nom
        def invT(X_nom, X_m):
            return X_m*np.sqrt(vf_nom) / (X_m/X_nom - (1 - np.sqrt(vf_nom)))
        inv_comp_rule = (invL, invT, invL, invT, invT, invT)

        matrix_prop = (E_m, E_m, nu_m, G_m, G_m, G_m)
        fiber_prop = tuple(f(X_nom, X_m) for f, X_nom, X_m in
            zip(inv_comp_rule, laminaprop, matrix_prop))
        new_laminaprop = tuple(f(X_f, X_m) for f, X_f, X_m in
            zip(comp_rule, fiber_prop, matrix_prop))

        DEBUG_STRING = 'E11={0:.2f}, E22={1:.2f}, nu12 = {2:.2f},' +\
            ' G12={3:.2f}, G13={4:.2f}, G23={5:.2f}'
        to_check = [(laminaprop, 'nominal laminate'),
                    (matrix_prop, 'matrix'),
                    (fiber_prop, 'calculated fiber'),
                    (new_laminaprop, 'imperfect laminate')]
        for prop, name in to_check:
            if not (all(x > 0 for x in prop) and prop[2] < 0.5):
                mat_str = DEBUG_STRING.format(*prop)
                raise ValueError(('One or more invalid value(s) for {0}' +
                    ' properties:\n{1}').format(name, mat_str))
        return new_laminaprop


    def _update_material(self, suffix, scaling_factor):
        from abaqus import mdb

        cc = self.impconf.conecyl
        mod = mdb.models[cc.model_name]

        warned = set()
        for name, laminaprop in zip(cc.laminapropKeys, cc.laminaprops):
            if len(laminaprop) == 6:
                new_laminaprop = self.calc_scaled_laminaprop(laminaprop, scaling_factor)
            else:
                if name not in warned:
                    warn(('Invalid number of lamina properties for material' +
                        '{0}, or material is isotropic. Fiber Fraction' +
                        ' Imperfection is not applied.').format(name))
                    warned.add(name)
                new_laminaprop = laminaprop
            new_mat = mod.Material(name=(name + suffix),
                                   objectToCopy=mod.materials[name])
            new_mat.elastic.setValues(table=(new_laminaprop,))


    def create(self):
        """Actually create the imperfection

        .. note:: Must be called from Abaqus.

        """
        from abaqus import mdb
        from desicos.abaqus.abaqus_functions import modify_composite_layup

        cc = self.impconf.conecyl
        part = mdb.models[cc.model_name].parts[cc.part_name_shell]

        if self.global_sf is not None:
            MAT_SUFFIX = '_scaled'
            self._update_material(MAT_SUFFIX, self.global_sf)
            def modify_mat_thick(index, kwargs):
                kwargs['thickness'] = cc.plyts[index] * self.global_sf
                kwargs['material'] = cc.laminapropKeys[index] + MAT_SUFFIX
                return kwargs
            modify_composite_layup(part, 'CompositePlate', modify_mat_thick)

        self.update_after_tis()
        self.created = True

    def update_after_tis(self):
        """Call this function after the thickness imperfection(s) are applied,
        to modify the material properties as well, if needed.

        """
        if not self.use_ti:
            return

        from abaqus import mdb
        from desicos.abaqus.abaqus_functions import modify_composite_layup

        cc = self.impconf.conecyl
        part = mdb.models[cc.model_name].parts[cc.part_name_shell]

        for layup_name in part.compositeLayups.keys():
            if layup_name.startswith('CLayup_'):
                layup = part.compositeLayups[layup_name]
                thickness = sum(p.thickness for p in layup.plies.values())
                scaling_factor = thickness / sum(cc.plyts)
                suffix = layup_name[-6:]
                self._update_material(suffix, scaling_factor)
                def modify_material(index, kwargs):
                    kwargs['material'] = cc.laminapropKeys[index] + suffix
                    return kwargs
                modify_composite_layup(part, layup_name, modify_material)
