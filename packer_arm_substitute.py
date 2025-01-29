#!/usr/bin/env python3

# Python script that roughly mimics the workings of packer on ARM,
# where it is not well supported
#
# 1. Given a vars.json file, download the iso specified by those vars to a cache
#    location
# 2. Start an automated VM install using that iso as a base, passing in a 
#    kickstart file via extra kernel args using libvirt
# 3. Attempt to log into the guest


import pexpect
import json
import requests
import hashlib
from pathlib import Path
import subprocess
from sys import argv
from time import sleep
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
    cmd = [
        'virt-install',
        '--name', iso_path.name,
        '--disk', f'pool={storage_pool},size={img_size}',
        '--boot', 'uefi',
        '--initrd-inject', kickstart_path,
        f'--extra-args="inst.ks=file:/{kickstart_path.name}"',
        '--noautoconsole',
        '--location', iso_path
    ]

    subprocess.call(cmd)

    return iso_path.name

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


def pexpect_login_console(domain_name: str, password: str, login: str = 'root'):
    ''' 
    Use pexpect to confirm that the regular bash login prompt eventually comes up
    when starting a post-install VM
    '''
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

    pexpect_proc = pexpect.spawn(console_cmd[0], console_cmd[1:])
    outcome = pexpect_proc.expect(['localhost login:', pexpect.TIMEOUT])
    if outcome != 0:
        raise RuntimeError("Timeout waiting for VM login prompt.")
    pexpect_proc.sendline(login)
    outcome = pexpect_proc.expect(['Password:', pexpect.TIMEOUT])
    if outcome != 0:
        raise RuntimeError("Timeout waiting for VM password prompt.")
    pexpect_proc.sendline(password)

    pexpect_proc.close()

    print(f"VM test login completed successfully.")

    stop_cmd = [
        'virsh',
        'shutdown',
        domain_name
    ]
    subprocess.call(stop_cmd)



def dump_libvirt_xml(domain_name: str, output_path: Path):
    '''
    Dump the libvirt xml definition of the created VM to allow replication of the VM
    '''
    pass
        
def get_pw(pw_file: Path) -> str:
    '''
    Read the expected password to a vm from a JSON file in the form '{"password":"<password>"}'
    '''
    with open(pw_file, 'r') as pwf:
        password_data = json.loads(pwf.read())

    return password_data['password']

def main():
    cache_path = Path(argv[1])
    config_path = Path(argv[2])
    storage_pool = argv[3]
    password_file = Path(argv[4])
    iso_path = download_iso(cache_path, config_path / 'vars.json')

    domain_name = launch_libvirt_build(iso_path, config_path / 'kickstart.ks', storage_pool)
    poll_libvirtd_progress(domain_name)

    password = get_pw(password_file)
    pexpect_login_console(domain_name, password)

if __name__ == '__main__':
    main()