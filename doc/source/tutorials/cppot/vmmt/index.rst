Virtual Material Model Tool (VMMT)
==================================

Introduction
------------

The basic problem with laminated cones is the change of the local fiber angle
due to the plane ply parts and the curved cone surface. Because of the curved
surface the fibers are lying on the geodesic path, see Figure 1. There are two
different fiber angles `\Theta_{s1}` and `\Theta_{s2}` at the positions `s_1`
and `s_2`. The variable s is part of the conical coordinate system. Goldfeld
[goldfeld2007]_ describes the local fiber angle `\Theta` as a function of s:

.. math::
    \Theta(s)=arcsin \left( \frac{s_1}{s} \cdot sin(\Theta_1) \right)

This approach is only valid for the path of a single fiber. A new approach is
to describe the local fiber angle by the difference between the angle of the
point of interest and the angle of the starting point of the ply part:

.. math::
    \Theta(\phi)= \Theta_1-(\phi-\phi_1)

This approach can be used for ply parts with a finite width and is the key
formula for this program.

.. figure:: ../../../../figures/modules/cppot/vmmt/fig_01.png
    :width: 700

    Figure 1: Path of Fiber on Cone

The objective of this tool is to calculate the local fiber angle and thickness
of any given point on a laminated cone. To do this the laminate will be
rebuild as a virtual model. Each ply (i) consist of a finite number of parts
(j) with a certain ply angle `\Theta_i` and offset angle `\phi_{i,j}`. These
are called ply-parts. After building the model another algorithm determines in
which ply-parts a given point lies and calculates the local fiber angles and
thickness.

This manual is supposed to explain the VMM-program and every function it
contains. In the ALPHA-Version the program has no GUI and the connection to
ABAQUS is not yet safe.

Coordinate systems
------------------

This program works with three different coordinate systems:
3D-Cartesian: 		Used for the model generation in ABAQUS

.. math::
    X,Y,Z \in [-\infty, +\infty]
2D-Cartesian: 	Used for working in the plane od the unwound cone (Definition
of Lines, Calculation of crossings,...)

.. math::
    x,y \in [-\infty,+\infty]

2D-polar:	Used for working in the plane of the unwound cone (Rotation of
points, Calculation of angles).

.. math::
	\phi \in [0^{\circ}, 360^{\circ}],r \in [0,+\infty]

.. figure:: ../../../../figures/modules/cppot/vmmt/fig_02.png
    :width: 350

    Figure 2: 2D-Polar and Cartesian CSYS

.. figure:: ../../../../figures/modules/cppot/vmmt/fig_03.png
    :width: 700

    Figure 3: Relationship between cone and unwound projection

Building the VMM
----------------

The VMM is the virtual model of the lay-up of the laminated cone. Every ply is
built out of a finite number of parts. Between the parts are no gaps. In the
ALPHA-Version only two different part shapes are available: rectangular and
trapezoidal. When using the rectangular shape the parts overlap each other, by
using the trapezoidal shape this can be avoided.

The VMM calculates the vertices of every ply-part and groups their
2D-cartesian coordinates in lists. After building this model it is possible to
determine on which parts a certain point lies and calculate the local fiber
angle and thickness.

The basic process flow for building the VMM is:
- (1) Get Lay-up Information
  For every ply:
  - (2) Build a prototype part
    For every ply-part:
    - (3) Copy and rotate the prototype part
      Save Layer part to VMM

The three highlighted  tasks are the main tasks of building the VMM:

1. Get Lay-up Information
.........................

This is done by defining a number of variables:

.. math::
    \begin{tabular}{l c r}
        Variable  & Definition & Format \\
        \hline
        E           & Material Paramters, List of floats                 & [E11,E22,G12,nu12,nu21] \\
        $n_{ply}$   & Number of plies, int                               & $i$ \\
        Theta       & Nominal fiber angle of each ply, List of floats    & [$\Theta_1,\Theta_2,\dots,\Theta_i$] \\
        Thick       & Thickness of each ply, List of floats              & [$t_1,t_2,\dots,t_i$] \\
        $phi_{off}$ & Offset-Angle for each ply, List of floats          & [$\phi_{off,1},\phi_{off,2},\dots,\phi_{off,i}$] \\
        Shape       & Defining the part shape of each ply, List of ints  & [$S_1,S_2,\dots,S_i$] \\
        $N_{parts}$ & Number of parts per ply for each ply, List of ints & [$n_1,n_2,\dots,n_i$]
    \end{tabular}

Example::

    E       = [150, 9.08, 5.39, 0.32, 0.02]
    n_ply   = 6
    Theta   = [0.0, 0.0, 60.0, -60.0, 45.0,-45.0]
    Thick   = [1, 1, 1, 1, 1, 1]
    phi_off = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    Shape   = [1, 1, 1, 1, 1, 1]
    N_parts = [10, 10, 10, 10, 10, 10]

2. Build the prototype-part
...........................

