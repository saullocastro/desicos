import numpy
old_names = [\
         'awcyl111in',
         'awcyl111out',
         'awcyl9201in',
         'awcyl9201out',
         'awcyl9202in',
         'awcyl9202out',
         'awcyl9203in',
         'awcyl9203out',
        ]
new_names = [\
         'awcyl111_inner_surf.txt',
         'awcyl111_outer_surf.txt',
         'awcyl9201_inner_surf.txt',
         'awcyl9201_outer_surf.txt',
         'awcyl9202_inner_surf.txt',
         'awcyl9202_outer_surf.txt',
         'awcyl9203_inner_surf.txt',
         'awcyl9203_outer_surf.txt',
        ]
def in2mm( value ):
    return value * 25.4

for i in range(len(old_names)):
    tmp = open( old_names[i], 'r' )
    lines = tmp.readlines()
    tmp.close()
    if old_names[i].find('awcyl111') > -1:
        lines = lines[0].split('\r')
    old = numpy.array([[float(v) for v in l.split()] for l in lines])
    rs     = old[:,0]
    thetas = old[:,1]
    zs     = old[:,2]
    # conversions
    rs = in2mm( rs )
    thetas = numpy.deg2rad(thetas)
    zs = in2mm( zs )
    #
    xs = rs * numpy.cos( thetas )
    ys = rs * numpy.sin( thetas )
    #
    shape = (len(zs),1)
    xs.shape = shape
    ys.shape = shape
    zs.shape = shape
    new = numpy.concatenate( (xs,ys,zs), axis=1 )

    tmp = open( new_names[i], 'w' )
    for point in new:
        tmp.write( '\t'.join( [str(v) for v in point] ) + '\n' )
    tmp.close()

