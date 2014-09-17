.. _dynamic_database:

Dynamic Database
================

One can store or delete entries in the dynamic database. This database
will be created in the path stored in::

    localDB_path.json

Two functions are used to work on this database:
:func:`desicos.conecylDB.conecylDB.save` and
:func:`desicos.conecylDB.conecylDB.delete`.  The following sections bring
examples about how to use these functions.

Creating a material
-------------------

Example::

    from desicos.conecylDB import save

    laminaprop = (125.774e3, 10.03e3, 0.271, 5.555e3, 5.555e3, 3.4e3)
    save('laminaprops', 'new_material', laminaprop)

Creating an allowable
---------------------

Example::

    from desicos.conecylDB import save

    allowables = (1741., -855., 29., -283., 98., 90.)
    save('allowables', 'new_allowable', allowables)

Creating a cone / cylinder sample
---------------------------------

Example::

    cc = {'r': 250.,
          'h': 510.,
          'plyt': 0.125,
          'laminapropKey',}

    save('cc', 'new_sample', cc)

The following sections explain the common steps required to include a
file in the database.

Deleting
--------

Example::

    from desicos.conecylDB import delete

    delete('ccs', 'new_conecyl')
    delete('laminaprops', 'new_material')
    delete('allowables', 'new_allowable')
