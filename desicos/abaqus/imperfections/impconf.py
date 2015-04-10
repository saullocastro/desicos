import os

import numpy as np

from desicos.logger import *
from uneven_edges import Shim, UnevenBottomEdge, UnevenTopEdge
from axisymmetric import Axisymmetric
from dimple import Dimple
from pload import PLoad
from lbmi import LBMI
from msi import MSI
from ti import TI
from cutout import Cutout


class ImpConf(object):
    """Imperfection Configuration

    Created by default as one attribute of the :class:`.ConeCyl` object,
    accessed through::

        cc = ConeCyl()
        impconf = cc.impconf

    If one has the ``impconf`` object and wants to access the corresponding
    :class:`ConeCyl` object, the attribute ``conecyl`` can be used as
    examplified below.  Note that if no :class:`.ConeCyl` is assigned to this
    imperfection configuration a ``None`` value will be obtained::

        cc = impconf.conecyl

    The imperfections are grouped in the attributes detailed below.

    ================== ======================================================
    Attributes         Description
    ================== ======================================================
    uneven_bottom_edge :class:`.UnevenBottomEdge` object
    uneven_top_edge    :class:`.UnevenTopEdge` object
    ploads             ``list`` of :class:`.PLoad` (Perturbation Load) objects
    dimples            ``list`` of :class:`.Dimple` (Dimple Imperfection)
                       objects
    axisymmetrics      ``list`` of :class:`.Axisymmetric` (Axisymmetric
                       Imperfection) objects
    lbmis              ``list`` of :class:`.LBMI` (Linear Buckling Mode-Shaped
                       Imperfection) objects
    tis                ``list`` of :class:`.TI` (Thickness Imperfection)
                       objects
    msis               ``list`` of :class:`.MSI` (Mid-Surface Imperfection)
                       objects
    cutouts            ``list`` of :class:`.Cutout` objects
    ================== ======================================================

    """
    def __init__(self):
        self.uneven_bottom_edge = UnevenBottomEdge()
        self.uneven_bottom_edge.impconf = self
        self.uneven_top_edge = UnevenTopEdge()
        self.uneven_top_edge.impconf = self
        self.imperfections = []
        self.ploads = []
        self.dimples = []
        self.axisymmetrics = []
        self.lbmis = []
        self.msis = []
        self.tis = []
        self.cutouts = []
        self.rename = True
        self.name = ''
        self.conecyl = None


    def __setstate__(self, attrs):
        # Called during unpickling (i.e. loading)
        # Calling __init__ prevents problems with missing attributes,
        # when loading from older versions
        self.__init__()
        self.__dict__.update(attrs)


    def add_axisymmetric(self, pt, b, wb):
        """Add an Axisymmetric Imperfection (AI)

        Parameters
        ----------
        pt : float
            Normalized meridional position.
        b : float
            Half-wave length.
        wb : float
            Imperfection amplitude (amplitude of the half-wave).

        Returns
        -------
        ax : :class:`.Axisymmetric` object.

        """
        ax = Axisymmetric(pt, b, wb)
        ax.impconf = self
        self.axisymmetrics.append(ax)
        return ax


    def add_dimple(self, thetadeg, pt, a, b, wb):
        """Add a Dimple Imperfection (DI)

        Parameters
        ----------
        thetadeg : float
            Circumferential position of the dimple.
        a : float
            Circumferential half-wave length of the dimple.
        b : float
            Meridional half-wave length of the dimple.
        wb : float
            Imperfection amplitude.

        Returns
        -------
        d : :class:`.Dimple` object.

        """
        d = Dimple(thetadeg, pt, a, b, wb)
        d.impconf = self
        self.dimples.append(d)
        return d


    def add_lbmi(self, mode, scaling_factor):
        """Add a Linear Buckling Mode-shaped Imperfection (LBMI)

        Parameters
        ----------
        mode : int
            Mode number corresponding to this eigenvector.
        scaling_factor : float
            Amplitude of this eigenvector when applied as an imperfection.

        Returns
        -------
        lbmi : :class:`.LBMI` object.

        """
        lbmi = LBMI(mode, scaling_factor)
        lbmi.impconf = self
        self.lbmis.append(lbmi)
        return lbmi


    def add_measured_u3s_bottom_edge(self, thetadegs, u3s):
        r"""Add a measured uneven bottom edge

        Straightforward method to include measured data about the bottom edge
        imperfection.

        Adopts the coordinate system of :ref:`this figure <figure_conecyl>`
        when defining the `u_3` displacements for each `\theta` value.

        The edge imperfection that actually goes for each node is a linear
        interpolation of the measured values.

        Parameters
        ----------
        thetadegs : list
            The circumferential positions where the imperfect bottom edge was
            measured, in degrees.
        u3s : list
            The measured imperfections representing displacements along the
            `X_3` axis :ref:`of the adopted model <figure_conecyl>`.

        """
        self.uneven_bottom_edge.add_measured_u3s(thetadegs, u3s)


    def add_measured_u3s_top_edge(self, thetadegs, u3s):
        r"""Add a measured uneven top edge

        Straightforward method to include measured data about the top edge
        imperfection.

        Adopts the coordinate system of :ref:`this figure <figure_conecyl>`
        when defining the `u_3` displacements for each `\theta` value.

        The edge imperfection that actually goes for each node is a linear
        interpolation of the measured values.

        Parameters
        ----------
        thetadegs : list
            The circumferential positions where the imperfect top edge was
            measured, in degrees.
        u3s : list
            The measured imperfections representing displacements along the
            `X_3` axis :ref:`of the adopted model <figure_conecyl>`.

        """
        self.uneven_top_edge.add_measured_u3s(thetadegs, u3s)


    def add_msi(self, imp_ms='', scaling_factor=1., R_best_fit=None,
                H_measured=None, path=None, use_theta_z_format=True,
                rotatedeg=0., ignore_bot_h=True, ignore_top_h=True,
                stretch_H=False, c0=None,
                m0=None, n0=None, funcnum=None):
        r"""Add a Mid-Surface Imperfection (MSI)

        Also called geometric imperfection.

        If the imperfection is :ref:`already included in the database
        <tutorials_conecylDB>` only the corresponding entry ``imp_ms`` and
        the scaling factor need to be specified.

        If the imperfection is not in the database one can specify the
        full path for the file containing the imperfection, the measured
        radius and height, as detailed below.

        Parameters
        ----------
        imp_ms : str, optional
            Name of the imperfection in the database.
        scaling_factor : float, optional
            Scaling factor applied to the original imperfection amplitude,
            usually to allow imperfection sensitivity studies.
        R_best_fit : float, optional
            Best fit radius obtained with functions :func:`.best_fit_cylinder`
            or :func:`.best_fit_cone`.
        alphadeg_measured : float
            The semi-vertex angle of the measured sample (it is ``0.`` for a
            cylinder).
        H_measured : float, optional
            The total height of the measured test specimen, including eventual
            resin rings at the edges.
        path : str, optional
            Full path to the file containing the imperfection data.
        use_theta_z_format : bool, optional
            If the imperfection file is in the `\theta, Z, imp` format
            instead of the `X, Y, Z` format.
        rotatedeg : float, optional
            Rotation angle in degrees telling how much the imperfection
            pattern should be rotated about the `X_3` (or `Z`) axis.
        ignore_bot_h : float, optional
            Used to ignore nodes from the bottom resin ring. The default value
            ``True`` will use data from the bottom resin ring, if it exists.
        ignore_top_h : float, optional
            Used to ignore nodes from the top resin ring. The default value
            ``True`` will use data from the top resin ring, if it exists.
        stretch_H : bool, optional
            If the measured imperfection does not cover the whole height it
            will be stretched. If ``stretch_H==True``, ``ignore_bot_h`` and
            ``ignore_top_h`` are automatically set to ``False``.
        c0 : str or np.ndarray, optional
            The coefficients representing the imperfection pattern. If
            supplied will overwrite the imperfection data passed using the
            other parameters. For more details see :func:`.calc_c0`.
        m0 : int, optional
            Number of terms along the meridian (`z`) used to obtain ``c0``,
            see :func:`.calc_c0`.
        n0 : int, optional
            Number of terms along the circumference (`\theta`) used to obtain
            ``c0``, see :func:`.calc_c0`.
        funcnum : int, optional
            The base function used to obtain ``c0``, see :func:`.calc_c0`.

        Returns
        -------
        msi : :class:`.MSI` object.

        """
        msi = MSI()
        msi.impconf = self
        msi.imp_ms = imp_ms
        msi.scaling_factor = scaling_factor
        msi.use_theta_z_format = use_theta_z_format
        msi.R_best_fit = R_best_fit
        msi.H_measured = H_measured
        msi.path = path
        msi.rotatedeg = rotatedeg
        msi.ignore_bot_h = ignore_bot_h
        msi.ignore_top_h = ignore_top_h
        msi.stretch_H = stretch_H

        if c0 is not None and not (m0 and n0 and funcnum):
            raise ValueError('Parameter "c0" must be supplied with ' +
                             '"m0", "n0" and "funcnum"')
        elif c0 is not None and m0 and n0 and funcnum:
            if funcnum==1:
                size = 2
            elif funcnum==2:
                size = 2
            elif funcnum==3:
                size = 4
            else:
                raise ValueError('Invalid value for "funcnum"!')
            if isinstance(c0, str):
                if not os.path.isfile(c0):
                    raise ValueError('File {0} not found!'.format(c0))
                else:
                    c0 = np.loadtxt(c0)
                    if c0.ndim==1:
                        if c0.shape[0] != size*m0*n0:
                            raise ValueError(
                                'Invalid "c0" for the given "m0" and "n0"!')
                    else:
                        raise ValueError(
                                'Array for "c0" must be one-dimensional!')
        msi.c0 = c0
        msi.m0 = m0
        msi.n0 = n0
        msi.funcnum = funcnum
        self.msis.append(msi)
        return msi


    def add_pload(self, thetadeg, pt, pltotal, step=1):
        """Add a Perturbation Load

        Parameters
        ----------
        thetadeg : float
            Circumferential position.
        pt : float
            Normalized meridional position.
        pltotal : float
            The magnitude of the perturbation load (it is always applied
            normally to the shell surface).
        step : int
            The step in which the perturbation load will be included. In
            ``step=1`` the load is constant along the analysis while in
            ``step=2`` the load is incremented.

        Returns
        -------
        pload : :class:`.PLoad` object.

        """
        pload = PLoad(thetadeg, pt, pltotal, step)
        pload.impconf = self
        self.ploads.append(pload)
        return pload


    def add_shim_bottom_edge(self, thetadeg, thick, width):
        """Add a Shim to the bottom edge

        Parameters
        ----------
        thetadeg : float
            Circumferential position where the shim starts.
        thick : float
            Thickness of the shim.
        width : float
            Perimetrical width of the shim (along the shell perimeter).

        Returns
        -------
        shim : :class:`.Shim` object.

        """
        shim = Shim(thetadeg, thick, width, self.uneven_bottom_edge)
        return shim


    def add_shim_top_edge(self, thetadeg, thick, width):
        """Add a Shim to the top edge

        Parameters
        ----------
        thetadeg : float
            Circumferential position where the shim starts.
        thick : float
            Thickness of the shim.
        width : float
            Perimetrical width of the shim (along the shell perimeter).

        Returns
        -------
        shim : :class:`.Shim` object.

        """
        shim = Shim(thetadeg, thick, width, self.uneven_top_edge)
        return shim


    def add_ti(self, imp_thick, scaling_factor):
        """Add Thickness Imperfection (TI)

        The imperfection must be already included in the database (:ref:`check
        this tutorial <tutorials_conecylDB>`).

        Parameters
        ----------
        imp_thick : str
            Name of the thickness imperfection in the database.
        scaling_factor : float
            Scaling factor applied to the original imperfection amplitude,
            usually to allow imperfection sensitivity studies.

        Returns
        -------
        ti : :class:`.TI` object.

        """
        ti = TI()
        ti.impconf = self
        ti.imp_thick = imp_thick
        ti.scaling_factor = scaling_factor
        self.tis.append(ti)
        return ti


    def add_cutout(self, thetadeg, pt, d, drill_offset_deg=0.,
                   clearance_factor=0.75):
        r"""Add a cutout

        Parameters
        ----------
        thetadeg : float
            Circumferential position of the dimple.
        pt : float
            Normalized meridional position.
        d : float
            Diameter of the drilling machine.
        drill_offset_deg : float
            Angular offset when the drilling is not normal to the shell
            surface. A positive offset means a positive rotation about the
            `\theta` axis, along the meridional plane.
        clearance_factor : float
            Fraction of the diameter to apply as clearance around the cutout.
            This clearance is partitoned and meshed separately from the rest of
            the cone / cylinder.

        Returns
        -------
        cutout : :class:`.Cutout` object.

        """
        cutout = Cutout(thetadeg, pt, d, drill_offset_deg, clearance_factor)
        cutout.impconf = self
        self.cutouts.append(cutout)
        return cutout


    def rebuild(self):
        self.imperfections = []
        i = -1
        # uneven bottom edge
        ube = self.uneven_bottom_edge
        i += 1
        ube.index = i
        ube.rebuild()
        self.imperfections.append(ube)
        # uneven top edge
        ute = self.uneven_top_edge
        i += 1
        ute.index = i
        ute.rebuild()
        self.imperfections.append(ute)
        # ploads
        for pload in self.ploads:
            i += 1
            pload.index = i
            pload.rebuild()
            self.imperfections.append(pload)
        # dimples
        for sb in self.dimples:
            i += 1
            sb.index = i
            sb.rebuild()
            self.imperfections.append(sb)
        # axisymmetrics
        for ax in self.axisymmetrics:
            i += 1
            ax.index = i
            ax.rebuild()
            self.imperfections.append(ax)
        # linear buckling mode-shaped imperfection (LBMI)
        for lbmi in self.lbmis:
            i += 1
            lbmi.index = i
            lbmi.rebuild()
            self.imperfections.append(lbmi)
        # cutout
        for cutout in self.cutouts:
            i += 1
            cutout.index = i
            cutout.rebuild()
            self.imperfections.append(cutout)
        # mid-surface imperfection (MSI)
        for msi in self.msis:
            i += 1
            msi.index = i
            msi.rebuild()
            self.imperfections.append(msi)
        # thickness imperfection (TI)
        for ti in self.tis:
            i += 1
            ti.index = i
            ti.rebuild()
            self.imperfections.append(ti)
        # name
        if self.rename:
            self.name = ('PLs_%02d_dimples_%02d_axisym_%02d' +\
                        '_lbmis_%02d_MSIs_%02d_TIs_%02d') % \
                        (len(self.ploads), len(self.dimples),
                          len(self.axisymmetrics), len(self.lbmis),
                          len(self.msis), len(self.tis))


    def create(self):
        for imp in self.imperfections:
            valid = True
            for pt in imp.pts:
                if pt<0 or pt>1.:
                    valid = False
                    break
            if imp and valid:
                imp.create()

