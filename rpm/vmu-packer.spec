Summary: Scripts for using packer for making VMU images
Name: vmu-packer
Version: 1.1.0
Release: 1%{?dist}
License: Apache 2.0
Source0: %{name}-%{version}.tar.gz
Requires: packer-io
BuildArch: noarch
%define _debuginfo_subpackages %{nil}

%description
%{summary}

%prep
%autosetup

%build
exit 0

%install
make install DESTDIR=%{buildroot}
mkdir -p %{buildroot}/var/log/%{name}
echo '{"password":"ENTER PASSWORD HERE"}' > %{buildroot}/etc/%{name}/password.json

%files
/usr/bin/vmu-rebuild-one
/usr/bin/vmu-rebuild-all
/usr/share/%{name}
%attr(700,root,root) %dir /etc/%{name}
%attr(600,root,root) %config(noreplace) /etc/%{name}/password.json
%dir /var/log/%{name}

%changelog
* Fri Dec 18 2020 Mátyás Selmeci <matyas@cs.wisc.edu> - 1.1.0-1
- Add CentOS 8 Stream

* Wed Dec 09 2020 Mátyás Selmeci <matyas@cs.wisc.edu> - 1.0.1-1
- Update to CentOS 8.3

* Tue Jul 21 2020 Mátyás Selmeci <matyas@cs.wisc.edu> - 1.0.0-1
- Initial release
