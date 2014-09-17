r"""
=============================================
Geometries (:mod:`desicos.abaqus.utils.geom`)
=============================================

.. currentmodule:: desicos.abaqus.utils.geom

"""
class Plane(object):
    """Plane object

    Defined by the attributes:

    =============  ==========================================================
    Attribute      Description
    =============  ==========================================================
    ``thetadeg``   ``float``, circumferential position in degrees
    ``p1``         ``tuple``, a tuple containing the `(X_1, X_2, X_3)`
                   coordinates for point 1
    ``p2``         ``tuple``, a tuple containing the `(X_1, X_2, X_3)`
                   coordinates for point 2
    ``p3``         ``tuple``, a tuple containing the `(X_1, X_2, X_3)`
                   coordinates for point 3
    part           Abaqus Part object corresponding to this plane
    feature        Abaqus Part Feature object corresponding to this plane
    datum          Abaqus Part Datum object corresponding to this plane
    =============  ==========================================================

    """
    def __init__(self):
        self.thetadeg = None
        self.p1 = None
        self.p2 = None
        self.p3 = None
        self.datum = None
        self.feature = None
        self.part = None

    def create(self):
        """Creates the plane based on three points

        The three points must be previously stored in the attributes ``p1``,
        ``p2`` and ``p3``.

        """
        self.feature = self.part.DatumPlaneByThreePoints(point1 = self.p1,
                                                         point2 = self.p2,
                                                         point3 = self.p3)
        self.datum = self.part.datums[self.feature.id]

    def __getattr__(self, attr):
        try:
            return getattr(self, attr)
        except:
            return getattr(self.datum, attr)

