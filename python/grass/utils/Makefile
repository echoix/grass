MODULE_TOPDIR = ../../..

include $(MODULE_TOPDIR)/include/Make/Other.make
# include $(MODULE_TOPDIR)/include/Make/Python.make


DSTDIR = $(ETC)/python/grass/utils

MODULES = \
	download

PYFILES := $(patsubst %,$(DSTDIR)/%.py,$(MODULES) __init__)
# PYCFILES := $(patsubst %,$(DSTDIR)/%.pyc,$(MODULES) __init__)
# PYCFILES := $(call pyc-files,$(PYFILES))

include $(MODULE_TOPDIR)/include/Make/Python.make

# edy:
# 	echo "Edouard_echo_target: $@ , Edouard_echo_target_dir: $(@D), Edouard_echo_prereq: $^ , Edouard_echo_prereq_first: $< , Edouard_echo_prereq_first_dir: $(<D)"
# 	$(call pyc-files,$(PYFILES))
# 	# echo "Edouard_edy_pycfilestwo: $(call pyc-files,$(PYFILES))"
# 	echo "Edouard_edy_pycfilestwo: $(PYCFILESTWO)"
# edy:
# 	echo "Edouard_edy3_pyfiles: $(PYFILES) , Edouard_edy3_pycfiles: $(call pyc-files,$(PYFILES)) , Edouard_edy3_pycfiles_real: $(realpath $(call pyc-files,$(PYFILES)) ) , Edouard_edy3_pycfiles_abs: $(abspath $(call pyc-files,$(PYFILES)) ) "
# 	echo "Edouard_edy2_target: $@ , Edouard_edy2_prereq: $^ , Edouard_edy2_target: $@ , Edouard_edy2_prereq_first: $< , Edouard_edy2_prereq_new: $? ,  Edouard_edy2_stem: $*,  Edouard_edy2_directory_target: $(@D) , Edouard_edy2_target_realpath: $(realpath $@) , Edouard_edy2_target_abspath: $(abspath $@)"

# default: $(PYFILES) $(call pyc-files,$(PYFILES)) | edy
# default: $(PYFILES) $(call pyc-files,$(PYFILES)) | edy
# default: $(PYFILES) $(call pyc-files,$(PYFILES)) edy
# default: $(PYFILES) $(PYCFILES) edy
# $(eval $(call pyc-compile,$(PYFILES)))
# default: $(PYFILES)
# $(eval $(call pyc-compile,$(PYFILES)))
# default: $(PYFILES) $(PYCFILES)
# $(eval $(call pyc-compile))
default: python_compile

# $(DSTDIR):
# 	$(MKDIR) $@

# $(DSTDIR)/$(PYCACHE_DIR): | $(DSTDIR)
# 	$(MKDIR) $@

# $(call pyc-files,$(PYFILES)) &: $(PYFILES)
# 	$(PYTHON) -m py_compile $^

# $(PYCACHE_DIR)/%.$(PY_CACHE_TAG).pyc: %.py
# $(DSTDIR)/$(PYCACHE_DIR)/%.$(PY_CACHE_TAG).pyc: $(DSTDIR)/%.py | $(DSTDIR) $(DSTDIR)/$(PYCACHE_DIR)
# $(DSTDIR)/$(PYCACHE_DIR)/%.$(PY_CACHE_TAG).pyc: $(DSTDIR)/%.py | $(DSTDIR) $(DSTDIR)/$(PYCACHE_DIR)
# $(DSTDIR)/$(PYCACHE_DIR)/%.$(PY_CACHE_TAG).pyc: $(DSTDIR)/%.py | $(DSTDIR) $(DSTDIR)/$(PYCACHE_DIR)
# 	echo "Edouard_pyc_rule2_target: $@ , Edouard_pyc_rule2_prereq: $^ , Edouard_pyc_rule2_target: $@ , Edouard_pyc_rule2_prereq_first: $< , Edouard_pyc_rule2_prereq_new: $? ,  Edouard_pyc_rule2_stem: $*,  Edouard_pyc_rule2_directory_target: $(@D) , Edouard_pyc_rule2_target_realpath: $(realpath $@) , Edouard_pyc_rule2_target_abspath: $(abspath $@)"
# 	$(PYTHON) -m compileall $?
# $(DSTDIR)/$(PYCACHE_DIR)/%.$(PY_CACHE_TAG).pyc: $(DSTDIR)/%.py | $(DSTDIR) $(DSTDIR)/$(PYCACHE_DIR)
# 	echo "Edouard_pyc_rule2_target: $@ , Edouard_pyc_rule2_prereq: $^ , Edouard_pyc_rule2_target: $@ , Edouard_pyc_rule2_prereq_first: $< , Edouard_pyc_rule2_prereq_new: $? ,  Edouard_pyc_rule2_stem: $*,  Edouard_pyc_rule2_directory_target: $(@D) , Edouard_pyc_rule2_target_realpath: $(realpath $@) , Edouard_pyc_rule2_target_abspath: $(abspath $@)"
# 	$(PYTHON) -m compileall $?
# 	# $(PYTHON) -m py_compile $<
# $(DSTDIR)/$(PYCACHE_DIR)/%.$(PY_CACHE_TAG).pyc: $(DSTDIR)/%.py | $(DSTDIR) $(DSTDIR)/$(PYCACHE_DIR)
# 	$(INSTALL_DATA) $< $@

# $(DSTDIR)/%.py: %.py | $(DSTDIR) $(DSTDIR)/$(PYCACHE_DIR)
# 	$(INSTALL_DATA) $< $@
# $(DSTDIR)/%: % | $(DSTDIR) $(DSTDIR)/$(PYCACHE_DIR)
# 	$(INSTALL_DATA) $< $@
# $(DSTDIR)/%: % | $(DSTDIR)
# 	$(INSTALL_DATA) $< $@

# $(eval $(call pyc-compile,$(PYFILES)))

# .PHONY: edy
# .PHONY: edy