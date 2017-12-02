Python API
==========

The functionalities of the :ref:`GUI <gui>` can all be accessed through
command lines. Although the :ref:`GUI <gui>` is more convenient for small
to middle studies, the ``Python API`` allows the configuration of
big studies where many different parameters can be changed between the
different models.

Creating a Model from the Database
----------------------------------

Example::

    from desicos.abaqus.conecyl import ConeCyl
    cc = ConeCyl()
    cc.fromDB('huehne_2008_z07')
    cc.create_model()

Applying Measured Imperfections using the Imperfection Database
---------------------------------------------------------------

Function :func:`desicos.abaqus.apply_imperfections.translate_nodes_ABAQUS` can
be readily used to apply imperfections from the database in a given finite
element model (cylinder or cone).

.. autofunction:: desicos.abaqus.apply_imperfections.translate_nodes_ABAQUS


Applying Measured Imperfections using Fourier Series
----------------------------------------------------

Assuming the analyst already has the coefficients `\{c_0\}` that will build
the imperfection function, :ref:`as explained here <tutorials_conecylDB>`, these can
be directly used to calculate the imperfection amplitude of each node. The
following example shows how this can be achieved using the module
:mod:`desicos.conecylDB.fit_data` (it must be run inside Abaqus)::

    from desicos.abaqus.apply_imperfections import translate_nodes_ABAQUS_c0

    model_names = mdb.models.keys()

    nodal_translations = None
    scaling_factors = [0.1, 0.25, 0.5, 0.75, 1., 1.25, 1.5, 1.75, 2., 2.5, 3.,
                       3.5, 4.]
    part_name = 'Cylinder'
    for scaling_factor, model_name in zip(scaling_factors, model_names):
        nodal_translations = translate_nodes_ABAQUS_c0(m0, n0, c0,
                funcnum=funcnum, model_name=model_name, part_name=part_name,
                H_model=H_model, H_measured=H_measured, R_model=R_model,
                scaling_factor=scaling_factor,
                nodal_translations=nodal_translations,
                fem_xaxis_from_bot2top=True)

it will translate all the nodes for each model according to the scaling factor
adopted. See the function documentation for more details:

.. autofunction:: desicos.abaqus.apply_imperfections.translate_nodes_ABAQUS_c0




