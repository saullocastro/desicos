import laminate_parameters
laminate_parameters = reload( laminate_parameters )
angles = [0,-45,45,90]
for num_plie in [4,6,8,10,12]:
    fam = laminate_parameters.LamFamily()
    fam.num_plies = num_plie
    fam.angles = angles
    fam.rebuild()
    fam.create_family()
    fam.plot()
    fam.save(r'c:\temp\%s.pickle' % fam.name)
