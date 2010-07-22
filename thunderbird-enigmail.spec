%global nspr_version 4.8
%global nss_version 3.12.3.99
%global cairo_version 1.8.8
%global freetype_version 2.1.9
%global sqlite_version 3.6.22
%global libnotify_version 0.4
%global moz_objdir objdir-tb

%global thunver  3.1.1

# The tarball is pretty inconsistent with directory structure.
# Sometimes there is a top level directory.  That goes here.
#
# IMPORTANT: If there is no top level directory, this should be 
# set to the cwd, ie: '.'
#%define tarballdir .
%global tarballdir comm-1.9.2

%global official_branding 1

%global version_internal  3.1
%global mozappdir         %{_libdir}/thunderbird-%{version_internal}
%global enigmail_extname  %{_libdir}/mozilla/extensions/{3550f703-e582-4d05-9a08-453d09bdfdc6}/{847b3a00-7ab1-11d4-8f02-006008948af5}


Summary:        Authentication and encryption extension for Mozilla Thunderbird
Name:           thunderbird-enigmail
Version:        1.1.2
%if 0%{?prever:1}
Release:        0.1.%{prever}%{?dist}
%else
Release:        1%{?dist}
%endif
URL:            http://enigmail.mozdev.org/
License:        MPLv1.1 or GPLv2+
Group:          Applications/Internet
Source0:        thunderbird-%{thunver}%{?thunbeta}.source.tar.bz2

Source10:       thunderbird-mozconfig
Source11:       thunderbird-mozconfig-branded

# ===== Enigmail files =====
%if 0%{?CVS}
# cvs -d :pserver:guest@mozdev.org:/cvs login
# => password is guest 
# cvs -d :pserver:guest@mozdev.org:/cvs co enigmail/src
# tar czf /home/rpmbuild/SOURCES/enigmail-20091121.tgz --exclude CVS -C enigmail/src .
Source100:      enigmail-%{CVS}.tgz
%else
Source100:      http://www.mozilla-enigmail.org/download/source/enigmail-%{version}%{?prever}.tar.gz
%endif

# http://www.mozdev.org/pipermail/enigmail/2009-April/011018.html
Source101: enigmail-fixlang.php

# Fix for version issues
Patch0:         thunderbird-version.patch
# Fix for jemalloc
Patch1:         mozilla-jemalloc.patch
# Fix for installation fail when building with dynamic linked libraries
Patch2:         thunderbird-shared-error.patch
# Fixes gcc complain that nsFrame::delete is protected
Patch4:         xulrunner-1.9.2.1-build.patch
# Fix missing includes for crash reporter, remove in 3.1 final
Patch5:         xulrunner-missing-headers.patch
Patch6:         remove-static.patch

# Enigmail patch
Patch101:       enigmail-1.1.2-perm.patch

%if %{official_branding}
# Required by Mozilla Corporation

%else
# Not yet approved by Mozillla Corporation

%endif

BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires:  nspr-devel >= %{nspr_version}
BuildRequires:  nss-devel >= %{nss_version}
BuildRequires:  cairo-devel >= %{cairo_version}
BuildRequires:  libnotify-devel >= %{libnotify_version}
BuildRequires:  libpng-devel
BuildRequires:  libjpeg-devel
BuildRequires:  zip
BuildRequires:  bzip2-devel
BuildRequires:  zlib-devel, gzip, zip, unzip
BuildRequires:  libIDL-devel
BuildRequires:  gtk2-devel
BuildRequires:  gnome-vfs2-devel
BuildRequires:  libgnome-devel
BuildRequires:  libgnomeui-devel
BuildRequires:  krb5-devel
BuildRequires:  pango-devel
BuildRequires:  freetype-devel >= %{freetype_version}
BuildRequires:  libXt-devel
BuildRequires:  libXrender-devel
BuildRequires:  hunspell-devel
BuildRequires:  sqlite-devel >= %{sqlite_version}
BuildRequires:  startup-notification-devel
BuildRequires:  alsa-lib-devel
BuildRequires:  autoconf213
BuildRequires:  desktop-file-utils
BuildRequires:  GConf2-devel


## For fixing lang
%if 0%{?CVS}
BuildRequires:  dos2unix, php-cli
%endif

# Without this enigmmail will require libxpcom.so and other .so  
# which are not provided by thunderbird (to avoid mistake, 
# because provided by xulrunner). 
AutoReq:  0
# All others deps already required by thunderbird
Requires: gnupg, thunderbird >= %{version_internal}

