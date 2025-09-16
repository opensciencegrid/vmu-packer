#!/usr/bin/env python3

# Python script that roughly mimics the workings of packer on ARM,
# where it is not well supported
#
# 1. Given a vars.json file, download the iso specified by those vars to a cache
#    location
# 2. Start an automated VM install using that iso as a base, passing in a 
#    kickstart file via extra kernel args using libvirt
# 3. Transfer a set of config files from the host into the guest via a volume mount
# 4. Attempt to log into the guest, copy the files into the local image, and run several shell commands
# 5. Optionally, transfer the resultant VM disk image from the libvirt storage pool to a location on disk

import pexpect
import json
import requests
import hashlib
from pathlib import Path
import subprocess
from time import sleep
import argparse
import random
from datetime import datetime, timedelta

# Attempt to cache things in a manner similar to packer

CACHE_DIR = Path() / 'packer_cache'
CHUNK_SIZE = 2**16

def hash_iso(iso_path: Path, algorithm: str = 'sha256') -> str:
    hash_func = hashlib.new(algorithm)
    with open(iso_path, 'rb') as iso_f:
        while chunk := iso_f.read(CHUNK_SIZE):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()

def download_iso(iso_dir: str, vars_path: Path) -> Path:
    ''' Given a vars.json, '''
    with open(vars_path, 'r') as varsf:
        iso_vars = json.loads(varsf.read())

    # TODO packer has a naming scheme for downloaded ISOs that's hard to replicate
    iso_url = iso_vars['iso_url']
    iso_name = Path(iso_url).name
    iso_path = iso_dir / iso_name

    
    algo, checksum = iso_vars['iso_checksum'].split(':')

    # If iso_path exists, check that it matches the expected checksum
    if not iso_path.exists():
        with requests.get(iso_url, stream=True) as r:
            r.raise_for_status()
            with open(iso_path, 'wb') as f:
                for i, chunk in enumerate(r.iter_content(chunk_size=CHUNK_SIZE)):
                    f.write(chunk)
                    if i % 5000 == 0:
                        print(f"Downloaded {CHUNK_SIZE * i / (1024 * 1024 * 1024)} GB of {iso_path}")

    iso_checksum = hash_iso(iso_path, algo)
    # TODO bail out here if these don't match!
    if checksum != iso_checksum:
        raise RuntimeError(f"Error downloading {iso_path}. Expected checksum {checksum}, got {iso_checksum}!")


    return iso_path

def launch_libvirt_build(iso_path: Path, kickstart_path: Path, storage_pool: str, img_size=10, fmt='raw') -> str:
    """
    Start an in-the-background libvert automated build based on the supplied iso, kickstart file,
    and output disk image
    """
    suffix = str(random.randint(1e5,1e6-1))
    name = iso_path.name + '-' + suffix
    cmd = [
        'virt-install',
        '--network', 'network=host-bridge,model=virtio',
#        '--network', 'default',
        '--name', name,
        '--disk', f'pool={storage_pool},size={img_size}',
#        '--disk', f'path=/var/lib/libvirt/images/{iso_path.name}.img,size={img_size},format=raw',
        '--boot', 'uefi',
        '--initrd-inject', kickstart_path,
        f'--extra-args="inst.ks=file:/{kickstart_path.name}"',
        '--noautoconsole',
        '--osinfo', 'detect=on,require=off',
        '--memory', '4096',
        '--location', iso_path
    ]

    subprocess.call(cmd)

    return name

