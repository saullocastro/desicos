"""
===========================================
Stringers (:mod:`desicos.abaqus.stringers`)
===========================================

.. currentmodule: desicos.abaqus.stringers

All stringer classes are grouped in this module.

Each stringer has a method ``create()``, that will be called from
:meth:`desicos.abaqus.conecyl.create_model()`. Below there is an example about
how to add the the blade type of stringers in a :class:`.ConeCyl` model::

    import numpy as np

    from desicos.abaqus.conecyl import ConeCyl

    cc = ConeCyl()

    cc.from_DB('huehne_2008_z07')

    stack = [0, 0, 90, 90, -45, +45]
    laminaprop = (142.5e3, 8.7e3, 0.28, 5.1e3, 5.1e3, 5.1e3)
    laminaprops = [laminaprop for _ in stack]
    plyts = [0.125 for _ in stack]

    for thetadeg in np.linspace(0, 360, 12, endpoint=False):
        cc.stringerconf.add_blade_composite(thetadeg=thetadeg, wbot=25, wtop=15,
                stack=stack, plyts=plyts, laminaprops=laminaprops, numel_flange=5)
    cc.create_model()


Stringers Configuration (:mod:`desicos.abaqus.stringers.stringerconf`)
----------------------------------------------------------------------
.. automodule:: desicos.abaqus.stringers.stringerconf
    :members:

Blade Stringers (:mod:`desicos.abaqus.stringers.blade`)
-------------------------------------------------------
.. automodule:: desicos.abaqus.stringers.blade
    :members:

"""
from __future__ import absolute_import

from .stringer import Stringer
from .stringerconf import StringerConf
from .blade import BladeComposite, BladeIsotropic
