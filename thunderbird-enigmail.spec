%define nspr_version 4.6
%define nss_version 3.10
%define cairo_version 1.0
%define dbus_glib_version 0.6

%define official_branding 1

%define thunver    3.0

%define CVS 20090521

Summary:        Authentication and encryption extension for Mozilla Thunderbird
Name:           thunderbird-enigmail
Version:        0.96a
Release:        0.3.cvs%{CVS}%{?dist}
URL:            http://enigmail.mozdev.org/
License:        MPLv1.1 or GPLv2+
Group:          Applications/Internet
Source0:        http://releases.mozilla.org/pub/mozilla.org/thunderbird/releases/%{thunver}/source/thunderbird-%{thunver}b2-source.tar.bz2

Source10:       thunderbird-mozconfig
Source11:       thunderbird-mozconfig-branded

# ===== Enigmail files =====
#Source100:  http://www.mozilla-enigmail.org/downloads/src/enigmail-%{version}.tar.gz

# cvs -d :pserver:guest@mozdev.org:/cvs login
# => password is guest 
# cvs -d :pserver:guest@mozdev.org:/cvs co enigmail/src
# tar czf /home/rpmbuild/SOURCES/enigmail-20090521.tgz -C enigmail/src .
Source100: enigmail-%{CVS}.tgz

# http://www.mozdev.org/pipermail/enigmail/2009-April/011018.html
Source101: enigmail-fixlang.php

# From sunbird.src.rpm
Source102: mozilla-extension-update.sh

# Build patches
Patch1:         mozilla-jemalloc.patch
Patch2:         thunderbird-shared-error.patch
Patch3:         xulrunner-elif.patch
Patch4:         thunderbird-pango.patch
Patch5:         thunderbird-imap-startup-crash.patch


%if %{official_branding}
# Required by Mozilla Corporation


%else
# Not yet approved by Mozillla Corporation


%endif

BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires:  libcurl-devel
BuildRequires:  cairo-devel >= %{cairo_version}
BuildRequires:  dbus-glib-devel >= %{dbus_glib_version}
BuildRequires:  libpng-devel, libjpeg-devel, gtk2-devel
BuildRequires:  zlib-devel, gzip, zip, unzip
BuildRequires:  nspr-devel >= %{nspr_version}
BuildRequires:  nss-devel >= %{nss_version}
BuildRequires:  libIDL-devel
BuildRequires:  desktop-file-utils
BuildRequires:  pango-devel >= 1.22
BuildRequires:  freetype-devel >= 2.1.9
BuildRequires:  libXt-devel
BuildRequires:  libXrender-devel
BuildRequires:  alsa-lib-devel
BuildRequires:  autoconf213
BuildRequires:  GConf2-devel
BuildRequires:  gnome-vfs2-devel
BuildRequires:  libgnomeui-devel


%define mozappdir %{_libdir}/thunderbird-%{thunver}b2

## For fixing lang
BuildRequires:  dos2unix, php-cli

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
#cd mozilla

%patch1 -p0 -b .jemalloc
%patch2 -p1 -b .shared-error
%patch3 -p0 -b .xulrunner-elif
%patch4 -p1 -b .pango-fix
%patch5 -p1 -b .imap-startup-crash

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
mkdir mailnews/extensions/enigmail
tar xzf %{SOURCE100} -C mailnews/extensions/enigmail

# ===== Fixing langpack
pushd mailnews/extensions/enigmail
for rep in $(cat lang/current-languages.txt)
do
   dos2unix lang/$rep/enigmail.dtd
   dos2unix lang/$rep/enigmail.properties
   php %{SOURCE101} ui/locale/en-US lang/$rep
done
popd

#===============================================================================

%build
#cd mozilla

# Build with -Os as it helps the browser; also, don't override mozilla's warning
# level; they use -Wall but disable a few warnings that show up _everywhere_
MOZ_OPT_FLAGS=$(echo $RPM_OPT_FLAGS | %{__sed} -e 's/-O2/-Os/' -e 's/-Wall//')

export RPM_OPT_FLAGS=$MOZ_OPT_FLAGS
export PREFIX='%{_prefix}'
export LIBDIR='%{_libdir}'

%define moz_make_flags -j1
#%ifarch ppc ppc64 s390 s390x
#%define moz_make_flags -j1
#%else
#%define moz_make_flags %{?_smp_mflags}
#%endif

export LDFLAGS="-Wl,-rpath,%{mozappdir}"
export MAKE="gmake %{moz_make_flags}"

# ===== Minimal build =====
make -f client.mk export
pushd objdir-tb/mozilla/modules/libreg
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
popd

pushd objdir-tb/mailnews/extensions/enigmail
make
make xpi
popd


#===============================================================================

%install
%{__rm} -rf $RPM_BUILD_ROOT

%{__mkdir_p} $RPM_BUILD_ROOT%{_libdir}

%{__unzip} -q objdir-tb/mozilla/dist/bin/enigmail-%{version}-linux-*.xpi -d $RPM_BUILD_ROOT%{_libdir}/%{name}
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
* Thu May 21 2009 Remi Collet <rpms@famillecollet.com> 0.96a-0.3.cvs20090521
- new CVS snapshot
- fix License and Sumnary

* Mon May 18 2009 Remi Collet <rpms@famillecollet.com> 0.96a-0.2.cvs20090516
- use mozilla-extension-update.sh from thunderbird-lightning

* Sat May 16 2009 Remi Collet <rpms@famillecollet.com> 0.96a-0.1.cvs20090516
- new CVS snapshot
- rpmfusion review proposal

* Thu Apr 30 2009 Remi Collet <rpms@famillecollet.com> 0.96a-0.1.cvs20090430.fc11.remi
- new CVS snapshot
- F11 build

* Mon Mar 16 2009 Remi Collet <rpms@famillecollet.com> 0.96a-0.1.cvs20090316.fc#.remi
- new CVS snapshot
- add enigmail-fixlang.php

* Sun Mar 15 2009 Remi Collet <rpms@famillecollet.com> 0.96a-0.1.cvs20090315.fc#.remi
- enigmail 0.96a (CVS), Thunderbird 3.0b2

