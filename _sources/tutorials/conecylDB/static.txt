.. _static_database:

Static Databases
================

Since many partners may contribute to this database, a list of all the
available databases is included in::

    databases.json

Data for the structures, material properties and allowables are stored
respectively in::

    ccs.py
    laminaprops.py
    allowables.py

ccs.py
------

These are static components that one can change in order to add
more samples. In ``ccs.py`` the ``ccs`` dictionary contains all the samples
in a format like::

    'zimmermann_1992_z33': {
        'msi': 'zimmermann_1992_z33',
        'r': 250.,
        'h': 510.,
        'elem_type':'S4R',
        'numel_r': 240,
        'plyt':0.125,
        'laminapropKey': 'geier_2002',
        'allowablesKey': 'degenhardt_2010_IM78552_cocomat',
        'stack': [0,0,19,-19,37,-37,45,-45,51,-51],
        'axial_displ': 1.,
        'ploads': [1, 10, 20, 30, 40, 46.5, 70, 90],
        'database':'dlr',

where ``database`` indicates from which database the sample belongs to. When
geometric imperfection measurements are available for a sample, the key
``msi`` is defined with the name of the imperfection file.
When thickness imperfections are available, the key ``ti`` is defined, as in
the example below::

    'degenhardt_2010_z15': {
        'msi': 'degenhardt_2010_z15',
        'ti': 'degenhardt_2010_z15',
        'r': 250.27,
        'h': 500.,
        'elem_type':'S4R',
        'numel_r': 240,
        'plyt':0.11575,
        'laminapropKey': 'degenhardt_2010_IM78552_cocomat',
        'allowablesKey': 'degenhardt_2010_IM78552_cocomat',
        'stack': [24,-24,41,-41],
        'axial_displ': 1.,
        'ploads': [1,2,3,4,5,10],
        'database':'dlr',
        },

The material properties are given by names stored in the ``laminapropKey``
key. If a different material is used for each ply, then a
``laminapropKeys`` key should be defined, containing a ``list`` with
a ``laminapropKey`` for each ply, and the length of this list must
be the same as the length of the stacking sequence, given by the ``stack``
key. If the plies have the same thickness, only the ``plyt`` key has to
be defined, otherwise a key ``plyts`` has to defined with a list of
ply thicknesses, with the same length as ``stack``. For the ``allowablesKey``
the same explanation of the ``laminapropKey`` applies.

laminaprops.py
--------------

Keeps the material properties, the dictionary ``laminaprops`` has
in each key a ``tuple`` or ``list`` with the properties::

    (E11, E22, nu12, G12, G13, G23)

for orthotropic materials or::

    (E11, E11, nu)

for isotropic materials. Each key in ``laminaprops`` corresponds to a
``laminapropKey`` in the ``ccs.py``.

allowables.py
-------------

Keeps the allowables' for the materials in the dictionary ``allowables``,
where each key corresponds to a ``allowablesKey`` in ``ccs.py``. Each value
is a ``tuple`` or ``list`` with::

    (S11t, S11c, S22t, S22c, S12, S13)
