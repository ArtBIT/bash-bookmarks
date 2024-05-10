Name:           gnome-bookmarks-search-provider
Version:        master
Release:        1
License:        GPL-3.0+
Summary:        Gnome Shell search provider for bash-bookmarks
Url:            https://github.com/artbit/gnome-bookmarks-search-provider
Requires:       gnome-shell
Requires:       python3-gobject
Requires:       python3-dbus
BuildRoot:      %{_tmppath}/%{name}-%{version}-build

%global debug_package %{nil}

%description
A Gnome Shell search provider for zbash-bookmarks

%prep
%setup -q -n %{name}-%{version}

%build

%install
sed -i -e 's|DATADIR=|DATADIR=$RPM_BUILD_ROOT|' install.sh
sed -i -e 's|LIBDIR=|LIBDIR=$RPM_BUILD_ROOT|' install.sh
./install.sh

%files
%defattr(-,root,root,-)
%doc README.md
%{_prefix}/lib/gnome-bookmarks-search-provider/gnome-bookmarks-search-provider.py
%{_prefix}/lib/systemd/user/org.gnome.Bookmarks.SearchProvider.service
%{_prefix}/share/dbus-1/services/org.gnome.Bookmarks.SearchProvider.service
%{_prefix}/share/applications/org.gnome.Bookmarks.SearchProvider.desktop
%{_prefix}/share/gnome-shell/search-providers/org.gnome.Bookmarks.SearchProvider.ini
