.. _process_raw_files:

Processing Raw Files
====================

Mid-Surface Imperfections (MSI)
-------------------------------

The raw files obtained from measured geometric imperfections usually come
with three columns::

    x1 y1 z1
    x2 y2 z2
    ...
    xn yn zn

and the recommended procedure to convert them to the "`\theta` `z` `imp`"
format is the function :func:`.xyz2thetazimp`, exemplified below::

   >>> from desicos.conecylDB.read_write import xyz2thetazimp

   >>> xyz2thetazimp(path, alphadeg_measured, R_measured, H_measured,
                     fmt='%1.8f')

It will create an output file with a prefix ``"_theta_z_imp.txt"`` where the
imperfection data is stored in the format::

    theta1 z1 imp1
    theta2 z2 imp2
    ...
    thetan zn impn

where ``thetai``, ``zi`` and ``impi`` are the `\theta` and `z` coordinates
and `imp` represents the imperfection at this coordinate for the `i^{th}`
point.

.. note:: It is also possible to use function :func:`.xyz2thetazimp` in other
          ways, as detailed in the corresponding documentation

Thickness Imperfections (TI)
----------------------------

Similarly to the mid-surface imperfections, the thickness imperfections
may come in a file with the format::

   x1 y1 z1 thick1
   x2 y2 z2 thick2
   ...
   xn yn zn thickn

and the recommended procedure to convert them to the "`\theta` `z` `thick`"
format is function :func:`.xyzthick2thetazthick`::

   >>> from desicos.conecylDB.read_write import xyzthick2thetazthick

   >>> xyzthick2thetazthick(path, alphadeg_measured, R_measured, H_measured,
                            fmt='%1.8f')

.. note:: It is possible to use function :func:`xyzthick2thetazthick``
          in other ways, as detailed in the corresponding documentation

