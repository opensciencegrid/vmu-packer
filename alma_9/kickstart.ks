#auth --enableshadow --passalgo=sha512 --kickstart
autopart --type=lvm --fstype=ext4 --nohome
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
timezone --utc America/Chicago
timesource --ntp-server ntp1.cs.wisc.edu
timesource --ntp-server ntp2.cs.wisc.edu
timesource --ntp-server ntp3.cs.wisc.edu
zerombr

%packages --inst-langs=en_US.utf8 --excludedocs
@core
at
bzip2
findutils
git-core
gzip
make
policycoreutils-python-utils
sed
libicu
tar
%end


%post --log=/root/ks.log
yum -y install yum-utils
yum -y config-manager --enable extras
yum -y config-manager --enable crb
yum -y config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
yum -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm
yum -y install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
yum -y distro-sync
systemctl enable docker
date > /etc/creation_date
mkdir /mnt/user
echo >> /etc/ssh/sshd_config
echo PermitRootLogin yes >> /etc/ssh/sshd_config
useradd -m runner
runuser -u runner -- /bin/sh -c 'mkdir /home/runner/actions-runner; cd /home/runner/actions-runner; pwd; curl -o actions-runner-linux-x64-2.309.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.309.0/actions-runner-linux-x64-2.309.0.tar.gz; tar xvzf ./actions-runner-linux-x64-2.309.0.tar.gz'
/home/runner/actions-runner/bin/installdependencies.sh
echo "runner	ALL=(ALL)	NOPASSWD: ALL" >> /etc/sudoers
%end
