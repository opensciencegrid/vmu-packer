#auth --enableshadow --passalgo=sha512 --kickstart
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
# Using external repos does not work on CentOS 8 for some reason; must get everything from the ISO.
#repo --name=AppStream --baseurl=http://mirror.chtc.wisc.edu/centos/8/AppStream/x86_64/kickstart/
#repo --name=BaseOS --baseurl http://mirror.chtc.wisc.edu/centos/8/BaseOS/x86_64/kickstart/
#repo --name=extras --baseurl=http://mirror.chtc.wisc.edu/centos/8/extras/x86_64/kickstart/
#repo --name=PowerTools --baseurl=http://mirror.chtc.wisc.edu/centos/8/PowerTools/x86_64/kickstart/
#repo --name=epel --baseurl=http://mirror.chtc.wisc.edu/epel/8/x86_64/
#url --url http://mirror.chtc.wisc.edu/centos/8/BaseOS/x86_64/kickstart/
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
yum -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm
yum -y distro-sync
date > /etc/creation_date
mkdir /mnt/user
%end
