Name: myfyrio
Version: 0.4.1
Release: 1
Summary: Application searching for similar/duplicate images
License: GPLv3
Packager: Maxim Shpak <maxim.shpak@posteo.uk>
URL: https://github.com/oratosquilla-oratoria/%{name}/
Source0: https://github.com/oratosquilla-oratoria/%{name}/archive/v%{version}.tar.gz


# turn off build-id in package
%define _build_id_links none

%description
Myfyrio is a programme that searches for similar/duplicate images

%prep
# unpack tarball
%setup -q

%build

%install
cp -rfa . %{buildroot}

%files
%{_datadir}/applications/*
%{_datadir}/%{name}/*

%post
rm -f /usr/bin/Myfyrio
ln -s /usr/share/myfyrio/Myfyrio /usr/bin/Myfyrio

if hash desktop-file-install 2>/dev/null; then
	desktop-file-install /usr/share/applications/myfyrio.desktop
fi

%postun
rm -f /usr/bin/Myfyrio

%define build_timestamp %(date +"%a %b %d %Y")

%changelog
* %{build_timestamp} %{packager} - %{version}-%{release}
- Initial package
