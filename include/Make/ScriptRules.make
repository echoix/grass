
# common dependencies and rules for building scripts

$(SCRIPTDIR)/%: %.py | $(SCRIPTDIR)
	$(INSTALL) $< $@

$(SCRIPTDIR)/%.py: %.py | $(SCRIPTDIR)
	$(INSTALL) $< $@

$(SCRIPTDIR):
	$(MKDIR) $(SCRIPTDIR)

$(ETCDIR)/%: % | $(ETCDIR)
	$(INSTALL_DATA) $< $@

$(ETCDIR):
	$(MKDIR) $(ETCDIR)
