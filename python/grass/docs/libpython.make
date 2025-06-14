# SPDX-License-Identifier: GPL-2.0-or-later
# Author: Edouard Choinière (2025-06-14)

MODULE_TOPDIR=../../..
include $(MODULE_TOPDIR)/include/Make/Vars.make
include $(MODULE_TOPDIR)/include/Make/Rules.make

# Target overrides
## Clean should call the base rules for clean
clean: libpythonclean
libpythonclean:
	@$(call run_grass,$(MAKE) clean)

apidoc: libpythonapidoc
libpythonapidoc:
	@echo "libpythonapidoc make target was removed is now a no-op"

## Redirect the targets to the sphinx makefile, inside a grass session,
## via the .DEFAULT target.
## For example, the target "libpythonhtml" will call the target "html"
## inside a grass session.
libpython%: %
	@$(call run_grass,$(MAKE) $@)

# The catch-all target as used in the generated makefile is not appropriate
# with our included Make modules. Replaced with the .DEFAULT target
.DEFAULT: Makefile
	echo "00..target: $@"
	echo "02..target: $@"
	@$(call run_grass,$(MAKE) $@)