def poll_libvirtd_progress(domain_name: str, sleep_interval: float = 5, timeout: float = 600):
    """
    Use `virsh list` to query whether an in-progress automated build is still running.
    Return once the automated build has completed
    """
    cmd = [
        'virsh',
        'list',
        '--state-running',
        '--name'
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()

    poll_start = datetime.now()
    while domain_name in out.decode() and datetime.now() - poll_start < timedelta(seconds=timeout):
        print(f"{domain_name} is still active after {(datetime.now() - poll_start).seconds} seconds, checking again in {sleep_interval} seconds")
        sleep(sleep_interval)
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
    
    if domain_name in out.decode():
        cmd = [
            'virsh',
            'destroy',
            domain_name
        ]
        subprocess.call(cmd)
        raise RuntimeError("VM build did not complete within time limit")
    
    print(f"VM build completed in {(datetime.now() - poll_start).seconds} seconds")

def _pexpect_with_timeout(pexpect_proc: any, cmd: str):
    outcome = pexpect_proc.expect([cmd, pexpect.TIMEOUT])
    if outcome != 0:
        raise RuntimeError(f"Timeout waiting for prompt '{cmd}' in pexpect")

def pexpect_console_setup(domain_name: str, password: str, host_dev: str = 'host_home', cmd="cp /tmp/host-data/* ~", login: str = 'root'):
    ''' 
    Use pexpect to confirm that the regular bash login prompt eventually comes up
    when starting a post-install VM
    '''
    print("Starting console login into VM")
    start_cmd = [
        'virsh',
        'start',
        domain_name
    ]
    subprocess.call(start_cmd)
    console_cmd = [
        'virsh',
        'console',
        domain_name
    ]

    pexpect_proc = pexpect.spawn(console_cmd[0], console_cmd[1:],timeout=60)

    _pexpect_with_timeout(pexpect_proc, 'localhost login:')
    pexpect_proc.sendline(login)

    _pexpect_with_timeout(pexpect_proc, 'Password:')
    pexpect_proc.sendline(password)

    print("Logged in successfully. Beginning setup.")
    _pexpect_with_timeout(pexpect_proc, '#')
    pexpect_proc.sendline("mkdir /tmp/host-data && mount -v -t virtiofs host_home /tmp/host-data")

    _pexpect_with_timeout(pexpect_proc, '#')
    pexpect_proc.sendline(cmd)

    _pexpect_with_timeout(pexpect_proc, '#')

    pexpect_proc.close()

    print(f"VM console setup completed successfully.")

    stop_cmd = [
        'virsh',
        'shutdown',
        domain_name
    ]
    subprocess.call(stop_cmd)

def configure_host_mount(domain_name: str, host_path: str):
    '''
    Configure a mount from the host to the guest by editing its XML
    via the CLI
    '''
    # Enable shared memory
    shm_cmd = [
        'virt-xml',
        domain_name,
        '--edit',
        '--memorybacking', 'source.type=memfd,access.mode=shared'
    ]
    subprocess.call(shm_cmd)

    # Add a virtiofs device
    virtiofs_cmd = [
        'virt-xml',
        domain_name,
        '--add-device',
        '--filesystem', f'driver.type=virtiofs,source.dir={host_path},target.dir=host_home'
    ]
    subprocess.call(virtiofs_cmd)


def export_iso(export_path: Path, domain_name: str, pool: str):
    '''
    (Optionally) export an iso from the storage pool to a path on disk
    '''
    print(f"Exporting VM Volume {domain_name} from pool {pool} to export path {export_path}")
    export_cmd = [
        'virsh', 'vol-download', '--vol', domain_name, '--pool', pool, export_path
    ]
    subprocess.call(export_cmd)

    print(f"Removing VM Volume {domain_name} from pool {pool}")
    delete_cmd = [
        'virsh', 'vol-delete', domain_name, pool
    ]
    subprocess.call(export_cmd)

def undefine_vm(domain_name: str):
    '''
    Undefine a VM
    '''
    print("Undefining VM")
    undefine_cmd = ['virsh', 'undefine', '--nvram', domain_name]
    subprocess.call(undefine_cmd)

        
def get_pw(pw_file: Path) -> str:
    '''
    Read the expected password to a vm from a JSON file in the form '{"password":"<password>"}'
    '''
    with open(pw_file, 'r') as pwf:
        password_data = json.loads(pwf.read())

    return password_data['password']

CMD = (
    "chmod +x /tmp/host-data/run-user-payload /tmp/host-data/osg-test.init && " 
    "cp /tmp/host-data/run-user-payload /root/run-user-payload && "
    "cp /tmp/host-data/osg-test.init /etc/osg-test.init && "
    "cp /tmp/host-data/resolv.conf /etc/resolv.conf && "
    "cp /tmp/host-data/osg-test.service /etc/systemd/system/osg-test.service && "
    "systemctl -q enable osg-test"
)

def main():
    # Simple arg parser with a bunch of required arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--config-path', required=True, help='Path to config file')
    parser.add_argument('-i','--iso-path', required=True, help='Path at which to cache source ISO image')
    parser.add_argument('-v','--host-path', required=True, help='Path on the host to volume-mount and copy into the VM post-setup')
    parser.add_argument('-p','--password-file', required=True, help='Path to a JSON file containing a password for the VM user')
    parser.add_argument('-s','--storage-pool', required=True, help='Storage pool to output complete disk image into')
    parser.add_argument('-o','--output-path', help='Path on disk to export complete disk image onto')

    args = parser.parse_args()

    cache_path = Path(args.iso_path)
    config_path = Path(args.config_path)
    password_file = Path(args.password_file)
    input_dir = Path(args.host_path)
    storage_pool = args.storage_pool

    # Download the iso
    iso_path = download_iso(cache_path, config_path / 'vars.json')

    # Install a VM based on the iso via libvirt
    domain_name = launch_libvirt_build(iso_path, config_path / 'kickstart.ks', storage_pool)
    poll_libvirtd_progress(domain_name)

    # Mount a host directory into the shut-down VM post setup
    configure_host_mount(domain_name, input_dir)

    # Restart the VM, log into it using virsh console, then run the specified commands in it
    password = get_pw(password_file)
    pexpect_console_setup(domain_name, password, cmd=CMD)

    # Clean up: remove the VM (the build artifact still exists in the storage pool)
    undefine_vm(domain_name)

    # If configured, 
    if args.output_path:
        export_iso(args.output_path, domain_name, storage_pool)


if __name__ == '__main__':
    main()
