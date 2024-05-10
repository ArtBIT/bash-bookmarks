#!/usr/bin/env bash
set -eu -o pipefail
cd "$(dirname "$(realpath "${0}")")"

DATADIR=${DATADIR:-/usr/share}
LIBDIR=${LIBDIR:-/usr/lib}

# The actual executable
install -Dm 0755 gnome-bookmarks-search-provider.py "${LIBDIR}"/gnome-bookmarks-search-provider/gnome-bookmarks-search-provider.py

# Search provider definition
install -Dm 0644 conf/org.gnome.Bookmarks.SearchProvider.ini "${DATADIR}"/gnome-shell/search-providers/org.gnome.Bookmarks.SearchProvider.ini

# Desktop file (for having an icon)
install -Dm 0644 conf/org.gnome.Bookmarks.SearchProvider.desktop "${DATADIR}"/applications/org.gnome.Bookmarks.SearchProvider.desktop

# DBus configuration (no-systemd)
install -Dm 0644 conf/org.gnome.Bookmarks.SearchProvider.service.dbus "${DATADIR}"/dbus-1/services/org.gnome.Bookmarks.SearchProvider.service

# DBus configuration (systemd)
install -Dm 0644 conf/org.gnome.Bookmarks.SearchProvider.service.systemd "${LIBDIR}"/systemd/user/org.gnome.Bookmarks.SearchProvider.service
