#auth --enableshadow --passalgo=sha512 --kickstart
autopart --type=lvm --fstype=ext4
bootloader --location=mbr --timeout=1 --append="console=tty0 console=ttyS0,115200"
cdrom
clearpart --all --initlabel
eula --agreed
firewall --disabled
firstboot --disabled
keyboard us
lang en_US.UTF-8
network --bootproto dhcp
reboot
rootpw --iscrypted $1$22074107$h/Rm55DAZ37/ZhaVMPmFP/
selinux --permissive
services --enabled=NetworkManager,sshd
skipx
text
timezone --isUtc --ntpservers ntp1.cs.wisc.edu,ntp2.cs.wisc.edu,ntp3.cs.wisc.edu America/Chicago
zerombr

%packages --instLangs=en_US.utf8 --excludedocs
@core
at
bzip2
findutils
git-core
gzip
make
policycoreutils-python-utils
sed
tar
%end


%post --log=/root/ks.log
yum -y config-manager --enable extras
yum -y config-manager --enable powertools
yum -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm
yum -y distro-sync
date > /etc/creation_date
mkdir /mnt/user
%end
