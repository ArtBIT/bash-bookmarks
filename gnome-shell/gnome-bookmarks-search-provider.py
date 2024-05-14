#!/usr/bin/python3
# This file is a part of gnome-bookmarks-search-provider.
# Gnome Search Provider boilerplate taken from https://github.com/jle64/gnome-pass-search-provider

import sys
import re
import subprocess
import json
from os import getenv
from os import walk
from os.path import expanduser
from os.path import join as path_join

import dbus.service
from dbus.mainloop.glib import DBusGMainLoop

from gi.repository import GLib

# Convenience shorthand for declaring dbus interface methods.
# s.b.n. -> search_bus_name
search_bus_name = "org.gnome.Shell.SearchProvider2"
sbn = dict(dbus_interface=search_bus_name)


class SearchBookmarksService(dbus.service.Object):
    """
        The bookmarks search daemon.
    """

    bus_name = "org.gnome.Bookmarks.SearchProvider"
    _object_path = "/" + bus_name.replace(".", "/")

    def __init__(self):
        self.session_bus = dbus.SessionBus()
        bus_name = dbus.service.BusName(self.bus_name, bus=self.session_bus)
        dbus.service.Object.__init__(self, bus_name, self._object_path)
        self.disable_notifications = (
            getenv("DISABLE_NOTIFICATIONS", "false").lower() == "true"
        )
        self.results = {}


        # read environment variable
        if getenv("BOOKMARKS_CMD"):
            self.cmd = getenv("BOOKMARKS_CMD")
        else:
            self.cmd = path_join(expanduser("~"), "Documents", "bookmarks", "bookmarks")

        # check if self.cmd is executable
        if not self.cmd:
            print("Error: bookmarks_CMD environment variable not set.")
            self.cmd = None

        if not subprocess.call(["which", self.cmd]):
            print(f"Error: {self.cmd} not found.")
            self.cmd = None

    @dbus.service.method(in_signature="sasu", **sbn)
    def ActivateResult(self, identifier, terms, timestamp):
        """
        ActivateResult is called when the user clicks on an individual result to
        open it in the application. The arguments are the result ID, the current
        search terms and a timestamp.
        """
        # open the url in the default browser
        result = self.results[identifier]
        if not result:
            self.notify("Error", f"Could not find the result with identifier {identifier}", error=True)
            return 

        # open the url in the default browser
        command = ['xdg-open', result['url']]
        with subprocess.Popen(command) as process:
            process.wait()


    @dbus.service.method(in_signature="as", out_signature="as", **sbn)
    def GetInitialResultSet(self, terms):
        """
        GetInitialResultSet is called when a new search is started. It gets an
        array of search terms as arguments, and should return an array of result
        IDs. gnome-shell will call GetResultMetas for (some) of these result IDs
        to get details about the result that can be be displayed in the result
        list.
        """
        results = self.search(terms)
        # results is a json array of search results
        # each search result is a dictionary with keys 'url', 'title', 'category', 'tags'

        # store the search results. key by id
        self.results = {result['id']: result for result in results}

        results = list(self.results.keys())

        return results

    @dbus.service.method(in_signature="as", out_signature="aa{sv}", **sbn)
    def GetResultMetas(self, identifiers):
        """
        GetResultMetas is called to obtain detailed information for results. It
        gets an array of result IDs as arguments, and should return a matching
        array of dictionaries (ie one a{sv} for each passed-in result ID). The
        following pieces of information should be provided for each result:
            “id”: the result ID
            “name”: the display name for the result
            “icon”: a serialized GIcon (see g_icon_serialize()), or alternatively,
            “gicon”: a textual representation of a GIcon (see g_icon_to_string()), or alternatively,
            “icon-data”: a tuple of type (iiibiiay) describing a pixbuf with width, height, rowstride, has-alpha, bits-per-sample, n-channels, and image data
            “description”: an optional short description (1-2 lines)
            “clipboardText”: an optional text to send to the clipboard on activation
        """
        # loop over the identifiers and return the result metas
        result_metas = []
        for identifier in identifiers:
            result = self.results[identifier]
            result_meta = {
                'id': identifier,
                'name': result['url'],
                'description': result['title'],
                'gicon': 'url-copy',
            }
            result_metas.append(result_meta)

        return result_metas

    @dbus.service.method(in_signature="asas", out_signature="as", **sbn)
    def GetSubsearchResultSet(self, previous_results, new_terms):
        """
        GetSubsearchResultSet is called to refine the initial search results
        when the user types more characters in the search entry. It gets the
        previous search results and the current search terms as arguments, and
        should return an array of result IDs, just like GetInitialResultSet.
        """
        results = self.search(new_terms)
        # results is a json array of search results
        # each search result is a dictionary with keys 'url', 'title', 'category', 'tags'
        self.results = {result['id']: result for result in results}
        results = list(self.results.keys())

        return results


    @dbus.service.method(in_signature="asu", terms="as", timestamp="u", **sbn)
    def LaunchSearch(self, terms, timestamp):
        """
        LaunchSearch is called when the user clicks on the provider icon to
        display more search results in the application. The arguments are the
        current search terms and a timestamp.
        """
        # since we are using commandline tool to search, we don't need to do anything here
        self.notify(f"Launched Bookmark search for {terms}")
        pass

    def notify(self, message, body="", error=False):
        if not error and self.disable_notifications:
            return
        try:
            self.session_bus.get_object(
                "org.freedesktop.Notifications", "/org/freedesktop/Notifications"
            ).Notify(
                "Bookmarks",
                0,
                "url-copy",
                message,
                body,
                "",
                {"transient": False if error else True},
                0 if error else 3000,
                dbus_interface="org.freedesktop.Notifications",
            )
        except dbus.DBusException as err:
            print(f"Error {err} while trying to display {message}.")

    def search(self, terms):
        """
        Perform bookmarks search using the commandline tool
        """
        if self.cmd is None:
            return []
        search_value = ' '.join(terms)
        # search all the files in the directory tree using commandline
        command = [self.cmd, 'suggest', search_value]
        result = subprocess.check_output(command)
        try:
            result = json.loads(result)
        except json.JSONDecodeError:
            self.notify("Error", f"Could not decode the search results: {result}", error=True)
            result = []
        return result

if __name__ == "__main__":
    DBusGMainLoop(set_as_default=True)
    provider = SearchBookmarksService()
    #provider.notify("Bookmarks Search Provider", self.cmd)
    #results = provider.GetResultMetas(provider.GetInitialResultSet(sys.argv[1:]))
    #print(results)
    # results = {result['url']: result for result in results}
    # print(list(results.keys()))

    GLib.MainLoop().run()
