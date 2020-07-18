=======
DESICOS
=======

Tools developed in the context of the 7th European Framework Project DESICOS 
(https://cordis.europa.eu/project/id/282522).

Documentation
-------------

Please, access the documentation here:

http://saullocastro.github.io/desicos/


DESICOS Plug-in for Abaqus
---------------------------

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
    
    
DESICOS Cone Ply Piece Optimization Tool
-----------------------------------------

Finds the optimal ply piece shape for laminated cones. There are four different tools that can be used:

The Input-Tool
The Cone Geometry-Tool
The Plot Ply Piece-Tool
The Evaluation-Tool


Semi-analytical tools
---------------------

The content of this repository dealing with semi-analytical models 
has been moved to: 

https://github.com/saullocastro/compmech/blob/master/README.rst

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


Licensing
---------

The new BSD License (`see the LICENSE file for details 
<https://raw.github.com/saullocastro/desicos/master/LICENSE>`_)
covers all files in the compmech repository unless stated otherwise.
