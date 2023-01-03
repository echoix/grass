set(dig2_SRCS
    # cmake-format: sortable
    allocation.c
    angle.c
    box.c
    cindex.c
    cindex_rw.c
    file.c
    frmt.c
    head.c
    inside.c
    line_dist.c
    linecros.c
    list.c
    plus.c
    plus_area.c
    plus_line.c
    plus_node.c
    plus_struct.c
    poly.c
    port_init.c
    portable.c
    prune.c
    spindex.c
    spindex_rw.c
    struct_alloc.c
    type.c
    update.c
)
build_module(
  NAME grass_dig2
  SOURCES ${dig2_SRCS}
  DEPENDS GDAL GEOS grass_gmath grass_gis grass_rtree
)
