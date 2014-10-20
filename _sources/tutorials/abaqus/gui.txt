.. _gui:

GUI
===
The user-friendly way to use the plug-in is through the graphic interface.
Just execute the file ``START_GUI.bat``.
You need Abaqus to be executable by the command line ``abaqus cae``
for this to work.

The plug-in for Abaqus looks like this:

.. figure:: ../../../figures/modules/abaqus/gui/fig_01.png

Loading and configuring a model
-------------------------------

Where the ``desicos.conecylDB`` is embedded, and the existing models
easily chosen from the :ref:`Static Database <static_database>` or from the
:ref:`Dynamic database <dynamic_database>`. When the option
``Enter New`` is active, the buttons ``Save`` is activated and
the user may save a new configuration into the database, which can
be deleted afterwards using the ``Delete`` button.

.. figure:: ../../../figures/modules/abaqus/gui/fig_02.png

Geometric parameters easily changed:

.. figure:: ../../../figures/modules/abaqus/gui/fig_03.png

Material properties taken from the database and easily changed. Note that the
:ref:`Dynamic database <dynamic_database>` is implemented here through the use
of the buttons ``Save`` (when the ``Enter New`` option is active)
and ``Delete``.

.. figure:: ../../../figures/modules/abaqus/gui/fig_04.png

The laminate is defined giving a different material and thickness to each
ply or defining only for the first ply when all the others should have the
same material and thicknesses.

.. figure:: ../../../figures/modules/abaqus/gui/fig_05.png

The mesh parameters are defined as shown below, and this data can also be
saved and loaded in the database.

.. figure:: ../../../figures/modules/abaqus/gui/fig_06.png

The analysis parameters are summarized as shown below. After the models
are created the user may change those. This analysis' configuration has
been optimized for the Single Perturbation Load Approach (SPLA).

.. figure:: ../../../figures/modules/abaqus/gui/fig_07.png

The number of output frames can be changed here, allowing some control
in the size of the output files. The ``Request stress output`` checkbox
must be activated if one intents to perform a stress analysis:

.. figure:: ../../../figures/modules/abaqus/gui/fig_08.png

Applying imperfections
----------------------

The perturbation loads can be applied using:

.. figure:: ../../../figures/modules/abaqus/gui/fig_09.png

The geometric dimples using:

.. figure:: ../../../figures/modules/abaqus/gui/fig_10.png

Axisymmetric imperfections:

.. figure:: ../../../figures/modules/abaqus/gui/fig_11.png

Imperfections from Linear buckling modes:

.. figure:: ../../../figures/modules/abaqus/gui/fig_12.png

Cutouts:

.. note:: The cutouts module needs improvement!

.. figure:: ../../../figures/modules/abaqus/gui/fig_13.png

Measured geometric imperfections that represent the normal displacement of
the shell mid-surface can be applied too. This **must** be
applied after creating the study (click on ``Create Study``):

.. figure:: ../../../figures/modules/abaqus/gui/fig_14.png

Similarly, thickness imperfections can be applied. If the study has not yet
been created, click on ``Create Study`` before applying the thickness
imperfections:

.. figure:: ../../../figures/modules/abaqus/gui/fig_15.png

Load imperfections can also be considered:

.. figure:: ../../../figures/modules/abaqus/gui/fig_16.png

Running the analysis
--------------------

It allows running the jobs in the structure of folders used by the plug-in
in order to keep the models organized. You can ``use multiple cpus`` or
use the ``job stopper``, which significantly accelerates the analysis time
by stopping the analysis after buckling.

If the post-buckled pattern have to be studied, it may be better to run one
analysis with the ``job stopper`` activated, obtain the axial compression
level that caused the buckling and then run another analysis disabling the
``job stopper`` in order to achieve the desired post-buckled pattern.

The run log file will be printed on the plug-in screen.

.. figure:: ../../../figures/modules/abaqus/gui/fig_17.png

Post processing
---------------

For all the options you can add the results to an Excel file or
even open the Excel after finished.

The load-shortening curves can be easily plotted:

.. figure:: ../../../figures/modules/abaqus/gui/fig_18.png

Or the knock-down curves:

.. figure:: ../../../figures/modules/abaqus/gui/fig_19.png

Or the stress analysis results:

.. figure:: ../../../figures/modules/abaqus/gui/fig_20.png

An extra options has been added to allow an opened representation of the
cylinder or cone, convinient for publications:

.. figure:: ../../../figures/modules/abaqus/gui/fig_21.png
