PY_CACHE_TAG = $(shell $(PYTHON) -c "import sys; print(sys.implementation.cache_tag)")
PY_SOURCES := $(wildcard *.py)
PYCACHE_DIR = __pycache__

%.pyc: $(PYCACHE_DIR)/%.$(PY_CACHE_TAG).pyc %.py
	$(warning "Edouard_fallback_pyc_rule")
	cp $< $@

$(PYCACHE_DIR)/%.$(PY_CACHE_TAG).pyc: %.py
	echo "Edouard_pyc_rule_target: $@ , Edouard_pyc_rule_prereq: $^ , Edouard_pyc_rule_target: $@ , Edouard_pyc_rule_prereq_first: $< , Edouard_pyc_rule_prereq_new: $? ,  Edouard_pyc_rule_stem: $*,  Edouard_pyc_rule_directory_target: $(@D) , Edouard_pyc_rule_target_realpath: $(realpath $@) , Edouard_pyc_rule_target_abspath: $(abspath $@)"
	$(PYTHON) -m py_compile $<

# define pyc-files
# PYCFILESTWO := $(join $(addsuffix $(PYCACHE_DIR)/, $(dir $(1))), $(notdir $(1:.py=.$(PY_CACHE_TAG).pyc)))
# endef
define pyc-files
$(join $(addsuffix $(PYCACHE_DIR)/, $(dir $(1))), $(notdir $(1:.py=.$(PY_CACHE_TAG).pyc)))
endef


define pyc-compile
$(warning "Edouard_pyc-compile: warning in define")
PYCFILES += $$(call pyc-files,$(PYFILES))
$$(PYCFILES) &: $$(PYFILES)
	echo "Edouard_in_pyc-compile9. Edouard_target: $$@ , Edouard_prereq: $$^ , Edouard_first: $$< , Edouard_param1: $(1)"
	$(PYTHON) -m py_compile $$^
# $(INSTALL_DATA) -v -D -t $$(^D) $$(^F)
# $(INSTALL_DATA) -v -D -t $$(@D) $$(@F)

$(DSTDIR)/%: % 
	$(INSTALL_DATA) -v -D -t $$(@D) $$<
endef
# $(INSTALL_DATA) -v -D -t $$< $$@
# $(INSTALL_DATA) -v -D -t $$@ $$<
# define pyc-compile
# $(warning "Edouard_pyc-compile: warning in define")
# PYCFILES += $$(call pyc-files,$(PYFILES))
# $$(PYCFILES) &: $$(PYFILES)
# 	echo "Edouard_in_pyc-compile9. Edouard_target: $$@ , Edouard_prereq: $$^ , Edouard_first: $$< , Edouard_param1: $(1)"
# 	$(PYTHON) -m py_compile $$^

# $(DSTDIR):
# 	$(MKDIR) $$@

# $(DSTDIR)/%: % | $(DSTDIR)
# 	$(INSTALL_DATA) -v -D -t $$@ $$<
# endef
# $(INSTALL_DATA) -D -t $$@ $$< $$@
# $(DSTDIR):
# 	$(MKDIR) $$@

# $(DSTDIR)/%.py: %.py | $(DSTDIR)
# 	$(INSTALL_DATA) $$< $$@

# $(warning "Edouard_pyc-compile: warning in define")
# $(warning "Edouard_pyc-compile: warning in define param1: $(1)")
# $$(call pyc-files,$(1)) &: $(1)
# 	# echo "Edouard_in_pyc-compile1. Edouard_target1: $(value @) , Edouard_prereq1: $(value ^) , Edouard_param11: $(1)"
# 	# echo "Edouard_in_pyc-compile. Edouard_target: $$($@) , Edouard_prereq: $$($^) , Edouard_param1: $(1)"
# 	echo "Edouard_in_pyc-compile7. Edouard_target: $$@ , Edouard_prereq: $$^ , Edouard_first: $$< , Edouard_param1: $(1)"
# 	$(PYTHON) -m py_compile $$^
# $$(DSTDIR)/$(PYCACHE_DIR)/%.$(PY_CACHE_TAG).pyc: $$(DSTDIR)/%.py
# 	echo "Edouard_in_pyc-compile3. Edouard_target3: $(value @) , Edouard_prereq3: $(value ^) , Edouard_param13: $(1)"
# 	echo "Edouard_in_pyc-compile4. Edouard_target: $$($@) , Edouard_prereq: $$($^) , Edouard_param1: $(1)"
# 	echo "Edouard_in_pyc-compile5. Edouard_target: $$@ , Edouard_prereq: $$($^) , Edouard_first:  $($($<)) , Edouard_param1: $(1)"
# 	echo "Edouard_in_pyc-compile6. Edouard_target: $$@ , Edouard_prereq: $$^ , Edouard_first: $$< , Edouard_param1: $(1)"
# 	echo "Edouard_in_pyc-compile2. Edouard_pyc_rule_target: $@ , Edouard_pyc_rule_prereq: $^ , Edouard_pyc_rule_target: $@ , Edouard_pyc_rule_prereq_first: $< , Edouard_pyc_rule_prereq_new: $? ,  Edouard_pyc_rule_stem: $*,  Edouard_pyc_rule_directory_target: $(@D) , Edouard_pyc_rule_target_realpath: $(realpath $@) , Edouard_pyc_rule_target_abspath: $(abspath $@)"
# 	$(PYTHON) -m py_compile $$<


# .SECONDARY: $(PYCACHE_DIR)/%.$(PY_CACHE_TAG).pyc
# .SECONDARY: $(PYCACHE_DIR)/%.$(PY_CACHE_TAG).pyc
# .NOTINTERMEDIATE: %.pyc $(PYCACHE_DIR)/%.$(PY_CACHE_TAG).pyc
python_compile_rule: $(eval $(call pyc-compile))
	$(warning "Edouard_python_compile_rule: warning in rule")
# python_compile_rule: $(eval $(call pyc-compile))
# 	$(warning "Edouard_python_compile_rule: warning in rule")
# 	# $(eval $(call pyc-compile))
# python_compile_rule_deps: python_compile_rule $(PYFILES) $(PYCFILES) | python_compile_rule

python_compile: $(PYFILES) $(PYCFILES) | python_compile_rule
# python_compile:  $(PYCFILES) | python_compile_rule
# python_compile: python_compile_rule
# python_compile: python_compile_rule python_compile_rule_deps
# python_compile: $(PYFILES) $(PYCFILES) | $(eval pyc-compile)


# $(DSTDIR):
# 	$(MKDIR) $@

# $(DSTDIR)/%: % | $(DSTDIR)
# 	$(INSTALL_DATA) $< $@
grass_script: $(ETC)/python/grass/script/

.PHONY: python_compile python_compile_rule python_compile_rule_deps