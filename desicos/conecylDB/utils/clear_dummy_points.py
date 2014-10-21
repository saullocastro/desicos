import os
import numpy
# it will apply a decreasing r_TOL and measure how many points were ignored for
# each value, than plot to see the r_TOL threshold that should be used.
# a new file will be created without the dummy points, for each case
# the read_file() is a copied version from measured_imp_ms.py

def read_file( file_name,
               cyl_coord_sys         = False,
               theta_in_degrees      = True,
               H_measured            = None,
               R_measured            = None,
               r_TOL                 = 1. ):
    print 'Reading imperfection file: %s ...' % file_name
    # user warnings
    # reading the imperfection file
    myfile = open( file_name, 'r' )
    lines = myfile.readlines()
    myfile.close()
    line_num = 0
    ignore = False
    measured_points = []
    for line in lines:
        line = line.strip()
        line_num += 1
        tmplist = [float(i) for i in line.split()[:3]]
        cartesian = numpy.array(tmplist, dtype='float32')
        if cyl_coord_sys:
            theta = cartesian[1]
            if theta_in_degrees:
                theta = numpy.deg2rad( theta )
            r     = cartesian[0]
            x = numpy.cos(theta) * r
            y = numpy.sin(theta) * r
            z = cartesian[2]
            cartesian = numpy.array([x, y, z], dtype='float32')
        measured_points.append([line_num,cartesian])
    # measuring model dimensions
    zlist = []
    for mp in measured_points:
        zlist.append( mp[1][2] )
    z_min = min(zlist)
    z_max = max(zlist)
    z_center  = (z_max + z_min)/2.
    H_points = (z_max - z_min)
    print 'R_measured     :', R_measured
    # applying user inputs
    R = R_measured
    H_model = H_points
    if not H_measured:
        H_measured = H_points
        print 'WARNING! The cylinder height of the measured points assumed\n'+\
              '         to be %1.2f' % H_measured
    print 'H_points       :', H_points
    print 'H_measured     :', H_measured
    print 'z_min          :', z_min
    print 'z_max          :', z_max
    r_TOL_min = (R * (1-r_TOL/100.))
    r_TOL_max = (R * (1+r_TOL/100.))
    kept = []
    skept = []
    for line_num_mp in measured_points:
        x = line_num_mp[1][0]
        y = line_num_mp[1][1]
        z = line_num_mp[1][2]
        radius = numpy.sqrt( x**2 + y**2 )
        if radius > r_TOL_max or radius < r_TOL_min:
            skept.append( line_num_mp )
        else:
            kept.append( line_num_mp )
    return kept, skept

if __name__ == '__main__':
    import matplotlib.pyplot as pyplot
    import sys
    sys.path.append(r'C:\Users\pfh-castro\doutorado\desicos\abaqus-conecyl-python')
    from conecylDB import imps, R_measured, H_measured
    if False:
        # procedure to find the r_TOL to use when creating the new files
        name = 'degenhardt_2010_z24'
        file_name = imps[name]['ms']
        H_measured = H_measured[name]
        R_measured = R_measured[name]
        r_TOLs = numpy.linspace(0.4,0.3,20)
        kept = {}
        skept = {}
        for r_TOL in r_TOLs:
            kept[r_TOL], skept[r_TOL] = read_file(file_name = file_name,
                                                  H_measured = H_measured,
                                                  R_measured = R_measured,
                                                  r_TOL = r_TOL)
            pyplot.plot(r_TOL, len(skept[r_TOL]))
        for r_TOL in r_TOLs:
            print r_TOL, len(skept[r_TOL])
        pyplot.show()

    if True:
        r_TOL_dict = {
                #'degenhardt_2010_z15':0.6421,
                #'degenhardt_2010_z17':0.5578,
                #'degenhardt_2010_z18':0.4025,
                #'degenhardt_2010_z20':0.3053,
                #'degenhardt_2010_z21':0.6842,
                #'degenhardt_2010_z22':0.2523,
                #'degenhardt_2010_z23':0.2833,
                'degenhardt_2010_z24':0.3263,
                #'degenhardt_2010_z25':0.2526,
                #'degenhardt_2010_z26':0.2736,
               }
        for name, r_TOL in r_TOL_dict.iteritems():
            file_name = imps[name]['ms']
            H = H_measured[name]
            R = R_measured[name]
            kept, skept = read_file(file_name = file_name,
                                    H_measured = H,
                                    R_measured = R,
                                    r_TOL = r_TOL)
            new_file = open('new_'+os.path.basename(file_name),'w')
            for line_num_mp in kept:
                mp = line_num_mp[1]
                new_file.write(('%1.3f %1.3f %1.3f ' % tuple(mp)) +'\n')
            new_file.close()



