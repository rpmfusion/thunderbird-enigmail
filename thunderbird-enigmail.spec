%define desktop_file_utils_version 0.9
%define nspr_version 4.6
%define nss_version 3.10
%define cairo_version 1.0

%define official_branding 1

%define thunver    2.0.0.21

Summary:        Authentication and encryption extension for Mozilla Thunderbird
Name:           thunderbird-enigmail
Version:        0.96.0
Release:        1%{?dist}
URL:            http://enigmail.mozdev.org/
License:        MPLv1.1 or GPLv2+
Group:          Applications/Internet
Source0:        http://releases.mozilla.org/pub/mozilla.org/thunderbird/releases/%{thunver}/source/thunderbird-%{thunver}-source.tar.bz2
Source10:       thunderbird-mozconfig
Source11:       thunderbird-mozconfig-branded

# ===== Enigmail files =====
Source100:  http://www.mozilla-enigmail.org/downloads/src/enigmail-%{version}.tar.gz

# From sunbird.src.rpm
Source102: mozilla-extension-update.sh


# Build patches
Patch1:         firefox-2.0-link-layout.patch
Patch2:         firefox-1.0-prdtoa.patch

Patch10:        thunderbird-0.7.3-psfonts.patch
Patch11:        thunderbird-0.7.3-gnome-uriloader.patch

# customization patches
Patch24:        thunderbird-2.0-default-applications.patch

# local bugfixes
Patch40:        firefox-1.5-bullet-bill.patch
Patch41:        firefox-2.0.0.4-undo-uriloader.patch
Patch42:        firefox-1.1-uriloader.patch

# font system fixes
Patch83:        firefox-1.5-pango-cursor-position.patch
Patch84:        firefox-2.0-pango-printing.patch
Patch85:        firefox-1.5-pango-cursor-position-more.patch
Patch86:        firefox-1.5-pango-justified-range.patch
Patch87:        firefox-1.5-pango-underline.patch
Patch88:        firefox-1.5-xft-rangewidth.patch
Patch89:        firefox-2.0-pango-ligatures.patch

# Other 
Patch102:       firefox-1.5-theme-change.patch
Patch103:       thunderbird-1.5-profile-migrator.patch
Patch111:       thunderbird-path.patch
Patch112:       thunderbird-2.0-enable-debug.patch

# Specific enigmail, to avoid : hidden symbol NS_NewGenericModule2
Patch200:       thunderbird-2.0.0.4-suse-visibility.patch

%if %{official_branding}
# Required by Mozilla Corporation


%else
# Not yet approved by Mozillla Corporation


%endif

BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
Requires:       nspr >= %{nspr_version}
Requires:       nss >= %{nss_version}
%if 0%{?rhel} >= 5
Requires:       launchmail
%endif
BuildRequires:  cairo-devel >= %{cairo_version}
BuildRequires:  libpng-devel, libjpeg-devel, gtk2-devel
BuildRequires:  zlib-devel, gzip, zip, unzip
BuildRequires:  nspr-devel >= %{nspr_version}
BuildRequires:  nss-devel >= %{nss_version}
BuildRequires:  libIDL-devel
BuildRequires:  desktop-file-utils
BuildRequires:  freetype-devel
BuildRequires:  libXt-devel
BuildRequires:  libXrender-devel

%define mozappdir %{_libdir}/thunderbird-%{thunver}

# Without this enigmmail will require libxpcom.so and other .so  
# which are not provided by thunderbird (to avoid mistake, 
# because provided by xulrunner). 
AutoReq:  0
# All others deps already required by thunderbird
Requires: gnupg, thunderbird >= %{thunver}

# Nothing usefull provided
AutoProv: 0

%global enigmail_extname '{847b3a00-7ab1-11d4-8f02-006008948af5}'
%global tbupdate                                          \\\
        %{_libdir}/%{name}/mozilla-extension-update.sh    \\\
        --appname thunderbird                             \\\
        --extname %{enigmail_extname}                     \\\
        --basedir %{_libdir}                              \\\
        --extpath %{_libdir}/%{name}                      \\\
        --action 


%description
Enigmail is an extension to the mail client Mozilla Thunderbird
which allows users to access the authentication and encryption
features provided by GnuPG 

#===============================================================================

%prep
%setup -q -c
cd mozilla

%patch1 -p1 -b .link-layout
%patch2 -p0

# to avoid : hidden symbol NS_NewGenericModule2
%patch200 -p0 -b .visibility