Instead of calculating each part of a layer independently only one prototype
part is created and afterwards its vertices are saved, copied and rotated. The
exact shape of the prototype part depends mainly on the size of the cone
`(s_0, s_1, s_2, \alpha)`., the nominal fiber angle of the ply (`\Theta`), the
number of parts per ply (N) and the chosen shape (rectangular, trapezoidal).

The prototype-part is built by the following function::

    Bpart.PPr(Theta, N, S, s0, s1, s2, alpha)

    Theta  nominal fiber angle of ply, float
    N      number of ply parts, int
    S      shape of ply parts, only ‘1’ and ‘2’ are valid
    s0     s-coordinate of upper cone edge
    s1     s-coordinate of starting point of ply part
    s2     s-coordinate of lower cone edge
    alpha  half cone angle

For further explanation of `s_0`, `s_1` and `s_2` see Figure 4.

.. figure:: ../../../../figures/modules/cppot/vmmt/fig_04.png
    :width: 700

    Figure 4: Definition `s_0`, `s_1` and `s_2`

Basically the function creates four lines (L1, L2, L3, L4) in the two
dimensional plane of the unwound cone. Each line is defined by their
functions:

.. math::
    :label: Equation 1

    y=m_i \cdot x+b_i

Where m is the gradient and b the intercept of the function. The gradient of
the L1 is calculated by the nominal fiber angle of the ply `\Theta`:

.. math::
    m_1=tan(\Theta)

Than a first point is defined on L1:

.. math::

    P_0:  (x_0=s_1, y_0=0)

So the intercept of L1 can be calculated by transforming the upper function:

.. math::
    b_1=y_0-m_1 \cdot x_0
    \\
    b_1=0-tan(\Theta) \cdot s_1

The function L1 is shown in Figure 5.

.. figure:: ../../../../figures/modules/cppot/vmmt/fig_05.png
    :width: 350

    Figure 5: Definition of L1

In the next step the crossing between L1 and the circles with radius of `s_0`
and `s_2` are calculated. A circle can be defined by:

.. math::
    R^2=x^2 + y^2

For a crossing of a Line the following formula has to be valid:

.. math::
    0=x^2+y^2-R^2

Now one can insert the function for L1:

.. math::
    0=x^2+(m_1 \cdot x + b_1 )^2-R^2
    \\
    0=(1+m_1^2 ) \cdot x^2 + (2\cdot m_1 \cdot b_1 )\cdot x+(b_1^2-R^2)

Which is basically a quadratic function and can be solved for
`x_{1\backslash2}` by:

.. math::
    :label: Equation 2

    x_{1\backslash2} = \frac{-B \pm \sqrt{B^2 - 4AC}}{2A}

In this case the three variables are defined as:

.. math::
    A = 1 + m_1^2
    \\
    B = 2 \cdot m_1 \cdot b_1
    \\
    C = b_1^2 - R^2

Naturally there are three different types of solutions for this equation. They
can be easily distinguished by the value of the root argument:

- (1) `B^2-4AC<0`: The solution is complex and the line does not touch or cut
  the circle
- (2) `B^2-4AC=0`: The solution is one real number and the line touches the
  circle at one point
- (3) `B^2-4AC>0`: The solution consists out of two real numbers and the line
  cuts the circle at two different points

For the first line and the outer radius `s_2` there must be two solutions,
because `s_1` is smaller than `s_2`. For some combinations of `s_1`, `s_0` and
`\Theta` it is possible that the L1 is not cutting the inner circle of `s_0`.
The Prototype-function uses for the construction of the first Line and Points
only the positive Solution of :ref:`Equation 2`.

P1 and P2 are the crossing point of L1 and the circle `s_0` respectively s_2,
see Figure 6.

.. figure:: ../../../../figures/modules/cppot/vmmt/fig_06.png
    :width: 350

    Figure 6: Definition of P0, P1 and P2

The next step is to calculate the point P3. Therefore the angle of a single
ply part is calculated by:

.. math::
    \phi_{ply-part} = \frac{\phi_{cone}}{N}
    \\
    \phi_{cone} = 360° \cdot sin(\alpha)

In which N is the number of ply-parts in this ply and \alpha the half-cone
angle.  Then the coordinates of P2 are transformed to a polar form:

.. math::
    P2 : (x_2, y_2) \rightarrow (r_2, \phi_2)

And add the angle `\phi_{ply-part}` to `\phi_2` then transformed backwards, see
also Figure 7.

.. math::
    P3 : (r_2, \phi_2 + \phi_{ply-part}) \ rightarrow (x_3, y_3)

.. figure:: ../../../../figures/modules/cppot/vmmt/fig_07.png
    :width: 350

    Figure 7: Creation of P3

The gradient of L3 and also the position of P4 depends on the chosen shape of
the ply part. For a rectangular the gradient m_3 is equal to m_1 and so L3 is
defined as:

.. math::
    y = m_1 \cdot x + (y_3 - m_1 \cdot x_3)

