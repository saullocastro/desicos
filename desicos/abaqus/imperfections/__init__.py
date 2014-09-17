"""
=======================================================
Imperfections (:mod:`desicos.abaqus.imperfections`)
=======================================================

.. currentmodule: desicos.abaqus.imperfections

Embodies all imperfections that will be included in the finite element
model.

The imperfections are grouped in one imperfection configuration
``ImpConf`` which knows how to add each imperfection type. In the example
below a perturbation load and an axisymmetric imperfection are included.
Note that the perturbation load is added in step 1 while the axial load in
step 2, meaning that the perturbation load will kept a constant load while
the axial load will be incremented along the non-linear analysis (see
detailed description in :class:`.ConeCyl`)::

    from desicos.abaqus.conecyl import ConeCyl

    cc = ConeCyl()
    cc.from_DB('huehne_2008_z07')
    cc.impconf.add_pload(pt=0.5, pltotal=4., step=1)
    cc.impconf.add_axisymmetric(pt=0.2, b=50, wb=1.)
    cc.axial_load = 100000
    cc.axial_step = 2
    cc.create_model()

The finite element model is created in two steps:
    - creating all the partitions at the moment the mesh is generated
    - creating all the imperfections in a later step

Each imperfection has a method ``rebuild()``, which must update two key
properties ``thetadegs`` and ``pts``, which are lists containing the necessary
data for creating the partitions correctly.

Additionaly, each imperfection has a method ``create()``, which creates the
imperfection itself, looking for the right nodes that should be translated and
so forth.

Invalid imperfections are identified when ``pt < 0.`` or ``pt > 1.``,
which are just ignored and an error message is printed.

Imperfection Configuration (:mod:`desicos.abaqus.imperfections.impconf`)
----------------------------------------------------------------------------
.. automodule:: desicos.abaqus.imperfections.impconf
    :members:

Imperfection (:mod:`desicos.abaqus.imperfections.imperfection`)
-------------------------------------------------------------------
.. automodule:: desicos.abaqus.imperfections.imperfection
    :members:

Axisymmetric (:mod:`desicos.abaqus.imperfections.axisymmetric`)
-------------------------------------------------------------------
.. automodule:: desicos.abaqus.imperfections.axisymmetric
    :members:

Dimple (:mod:`desicos.abaqus.imperfections.dimple`)
-------------------------------------------------------------------
.. automodule:: desicos.abaqus.imperfections.dimple
    :members:

LBMI (:mod:`desicos.abaqus.imperfections.lbmi`)
-------------------------------------------------------------------
.. automodule:: desicos.abaqus.imperfections.lbmi
    :members:

Geometric Imperfection (:mod:`desicos.abaqus.imperfections.msi`)
-------------------------------------------------------------------
.. automodule:: desicos.abaqus.imperfections.msi
    :members:

Perturbation Load (:mod:`desicos.abaqus.imperfections.pload`)
-------------------------------------------------------------------
.. automodule:: desicos.abaqus.imperfections.pload
    :members:

Thickness Imperfection (:mod:`desicos.abaqus.imperfections.ti`)
-------------------------------------------------------------------
.. automodule:: desicos.abaqus.imperfections.ti
    :members:

Uneven Edges (:mod:`desicos.abaqus.imperfections.uneven_edges`)
-------------------------------------------------------------------
.. automodule:: desicos.abaqus.imperfections.uneven_edges
    :members:

"""
from impconf import ImpConf
from imperfection import Imperfection
import axisymmetric
import dimple
import pload
import lbmi
import msi
import ti
import uneven_edges
