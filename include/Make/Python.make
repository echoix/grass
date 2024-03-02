
PY_CACHE_TAG = $(shell $(PYTHON) -c "import sys; print(sys.implementation.cache_tag)")
PY_SOURCES := $(wildcard *.py)
PYCACHE_DIR = __pycache__
# # Trying to use later evaluation here
# PYFILES_TO_COMPILE = $(PYFILES)

# %.pyc: %.py
# 	echo "Edouard_echo_target: $@ , Edouard_echo_dir: $(@D)" 

# $(PYCACHE_DIR)/%.$(PY_CACHE_TAG).pyc: %.py | $(PYCACHE_DIR)
# 	echo "Edouard_echo_target: $@ , Edouard_echo_target_dir: $(@D), Edouard_echo_prereq: $^ , Edouard_echo_prereq_first: $< , Edouard_echo_prereq_first_dir: $(<D)" 
# 	$(PYTHON) -m py_compile $<

# $(PYCACHE_DIR):
# 	$(MKDIR) $@
# PYCFILES := $(join $(addsuffix ../$(PYCACHE_DIR)/, $(dir $(PYFILES))), $(notdir $(PYFILES:.py=.pyc)))
PYCFILES := $(join $(addsuffix $(PYCACHE_DIR)/, $(dir $(PYFILES))), $(notdir $(PYFILES:.py=.$(PY_CACHE_TAG).pyc)))

# $(PYCFILES) &: $(PYFILES)
# 	echo "Edouard12_pyfiles: $(PYFILES), Edouard12_pycfiles: $(PYCFILES), Edouard12_prereq: $^ , Edouard12_target: $@ , Edouard12_prereq_first: $< , Edouard12_prereq_new: $?"
# 	$(PYTHON) -m compileall $?
# $(join $(addsuffix ../$(PYCACHE_DIR)/, $(dir $(PYFILES))), $(notdir $(PYFILES:.py=.pyc))): $(PYFILES)
# 	echo "Edouard5_pyfiles: $(PYFILES), Edouard5_prereq: $^ , Edouard5_target: $@ , Edouard5_prereq_first: $< , Edouard5_prereq_new: $?"
# #	$(PYTHON) -m compileall $^


# $(PYCACHE_DIR)/%.$(PY_CACHE_TAG).pyc: %.py
# 	echo "Edouard8_pyfiles: $(PYFILES), Edouard8_prereq: $^ , Edouard8_target: $@ , Edouard8_prereq_first: $< , Edouard8_prereq_new: $?"
# 	$(PYTHON) -m compileall $^

# %.pyc: $(patsubst %.$(PY_CACHE_TAG).pyc,%.py, %.py)
# 	echo "Edouard9_prereq: $^ ,  Edouard9_target: $@ , "
# 	$(PYTHON) -m compileall $^

# $(dir %)$(PYCACHE_DIR)/$(notdir %).$(PY_CACHE_TAG).pyc: %.py
# 	echo "Edouard8_pyfiles: $(PYFILES), Edouard8_prereq: $^ , Edouard8_target: $@ , Edouard8_prereq_first: $< , Edouard8_prereq_new: $?"
# 	$(PYTHON) -m compileall $^
# $(dir %)/./$(PYCACHE_DIR)/$(notdir %).$(PY_CACHE_TAG).pyc: %.py
# 	echo "Edouard8_pyfiles: $(PYFILES), Edouard8_prereq: $^ , Edouard8_target: $@ , Edouard8_prereq_first: $< , Edouard8_prereq_new: $?"
# 	$(PYTHON) -m compileall $^
# $(join $(addsuffix ./$(PYCACHE_DIR)/, $(dir $(PYFILES))), $(notdir $(PYFILES:.py=.pyc))): $(PYFILES)
# 	echo "Edouard6_pyfiles: $(PYFILES), Edouard6_prereq: $^ , Edouard6_target: $@ , Edouard6_prereq_first: $< , Edouard6_prereq_new: $?"
# 	$(PYTHON) -m compileall $^
# $(join $(addsuffix ./$(PYCACHE_DIR)/, $(dir %)), $(notdir $(%:.py=.pyc))): $(PYFILES)
# 	echo "Edouard7_pyfiles: $(PYFILES), Edouard7_prereq: $^ , Edouard7_target: $@ , Edouard7_prereq_first: $< , Edouard7_prereq_new: $?"
# 	$(PYTHON) -m compileall $^
# pyc: $(PYFILES) $(join $(addsuffix ../$(PYCACHE_DIR)/, $(dir $(PYFILES))), $(notdir $(PYFILES:.py=.pyc)))
# pyc_compile: $(PYFILES) $(join $(addsuffix ../$(PYCACHE_DIR)/, $(dir $(PYFILES))), $(notdir $(PYFILES:.py=.pyc)))
# 	echo "Edouard3_pyfiles: $(PYFILES), Edouard3_prereq: $^"
# pyc_compile: $(PYFILES) $(join $(addsuffix $(PYCACHE_DIR)/, $(dir $(PYFILES))), $(notdir $(PYFILES:.py=.pyc)))
# 	echo "Edouard3_pyfiles: $(PYFILES), Edouard3_prereq: $^ , Edouard3_prereq_newer: $?"

