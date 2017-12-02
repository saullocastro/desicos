============
Introduction
============

Plug-in for Abaqus
==================

With the aim to provide fast tools for pre- and post-processing tasks
using the finite element software Abaqus, one can
use the user-friendly version of the plug-in with a graphic interface (GUI)
by executing the file ``START_GUI.bat``.

You need Abaqus to be executable by the command line ``abaqus cae``

All (and more) fuctionalities from the GUI can be accessed from the Python IDE
in Abaqus, one short example to create a model would be::

    from desicos.abaqus.conecyl import ConeCyl
    cc = ConeCyl()
    cc.fromDB('huehne_2008_z07')
    cc.create_model()

See the :ref:`desicos.abaqus <module_abaqus>` documentation for more details.

Composite Module
================

Used to calculate laminate properties based on input data of stacking
sequence and lamina properties.

Example::

    from desicos.composite.laminate import read_stack
    from desicos.conecylDB.laminaprops import laminaprops

    laminaprop = laminaprops['degenhardt_2010_IM78552_cocomat']
    lam = read_stack([0, 90, 45, -45], plyt=0.125, laminaprop)

Where ``lam`` is a :class:`desicos.composite.Laminate` object and the
constitutive matrices can be accessed doing ``lam.ABD`` (CLPT) or ``lam.ABDE``
(FSDT). See the :ref:`desicos.composite <module_composite>` documentation
for more details.

Cone / Cylinder Database (Imperfection Database)
================================================

A database containing data from structures studied in previous publications
and the imperfection database for some samples that had their geometric
imperfection and/or thickness imperfections measured. See the
:ref:`desicos.conecylDB <module_conecylDB>` documentation for more details.


Semi-Analytical Tools
=====================

The content of this repository dealing with semi-analytical models
has been moved to:

http://compmech.github.io/compmech/theory/conecyl/index.html

And the modules previously accessed using::

    import desicos

can now be accessed doing::

    import compmech.conecyl

The aim of this module is to provide a fast and free solver for the linear and
non-linear buckling analyses of unstiffened structures in the context of
DESICOS.

Stochastic Tools
================

Developed by Pavel Schor (schor.pavel@gmail.com), this package brings
algorithms to create new imperfection samples based on initially given
samples. This module is contained inside the "stochastic" folder.

More information in:

https://github.com/desicos/desicos/blob/master/doc/source/tutorials/stochastic/firstEx.rst

Known issues:

https://github.com/desicos/desicos/blob/master/doc/source/tutorials/stochastic/overview.rst

Cone Ply Piece Optimization Tool (cppot)
========================================

Developed by Florian Burau (flo.burau@gmail.com) and greatly improved by
Jasper Reichardt (jreichardt91@gmail.com) this package offers a graphic
interface to help the analyst during the manufacturing process of conical
structures by finding the optimal ply piece shapes that should be cut during
the manufacture process.
