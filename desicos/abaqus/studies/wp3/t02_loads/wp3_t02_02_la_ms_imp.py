import sys
import os
import numpy
#
source_python = r'C:\Users\pfh-castro\doutorado\desicos\abaqus-conecyl-python'
sys.path.append( source_python )
import study
import conecylDB
#
cname_imp_name = {\
            'huehne_2002_z14':'z15',
            'huehne_2002_z22':'z15',
            'huehne_2002_z23':'z33',
            'huehne_2002_z24':'z33',
            'huehne_2002_z26':'z15',
            'huehne_2002_z27':'z15',
            }
#
studies = study.Studies()
studies.name = 'wp3_t02_02_la_ms_imp'
betadegs_dict = {}
for cname, imp_name in cname_imp_name.iteritems():
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
    ts = [0.05,0.10,0.20,0.30,0.40,0.50,0.0]
    betadegs = [ numpy.rad2deg(numpy.arctan(t/d)) for t in ts ]
    betadegs_dict[ cname ] = betadegs
    count = 0
    for betadeg in betadegs:
        count += 1
        cc = std.add_cc_fromDB( cname )
        cc.separate_load_steps = False
        cc.betadeg = betadeg
        cc.rebuild()
        cc.damping_factor2 = 5.e-7
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
        cc.rename = False
        cc.jobname = study_name + '_model_%02d' % count
    std.create_models( write_input_files=False )
    # applying mid-surface imperfections
    import measured_imp_ms
    import gui.gui_defaults as gui_defaults
    imp_file_name = gui_defaults.imps[ imp_name ]['geom']
    H_measured = gui_defaults.H_measured[ imp_name ]
    R_measured = gui_defaults.R_measured[ imp_name ]
    reload( measured_imp_ms )
    nodes_new_dict = None
    for cc in std.ccs[1:]:
        model_name = cc.jobname
        nodes_new_dict = measured_imp_ms.\
                         disturb_my_model_ABAQUS_CAE(\
                             imperfection_file_name = imp_file_name,
                             model_name         = cc.jobname,
                             part_name          = cc.part.name,
                             H_model            = cc.h,
                             H_measured         = H_measured,
                             R_model            = cc.r,
                             R_measured         = R_measured,
                             semi_angle         = cc.alphadeg,
                             nodes_new_dict     = nodes_new_dict )
    std.write_inputs()
    studies.studies.append(std)
