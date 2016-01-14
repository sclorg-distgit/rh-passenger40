%global scl_name_prefix  rh-
%global scl_name_base    passenger
%global scl_name_version 40
%global scl              %{scl_name_prefix}%{scl_name_base}%{scl_name_version}
%scl_package %scl

# Turn on new layout -- prefix for packages and location
# for config and variable files
# This must be before calling %%scl_package
%{!?nfsmountable: %global nfsmountable 1}

# do not produce empty debuginfo package
%global debug_package %{nil}

Summary:       Package that installs %scl
Name:          %scl_name
Version:       2.0
Release:       8%{?dist}
License:       GPLv2+
Group: Applications/File
Source0: README
Source1: LICENSE

BuildRoot:     %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires: scl-utils-build
# Temporary work-around
BuildRequires: iso-codes
BuildRequires: help2man
BuildRequires: ruby193-scldevel
BuildRequires: ruby193-rubygems-devel

Requires: %{scl_prefix}passenger
Requires: %{scl_prefix}mod_passenger

%description
This is the main package for %scl Software Collection.

%package runtime
Summary:   Package that handles %scl Software Collection.
Requires:  scl-utils
Requires(post): policycoreutils-python

%description runtime
Package shipping essential scripts to work with %scl Software Collection.

%package build
Summary:   Package shipping basic build configuration
Requires:  scl-utils-build

%description build
Package shipping essential configuration macros to build %scl Software Collection.

%package scldevel
Summary:   Package shipping development files for %scl
Group:     Development/Languages

%description scldevel
Package shipping development files, especially usefull for development of
packages depending on %scl Software Collection.

%prep
%setup -c -T
# This section generates README file from a template and creates man page
# from that file, expanding RPM macros in the template file.
cat >README <<'EOF'
%{expand:%(cat %{SOURCE0})}
EOF

# copy the license file so %%files section sees it
cp %{SOURCE1} .

cat <<EOF | tee enable
export PATH=%{_bindir}:%{_sbindir}\${PATH:+:\${PATH}}
export MANPATH=%{_mandir}:\${MANPATH}
export LD_LIBRARY_PATH=%{_libdir}\${LD_LIBRARY_PATH:+:\${LD_LIBRARY_PATH}}
export PKG_CONFIG_PATH=%{_libdir}/pkgconfig\${PKG_CONFIG_PATH:+:\${PKG_CONFIG_PATH}}
EOF

# generate rpm macros file for depended collections
cat << EOF | tee scldev
%%scl_%{scl_name_base}         %{scl}
%%scl_prefix_%{scl_name_base}  %{scl_prefix}
EOF

%build
# generate a helper script that will be used by help2man
cat >h2m_helper <<'EOF'
#!/bin/bash
[ "$1" == "--version" ] && echo "%{scl_name} %{version} Software Collection" || cat README
EOF
chmod a+x h2m_helper

# generate the man page
help2man -N --section 7 ./h2m_helper -o %{scl_name}.7

%install
mkdir -p %{buildroot}%{_scl_scripts}/root
install -m 644 enable  %{buildroot}%{_scl_scripts}/enable
install -D -m 644 scldev %{buildroot}%{_root_sysconfdir}/rpm/macros.%{scl_name_base}-scldevel

# install generated man page
mkdir -p %{buildroot}%{_mandir}/man1/
mkdir -p %{buildroot}%{_mandir}/man3/
mkdir -p %{buildroot}%{_mandir}/man7/
mkdir -p %{buildroot}%{_mandir}/man8/
mkdir -p %{buildroot}%{_libdir}/pkgconfig/
mkdir -p %{buildroot}%{_datadir}/aclocal/
mkdir -p %{buildroot}%{_datadir}/gems/cache
mkdir -p %{buildroot}%{_datadir}/gems/doc
mkdir -p %{buildroot}%{_datadir}/gems/gems
mkdir -p %{buildroot}%{_datadir}/gems/specifications
mkdir -p %{buildroot}%{_libdir}/gems/exts

install -m 644 %{scl_name}.7 %{buildroot}%{_mandir}/man7/%{scl_name}.7

