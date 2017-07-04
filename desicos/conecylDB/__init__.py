r"""
===================================================
Cone / Cylinder DataBase (:mod:`desicos.conecylDB`)
===================================================

.. currentmodule:: desicos.conecylDB

The ``desicos.conecylDB`` module includes all the information about cones
and cylinders required to reproduce structures that were investigated
by many publications and in the context of DESICOS.

It also includes the tools necessary to work with the Imperfection
DataBase.  Unfortunately, the files composing this database cannot be made
available with the repository, but all the tools required to post process
an imperfection file had been made available.

.. automodule:: desicos.conecylDB.conecylDB
    :members:

.. automodule:: desicos.conecylDB.ccs
    :members:

.. automodule:: desicos.conecylDB.laminaprops
    :members:

.. automodule:: desicos.conecylDB.allowables
    :members:

.. automodule:: desicos.conecylDB.fit_data
    :members:

.. automodule:: desicos.conecylDB.interpolate
    :members:

.. automodule:: desicos.conecylDB.read_write
    :members:

"""
from __future__ import absolute_import
from .conecylDB import *
