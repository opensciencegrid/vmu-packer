Summary: Scripts for using packer for making VMU images
Name: vmu-packer
Version: 1.3.0
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
* Mon Nov 15 2021 Mátyás Selmeci <matyas@cs.wisc.edu> - 1.3.0-1
- Update to CentOS 8.4 (SOFTWARE-4886)

* Wed Jun 23 2021 Mátyás Selmeci <matyas@cs.wisc.edu> - 1.2.0-1
- Name the CentOS Stream 8 image centos_stream_8 instead of centos_8_stream
- Add Rocky Linux 8.4
- Use default file system type in CentOS 8 images instead of forcing ext4

* Tue Jan 12 2021 Mátyás Selmeci <matyas@cs.wisc.edu> - 1.1.1-1
- Build CentOS 8 Stream in vmu-rebuild-all

* Fri Dec 18 2020 Mátyás Selmeci <matyas@cs.wisc.edu> - 1.1.0-1
- Add CentOS 8 Stream

* Wed Dec 09 2020 Mátyás Selmeci <matyas@cs.wisc.edu> - 1.0.1-1
- Update to CentOS 8.3

* Tue Jul 21 2020 Mátyás Selmeci <matyas@cs.wisc.edu> - 1.0.0-1
- Initial release
