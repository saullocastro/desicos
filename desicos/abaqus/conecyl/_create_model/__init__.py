def _create_model( cc ):
    if cc.created_model:
        return
    cc.rebuild()
    import _create_baseline
    _create_baseline._create_baseline( cc )

    import _create_partitions
    _create_partitions._create_sketch_planes( cc )
    _create_partitions._create_partitions( cc )

    import _create_cs_mer
    _create_cs_mer._create_cs_mer( cc )

    import _create_mesh_load_BC
    _create_mesh_load_BC._create_mesh_load_BC( cc )

    return True

