add_library(grass_gis
        adj_cellhd.c alloc.c aprintf.c
        area.c area_ellipse.c area_poly1.c area_poly2.c
        area_sphere.c ascii_chk.c asprintf.c basename.c bres_line.c clicker.c
        cmprbzip.c cmprlz4.c cmprrle.c cmprzlib.c cmprzstd.c color_rules.c
        color_str.c commas.c compress.c compress.h copy_dir.c copy_file.c
        counter.c date.c datum.c debug.c distance.c done_msg.c endian.c env.c
        error.c file_name.c find_etc.c find_file.c find_rast.c find_rast3d.c
        find_vect.c fmode.c G.h geodesic.c geodist.c get_ellipse.c get_projinfo.c
        get_window.c getl.c gis_local_proto.h gisbase.c gisdbase.c gisinit.c
        handler.c home.c ilist.c intersect.c is.c key_value1.c key_value2.c
        key_value3.c key_value4.c legal_name.c line_dist.c list.c ll_format.c
        ll_scan.c locale.c location.c lrand48.c ls.c ls_filter.c lz4.c lz4.h
        mach_name.c make_loc.c make_mapset.c mapcase.c mapset.c mapset_msc.c
        mapset_nme.c mkstemp.c myname.c named_colr.c new_des nl_to_spaces.c
        nme_in_mps.c open.c open_misc.c overwrite.c pager.c parser.c
        parser_dependencies.c parser_help.c parser_html.c parser_interface.c
        parser_json.c parser_local_proto.h parser_rest.c parser_script.c
        parser_standard_options.c parser_wps.c paths.c percent.c pi.h plot.c
        pole_in_poly.c popen.c progrm_nme.c proj1.c proj2.c proj3.c projections
        put_window.c putenv.c radii.c rd_cellhd.c remove.c rename.c renamed_options
        rhumbline.c rotate.c seek.c set_window.c short_way.c sleep.c snprintf.c
        spawn.c state27 state83 strings.c tempfile.c timestamp.c token.c trim_dec.c
        units.c user_config.c verbose.c view.c whoami.c win32_pipes.c wind_2_box.c
        wind_format.c wind_in.c wind_limits.c wind_overlap.c wind_scan.c window_map.c
        worker.c wr_cellhd.c writ_zeros.c xdr.c zero.c zone.c)
add_library(GRASS::gis ALIAS grass_gis)

target_sources(grass_gis
        PUBLIC
        FILE_SET installed_headers
        TYPE HEADERS
        BASE_DIRS
        ${GRASS_SOURCE_DIR}/include
        FILES ${GRASS_SOURCE_DIR}/include/grass/config.h
        )

target_link_libraries(grass_gis PRIVATE grass_datetime)