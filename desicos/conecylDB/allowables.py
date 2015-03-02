r"""
Lamina Allowables (:mod:`desicos.conecylDB.allowables`)
========================================================

.. currentmodule:: desicos.conecylDB.allowables

This static database stores all entries in the dictionary ``allowables``
which can be imported as::

    from desicos.conecylDB.allowables import allowables

In the dictionary ``allowables`` each entry is stored as a tuple:

- (`{S_{11}}_T`, `{S_{11}}_C`, `{S_{22}}_T`, `{S_{22}}_C`, `S_{12}`, `S_{13}`)

where `C` and `T` stand for compression or tensile allowables. More
entries can be added here if one wishes to update the static database.

"""
#allowables = ( s11t,s11c,s22t,s22c,s12,s13 )
allowables = {
    'desicos_2015_IM78552_DLR':
        (2530.8, -1049., 58.72, -241., 125.43, 125.43),
    'degenhardt_2010_IM78552_cocomat':
        (1741., -855., 29., -283., 98., 90.),
    'degenhardt_2010_IM78552_isa':
        (2440., -1332., 42., -269., 129., 129.),
    'efre_2014':
        (1752.25, -478.22, 40.48, -122.87, 61.53, 61.53),
    'hilburger_2014_AlLi':
        (434., -434., 434., -434., 303., 303.),
            }
