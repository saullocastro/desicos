.. _process_raw_files:

Processing Geometric Imperfection Data
======================================

This part of the turorial will explain in a step-by-step example how one
can use the :ref:`developed modules <modules>` to post-process measured
imperfection data.

The following steps will be discussed:

- raw data from measurement system

- finding

Raw Data from Mesurement Systems
--------------------------------

The raw files obtained from measured geometric imperfections usually come
with three columns::

    x1 y1 z1
    x2 y2 z2
    ...
    xn yn zn


The `following sample
<https://raw.githubusercontent.com/desicos/desicos/master/doc/source/tutorials/conecylDB/processing_measured_imp_data/sample.txt>`_
has been used to illustrate this tutorial (first 10 lines shown below):

.. literalinclude:: sample.txt
    :lines: 1-10

The following script is used to plot the sample with the imperfection
exagerated. Note that :ref:`best_fit_raw_data.py <best_fit_raw_data>` has to
be executed before.

``plot_sample_3d.py``

.. literalinclude:: plot_sample_3d.py

giving:

.. figure:: plot_sample_3d.png


In order to transform the raw data to the :ref:`finite element coordinate
system <figure_conecyl>`, the recommended procedure is the function
:func:`.xyz2thetazimp`, exemplified below. This function converts the "`x` `y`
`z`" data to a to convert them to a "`\theta` `z` `imp`" format. This function
is a wrapper that calls funcion :func:`.best_fit_cylinder` or
:func:`.best_fit_cone`, where the right coordinate transformation is
calculated.

.. _best_fit_raw_data:

``best_fit_raw_data.py``

.. literalinclude:: best_fit_raw_data.py

It will create an output file with a prefix ``"_theta_z_imp.txt"`` where the
imperfection data is stored in the format::

    theta1 z1 imp1
    theta2 z2 imp2
    ...
    thetan zn impn

where ``thetai`` and ``zi`` are the coordinates `\theta` and `z`, while
``impi`` represents the imperfection amplitude at this coordinate. An example
of the transformed imperfection data is given below (first 10 lines), and
`the full output is given here
<https://raw.githubusercontent.com/desicos/desicos/master/doc/source/tutorials/conecylDB/processing_measured_imp_data/sample_theta_z_imp.txt>`_:

.. literalinclude:: sample_theta_z_imp.txt
    :lines: 1-10

.. note:: It is also possible to use :func:`.xyz2thetazimp` in other
          ways, as detailed in the function's documentation

The transformed data can also be visualized in the 3-D domain, which was
accomplished using the following script:

``plot_sample_3d_tranformed.py``

.. literalinclude:: plot_sample_3d_transformed.py

giving:

.. figure:: plot_sample_3d_transformed.png

Note that due to the axisymmetry it may happen that the final result has some
offset rotation. For this reason the interpolation routines that will be
discussed in the next sessions of this tutorial include a ``rotatedeg``
parameter that the analyst should use in order to correct this angular offset.


Inverse-Weighted Interpolation
------------------------------

Function :func:`.iterp_theta_z_imp` is the one used to interpolate the
measured data into a given mesh. In the example below the mesh creates using
:func:`np.meshgrid` is used for plotting purposes. Note that the an angular
offset of ``-88.5`` degrees was used in order to adjust the imperfection.

``interpolate_inv_weighted.py``

.. literalinclude:: interpolate_inv_weighted.py

An the generated data can be plotted using the following code:

``plot_inv_weighted.py``

.. literalinclude:: plot_inv_weighted.py

giving:

.. figure:: plot_inv_weighted.png
    :width: 400


Half-Cosine Function
--------------------

Function :func:`.calc_c0` is used to interpolate the measured data using
Fourier series. The half-cosine function corresponds to the parameter
``funcnum = 2``, as can be seen in the function's documentation.

The following script was used to calculate the coefficients `\{c_0\}`. Note
how the angular offset is applied using the ``rotatedeg`` parameter:

``interpolate_half_cosine.py``

.. literalinclude:: interpolate_half_cosine.py

and the following routine was used to plot the corresponding imperfection
field:

``plot_half_cosine.py``

.. literalinclude:: plot_half_cosine.py

giving:

.. figure:: plot_half_cosine.png
    :width: 400


The relatively poor correlation between the half-cosine and the
inverse_weighted is primarily due to the reduced amount of measured data used
for this tutorial. Using real imperfection data the correlation is much
closer, as shown in the additional examples below.

Additional Examples using the Half-Cosine Function
--------------------------------------------------

The example below shows how to use this function and then plot the
displacement patterns using different approximation levels:

``half_cosine_additional_example.py``

.. literalinclude:: half_cosine_additional_example.py


which will result in the following figures for ``funcnum=1``:

`m_0=20`, `n_0=30`:

.. figure:: ..\..\..\..\figures\modules\conecylDB\fit_data\fw0_f1_z25_m_020_n_030.png

`m_0=30`, `n_0=45`:

.. figure:: ..\..\..\..\figures\modules\conecylDB\fit_data\fw0_f1_z25_m_030_n_045.png

`m_0=40`, `n_0=60`:

.. figure:: ..\..\..\..\figures\modules\conecylDB\fit_data\fw0_f1_z25_m_040_n_060.png

`m_0=50`, `n_0=75`:

.. figure:: ..\..\..\..\figures\modules\conecylDB\fit_data\fw0_f1_z25_m_050_n_075.png

and for ``funcnum=2``:

`m_0=20`, `n_0=30`:

.. figure:: ..\..\..\..\figures\modules\conecylDB\fit_data\fw0_f2_z25_m_020_n_030.png

`m_0=30`, `n_0=45`:

.. figure:: ..\..\..\..\figures\modules\conecylDB\fit_data\fw0_f2_z25_m_030_n_045.png

`m_0=40`, `n_0=60`:

.. figure:: ..\..\..\..\figures\modules\conecylDB\fit_data\fw0_f2_z25_m_040_n_060.png

`m_0=50`, `n_0=75`:

.. figure:: ..\..\..\..\figures\modules\conecylDB\fit_data\fw0_f2_z25_m_050_n_075.png

It can be seen how the `w_0` function approximates the measured imperfection
pattern with the increase of `m_0` and `m_0`. The measured imperfection
pattern is shown below, and it was plotted after performing the
inverse-weighted interpolation already described.

.. figure:: ..\..\..\..\figures\modules\conecylDB\fit_data\measured_z25.png

Comparing the results using ``funcnum=1`` and ``funcnum=2``, one see that
the latter approaches closer the real measurements, since it relaxes the
condition `w_0 = 0` at the edges.


Processing Measured Thickness Imperfection Data
===============================================

The procedure described for geometric imperfections is also applicable for
thickness imperfections. The measured imperfection data usually
comes in a 4 columns format where the thickness measurement is given for each
spatial position: `x_i`, `y_i`, `z_i`::

   x1 y1 z1 thick1
   x2 y2 z2 thick2
   ...
   xn yn zn thickn

The recommended procedure to transform the raw data to the :ref:`finite
element coordinate system <figure_conecyl>` is the function
:func:`.xyzthick2thetazthick`, that also calls internally the
:func:`.best_fit_cylinder` or the :func:`.best_fit_cone` routines::

   >>> from desicos.conecylDB.read_write import xyzthick2thetazthick

   >>> xyzthick2thetazthick(path, alphadeg_measured, R_measured, H_measured,
                            fmt='%1.8f')

.. note:: It is possible to use function :func:`xyzthick2thetazthick``
          in other ways, as detailed in the corresponding documentation

