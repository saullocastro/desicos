import laminate_parameters
laminate_parameters = reload( laminate_parameters )
angles = [0,-30,30,-45,45,-60,60,90]
for num_plies in [3,4,5]:
    fam = laminate_parameters.LamFamily()
    fam.num_plies = num_plies
    fam.angles = angles
    fam.rebuild()
    fam.create_family( balanced=False,
                       use_iterator=True )
    fam.rebuild_params()
    fam.plot( keys='all', savefig=False, fit_plots=False )
