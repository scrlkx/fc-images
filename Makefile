EXTENSION_NAME := fc_images_nautilus.py
EXTENSION_SRC  := $(CURDIR)/nautilus_extension.py
EXTENSIONS_DIR := $(HOME)/.local/share/nautilus-python/extensions

.PHONY: install-deps install-extension uninstall-extension restart-nautilus

install-deps:
	sudo dnf install -y nautilus-python

install-extension: $(EXTENSION_SRC)
	mkdir -p $(EXTENSIONS_DIR)
	ln -sf $(EXTENSION_SRC) $(EXTENSIONS_DIR)/$(EXTENSION_NAME)
	@echo "Extension installed at $(EXTENSIONS_DIR)/$(EXTENSION_NAME)"
	@echo "Execute 'make restart-nautilus' to load."

uninstall-extension:
	rm -f $(EXTENSIONS_DIR)/$(EXTENSION_NAME)
	@echo "Extension removed. Execute 'make restart-nautilus' to unload."

restart-nautilus:
	nautilus -q 2>/dev/null || true
	@echo "Nautilus restarted — the extensions will be loaded when opening Files."