# Nothing usefull provided
AutoProv: 0


%description
Enigmail is an extension to the mail client Mozilla Thunderbird
which allows users to access the authentication and encryption
features provided by GnuPG 

#===============================================================================

%prep
%setup -q -c
cd %{tarballdir}

sed -e 's/__RPM_VERSION_INTERNAL__/%{version_internal}/' %{P:%%PATCH0} \
    > version.patch
%{__patch} -p1 -b --suffix .version --fuzz=0 < version.patch

%patch1 -p0 -b .jemalloc
%patch2 -p1 -b .shared-error
%patch4 -p1 -b .protected
%patch5 -p0 -b .stat
%patch6 -p1 -b .static

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
# ===== Fixing langpack
%if 0%{?CVS}
mkdir mailnews/extensions/enigmail
tar xzf %{SOURCE100} -C mailnews/extensions/enigmail

pushd mailnews/extensions/enigmail
for rep in $(cat lang/current-languages.txt)
do
   dos2unix lang/$rep/enigmail.dtd
   dos2unix lang/$rep/enigmail.properties
   php %{SOURCE101} ui/locale/en-US lang/$rep
done
popd
%else
tar xzf %{SOURCE100} -C mailnews/extensions
pushd mailnews/extensions/enigmail
%patch101 -p1
popd
%endif

#===============================================================================

%build
cd %{tarballdir}

INTERNAL_GECKO=%{version_internal}
MOZ_APP_DIR=%{mozappdir}

# Build with -Os as it helps the browser; also, don't override mozilla's warning
# level; they use -Wall but disable a few warnings that show up _everywhere_
MOZ_OPT_FLAGS=$(echo $RPM_OPT_FLAGS | %{__sed} -e 's/-O2/-Os/' -e 's/-Wall//')

export RPM_OPT_FLAGS=$MOZ_OPT_FLAGS
export PREFIX='%{_prefix}'
export LIBDIR='%{_libdir}'

%define moz_make_flags -j1
%ifarch ppc ppc64 s390 s390x
%define moz_make_flags -j1
%else
%define moz_make_flags %{?_smp_mflags}
%endif

export LDFLAGS="-Wl,-rpath,%{mozappdir}"
export MAKE="gmake %{moz_make_flags}"

# ===== Minimal build =====
make -f client.mk export
pushd %{moz_objdir}/mozilla/modules/libreg
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

pushd %{moz_objdir}/mailnews/extensions/enigmail
make
make xpi
popd


#===============================================================================

%install
cd %{tarballdir}
%{__rm} -rf $RPM_BUILD_ROOT

%{__mkdir_p} $RPM_BUILD_ROOT%{enigmail_extname}

%{__unzip} -q %{moz_objdir}/mozilla/dist/bin/enigmail-*-linux-*.xpi -d $RPM_BUILD_ROOT%{enigmail_extname}
%{__chmod} +x $RPM_BUILD_ROOT%{enigmail_extname}/wrappers/*.sh


%clean
%{__rm} -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%{enigmail_extname}


#===============================================================================

%changelog
* Thu Jul 22 2010 Remi Collet <rpms@famillecollet.com> 1.1.2-1
- Enigmail 1.1.2 (against thunderbird 3.1.1)
- move to /usr/lib/mozilla/extensions (as lightning)
- sync patches with F-13

* Sat Jun 26 2010 Remi Collet <rpms@famillecollet.com> 1.1.1-2
- new sources (only fix displayed version)

* Sat Jun 26 2010 Remi Collet <rpms@famillecollet.com> 1.1.1-1.1
- missing BR libnotify-devel

* Sat Jun 26 2010 Remi Collet <rpms@famillecollet.com> 1.1.1-1
- Enigmail 1.1.1 (against thunderbird 3.1)

* Mon Feb 01 2010 Remi Collet <rpms@famillecollet.com> 1.0.1-1
- Enigmail 1.0.1 (against thunderbird 3.0.1)

* Mon Nov 30 2009 Remi Collet <rpms@famillecollet.com> 1.0.0-1
- Enigmail 1.0 (against thunderbird 3.0rc1)

* Sat Nov 21 2009 Remi Collet <rpms@famillecollet.com> 1.0-0.1.cvs20091121
- new CVS snapshot (against thunderbird 3.0rc1)

* Tue Jul 21 2009 Remi Collet <rpms@famillecollet.com> 0.97a-0.1.cvs20090721
- new CVS snapshot (against thunderbird 3.0b3)

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

