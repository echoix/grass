MODULE_TOPDIR = ../../..

include $(MODULE_TOPDIR)/include/Make/Other.make
# include $(MODULE_TOPDIR)/include/Make/Python.make

DSTDIR = $(ETC)/python/grass/utils

MODULES = \
	download
# SRCPYFILES = $(MODULES) __init__
# PYFILES := $($(MODULES) __init__:%.py=$(DSTDIR)/%.py)
PYFILES := $(patsubst %,$(DSTDIR)/%.py,$(MODULES) __init__)
# PYCFILES := $(patsubst %,$(DSTDIR)/%.pyc,$(MODULES) __init__)
# PYCFILES := $(join $(addsuffix ../$(PYCACHE_DIR)/, $(dir $(PYFILES))), $(notdir $(PYFILES:.py=.pyc)))

# include $(MODULE_TOPDIR)/include/Make/Other.make
include $(MODULE_TOPDIR)/include/Make/Python.make

# default: $(PYFILES) pyc
# default: $(PYFILES) pyc_compile $(PYCFILES)
# 	echo "Edouard4_pyfiles: $(PYFILES), Edouard4_prereq: $^ "

# default: $(PYFILES:%.py=$(DSTDIR)/%.py) pyc_compile
# 	echo "Edouard4_pyfiles: $(PYFILES), Edouard4_prereq: $^ "
# default: $(PYFILES) $(PYCFILES)


default: $(PYFILES) pyc_compile
	echo "Edouard4_pyfiles: $(PYFILES), Edouard4_prereq: $^ , Edouard4_target: $@"
# default: $(SRCPYFILES:%=%.py) $(PYFILES) pyc_compile   $(PYCFILES) 
# 	echo "Edouard4_pyfiles: $(PYFILES), Edouard4_prereq: $^ , Edouard4_target: $@ "

# default: $(SRCPYFILES:%=%.py) $(PYFILES) $(PYCFILES) pyc_compile
# 	echo "Edouard4_pyfiles: $(PYFILES), Edouard4_prereq: $^ , Edouard4_target: $@ "
# 	# $(PYTHON) -m compileall $(SRCPYFILES:%=%.py)
$(DSTDIR):
	$(MKDIR) $@

$(DSTDIR)/%: % | $(DSTDIR)
	$(INSTALL_DATA) $< $@

# OBJ=$(join $(addsuffix ../obj/, $(dir $(SOURCE))), $(notdir $(SOURCE:.cpp=.o)))