prefixes = [\
         'z15',
         'z17',
         'z18',
         'z20',
         'z21',
         'z22',
         'z23',
         'z24',
         'z25',
         'z26',
        ]

def read_file( file_name,
               R_measured,
               t_measured = None,
               H_measured  = None,
               stretch_H   = False,
               z_offset_1  = None ):
    print 'Reading imperfection file: %s ...' % file_name
    # user warnings
    if stretch_H:
        if z_offset_1:
            print 'WARNING! Because of the stretch_H option,'
            print '         consider setting z_offset_1 to None'
    # reading the imperfection file
    myfile = open( file_name, 'r' )
    lines = myfile.readlines()
    myfile.close()
    count = -1
    measured_points = {}
    for line in lines:
        line = line.strip()
        count += 1
        fields = line.split()
        if len(fields) <> 5:
            continue
        tmplist = [float(i) for i in fields[2:]]
        data = numpy.array(tmplist, dtype='float32')
        measured_points[count] = data
    # measuring model dimensions
    zlist = []
    tlist = []
    t_set = set()
    for mp in measured_points.values():
        zlist.append( mp[0] )
        tlist.append( mp[2] )
        t_set.add( mp[2] )
    z_min = min(zlist)
    z_max = max(zlist)
    z_center  = (z_max + z_min)/2.
    H_points = (z_max - z_min)
    # applying user inputs
    if not H_measured:
        H_measured = H_points
        print 'WARNING! The cylinder height of the measured points ' +\
              'assumed to be %1.2f' % H_measured
    t_av = t_measured
    if not t_measured:
        t_av = sum( tlist ) / float(len(tlist))
    # calculating default z_offset_1
    if not z_offset_1:
        z_offset_1 = (H_measured - H_points) / 2.
    offset_z = z_min - z_offset_1
    print 'H_points       :', H_points
    print 'H_measured     :', H_measured
    print 'z_min          :', z_min
    print 'z_max          :', z_max
    print 't_av           :', t_av
    norm_measured_points = {}
    offset_mps = {}
    for k,mp in measured_points.iteritems():
        thetarad = mp[1] / R_measured
        x_scaled = numpy.cos( thetarad )
        y_scaled = numpy.sin( thetarad )
        t_scaled = mp[2] / t_av

        x = x_scaled * R_measured
        y = y_scaled * R_measured
        z = mp[0] - offset_z

        z_scaled = z / H_measured
        if stretch_H:
            z_scaled = z/H_points # will make the maximum 1.
        norm_measured_points[k]    = \
            numpy.array( [ x_scaled, y_scaled, z_scaled, t_scaled ],
                         dtype='float32')
        offset_mps[k] = numpy.array([x, y, z, mp[2]], dtype='float32')
    t_set_norm = set( [t/t_av for t in t_set] )
    #return measured_points, norm_measured_points, t_set_norm
    return offset_mps

for prefix in prefixes:
    file_name = prefix + '_thick.txt'
    import gui.gui_defaults as defaults
    t_measured = defaults.t_measured[ prefix ]
    R_measured = defaults.R_measured[ prefix ]
    H_measured = defaults.H_measured[ prefix ]
    offset_mps = read_file( file_name = file_name,
                            R_measured = R_measured,
                            t_measured = t_measured,
                            H_measured = H_measured )

    tmp = open( prefix + '_thick_new.txt', 'w' )
    for value in offset_mps.values():
        tmp.write( '\t'.join( [str(v) for v in value]) + '\n' )
    tmp.close()

