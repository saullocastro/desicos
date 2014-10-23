r"""
===================================================
ConeCyl (:mod:`desicos.abaqus.conecyl`)
===================================================

.. currentmodule:: desicos.abaqus.conecyl

Cone/Cylinder Model
=====================

Figure 1 provides a schematic view of the typical model created using this
module. Two coordinate systems are defined: one rectangular with axes `X_1`,
`X_2`, `X_3` and a cylindrical with axes `R`, `Th`, `Z`.

.. _figure_conecyl:

.. figure:: ../../../figures/modules/abaqus/conecyl/conecyl_model.png
    :width: 400

    Figure 1: Cone/Cylinder Model

The complexity of the actual model created in Abaqus goes beyond the
simplification above

Boundary Conditions
===================

Based on the coordinate systems shown in Figure 1 the following boundary
condition parameters can be controlled:

- constraint for radial and circumferential displacement (`u_R` and `v`) at
  the bottom and top edges
- simply supported or clamped bottom and top edges, consisting in the
  rotational constraint along the meridional coordinate, called `\phi_x`.
- use of resin rings as described in :ref:`the next section <resin_rings>`
- the use of distributed or concentrated load at the top edge will be
  automatically determined depending on the attributes of the current
  :class:`.ConeCyl` object
- application of shims at the top edge as detailed in
  :meth:`.ImpConf.add_shim_top_edge`, following this example::

    from desicos.abaqus.conecyl import ConeCyl

    cc = ConeCyl()
    cc.from_DB('castro_2014_c02')
    cc.impconf.add_shim(thetadeg, thick, width)

- application of uneven top edges as detailed in
  :meth:`.UnevenTopEdge.add_measured_u3s`, following this example::

    thetadegs = [0.0, 22.5, 45.0, 67.5, 90.0, 112.5, 135.0, 157.5, 180.0,
                 202.5, 225.0, 247.5, 270.0, 292.5, 315.0, 337.5, 360.0]
    u3s = [0.0762, 0.0508, 0.1270, 0.0000, 0.0000, 0.0762, 0.2794, 0.1778,
           0.0000, 0.0000, 0.0762, 0.0000, 0.1016, 0.2032, 0.0381, 0.0000,
           0.0762]
    cc.impconf.add_measured_u3s_top_edge(thetadegs, u3s)

.. _resin_rings:

Resin Rings
===========

When resin rings are used the actual boundary condition will be determined by
the parameters defining the resin rings (cf. Figure 2), and therefore no clamped conditions
will be applied in the shell edges.

.. figure:: ../../../figures/modules/abaqus/conecyl/resin_rings.png
    :width: 400

    Figure 2: Resin Rings

Defining resin rings can be done following the example below, where each
attribute is detailed in the :class:`.ConeCyl` class description::

    from desicos.abaqus.conecyl import ConeCyl

    cc = Conecyl()
    cc.from_DB('castro_2014_c02')
    cc.resin_add_BIR = False
    cc.resin_add_BOR = True
    cc.resin_add_TIR = False
    cc.resin_add_TOR = True
    cc.resin_E = 2454.5336
    cc.resin_nu = 0.3
    cc.resin_numel = 3
    cc.resin_bot_h = 25.4
    cc.resin_top_h = 25.4
    cc.resin_bir_w1 = 25.4
    cc.resin_bir_w2 = 25.4
    cc.resin_bor_w1 = 25.4
    cc.resin_bor_w2 = 25.4
    cc.resin_tir_w1 = 25.4
    cc.resin_tir_w2 = 25.4
    cc.resin_tor_w1 = 25.4
    cc.resin_tor_w2 = 25.4

The ConeCyl Class
=================

.. automodule:: desicos.abaqus.conecyl.conecyl
    :members:

"""
from conecyl import *