%scl_install

cat >> %{buildroot}%{_scl_scripts}/service-environment << EOF
# Services are started in a fresh environment without any influence of user's
# environment (like environment variable values). As a consequence,
# information of all enabled collections will be lost during service start up.
# If user needs to run Passenger with any software collection enabled, this
# collection has to be written into particular variable in
# /opt/rh/sclname/service-environment file.
RH_PASSENGER40_RUBY193_SCLS_ENABLED="%{scl} ruby193"
RH_PASSENGER40_RUBY200_SCLS_ENABLED="%{scl} ruby200 ror40"
RH_PASSENGER40_RUBY22_SCLS_ENABLED="%{scl} rh-ruby22 rh-ror41"
EOF

# create directory for SCL register scripts
mkdir -p %{buildroot}%{?_scl_scripts}/register.content
mkdir -p %{buildroot}%{?_scl_scripts}/register.d
cat <<EOF | tee %{buildroot}%{?_scl_scripts}/register
#!/bin/sh
ls %{?_scl_scripts}/register.d/* | while read file ; do
    [ -x \$f ] && source \$(readlink -f \$file)
done
EOF
# and deregister as well
mkdir -p %{buildroot}%{?_scl_scripts}/deregister.d
cat <<EOF | tee %{buildroot}%{?_scl_scripts}/deregister
#!/bin/sh
ls %{?_scl_scripts}/deregister.d/* | while read file ; do
    [ -x \$f ] && source \$(readlink -f \$file)
done
EOF

%post runtime
# Simple copy of context from system root to DSC root.
# In case new version needs some additional rules or context definition,
# it needs to be solved.
# Unfortunately, semanage does not have -e option in RHEL-5, so we have to
# have its own policy for collection
semanage fcontext -a -e / %{_scl_root} >/dev/null 2>&1 || :
restorecon -R %{_scl_root} >/dev/null 2>&1 || :
selinuxenabled && load_policy || :

%files

%files runtime
%defattr(-,root,root)
%doc README LICENSE
%scl_files
%dir %{_mandir}/man1
%dir %{_mandir}/man3
%dir %{_mandir}/man7
%dir %{_mandir}/man8
%dir %{_libdir}/pkgconfig
%dir %{_datadir}/aclocal
%{_datadir}/gems
%{_libdir}/gems
%{_mandir}/man7/%{scl_name}.*
%config(noreplace) %{_scl_scripts}/service-environment
%attr(0755,root,root) %{?_scl_scripts}/register
%attr(0755,root,root) %{?_scl_scripts}/deregister
%{?_scl_scripts}/register.content
%dir %{?_scl_scripts}/register.d
%dir %{?_scl_scripts}/deregister.d

%files build
%defattr(-,root,root)
%{_root_sysconfdir}/rpm/macros.%{scl}-config

%files scldevel
%defattr(-,root,root)
%{_root_sysconfdir}/rpm/macros.%{scl_name_base}-scldevel

%changelog
* Thu Mar 17 2015 Jan Kaluza <jkaluza@redhat.com> - 2.0-8
- add missing README (#1200708)

* Thu Mar 12 2015 Jan Kaluza <jkaluza@redhat.com> - 2.0-7
- add unowned directories (#1201233)

* Tue Mar 10 2015 Jan Kaluza <jkaluza@redhat.com> - 2.0-6
- rebuild to remove scls directory (#1200053)

* Tue Feb 17 2015 Jan Kaluza <jkaluza@redhat.com> - 2.0-5
- fix -scldevel macros (#1193390)

* Mon Jan 26 2015 Jan Kaluza <jkaluza@redhat.com> - 2.0-4
- add support for NFS

* Mon Jan 19 2015 Jan Kaluza <jkaluza@redhat.com> - 2.0-3
- add support for rh-ruby22 SCL

* Thu Jan 08 2015 Jan Kaluza <jkaluza@redhat.com> - 2.0-2
- add service-environment config file

* Tue Jan 06 2015 Jan Kaluza <jkaluza@redhat.com> - 2.0-1
- initial packaging