%patch10 -p1 -b .psfonts
%patch11 -p1 -b .gnome-uriloader
%patch24 -p1 -b .default-applications
%patch40 -p1
%patch41 -p1
%patch42 -p0
# font system fixes
%patch83 -p1 -b .pango-cursor-position
%patch84 -p0 -b .pango-printing
%patch85 -p1 -b .pango-cursor-position-more
%patch86 -p1 -b .pango-justified-range
%patch87 -p1 -b .pango-underline
%patch88 -p1 -b .nopangoxft2
%patch89 -p1 -b .pango-ligatures
pushd gfx/src/ps
  # This sort of sucks, but it works for now.
  ln -s ../gtk/nsFontMetricsPango.h .
  ln -s ../gtk/nsFontMetricsPango.cpp .
  ln -s ../gtk/mozilla-decoder.h .
  ln -s ../gtk/mozilla-decoder.cpp .
popd


%patch102 -p0 -b .theme-change
%patch103 -p1 -b .profile-migrator
%patch111 -p1 -b .path
%patch112 -p1 -b .debug

%if %{official_branding}
# Required by Mozilla Corporation


%else
# Not yet approved by Mozillla Corporation


%endif



%{__rm} -f .mozconfig
%{__cp} %{SOURCE10} .mozconfig
%if %{official_branding}
%{__cat} %{SOURCE11} >> .mozconfig
%endif

# ===== Enigmail work =====
tar xzf %{SOURCE100}
mv enigmail mailnews/extensions/

#===============================================================================

%build
cd mozilla

# Build with -Os as it helps the browser; also, don't override mozilla's warning
# level; they use -Wall but disable a few warnings that show up _everywhere_
MOZ_OPT_FLAGS=$(echo $RPM_OPT_FLAGS | %{__sed} -e 's/-O2/-Os/' -e 's/-Wall//')

export RPM_OPT_FLAGS=$MOZ_OPT_FLAGS
export PREFIX='%{_prefix}'
export LIBDIR='%{_libdir}'

%ifarch ppc ppc64 s390 s390x
%define moz_make_flags -j1
%else
%define moz_make_flags %{?_smp_mflags}
%endif

export LDFLAGS="-Wl,-rpath,%{mozappdir}"
export MAKE="gmake %{moz_make_flags}"
# make -f client.mk build
make -f client.mk export
pushd modules/libreg
make
cd ../../xpcom/string
make
cd ..
make
cd obsolete
make
popd

# ===== Enigmail work =====
pushd mailnews/extensions/enigmail
./makemake -r
make
make xpi
popd


#===============================================================================

%install
%{__rm} -rf $RPM_BUILD_ROOT

%{__mkdir_p} $RPM_BUILD_ROOT%{_libdir}

%{__unzip} -q mozilla/dist/bin/enigmail-%{version}-linux-*.xpi -d $RPM_BUILD_ROOT%{_libdir}/%{name}
%{__install} -p -m 755 %{SOURCE102} $RPM_BUILD_ROOT%{_libdir}/%{name}/mozilla-extension-update.sh



%clean
%{__rm} -rf $RPM_BUILD_ROOT


%post
%{tbupdate} install || :


%preun
if [ $1 = 0 ]; then
    %{tbupdate} remove || :
fi

%postun
# This is needed not to reverse the effect of our preun, which
# is guarded against upgrade, but because of our triggerun,
# which is run on self-upgrade, though triggerpostun isn't
if [ $1 != 0 ]; then
    %{tbupdate} install || :
fi

%triggerin -- thunderbird
%{tbupdate} install || :

%triggerun -- thunderbird
%{tbupdate} remove || :

%triggerpostun -- thunderbird
# Guard against being run post-self-uninstall, even though that
# doesn't happen currently (see comment above)
if [ $1 != 0 ]; then
    %{tbupdate} install || :
fi


%files
%defattr(-,root,root,-)
%{_libdir}/%{name}


#===============================================================================

%changelog
* Sat Jul 18 2009 Remi Collet <rpmfusion@famillecollet.com> 0.96.0-1
- update to 0.96.0 (thunderbird 2 only)

* Sat May 23 2009 Remi Collet <rpmfusion@famillecollet.com> 0.95.7-1.fc10.1
- fix mozconfig

* Sat May 23 2009 Remi Collet <rpmfusion@famillecollet.com> 0.95.7-1
- Initial rpmfusion RPM

