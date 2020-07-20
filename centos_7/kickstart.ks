auth --enableshadow --passalgo=sha512 --kickstart
# For some reason libguest can't detect the default (xfs)
# file system for CentOS 7 installs;  Overridden to use
# ext4 - Moate
autopart --type=lvm --fstype=ext4
# "biosdevname=0 net.ifnames=0"   gives traditional interface names eth0, eth1, ...
bootloader --location=mbr --timeout=1 --append="biosdevname=0 net.ifnames=0 console=tty0 console=ttyS0,115200"
url --url http://mirror.chtc.wisc.edu/centos/7/os/x86_64/
clearpart --all --initlabel
firewall --disabled
firstboot --disable
install
keyboard us
lang en_US.UTF-8
network --device eth0 --bootproto dhcp
reboot
repo --name=CentOS7-Updates --baseurl=http://mirror.chtc.wisc.edu/centos/7/updates/x86_64/
repo --name=CentOS7-Extras --baseurl=http://mirror.chtc.wisc.edu/centos/7/extras/x86_64/
repo --name=epel --baseurl=http://mirror.chtc.wisc.edu/epel/7/x86_64/
rootpw --iscrypted $1$22074107$h/Rm55DAZ37/ZhaVMPmFP/
selinux --permissive
skipx
text
timezone --isUtc --ntpservers ntp1.cs.wisc.edu,ntp2.cs.wisc.edu,ntp3.cs.wisc.edu America/Chicago
zerombr

%packages --instLangs=en_US.utf8 --nobase --excludedocs
@core
ntpdate
yum-plugin-priorities
at
bzip2
git
policycoreutils-python
%end


%post --log=/root/ks.log
yum -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
yum -y distro-sync
echo "enabled=0" >> /etc/yum/pluginconf.d/fastestmirror.conf
date > /etc/creation_date
mkdir /mnt/user
%end