And P4 is the crossing point of L3 and the circle `s_0`.

If the shape is trapezoidal the point P4 is calculated by rotating P1 by
`\phi_{ply-part}` analogous to the creation of P3.

By now we have two points on each circle, but the connection line between P2
and P3 lies inside the circle `s_2`. To correct this error P2 and P3 have to
be moved. This is done by defining that L2 must be orthogonally to L1:

.. math::
    m_2 = tan(\Theta+90^{\circ})

The intercept `b_2` is then changed until L2 does not cut or touch the circle
`s_2`. The procedure for P1, P4 and L4 is equivalent, see Figure 8.


.. figure:: ../../../../figures/modules/cppot/vmmt/fig_08.png
    :width: 350

    Figure 8: Definition of L2 and L4

In the end the prototype is defined by the points P1, P2, P3, P4 and the
function ``Bpart.PPr()`` returns these points in the following shape::

    PPr = [x1, y1, x2, y2, x3, y3, x4, y4]

In Figure 9 one can see the finished prototype part.

.. figure:: ../../../../figures/modules/cppot/vmmt/fig_09.png
    :width: 350

    Figure 9: Prototype-part

Copy and rotate the prototype-part
----------------------------------

After the prototype-part is finished the vertices P1 to P4 are rotated around
the origin of the CSYS to achieve a full coverage of the area of the unwound
cone. This is achieved by the function ``Bpart.Pro()``::

    Bpart.PRo(PPr, phi_off, Theta, N, alpha)

The function needs different inputs::

    PPr      Cartesian Coordinates of the Prototype Part, List of 8 floats
    phi_off  Offset angle of ply in degree, float
    Theta    Nominal fiber angle of ply in degree, float
    N        Number of ply-parts, int
    Alpha    Half cone angle in degree, float

The first ply part is placed by converting the coordinates of the prototype
points from Cartesian to polar form and add each to the angle of the point
phi_off:

.. math::
    \phi_{1,1}=\phi_{Prototype,P1}+\phi_{off}
    \\
    \phi_{1,2}=\phi_{Prototype,P2}+\phi_{off}
    \\
    \phi_{1,3}=\phi_{Prototype,P3}+\phi_{off}
    \\
    \phi_{1,4}=\phi_{Prototype,P4}+\phi_{off}

In Figure 10 is an example shown. The red trapez is the first part of the
ply-parts.

The points of the other ply-parts are calculated by adding `k \cdot
\phi_{ply-part}` to `\phi_{1,1}`, `\phi_{1,2}`, `\phi_{1,3}` and `\phi_{1,4}`.
K is the running number of the ply parts.

.. math::
    \phi_{k+1,1}=\phi_{1,1}+k \cdot \phi_{ply-part}
    \\
    \phi_{k+1,2}=\phi_{1,2}+k \cdot \phi_{ply-part}
    \\
    \phi_{k+1,3}=\phi_{1,3}+k \cdot \phi_{ply-part}
    \\
    \phi_{k+1,4}=\phi_{1,4}+k \cdot \phi_{ply-part}

In Figure 10 this shown by the blue trapez.

.. figure:: ../../../../figures/modules/cppot/vmmt/fig_10.png
    :width: 700

    Figure 10: Definition of `\phi_{off}` and `\phi_{ply-part}`

This procedure will go on until the whole area of the unwound cone is covered. This is checked by two simple if-statements:
- if: `\phi_{k,n} > \phi_{cone}`,for all `n \in [0,4],k \in [0,N]`
- if: `\phi_{k,n} < 0^{\circ}`,for all `n \in [0,4],k \in [0,N]`

.. figure:: ../../../../figures/modules/cppot/vmmt/fig_11.png
    :width: 700

    Figure 11: Complete ply

In Figure 11 is the complete ply shown.

For the other plies the steps (2.) and (3.) are repeated.

Finding the local fiber angle and thickness
-------------------------------------------

To investigate the effects of the changing fiber angle and thickness one has
to find a method to find out in which parts a certain point lies. This problem
is known as the point in polygon problem. There are several different
approaches to solve this problem. This program uses a simple algorithm known
as the Angle Summation Method. If a point lies inside of a convex polygon the
sum of the inner angles between connecting lines of the vertices and the point
is equal to 360°. If the point lies on one of the edges of the polygon the sum
is equal to 180° and if it is outside of the polygon the sum is 0°. For a
better explanation see Figure (TODO)

Basically one has to calculate the angle of triangle defined by three points
or between two vectors connecting the given point and two neighboring vertices
of the polygon. It is known that:

.. math::
    \vec{a} \cdot \vec{b} = \|\vec{a}\|\|\vec{b}\|cos(\angle(\vec{a},\vec{b}))
    \\
    \angle(\vec{a}, \vec{b})=arccos \left(
        \frac{\vec{a} \cdot \vec{b}}{\|\vec{a}\|\|\vec{b}\|} \right)

The complicated part of this function was to make sure the angles are
correctly summed up and are using the same direction.