# PYCFILES = $(join $(addsuffix $(PYCACHE_DIR)/, $(dir $(PYFILES))), $(notdir $(PYFILES:.py=.pyc)))
# $(abspath ./$(PYCACHE_DIR)/%.$(PY_CACHE_TAG).pyc): %.py
# 	echo "Edouard10_pyfiles: $(PYFILES), Edouard10_prereq: $^ , Edouard10_target: $@ , Edouard10_prereq_first: $< , Edouard10_prereq_new: $?"

$(PYCFILES): pyc_compile

pyc_compile: $(PYFILES)
	echo "Edouard3_pyfiles: $(PYFILES), Edouard3_prereq: $^ , Edouard3_prereq_newer: $?, Edouard3_pycfiles: $(PYCFILES) , Edouard3_pycfiles_man: $(join $(addsuffix $(PYCACHE_DIR)/, $(dir $(PYFILES))), $(notdir $(PYFILES:.py=.$(PY_CACHE_TAG).pyc))), Edouard3_target: $@ ,"
	$(PYTHON) -m compileall $?

$(DSTDIR)/%.pyc: %.pyc | $(DSTDIR)
	echo "Edouard13_target: $@, Edouard13_prereq: $^"
	$(INSTALL_DATA) $< $@
# pyc_compile: $(PYFILES) $(PYCFILES)
# 	echo "Edouard3_pyfiles: $(PYFILES), Edouard3_prereq: $^ , Edouard3_prereq_newer: $?, Edouard3_pyc1: $(join $(addsuffix $(PYCACHE_DIR)/, $(dir $(PYFILES))), $(notdir $(PYFILES:.py=.pyc))) , Edouard3_pycfiles: $(PYCFILES) , Edouard3_pycfiles_man: $(join $(addsuffix $(PYCACHE_DIR)/, $(dir $(PYFILES))), $(notdir $(PYFILES:.py=.$(PY_CACHE_TAG).pyc))), Edouard3_target: $@ ,"
# $(PYTHON) -m compileall $?
# pyc_compile $(join $(addsuffix $(PYCACHE_DIR)/, $(dir $(PYFILES))), $(notdir $(PYFILES:.py=.pyc))): $(PYFILES)
# 	echo "Edouard3_pyfiles: $(PYFILES), Edouard3_prereq: $^ , Edouard3_prereq_newer: $?, Edouard3_pyc: $(join $(addsuffix $(PYCACHE_DIR)/, $(dir $(PYFILES))), $(notdir $(PYFILES:.py=.pyc))) , Edouard3_target: $@ ,"
# 	$(PYTHON) -m compileall $?
# pyc_compile: $(PYFILES) $(join $(addsuffix $(PYCACHE_DIR)/, $(dir $(PYFILES))), $(notdir $(PYFILES:.py=.pyc)))
# 	echo "Edouard3_pyfiles: $(PYFILES), Edouard3_prereq: $^ , Edouard3_prereq_newer: $?, Edouard3_pyc: $(join $(addsuffix $(PYCACHE_DIR)/, $(dir $(PYFILES))), $(notdir $(PYFILES:.py=.pyc))), Edouard3_pyc2: $(PYFILES:%.py=$(PYCACHE_DIR)/%.$(PY_CACHE_TAG).pyc)"
# pyc_compile: $(PYFILES) $(join $(addsuffix ./$(PYCACHE_DIR)/, $(dir $(PYFILES))), $(notdir $(PYFILES:.py=.pyc)))
# 	echo "Edouard3_pyfiles: $(PYFILES), Edouard3_prereq: $^ , Edouard3_prereq_newer: $?"
# pyc_compile: $($(PYFILES))
# 	echo "Edouard3_pyfiles: $(PYFILES), Edouard3_prereq: $^"
# echo "Edouard2_echo_target: $@ , Edouard2_echo_target_dir: $(@D), Edouard2_echo_prereq: $^ , Edouard2_echo_prereq_first: $< , Edouard2_echo_prereq_first_dir: $(<D) , Edouard2_echo_newer_prereq: $? " 
# $(PYTHON) -m compileall 
# pyc_compile: $(PYFILES_TO_COMPILE)
# 	echo "Edouard2_echo_target: $@ , Edouard2_echo_target_dir: $(@D), Edouard2_echo_prereq: $^ , Edouard2_echo_prereq_first: $< , Edouard2_echo_prereq_first_dir: $(<D) , Edouard2_echo_newer_prereq: $? " 
# # $(PYTHON) -m compileall 
# pyc_compile: $(PYFILES)
# 	echo "Edouard2_echo_target: $@ , Edouard2_echo_target_dir: $(@D), Edouard2_echo_prereq: $^ , Edouard2_echo_prereq_first: $< , Edouard2_echo_prereq_first_dir: $(<D) , Edouard2_echo_newer_prereq: $? " 
# # $(PYTHON) -m compileall 

.PHONY: pyc_compile