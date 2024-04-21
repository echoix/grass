MODULE_TOPDIR = ../..

LIBES = $(RASTER3DLIB) $(RASTERLIB) $(GISLIB)
DEPENDENCIES = $(RASTER3DDEP) $(GISDEP) $(RASTERDEP)

PROGRAMS = r.colors r3.colors

r_colors_OBJS = raster_main.o edit_colors.o rules.o stats.o
r3_colors_OBJS = raster3d_main.o edit_colors.o rules.o stats.o

include $(MODULE_TOPDIR)/include/Make/Multi.make

default: multi thumbnails
GRASS_SCRIPT_DEPS = $(patsubst %,$(ETC)/python/grass/script/%.py,core db raster raster3d vector array setup task utils)

thumbnails: $(BIN)/r.mapcalc$(EXE) $(BIN)/r.colors$(EXE) $(HTMLDIR)/colortables $(GRASS_SCRIPT_DEPS)
	echo "Edouard_rcolor: target: $@, prereq_all: $^, bin: $(BIN), etc: $(ETC)"
ifndef CROSS_COMPILING
	-$(call run_grass, $(GRASS_HOME)/utils/thumbnails.py)
endif

$(HTMLDIR)/colortables: $(HTMLDIR)
	$(MKDIR) $@

$(BIN)/r.mapcalc$(EXE):
	$(MAKE) -C $(MODULE_TOPDIR)/raster/r.mapcalc $(BIN)/$(PGM2)$(EXE)
# $(BIN)/r.mapcalc$(EXE):
# 	$(MAKE) -C ../r.mapcalc

$(GRASS_SCRIPT_DEPS) &:
	echo "Edouard_rcolor_gs: etc: $(ETC) , target: $@"
	$(MAKE) -C $(MODULE_TOPDIR)/python/grass/script

.PHONY: thumbnails
