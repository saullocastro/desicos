from __future__ import absolute_import

class StringerConf(object):
    """Stringer configuration class

    """
    def __init__(self):
        self.conecyl = None
        self.stringers = []


    def add_blade_composite(self, thetadeg, wbot, wtop, stack, plyts,
            laminaprops, numel_flange=4):
        """Add a composite blade stringer

        Parameters
        ----------
        thetadeg : float
            Circumferential position in degrees.
        wbot : float
            Flange width at the bottom edge.
        wtop : float
            Flange width at the top edge.
        stack : list
            Laminate stacking sequence.
        plyts : list
            Ply thicknesses.
        laminaprops : list
            The properties for each lamina.
        numel_flange : int, optional
            The number of elements along the width.

        """
        from blade import BladeComposite

        stringer = BladeComposite(thetadeg=thetadeg, wbot=wbot, wtop=wtop,
                stack=stack, plyts=plyts, laminaprops=laminaprops,
                numel_flange=numel_flange)
        stringer.stringerconf = self
        self.stringers.append(stringer)


    def add_blade_isotropic(self, thetadeg, wbot, wtop, h, E, nu,
                            numel_flange=4):
        """Add an isotropic blade stringer

        Implemented as a special case of the composite stringer for
        isotropic material.

        Parameters
        ----------
        thetadeg : float
            Circumferential position in degrees.
        wbot : float
            Flange width at the bottom edge.
        wtop : float
            Flange width at the top edge.
        h : float
            Stringer thickness
        E : float
            Young Modulus
        nu : float
            Poisson's ratio
        numel_flange : int, optional
            The number of elements along the width.

        """
        from .blade import BladeIsotropic

        stringer = BladeIsotropic(thetadeg=thetadeg, wbot=wbot, wtop=wtop,
                h=h, E=E, nu=nu, numel_flange=numel_flange)
        self.stringers.append(stringer)


    def create(self):
        for stringer in self.stringers:
            stringer.create()
