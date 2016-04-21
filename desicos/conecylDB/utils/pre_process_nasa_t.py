num_t_sets = 16

import sys
import numpy
sys.path.append(r'C:\Users\pfh-castro\doutorado\desicos\abaqus-conecyl-python')

# local modules
import utils
import conecylDB

prefixes = [\
         'awcyl111',
         'awcyl9201',
         'awcyl9202',
         'awcyl9203',
           ]

import measured_imp_ms
reload( measured_imp_ms )


for prefix in prefixes:

    m, in_points, norm = measured_imp_ms.read_file(\
                                file_name = prefix + '_inner_surf.txt',
                                H_measured = conecylDB.H_measured[ prefix ],
                                R_measured = conecylDB.R_measured[ prefix ],
                                r_TOL = 20. )

    out_points = measured_imp_ms.translate_nodes(\
                        imperfection_file_name = prefix + '_outer_surf.txt',
                        nodes_dict             = in_points,
                        H_model                = conecylDB.H_measured[ prefix ],
                        H_measured             = conecylDB.H_measured[ prefix ],
                        R_model                = conecylDB.R_measured[ prefix ],
                        R_measured             = conecylDB.R_measured[ prefix ],
                        semi_angle             = 0.,
                        cyl_coord_sys          = False,
                        theta_in_degrees       = True,
                        stretch_H              = False,
                        z_offset_1             = None,
                        scaling_factor         = 1.,
                        r_TOL                  = 20.,
                        num_closest_points     = 5,
                        power_parameter        = 2,
                        num_sec_z              = 1,  )

    thicknesses = {}
    for k in out_points.keys():
        dist = out_points[k] - in_points[k]
        thicknesses[k] = numpy.linalg.norm( dist )

    t_values = thicknesses.values()
    t_intervals = numpy.linspace( min(t_values), max(t_values), num_t_sets )

    tmp = open( prefix + '_thick.txt', 'w' )
    for k, value in out_points.iteritems():
        actual_t = thicknesses[k]
        index = utils.index_within_linspace( t_intervals, actual_t )
        discrete_t = t_intervals[ index ]
        tmp_list = [str(v) for v in value] + [str(discrete_t)]
        tmp.write( '\t'.join( tmp_list ) + '\n' )
    tmp.close()
