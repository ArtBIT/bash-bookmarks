# Makefile for bash-bookmarks
# Author: Djordje Ungar
# Created: 2024-05-14
#
# Usage:
# make install
# make uninstall
#
# License: MIT
#

# Variables
SHELL := /bin/bash

# The directory where the script will be installed
INSTALL_DIR=~/.local/share/bash-bookmarks

# The name of the script
SCRIPT_NAME=bookmarks

# The path to the script
SCRIPT_PATH=$(INSTALL_DIR)/$(SCRIPT_NAME)
#
# The path to the uninstall script
UNINSTALL_SCRIPT_PATH=$(INSTALL_DIR)/uninstall-$(SCRIPT_NAME)

SERVICE_NAME=$(SCRIPT_NAME)
#SYSTEMD_USER_DIR=$(shell pkg-config systemd --variable=systemduserconfdir)
SYSTEMD_USER_DIR=~/.config/systemd/user
APPLICATIIONS_DIR=~/.local/share/applications

all: install-all

install: files rc service uri done

install-base: files rc done

files:
	@echo "Installing $(SCRIPT_NAME)..."

	@echo "Copying script files"
	@mkdir -p $(INSTALL_DIR)

	@# And automatically start creating the uninstall script
	@echo "#!/bin/bash" > $(UNINSTALL_SCRIPT_PATH)
	@echo "rm -rf $(INSTALL_DIR)" >> $(UNINSTALL_SCRIPT_PATH)
	@chmod 755 $(UNINSTALL_SCRIPT_PATH)

	@cp $(SCRIPT_NAME) $(SCRIPT_PATH)
	@cp .bookmarks.env $(INSTALL_DIR)
	@cp .bookmarksrc $(INSTALL_DIR)
	@chmod 755 $(SCRIPT_PATH)

rc:
	@echo "Adding rc to .bashrc..."
	@if ! grep -q "source $(INSTALL_DIR)/.bookmarksrc" ~/.bashrc; then \
		echo "source $(INSTALL_DIR)/.bookmarksrc" >> ~/.bashrc; \
		echo "sed -i '/source $(INSTALL_DIR)\/.bookmarksrc/d' ~/.bashrc" >> $(UNINSTALL_SCRIPT_PATH); \
	fi

server:
	@echo "Copying server files..."
	@# Copy the server file to install_dir
	@cp $(SCRIPT_NAME)-server.py $(INSTALL_DIR)
	@cp -r ./static $(INSTALL_DIR)


service: server
	@echo "Creating service..."
	@mkdir -p $(SYSTEMD_USER_DIR)

	@echo "Installing $(SCRIPT_NAME) service to $(SYSTEMD_USER_DIR)"
	@cp  $(SERVICE_NAME).service $(SYSTEMD_USER_DIR)/

	@# Enable the service to start on boot
	@systemctl --user enable $(SERVICE_NAME)

	@echo "systemctl --user disable $(SERVICE_NAME)" >> $(UNINSTALL_SCRIPT_PATH)
	@echo "rm -f $(SYSTEMD_USER_DIR)/$(SERVICE_NAME).service" >> $(UNINSTALL_SCRIPT_PATH)

	@# start it
	@systemctl --user start $(SERVICE_NAME)


uri:
	@echo "Creating uri handler..."
	@cp  $(SCRIPT_NAME)-uri-handler $(INSTALL_DIR)
	@echo "Uri handler created."

	@echo "Creating desktop file..."
	@cp $(SCRIPT_NAME).desktop $(APPLICATIIONS_DIR)
	@echo "rm $(APPLICATIIONS_DIR)/$(SCRIPT_NAME).desktop" >> $(UNINSTALL_SCRIPT_PATH)

	@update-desktop-database
	@echo "Desktop file created."

	

search-provider:
	@echo "Registering bookmarks gnome search provider..."
	@cd gnome; ./install.sh

mime:
	xdg-mime default bookmarks.desktop x-scheme-handler/bookmarks
	@# Test
	@# xdg-open 'bookmarks://?title=Test&uri=https%3A%2F%2Fgoogle.com&category=search&tags=[]'

done:
	@echo "Installation done."

uninstall:
	@echo "Uninstalling $(SCRIPT_NAME)..."
	@$(UNINSTALL_SCRIPT_PATH)
	@echo "Uninstallation done."

.PHONY: all install install-all uninstall service uri done

