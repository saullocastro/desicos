r"""
===================================================
Abaqus plug-in (:mod:`desicos.abaqus`)
===================================================

.. currentmodule:: desicos.abaqus

The ``desicos.abaqus`` module includes the DESICOS plug-in for Abaqus
whose functionalities can be used in two main ways, using the Graphic
User Interface (GUI) or using the Python API.


GUI
===
The user-friendly way to use the plug-in is through the graphic interface.
Just execute the file ``START_GUI.bat``.
You need Abaqus to be executable by the command line ``abaqus cae``
for this to work.


Python API
==========

You can access all and more fuctionalities from the Python IDE in Abaqus::

    >>> from desicos.abaqus.conecyl import ConeCyl
    >>> cc = ConeCyl()
    >>> cc.fromDB('huehne_2008_z07')
    >>> cc.create_model()
"""
