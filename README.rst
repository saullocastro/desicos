=======
DESICOS
=======

Tools developed in the context of the European Project DESICOS 
(http://www.desicos.eu).

Documentation
-------------

Please, access the documentation here:

http://desicos.github.io/desicos/


Plug-in for Abaqus
------------------

With the aim to provide fast tools for pre- and post-processing tasks
using the finite element software Abaqus, one can 
use the user-friendly version of the plug-in with a graphic interface
by executing the file `START_GUI.bat`.

You need Abaqus to be executable by the command line `abaqus cae`

To access all and more fuctionalities from the Python IDE in Abaqus::

    >>> from desicos.abaqus.conecyl import ConeCyl
    >>> cc = ConeCyl()
    >>> cc.fromDB('huehne_2008_z07')
    >>> cc.create_model()

Semi-analytical tools
---------------------

The content of this repository dealing with semi-analytical models 
has been moved to: 

https://github.com/compmech/compmech/blob/master/README.rst

And the modules previously accessed using::

    import desicos

can now be accessed doing::

    import compmech.conecyl

The aim of this module is to provide a fast and free solver for the linear and
non-linear buckling problems being investigated in the context of DESICOS.

Stochastic tools
----------------

Developed by Pavel Schor (schor.pavel@gmail.com), this package brings
algorithms to create new imperfection data based on initially given samples.
This module is contained inside the "stochastic" folder.

More information in:

https://github.com/desicos/desicos/blob/master/doc/source/firstEx.rst

Known issues:

https://github.com/desicos/desicos/blob/master/doc/source/overview.rst

Licensing
---------

The new BSD License (`see the LICENSE file for details 
<https://raw.github.com/desicos/desicos/master/LICENSE>`_)
covers all files in the compmech repository unless stated otherwise.
