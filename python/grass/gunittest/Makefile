MODULE_TOPDIR = ../../..

include $(MODULE_TOPDIR)/include/Make/Other.make
include $(MODULE_TOPDIR)/include/Make/Python.make

PYDIR = $(ETC)/python
GDIR = $(PYDIR)/grass
DSTDIR = $(GDIR)/gunittest

# TODO: add multireport multirunner
MODULES = case gmodules loader result runner checkers gutils invoker main reporters utils

PYFILES := $(patsubst %,$(DSTDIR)/%.py,$(MODULES) __init__ __main__)
PYCFILES := $(patsubst %,$(DSTDIR)/%.pyc,$(MODULES) __init__ __main__)

default: $(PYFILES) $(PYCFILES) $(GDIR)/__init__.py $(GDIR)/__init__.pyc $(GDIR)/__main__.py $(GDIR)/__main__.pyc

$(PYDIR):
	$(MKDIR) $@

$(GDIR): | $(PYDIR)
	$(MKDIR) $@

$(DSTDIR): | $(GDIR)
	$(MKDIR) $@

$(DSTDIR)/%: % | $(DSTDIR)
	$(INSTALL_DATA) $< $@
