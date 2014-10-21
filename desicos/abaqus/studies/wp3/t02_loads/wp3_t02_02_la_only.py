import sys
import os
import numpy
#
source_python = r'C:\Users\pfh-castro\doutorado\desicos\abaqus-conecyl-python'
sys.path.append( source_python )
import study
import conecylDB
#
cname_ploads = {\
            'huehne_2002_z26':[1,2,3,4,5,6,10],
            'huehne_2002_z27':[1,2,3,4,5,6,10],
            'huehne_2002_z14':[1,2,3,5,10,20,30],
            'huehne_2002_z22':[1,2,3,5,10,20,30],
            'huehne_2002_z23':[1,5,10,30,50,70,90],
            'huehne_2002_z24':[1,5,10,30,50,70,90],
            }
#
studies = study.Studies()
studies.name = 'wp3_t02_02_la_only'
betadegs_dict = {}
for cname, ploads in cname_ploads.iteritems():
    study_name = studies.name + '_' + cname.split('_2002_')[1]
    ###########################################
    ########  FILE MANAGEMENT SECTION  ########
    ###########################################
    study_dir  = os.path.join( r'C:\Temp','abaqus',study_name )
    if not os.path.isdir( study_dir ):
        os.makedirs( study_dir )
    output_dir = os.path.join( study_dir,'outputs' )
    print 'configuring folders...'
    print '\t' + output_dir
    if not os.path.isdir( output_dir ):
        os.makedirs( output_dir )
    ###########################################
    std = study.Study()
    std.name = study_name
    std.rebuild()
    cylDB = conecylDB.ccs[ cname ]
    d = 2 * cylDB['r']
    ts = [0,0.05,0.10,0.20,0.30,0.40,0.50]
    betadegs = [ numpy.rad2deg(numpy.arctan(t/d)) for t in ts ]
    betadegs_dict[ cname ] = betadegs
    count = 0
    for betadeg in betadegs:
        count += 1
        cc = std.add_cc_fromDB( cname )
        cc.separate_load_steps = False
        cc.betadeg = betadeg
        cc.damping_factor2 = 1.e-7
        cc.initialInc2 = 1.e-2
        cc.minInc2 = 1.e-6
        cc.maxInc2 = 1.e-2
        cc.maxNumInc2 = 100000
        cc.axial_displ = 1.5
        if cname.find( 'z14' ) > -1 \
        or cname.find( 'z23' ) > -1:
            cc.axial_displ = 2.
        if cname.find( 'z27' ) > -1:
            cc.axial_displ = 2.5
            cc.damping_factor2 = 5.e-7
        if cname.find( 'z22' ) > -1:
            cc.damping_factor2 = 5.e-7
        cc.rename = False
        cc.jobname = study_name + '_model_%02d' % count
    std.create_models()
    studies.studies.append(std)
