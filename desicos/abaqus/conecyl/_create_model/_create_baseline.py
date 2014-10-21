from abaqus import *
from regionToolset import Region
from abaqusConstants import *

import desicos.abaqus.abaqus_functions as abaqus_functions

def _create_baseline( self ):
    # abaqus modules
    self.rebuild( force=True )
    R          = self.r # mm
    #
    backwardCompatibility.setValues(includeDeprecated = True,
                                    reportDeprecated  = False)
    #
    #Mdb()
    #mdb.saveAs(pathName=r'C:\Temp\abaqus\cylinder.cae')
    self.mdb = mdb
    #RESETING THE CURRENT VIEWPORT
    myView = session.viewports[session.currentViewportName]
    myView.setValues( displayedObject = None )
    #CREATING A NEW MODEL
    mod = mdb.Model(name=self.jobname)
    self.mod = mod
    #DELETING THE DEFAULT MODEL
    tmp = 'Model-1'
    if tmp in mdb.models.keys():
        del mdb.models[tmp]
    #CREATING A NEW PART
    part = mod.Part( name = 'Cylinder',
                     dimensionality = THREE_D,
                     type = DEFORMABLE_BODY )
    self.part = part
    #CREATING THE SKETCH which will be used to create the shell geometry
    s1 = mod.ConstrainedSketch( name='SketchCylinder',
                                sheetSize=max( [2.1*R, 1.1*self.h] ) )
    #sketch profile to be extruded
    s1.CircleByCenterPerimeter( center = (0.0, 0.0),
                                point1 = (  R, 0.0) )
    #
    #CREATING A LOCAL COORDINATE SYSTEM TO USE IN THE BOUNDARY CONDITIONS
    local_csys = part.DatumCsysByThreePoints( name='CSYSCylinder',
                                              coordSysType=CYLINDRICAL,
                                              origin = (0,0,0),
                                              point1 = (1,0,0),
                                              point2 = (1,1,0) )
    part_local_csys_datum = part.datums[local_csys.id]
    self.local_csys = local_csys
    #CREATING THE CYLINDER SHELL GEOMETRY
    myCyl = part.BaseShellExtrude( depth = self.h,
                                   draftAngle = -self.alphadeg,
                                   sketch=s1, )
    #_________________________________________________________
    #
    # lamina
    #_________________________________________________________
    #
    if self.direct_ABD_input == False:
        # CREATING MATERIALS
        mat_names = []
        for i, laminaprop in enumerate(self.laminaprops):
            if len(laminaprop) <= 4:
                material_type = ISOTROPIC
                laminaprop = (laminaprop[0], laminaprop[2])
            else:
                material_type = LAMINA
            mat_name = self.laminapropKeys[i]
            mat_names.append( mat_name )
            if not mat_name in mod.materials.keys():
                myMat = mod.Material( name=mat_name )
                myMat.Elastic( table = ( laminaprop, ) ,
                               type  = material_type )
                #TODO should we find a better way to use allowables? To
                # guarantee that always i < len(self.allowables), for instance?
                if i < len(self.allowables) and material_type <> ISOTROPIC:
                    ALLOWABLES = tuple([abs(j) for j in self.allowables[i]])
                    myMat.HashinDamageInitiation( table = ( ALLOWABLES, ) )
        abaqus_functions.create_composite_layup(
                          name = 'CompositePlate',
                          stack = self.stack,
                          plyts = self.plyts,
                          mat_names = mat_names,
                          part = part,
                          region = Region( faces=part.faces ),
                          part_local_csys_datum=part_local_csys_datum, )


