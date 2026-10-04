
# common dependencies and rules for building scripts

$(SCRIPTDIR)/%: %.sh | $(SCRIPTDIR)
	$(INSTALL) $< $@

$(SCRIPTDIR)/%.sh: %.sh | $(SCRIPTDIR)
	$(INSTALL) $< $@

$(SCRIPTDIR):
	$(MKDIR) $(SCRIPTDIR)

$(ETCDIR)/%: % | $(ETCDIR)
	$(INSTALL_DATA) $< $@

$(ETCDIR):
	$(MKDIR) $(ETCDIR)
