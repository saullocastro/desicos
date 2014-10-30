import os
from os.path import basename
import traceback
import multiprocessing

import numpy as np

import desicos.conecylDB as conecylDB
from desicos.logger import *
from desicos.abaqus.constants import *
from desicos.composite.laminate import read_stack
from desicos.conecylDB import fetch
from desicos.abaqus.utils import vec_calc_elem_cg


class ConeCyl(object):
    r"""ConeCyl object

    Carries all the information necessary to create a finite element model for
    the analysis of conical and cylindrical structures. The tables below show
    the attributes grouped by cathegory.

    =====================  ==================================================
    General Attributes     Description
    =====================  ==================================================
    ``name_DB``            ``str``, name of the corresponding
                           :mod:`desicos.conecylDB.ccs` entry
    ``model_name``         ``str``, Name of the corresponding model in Abaqus
    ``rename``             ``bool``, tells to automatically rename during
                           :meth:`rebuild`
    ``rebuilt``            ``bool``, tells if :meth:`rebuild` already finished
    ``created_model``      ``bool``, tells if the corresponding model was
                           already created in Abaqus
    ``impconf``            The corresponding imperfection configuration (see
                           :class:`.ImpConf`)
    =====================  ==================================================

    =====================  ==================================================
    Geometric Attributes   Description
    =====================  ==================================================
    ``rbot``               Radius at the bottom edge
    ``rtop``               Radius at the top edge
    ``H``                  Height
    ``L``                  Meridional length (same as ``H`` for cylinders)
    ``alphadeg``           Cone semi-vertex angle in degrees
    =====================  ==================================================

    =====================  ==================================================
    Laminate Attributes    Description
    =====================  ==================================================
    ``stack``              ``list``, stacking sequence with angles in degrees
    ``plyt``               ``float``, ply thickness that will be used for all
                           plies
    ``plyts``              ``list``, ply thicknesses for each ply (overwrites
                           ``plyt`` if both are given). If this has a
                           different length than ``stack``, the first
                           thickness will be applied for all plies
    ``laminapropKey``      ``str``, name of the lamina properties contained in
                           the database (see :mod:`conecylDB.laminaprops`
    ``laminapropKeys``     ``list`` a list of strings when different lamina
                           property names are given for each ply (overwrites
                           ``laminapropKey`` when given)
    ``laminaprop``         ``list``, lamina properties given as
                           ``[E11, E22, nu12, G12, G13, G23]``
    ``laminaprops``        ``list`` a list of lists when different lamina
                           properties should be used for each ply (overwrites
                           ``laminaprop``, ``laminapropKey`` and
                           ``laminapropKeys``, when given)
    ``allowable``          ``list``, lamina allowables given as
                           ``[S11t, S11c, S22t, S22c, S12, S13]``
    ``allowables``         ``list`` a list of lists when different lamina
                           allowables should be used for each ply
    =====================  ==================================================

    =====================  ==================================================
    Load                   Description
    =====================  ==================================================
    ``displ_controlled``   ``bool``, if the axial compression is displacement
                           controlled
    ``pressure_load``      ``float``, the pressure load to be applied (a
                           positive value will create a positive pressure, if
                           ``None, False, 0`` no pressure is applied)
    ``pressure_step``      ``int``, if pressure should be applied in the first
                           (constant) or second (incremented) step
    ``axial_displ``        ``float``, the axial displacement

                           .. note:: Applicable if ``displ_controlled=True``

    ``axial_load``         ``float``, the axial load

                           .. note:: Applicable if ``displ_controlled=False``

    ``axial_step``         ``int``, if the axial load should be applied in
                           the first (constant) or second (incremented) step
    ``Nxxtop``             ``str``, allows the use of a general equation for the
                           distributed force `N_{xx}` at the top edge. The
                           coordinates of the top edge are given in
                           cylindrical coordinates: ``R``, ``Th``, ``Z``; and
                           common functions like ``cos``, ``sin``, ``tan``,
                           ``acos``, ``asin``, ``atan``, ``pow`` and constants
                           like ``pi``, ``e`` etc can be used. Example::
                               cc.Nxxtop = "cos(Th)+sin(Th)"

                           .. note:: If ``Nxxtop`` is not given the formula:

                                     .. math::
                                           {N_{xx}}_{top} = \frac{F_C}{2 \pi
                                           R_{top} cos(\alpha)}
                                     will be adopted, where `F_C` is the
                                     ``axial_load`` attribute

                           .. note:: Applicable if ``displ_controlled=False``

    ``Nxxtop_vec``         ``tuple``, the direction to apply ``Nxxtop``.
                           Applicable only when ``Nxxtop`` is defined. This
                           vector is defined with two points in the
                           cylindrical coordinate system of :ref:`Figure 1
                           <figure_conecyl>`:

                           .. math::
                               ((R_1, Th_1, Z_1), (R_2, Th_2, Z_2))

                           If no direction is given ``Nxxtop`` will be applied
                           along the shell membrane direction

                           .. note:: Applicable if ``displ_controlled=False``

    ``linear_buckling``    ``bool``, tells if the current model is for linear
                           buckling analysis. If ``True`` the created model
                           will have no imperfection and only an unitary axial
                           load applied at the top edge
    =====================  ==================================================
    .. note:: The routines automatically determine whether the load should be
              distributed or applied in a reference point based on the defined
              boundary conditions

    =====================  ==================================================
    Boundary Conditions    Description
    =====================  ==================================================
    ``bc_fix_bottom_uR``   ``bool``, if the radial displacement should be
                           constrained at the bottom edge (:ref:`cf. Figure 1
                           <figure_conecyl>`)
    ``bc_fix_bottom_v``    ``bool``, if the circumferential displacement
                           should be constrained at the bottom edge (:ref:`cf.
                           Figure 1 <figure_conecyl>`)
    ``bc_bottom_clamped``  ``bool``, if the bottom edge should be clamped

                           .. note:: Only applicable when
                                     ``cc.resin_add_BIR==False and``
                                     ``cc.resin_add_BOR==False``

    ``bc_fix_top_uR``      ``bool``, if the radial displacement should be
                           constrained at the top edge (:ref:`cf. Figure 1
                           <figure_conecyl>`)
    ``bc_fix_top_v``       ``bool``, if the circumferential displacement
                           should be constrained at the top edge (:ref:`cf.
                           Figure 1 <figure_conecyl>`)
    ``bc_top_clamped``     ``bool``, if the top edge should be clamped

                           .. note:: Only applicable when
                                     ``cc.resin_add_TIR==False and ``
                                     ``cc.resin_add_TOR==False``
    =====================  ==================================================

    =====================  ==================================================
    Resin Rings            Description (:ref:`the attributes are illustrated
                           here <resin_rings>`)
    =====================  ==================================================
    ``resin_add_BIR``      ``bool``, tells if a resin ring should be added
                           to the inner part of the bottom edge
    ``resin_add_BOR``      ``bool``, tells if a resin ring should be added
                           to the outer part of the bottom edge
    ``resin_add_TIR``      ``bool``, tells if a resin ring should be added
                           to the inner part of the top edge
    ``resin_add_TOR``      ``bool``, tells if a resin ring should be added
                           to the outer part of the top edge
    ``resin_numel``        Number of solid elements in the resin ring
    ``resin_E``            Young modulus of the resin material
    ``resin_nu``           Poisson ratio of the resin material
    ``resin_bot_h``        Thickness of the bottom resin ring
    ``resin_top_h``        Thickness of the top resin ring
    ``resin_bir_w1``       Lower face width of the bottom inner ring
    ``resin_bir_w2``       Upper face width of the bottom inner ring
    ``resin_bor_w1``       Lower face width of the bottom outer ring
    ``resin_bor_w2``       Upper face width of the bottom outer ring
    ``resin_tir_w1``       Lower face width of the top inner ring
    ``resin_tir_w2``       Upper face width of the top inner ring
    ``resin_tor_w1``       Lower face width of the top outer ring
    ``resin_tor_w2``       Upper face width of the top outer ring
    =====================  ==================================================

    =====================  ==================================================
    Mesh Parameters        Description
    =====================  ==================================================
    ``numel_r``            Number of elements around the circumference. This
                           is sufficient to define the whole mesh size since
                           the algorithms will keep an element aspect-ratio
                           close to 1:1
    ``elem_type``          Element type. Tested with: ``'S4'``, ``'S4R'``,
                           ``'S8R'``, ``'S8R5'``
    =====================  ==================================================

    The analysis will be divided in one or two steps, and the corresponding
    analysis parameters for each step are ending with ``1`` or ``2``. When
    only one step is used the parameters corresponding to step 2 will be
    applied.

    =======================  =================================================
    Analysis Parameters      Description
    =======================  =================================================
    ``separate_load_steps``  ``bool``, tells if  the load steps should be
                             separated into two:
                                1) constant loads
                                2) incremented loads
    ``initialInc1``          Initial increment size for step 1
    ``initialInc2``          Initial increment size for step 2
    ``minInc1``              Minimum increment size for step 1
    ``minInc2``              Minimum increment size for step 2
    ``maxInc1``              Maximum increment size for step 1
    ``maxInc2``              Maximum increment size for step 2
    ``maxNumInc1``           Maximum number of increments for step 1
    ``maxNumInc2``           Maximum number of increments for step 2
    ``damping_factor1``      If `\ne` ``None`` artificial damping will be
                             applied to step 1
    ``damping_factor2``      If `\ne` ``None`` artificial damping will be
                             applied to step 2
    ``timeInterval``         ``float``, the time interval where the outputs
                             will be printed
    ``stress_output``        ``bool``, tells to print stress outputs
    ``force_output``         ``bool``, tells to print force outputs
    ``output_requests``      ``list``, contains all the output variables that
                             will be printed in the output
    ``ncpus``                Number of CPUs to run the jobs

    =======================  =================================================

    """
    def __init__(self):
        import desicos.abaqus.imperfections as imperfections

        self.index = 0
        self.name_DB = ''
        self.rename = True
        self.model_name = ''
        self.part_name_shell = 'Shell'
        self.rebuilt = False
        self.created_model = False
        # geometry related
        self.rbot = None
        self.rtop = None
        self.H = None
        self.L = None
        self.alphadeg = 0.
        self.alpharad = None
        self.betadeg = 0.
        self.omegadeg = 0.
        self.cutouts = []
        self.thetadegs = []
        self.pts = []

        # resin rings
        self.resin_add_BIR = False
        self.resin_add_BOR = False
        self.resin_add_TIR = False
        self.resin_add_TOR = False
        self.resin_numel = 3
        self.resin_E = 2454.5336 # MPa
        self.resin_nu = 0.3
        self.resin_bot_h = 1*25.4
        self.resin_top_h = 1*25.4
        self.resin_bir_w1 = 1*25.4
        self.resin_bir_w2 = 1*25.4
        self.resin_bor_w1 = 1*25.4
        self.resin_bor_w2 = 1*25.4
        self.resin_tir_w1 = 1*25.4
        self.resin_tir_w2 = 1*25.4
        self.resin_tor_w1 = 1*25.4
        self.resin_tor_w2 = 1*25.4

        # laminaprop related
        # laminaprop below from COCOMAT, see Degenhardt, 2010
        # (142.5e3,8.7e3,0.28,5.1e3,5.1e3,3.4e3)
        self.laminaprop = None
        # property related
        self.laminate_t = None
        self.plyt = None
        self.stack = []
        self.plyts = []
        self.laminaprops = []
        self.allowables  = []
        self.laminapropKey  = 'material'
        self.laminapropKeys  = []
        self.lam = None

        # load related
        self.displ_controlled = True
        self.pressure_load = None
        self.pressure_step = 1
        self.axial_displ = None
        self.axial_load = None
        self.Nxxtop = None
        self.Nxxtop_vec = ((0,0,0), (0,0,-1))
        self.axial_step = 2
        self.linear_buckling = False
        self.separate_load_steps = True
        self.impconf = imperfections.ImpConf()
        self.impconf.conecyl = self

        # boundary conditions
        self.bc_fix_bottom_uR = True
        self.bc_fix_bottom_v = True
        self.bc_bottom_clamped = True
        self.bc_fix_top_uR = True
        self.bc_fix_top_v = True
        self.bc_top_clamped = True
        self.bc_gaps_bottom_edge = False
        self.bc_gaps_top_edge = False
        self.distr_load_top = None

        # mesh related
        self.numel_r = 140
        self.elem_type = 'S8R5'
        self.mesh_size = None
        self.elsize_r  = None
        self.elsize_r2 = None
        self.elsize_h  = None

        # analysis related
        self.direct_ABD_input = False
        #
        self.ncpus = multiprocessing.cpu_count()-1
        self.step1Name = ''
        self.step2Name = ''
        self.minInc1 = 1.e-6
        self.initialInc1 = 1.
        self.maxInc1 = 1.
        self.maxNumInc1 = 10000
        #
        self.minInc2 = 1.e-6
        self.initialInc2 = 0.01
        self.maxInc2 = 0.01
        self.maxNumInc2 = 100000
        #
        self.damping_factor1 = None
        self.damping_factor2 = 1.e-7
        self.timeInterval = 0.025
        # file management related
        self.tmp_dir = TMP_DIR
        self.study = None
        self.study_dir = TMP_DIR
        self.output_dir = os.path.join(TMP_DIR, 'outputs')
        #OUTPUTS
        self.ls_curve = None
        self.ener_total = 0.
        self.zdisp = []
        self.zload = []
        self.stress_min_num     = {}
        self.stress_min_ms      = {}
        self.stress_min_pos_num = {}
        self.stress_max_num     = {}
        self.stress_max_ms      = {}
        self.stress_max_pos_num = {}
        self.hashin_max_num     = {}
        self.hashin_max_ms      = {}
        self.hashin_max_pos_num = {}
        self.output_requests = ['UT', 'NFORC']
        self.stress_output = False
        self.force_output = False


    def from_DB(self, name_DB=''):
        """Fetch all the cone/cylinder data from the database

        Parameters
        ----------
        name_DB : str
            Name of the corresponding :mod:`desicos.conecylDB.ccs` entry.

        Returns
        -------
            cc : :class:`.ConeCyl` object with the updated properties.

        """
        if name_DB != '':
            self.name_DB = name_DB
        ccs = conecylDB.ccs.ccs
        if self.name_DB in ccs.keys():
            ccdict = ccs[self.name_DB]
            for k,v in ccdict.iteritems():
                if k=='r':
                    setattr(self, 'rbot', v)
                if k=='h':
                    setattr(self, 'H', v)
                if k == 'pload':
                    pload = imperfections.pload.PLoad(theta=0.,
                                                      pt=0.5,
                                                      pltotal=v)
                    pload.impconf = self.impconf
                    setattr(self.impconf, 'ploads', [pload])
                else:
                    setattr(self, k, v)
        else:
            error('{0} not found in the conecylDB'.format(self.name_DB))
            return None

        return self


    def rebuild(self, force=False, save_rebuild=True):
        """Updates the properties of the current :class:`.ConeCyl` object

        Parameters
        ----------
        force : bool
            Force the update even if it is already rebuilt (even if
            the ``rebuilt`` attribute is ``True``).
        save_rebuild : bool
            Tells if the ``rebuilt`` attribute should be ``True`` after the
            update.

        """
        if self.rebuilt and not force:
            return

        if self.model_name:
            self.rename = False

        if self.force_output:
            self.output_requests += ['SF']

        if save_rebuild:
            #if len(self.impconf.ploads) == 0:
                #print 'WARNING - separate_load_steps changed to False'
                #self.separate_load_steps = False
            if not self.separate_load_steps:
                self.num_of_steps = 1
            if self.separate_load_steps:
                self.num_of_steps = 2

        # angle in radians
        if self.alphadeg != None:
            self.alpharad = np.deg2rad(self.alphadeg)

        self.rtop = self.rbot
        if self.rbot != None and self.H != None and self.alpharad != None:
            self.rtop = self.rbot - np.tan(self.alpharad) * self.H
        self.L = self.H/np.cos(self.alpharad)

        # mesh
        self.rmesh = ((self.rbot - self.rtop)*self.rtop/self.rbot + self.rtop)
        self.mesh_size = 2*np.pi*self.rmesh/self.numel_r

        # imperfections
        if self.betadeg:
            self.impconf.uneven_top_edge.betadeg = self.betadeg
            self.impconf.uneven_top_edge.omegadeg = self.omegadeg
        self.impconf.rebuild()

        # cutouts
        for cutout in self.cutouts:
            cutout.rebuild()

        if not isinstance(self.allowables, list):
            self.allowables = [self.allowables for i in self.stack]

        # laminapropKeys
        if not self.laminapropKeys:
            self.laminapropKeys = [self.laminapropKey for i in self.stack]

        # laminaprops
        if not self.laminaprops:
            laminaprops = fetch('laminaprops')
            if self.laminaprop:
                self.laminaprops = [self.laminaprop for i in self.stack]
            else:
                self.laminaprops = [laminaprops[k] for k in self.laminapropKeys]

        # ply thicknesses
        if not self.plyts:
            self.plyts = [self.plyt for i in self.stack]
        else:
            if isinstance(self.plyts, list):
                if len(self.plyts) != len(self.stack):
                    self.plyts = [plyts[0] for i in self.stack]
            else:
                self.plyts = [plyts for i in self.stack]

        # calculating ABD matrix
        if self.direct_ABD_input:
            self.calc_ABD_matrix()

        # model_name
        if self.rename:
            if not self.study:
                tmp = [self.name_DB] + [self.impconf.name]
                self.model_name = '_'.join(tmp)
            else:
                self.model_name = (self.study.name +
                                   '_model_{0:02d}'.format(self.index+1))

        # defining if bottom edge will have GAP elements
        if self.impconf.uneven_bottom_edge:
            self.bc_gaps_bottom_edge = True
        else:
            self.bc_gaps_bottom_edge = False

        # defining if top edge will have GAP elements
        if self.bc_fix_top_uR and self.bc_fix_top_v:
            if self.displ_controlled:
                if self.impconf.uneven_top_edge:
                    self.bc_gaps_top_edge = True
                else:
                    self.bc_gaps_top_edge = False
            else:
                self.bc_gaps_top_edge = False

        else:
            if self.displ_controlled:
                self.bc_gaps_top_edge = True
            else:
                self.bc_gaps_top_edge = False


        if self.linear_buckling:
            self.bc_gaps_bottom_edge = False
            self.bc_gaps_top_edge = False


        if (not self.bc_fix_top_uR or not self.bc_fix_top_v or self.Nxxtop):
            self.distr_load_top = True
        if (not self.linear_buckling and self.impconf.uneven_top_edge
            and self.distr_load_top):
            warn('Distributed load is not compatible with uneven top edge ' +
                 'conditions!')
            warn('Using a concentrated load at the reference point!')
            self.distr_load_top = False

        if save_rebuild:
            self.rebuilt = True


    def prepare_to_save(self):
        """Prepare the :class:`ConeCyl` to be saved

        Any reference to Abaqus objects are removed in this method.

        """
        self.rebuilt = False
        return


    def fr(self, z):
        """Calculates the radius at a given ``z`` position

        Parameters
        ----------
        z : float
            Axial position from bottom to top.

        Returns
        -------
        r : float
            The calculated radius.

        """
        return self.rbot - z*np.tan(self.alpharad)


    def r_z_from_pt(self, pt=0.5):
        """Radius and the axial position from a given normalized position

        Parameters
        ----------
        pt : float or np.ndarray
            Normalized meridional position.

        Returns
        -------
        r, z : tuple
            The radius and the actual axial position at the given normalized
            position. It is a tuple of floats if ``pt`` is a float or a tuple
            of ``numpy.ndarray`` objects if ``pt`` is an array.

        """
        r = self.rbot + (self.rtop - self.rbot)*pt
        z = self.H*pt
        return r, z


    def create_model(self):
        """Triggers the routines to create the model in Abaqus

        The auxiliary module ``_create_model.py`` is used, from where the
        functions ``_create_mesh()``, ``_create_load_steps()`` and
        ``_create_loads_bcs()`` are executed in this order.

        .. note:: Must be called from Abaqus

        .. note:: When new functionalities have to be implemented or for any
                  debugging purposes, one can conveniently change file
                  ``_create_model.py`` directly, and using the ``__main__``
                  section at the end of this file makes it easy to test
                  whatever necessary methods. The tests can be repeatedly run
                  doing::

                      import os

                      from desicos.abaqus.constants import DAHOME
                      os.chdir(os.path.join(DAHOME, 'conecyl'))
                      execfile('_create_model.py')


        """
        self.rebuild()
        from _create_model import (_create_mesh, _create_load_steps,
                                   _create_loads_bcs)

        _create_mesh(self)
        _create_load_steps(self)
        _create_loads_bcs(self)
        created_model = True


    def write_job(self, submit=False, wait=True, multiple_cores=False):
        """Writes the job of the corresponding Abaqus model

        .. note:: Must be called from Abaqus

        Parameters
        ----------
        submit : bool, optional
            If the job should be submitted.
        wait : bool, optional
            If the routine should wait in case the job was submitted.
        multiple_cores : bool, optional
            If multiple cores should be used in the run. Some licenses are
            limited to one core.

        """
        import abaqus

        os.chdir(self.output_dir)
        job = abaqus.mdb.jobs[self.model_name]
        job.writeInput()
        inppath = self.model_name + '.inp'
        if submit:
            if multiple_cores:
                os.system('abaqus job={0} input={1} cpus={2}'.format(
                          self.model_name, inppath, self.ncpus))
            else:
                os.system('abaqus job={0} input={1}'.format(self.model_name,
                          inppath))
        os.chdir(self.tmp_dir)


    def read_walltime(self):
        try:
            tmppath = os.path.join(self.output_dir, self.model_name + '.msg')
            with open(tmppath, 'r') as tmp:
                lines = tmp.readlines()
                w = lines[-1].split()[-1]
                return float(w)
        except:
            return None


    def attach_results(self):
        """Attach the odb file into Abaqus

        If the odb file exists it will be attached in ``session.odbs``, in
        Abaqus.

        .. note:: Must be called from Abaqus

        """
        import abaqus

        odbname = self.model_name + '.odb'
        odbpath = os.path.join(self.output_dir, odbname)
        if not os.path.isfile(odbpath):
            warn('result was not found')
            return False
        session = abaqus.session
        if not odbpath in session.odbs.keys():
            return session.openOdb(name=odbname, path=odbpath, readOnly=True)
        else:
            return session.odbs[odbname]


    def detach_results(self, odb):
        """Detach an odb file from Abaqus

        .. note:: Must be called from Abaqus

        Parameters
        ----------
        odb : Abaqus' :class:`Odb` object.

        """
        import visualization
        visualization.closeOdb(odb)


    def read_outputs(self, **kwargs):
        import _read_outputs
        return _read_outputs.read_outputs(self, **kwargs)


    def plot_displacements(self, **kwargs):
        import _plot
        return _plot.plot_displacements(self, **kwargs)


    def plot_forces(self, **kwargs):
        import _plot
        return _plot.plot_forces(self, **kwargs)


    def plot_stress_analysis(self, **kwargs):
        import _plot
        return _plot.plot_stress_analysis(self, **kwargs)
        import abaqus_functions
        abaqus_functions.configure_session()


    def plot_xy(self, xs, ys, **kwargs):
        import _plot
        return _plot.plot_xy(self, xs, ys, **kwargs)


    def plot_opened(self, ignore=[], create_npz_only=False, ax=None,
            figsize=(3.3, 3.3), save_png=True, aspect='equal', clean=True,
            plot_type=1, outpath='', pngname='plot_from_abaqus.png',
            npzname='plot_from_abaqus.npz', pyname='plot_from_abaqus.py',
            num_levels=400):
        r"""Print a field output for a cylinder/cone model from Abaqus

        Parameters
        ----------
        ignore : list, optional
            A list with the node ids to be ignored. It must contain any nodes
            outside the mapped mesh included in
            ``parts['part_name_shell'].nodes``.
        create_npz_only : bool, optional
            If ``True`` only the data belonging to the desired field output
            will be saved in a ``.npz`` file, and no plotting is performed.
        ax : AxesSubplot, optional
            When ``ax`` is given, the contour plot will be created inside it.
        figsize : tuple, optional
            The figure size given by ``(width, height)``.
        save_png : bool, optional
            Flag telling whether the contour should be saved to an image file.
        aspect : str, optional
            String that will be passed to the ``AxesSubplot.set_aspect()``
            method.
        clean : bool, optional
            Clean axes ticks, grids, spines etc.
        plot_type : int, optional
            For cylinders only ``4`` and ``5`` are valid.
            For cones all the following types can be used:

            - ``1``: concave up (default for cones)
            - ``2``: concave down
            - ``3``: stretched closed
            - ``4``: stretched opened (`r(z) \times \theta` vs. `H`)
            - ``5``: stretched opened (`r_{bottom}` vs. `H`)
        outpath : str, optional
            Output path where the data from Abaqus and the plots are
            saved (see notes).
        pngname : str, optional
            The file name for the generated image file.
        npzname : str, optional
            The file name for the generated npz file.
        pyname : str, optional
            The file name for the generated Python file.
        num_levels : int, optional
            Number of contour levels (higher values make the contour smoother).

        Returns
        -------
        out : tuple
            Where ``out[0]`` and ``out[1]`` contain the circumferential and
            meridional grids of coordinates and ``out[2]`` the corresponding
            field output.

        Notes
        -----
        The data is saved using ``np.savez()`` into ``outpath`` as
        ``npzname`` with an accompanying script for plotting
        ``pyname``, very handy when Matplotlib is not
        importable from Abaqus.

        """
        from abaqus import mdb
        from abaqusConstants import NODAL
        import desicos.abaqus.abaqus_functions as abaqus_functions

        if self.model_name in mdb.models.keys():
            part = mdb.models[self.model_name].parts[self.part_name_shell]
        else:
            text = 'The model corresponding to the active odb must be loaded'
            raise RuntimeError(text)

        elements = part.elements
        nodes = part.nodes
        sina = np.sin(self.alpharad)
        cosa = np.cos(self.alpharad)

        npzname = npzname.split('.npz')[0] + '.npz'
        pyname = pyname.split('.py')[0] + '.py'
        pngname = pngname.split('.png')[0] + '.png'

        npzname = os.path.join(outpath, npzname)
        pyname = os.path.join(outpath, pyname)
        pngname = os.path.join(outpath, pngname)

        odb = abaqus_functions.get_current_odb()
        odbDisplay = abaqus_functions.get_current_odbdisplay()
        frame = abaqus_functions.get_current_frame()
        fieldOutputKey = odbDisplay.primaryVariable[0]
        sub_vector = odbDisplay.primaryVariable[5]

        valid_plot_types = (1, 2, 3, 4, 5)
        if not plot_type in valid_plot_types:
            raise ValueError('Valid values for plot_type are:\n\t\t' +
                             ' or '.join(map(str, valid_plot_types)))

        if not create_npz_only:
            try:
                import matplotlib.pyplot as plt
                import matplotlib
            except:
                create_npz_only = True
        try:
            frame_num = int(frame.frameValue)
            field = frame.fieldOutputs[fieldOutputKey]
            nodal_out = False
            if field.values[0].position == NODAL:
                nodal_out = True

            if nodal_out:
                odbSet = odb.rootAssembly.nodeSets['SHELL_FACES']
                coords = np.array([n.coordinates for n in nodes])
                labels = np.array([n.label for n in nodes])
                if ignore:
                    mask = np.in1d(labels, ignore)
                    labels = labels[mask]
                    coords = coords[mask]
                thetas = np.arctan2(coords[:, 1], coords[:, 0])
            else:
                odbSet = odb.rootAssembly.elementSets['SHELL_FACES']
                coords = vec_calc_elem_cg(elements)
                thetas = np.arctan2(coords[:, 1], coords[:, 0])

            field = field.getSubset(region=odbSet)

            attributes = {
                          'Magnitude': 'magnitude',
                          'Mises': 'mises',
                          'Min. In-Plane Principal': 'minInPlanePrincipal',
                          'Max. In-Plane Principal': 'maxInPlanePrincipal',
                          'Min. Principal': 'minPrincipal',
                          'Mid. Principal': 'midPrincipal',
                          'Max. Principal': 'maxPrincipal',
                          'Out-of-Plane Principal': 'outOfPlanePrincipal',
                          'Tresca': 'tresca',
                          'Third Invariant': 'inv3',
                         }
            components = {
                          'S11': 0,
                          'S22': 1,
                          'S33': 2,
                          'S12': 3,
                          'SF1': 0,
                          'SF2': 1,
                          'SF3': 3,
                          'SM2': 0,
                          'SM1': 1,
                          'SM3': 2,
                         }

            if sub_vector == '':
                out = np.array([val.data for val in field.values])

            elif sub_vector in attributes.keys():
                attr = attributes.get(sub_vector)
                out = np.array([getattr(v, attr) for v in field.values])

            elif sub_vector in components.keys():
                pos = components[sub_vector]
                out = np.array([v.data[pos] for v in field.values])

            elif sub_vector in ('U1', 'UT1', 'U2', 'UT2', 'U3', 'UT3'):
                uvw_rec = np.array([val.data for val in field.values])

                u1_rec = uvw_rec[:,0]
                u2_rec = uvw_rec[:,1]
                u3_rec = uvw_rec[:,2]

                u3_cyl = u3_rec
                u2_cyl = u2_rec*np.cos(thetas) - u1_rec*np.sin(thetas)
                u1_cyl = u2_rec*np.sin(thetas) + u1_rec*np.cos(thetas)

                u1_cone = u1_cyl*cosa + u3_cyl*sina
                u2_cone = u2_cyl
                u3_cone = u3_cyl*cosa - u1_cyl*sina

                displ_vecs = {'U1':u1_cone, 'U2':u2_cone, 'U3':u3_cone,
                              'UT1':u1_cone, 'UT2':u2_cone, 'UT3':u3_cone}
                out = displ_vecs[sub_vector]

            else:
                raise NotImplementedError('{0} cannot be used!'.format(
                    sub_vector))

            if not nodal_out:
                firstElement = None
                numIntPts = 0
                for v in field.values:
                    if firstElement is None:
                        firstElement = v.elementLabel
                    if v.elementLabel == firstElement:
                        numIntPts += 1
                    else:
                        break
                out = out.reshape(-1, numIntPts).mean(axis=1)

            if 'S8' in self.elem_type and nodal_out:
                center_nodes = []
                for el in elements:
                    center_nodes += el.connectivity[4:]
                mask = np.in1d(labels, center_nodes)
                thetas = thetas[mask]
                coords = coords[mask]
                out = out[mask]

            zs = coords[:, 2]

            #first sort
            nt = self.numel_r
            asort = zs.argsort()
            zs = zs[asort].reshape(-1, nt)
            thetas = thetas[asort].reshape(-1, nt)
            out = out[asort].reshape(-1, nt)

            #second sort
            asort = thetas.argsort(axis=1)
            for i, asorti in enumerate(asort):
                zs[i,:] = zs[i,:][asorti]
                thetas[i,:] = thetas[i,:][asorti]
                out[i,:] = out[i,:][asorti]

            H = self.H
            rtop = self.rtop
            rbot = self.rbot
            L = H/cosa

            def fr(z):
                return rbot - z*sina/cosa

            if self.alpharad == 0.:
                plot_type = 4
            if plot_type == 1:
                r_plot = fr(zs)
                if self.alpharad==0.:
                    r_plot_max = L
                else:
                    r_plot_max = rtop/sina + L
                y = r_plot_max - r_plot*np.cos(thetas*sina)
                x = r_plot*np.sin(thetas*sina)
            elif plot_type == 2:
                r_plot = fr(zs)
                y = r_plot*np.cos(thetas*sina)
                x = r_plot*np.sin(thetas*sina)
            elif plot_type == 3:
                r_plot = fr(zs)
                r_plot_max = rtop/sina + L
                y = r_plot_max - r_plot*np.cos(thetas)
                x = r_plot*np.sin(thetas)
            elif plot_type == 4:
                x = fr(zs)*thetas
                y = zs
            elif plot_type == 5:
                x = fr(0)*thetas
                y = zs

            cir = x
            mer = y
            field = out

            if not create_npz_only:
                levels = np.linspace(field.min(), field.max(), num_levels)
                if ax==None:
                    fig = plt.figure(figsize=figsize)
                    ax = fig.add_subplot(111)
                else:
                    if isinstance(ax, matplotlib.axes.Axes):
                        ax = ax
                        fig = ax.figure
                        save_png = False
                    else:
                        raise ValueError('"ax" must be an Axes object')
                ax.contourf(cir, mer, field, levels=levels)
                ax.grid(False)
                ax.set_aspect(aspect)
                ax.xaxis.set_ticks_position('bottom')
                ax.yaxis.set_ticks_position('left')
                #lim = self.rtop*np.pi
                #ax.xaxis.set_ticks([-lim, 0, lim])
                #ax.xaxis.set_ticklabels([r'$-\pi$', '$0$', r'$+\pi$'])
                #ax.set_title(
                    #r'$PL=20 N$, $F_{{C}}=50 kN$, $w_{{PL}}=\beta$, $mm$')
                if clean:
                    ax.xaxis.set_ticks_position('none')
                    ax.yaxis.set_ticks_position('none')
                    ax.xaxis.set_ticklabels([])
                    ax.yaxis.set_ticklabels([])
                    ax.set_frame_on(False)
                if save_png:
                    log('')
                    log('Plot saved at: {0}'.format(pngname))
                    plt.tight_layout()
                    plt.savefig(pngname, transparent=True,
                                bbox_inches='tight', pad_inches=0.05,
                                dpi=400)

            else:
                log('Matplotlib cannot be imported from Abaqus')
            np.savez(npzname, cir=cir, mer=mer, field=field)
            with open(pyname, 'w') as f:
                f.write("import os\n")
                f.write("\n")
                f.write("import numpy as np\n")
                f.write("import matplotlib.pyplot as plt\n")
                f.write("\n")
                f.write("add_title = False\n")
                f.write("tmp = np.load(r'{0}')\n".format(basename(npzname)))
                f.write("pngname = r'{0}'\n".format(basename(pngname)))
                f.write("cir = tmp['cir']\n")
                f.write("mer = tmp['mer']\n")
                f.write("field = tmp['field']\n")
                f.write("clean = {0}\n".format(clean))
                f.write("plt.figure(figsize={0})\n".format(figsize))
                f.write("ax = plt.gca()\n")
                f.write("levels = np.linspace(field.min(), field.max(), {0})\n".format(
                        num_levels))
                f.write("ax.contourf(cir, mer, field, levels=levels)\n")
                f.write("ax.grid(False)\n")
                f.write("ax.set_aspect('{0}')\n".format(aspect))
                f.write("ax.xaxis.set_ticks_position('bottom')\n")
                f.write("ax.yaxis.set_ticks_position('left')\n")
                f.write("ax.xaxis.set_ticks([{0}, 0, {1}])\n".format(
                        -self.rtop*np.pi, self.rtop*np.pi))
                f.write("ax.xaxis.set_ticklabels([r'$-\pi$', '$0$', r'$+\pi$'])\n")
                f.write("if add_title:\n")
                f.write("    ax.set_title(r'Abaqus, $PL=20 N$, $F_{{C}}=50 kN$, $w_{{PL}}=\beta$, $mm$')\n")
                f.write("if clean:\n")
                f.write("    ax.xaxis.set_ticks_position('none')\n")
                f.write("    ax.yaxis.set_ticks_position('none')\n")
                f.write("    ax.xaxis.set_ticklabels([])\n")
                f.write("    ax.yaxis.set_ticklabels([])\n")
                f.write("    ax.set_frame_on(False)\n")
                f.write("plt.savefig(pngname, transparent=True,\n")
                f.write("            bbox_inches='tight', pad_inches=0.05, dpi=400)\n")
                f.write("plt.show()\n")
            log('')
            log('Output exported to "{0}"'.format(npzname))
            log('Please run the file "{0}" to plot the output'.format(
                  pyname))
            log('')

            return cir, mer, field

        except:
            traceback.print_exc()
            error('Opened plot could not be generated! :(')


    def check_completed(self, wait=False, print_found=False):
        if not self.rebuilt:
            self.rebuild()
        tmp = os.path.join(self.output_dir, self.model_name + '.log')
        if wait == True:
            log('Waiting for job completion...')
        #TODO a general function to check the log file
        while True:
            if os.path.isfile(tmp):
                tmpfile = open(tmp, 'r')
                lines = tmpfile.readlines()
                tmpfile.close()
                if len(lines) == 0:
                    continue
                if len(lines) < 2:
                    continue
                if lines[-2].find('End Abaqus/Standard Analysis') > -1:
                    if print_found:
                        log('RUN COMPLETED for model {0}'.format(
                            self.model_name))
                    return True
                elif lines[-1].find('Abaqus/Analysis exited with errors') > -1:
                    if print_found:
                        log('RUN COMPLETED WITH ERRORS for model {0}'.format(
                            self.model_name))
                    return True

                else:
                    if not wait:
                        warn('RUN NOT COMPLETED for model {0}'.format(
                             self.model_name))
                        return False
            else:
                if not wait:
                    warn('RUN NOT STARTED for model {0}'.format(
                         self.model_name))
                    return False
            if wait:
                import time
                time.sleep(5)


    def stress_analysis(self, **kwargs):
        if self.linear_buckling:
            return True
        if not self.check_completed():
            return False
        self.read_outputs(last_frame=False,
                           last_cross_section=False,
                           read_fieldOutputs=True)
        import _stress_analysis
        ans = _stress_analysis.calc_frames(self, **kwargs)
        self.read_outputs()
        self.plot_stress_analysis()

        return ans


    def create_cutout(self, theta, pt, d, numel=None):
        """Create a cutout in the shell surface.

        This function is buggy, intended to easily create cutouts on the shell
        surface. Doesn't work for all cases and the mesh quality must be
        improved.

        Parameters
        ----------
        theta : float
            Cylindrical coordinate theta in degrees.
        pt : float
            Coordinate z/cylinder height (or cone height).
        d : float
            Cutout diameter.

        """
        from desicos.abaqus.cutout import Cutout
        cutobj = Cutout()
        cutobj.theta = theta
        cutobj.pt = pt
        cutobj.d = d
        if numel != None:
            cutobj.numel = numel
        cutobj.index = len(self.cutouts)
        cutobj.conecyl = self
        self.cutouts.append(cutobj)
        return cutobj


    def calc_ABD_matrix(self):
        """Calculates the laminate stiffness matrix (ABD matrix)

        Requires that all the laminate attributes are defines.

        Returns
        -------

        lam : :class:`.Laminate` object.

        """
        self.lam = read_stack(stack=self.stack,
                              plyt=self.plyt,
                              laminaprop=self.laminaprop,
                              plyts=self.plyts,
                              laminaprops=self.laminaprops)
        return self.lam


    def calc_nasaKDF(self):
        """Calculates the KDF using the NASA SP-8007 guideline

        Returns
        -------
        nasaKDF : float
            The knock-down factor (KDF) calculates using the NASA SP-8007.

        """
        self.calc_ABD_matrix()
        if self.alphadeg > 0. :
            rm = (self.rbot + self.rtop)/2.
            req = rm/np.cos(self.alpharad)
        else:
            req = self.rbot
        Ex = self.lam.A[0,0]
        Ey = self.lam.A[1,1]
        Dx = self.lam.D[0,0]
        Dy = self.lam.D[1,1]
        teq = 3.4689* (Dx*Dy/(Ex*Ey))**0.25
        phi = 1/16. * (req/teq)**0.5
        self.nasaKDF = 1. - 0.901*(1-np.e**-phi)
        return self.nasaKDF


    def calc_partitions(self, thetadegs=[], pts=[]):
        """Updates all circumferential and axial positions to partition

        This method reads all the imperfections and collects the
        circumferential positions ``thetadegs`` and the normalized meridional
        positions ``pts`` where partitions should be created. These two lists
        will be used in the routines to create an Abaqus model.

        Parameter
        ---------
        thetadegs : list, optional
            Additional positions where circumferential partitions are desired
        pts : list, optional
            Additional positions where meridional partitions are desired

        """
        thetadegs += [0]
        for imp in self.impconf.imperfections:
            valid = True
            for pt in imp.pts:
                if pt<0 or pt>1.:
                    error('Invalid imperfection: {0}, {1}'.format(imp.index,
                          imp.name))
                    warn('Ignored imperfection: {0}, {1}'.format(imp.index,
                         imp.name))
                    valid = False
                    break
            if valid:
                thetadegs += imp.thetadegs
                pts += imp.pts
        self.thetadegs = sorted(list(set(thetadegs)))
        self.pts = sorted(list(set(pts)))
        return self.thetadegs, self.pts


    def get_step_name(self, step):
        """Get the step name corresponding to an integer number

        Parameters
        ----------
        step : int
            A step number. Abaqus' "Initial" step does not count, such that
            ``step=1`` will be the first step after the "Initial" step.

        Returns
        -------
        step_name : str
            The step name.
        """
        if step<=1:
            return self.step1Name
        elif step>=2:
            return self.step2Name
        else:
            raise ValueError('Invalid step number!')

