#
# This file is part of Freedom Maker.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Library of small actions that make up image building.

Most simple wrappers over command line utilities without any understanding of
state of build process.
"""

import contextlib
import logging
import os
import re
import shutil
import tempfile

import cliapp

logger = logging.getLogger(__name__)


def run(*args, **kwargs):
    """Run a command."""

    def log_stdout(data):
        """Handle stdout data from executed command."""
        logger.debug('> %s', str(data.decode().strip()))

    def log_stderr(data):
        """Handle stderr data from executed command."""
        logger.debug('2> %s', str(data.decode().strip()))

    logger.info('Executing command - %s %s', args, kwargs)
    environ = kwargs['env'] if 'env' in kwargs else os.environ.copy()
    environ['LC_ALL'] = 'C'
    environ['LANGUAGE'] = 'C'
    environ['LANG'] = 'C'
    environ['DEBIAN_FRONTEND'] = 'noninteractive'
    environ['DEBCONF_NONINTERACTIVE_SEEN'] = 'true'
    kwargs['env'] = environ
    kwargs['stdout_callback'] = log_stdout
    kwargs['stderr_callback'] = log_stderr
    return cliapp.runcmd(*args, **kwargs)


def run_in_chroot(state, *args, **kwargs):
    """Run a command inside chroot of mount point."""
    args = [['chroot', state['mount_point']] + arg for arg in args]
    run(*args, **kwargs)


def path_in_mount(state, path):
    """Return the path inside the mount point of image.

    If as absolute path is provided as path, it will returned as it is.

    """
    return os.path.join(state['mount_point'], path)


def schedule_cleanup(state, method, *args, **kwargs):
    """Make a note of the cleanup operations to happen."""
    state.setdefault('cleanup', []).append([method, args, kwargs])


def cleanup(state):
    """Run all the scheduled cleanups in reverse order."""
    state.setdefault('cleanup', [])
    for cleanup_step in reversed(state['cleanup']):
        method, args, kwargs = cleanup_step
        method(*args, **kwargs)


def create_image(state, filename, size):
    """Create an empty sparse file using qemu-image."""
    logger.info('Creating image %s of size %s', filename, size)
    run(['qemu-img', 'create', '-f', 'raw', filename, size])
    state['image_file'] = filename


def create_partition_table(device, partition_table_type):
    """Create an empty partition table in given device."""
    logger.info('Creating partition table on %s of type %s', device,
                partition_table_type)
    run(['parted', '-s', device, 'mklabel', partition_table_type])


def create_partition(state, label, device, start, end, filesystem_type):
    """Create a primary partition in a given device."""
    filesystem_map = {'vfat': 'fat32'}
    filesystem_type = filesystem_map.get(filesystem_type, filesystem_type)

    partition_type = 'primary'
    logger.info('Creating partition %s in %s (range %s - %s) of type %s',
                label, device, start, end, filesystem_type)
    run([
        'parted', '-s', device, 'mkpart', partition_type, filesystem_type,
        start, end
    ])

    state.setdefault('partitions', []).append(label)


def set_boot_flag(device, partition_number):
    """Set boot flag on a partition of a device."""
    logger.info('Setting boot flag on %s partition for %s', partition_number,
                device)
    run(['parted', '-s', device, 'set', str(partition_number), 'boot', 'on'])


def loopback_setup(state, image_file):
    """Perform mapping to loopback devices from partitions in image file."""
    logger.info('Setting up loopback mappings for %s', image_file)
    output = run(['kpartx', '-asv', image_file]).decode()
    loop_device = None
    devices = []
    partition_number = 0
    for line in output.splitlines():
        columns = line.split()
        if columns[0] == 'add':
            device = '/dev/mapper/{}'.format(columns[2])
            label = state['partitions'][partition_number]
            state.setdefault('devices', {})[label] = device
            devices.append(device)
            partition_number += 1
            if not loop_device:
                loop_device = re.match(r'^(loop\d+)p\d+$', columns[2])[1]
                loop_device = '/dev/{}'.format(loop_device)
                state['loop_device'] = loop_device

    # Cleanup runs in reverse order
    if loop_device:
        schedule_cleanup(state, force_release_loop_device, loop_device)

    for device in devices:
        schedule_cleanup(state, force_release_partition_loop, device)

    schedule_cleanup(state, loopback_teardown, image_file)


def force_release_partition_loop(loop_device):
    """Force release a partition mapping on a loop device."""
    logger.info('Force releasing partition on loop device %s', loop_device)
    run(['dmsetup', 'remove', loop_device], ignore_fail=True)


def force_release_loop_device(loop_device):
    """Force release of a loop setup for entire device"""
    logger.info('Force releasing loop setup for device %s', loop_device)
    run(['losetup', '-d', loop_device], ignore_fail=True)


def loopback_teardown(image_file):
    """Unmap loopback devices from partitions in image file."""
    logger.info('Tearing down loopback mappings for %s', image_file)
    run(['kpartx', '-dsv', image_file])


def create_filesystem(device, filesystem_type):
    """Create a filesystem on a given device."""
    logger.info('Creating filesystem on %s of type %s', device,
                filesystem_type)
    run(['mkfs', '-t', filesystem_type, device])


def mount_filesystem(state,
                     label_or_path,
                     sub_mount_point,
                     is_bind_mount=False):
    """Mount a device on a mount point."""
    if not sub_mount_point:
        mount_point = tempfile.mkdtemp()
        state['mount_point'] = mount_point
    else:
        mount_point = path_in_mount(state, sub_mount_point)
        os.makedirs(mount_point, exist_ok=True)

    if not is_bind_mount:
        device = state['devices'][label_or_path]
        options = []
    else:
        device = label_or_path
        options = ['-o', 'bind']

    logger.info('Mounting device %s on %s with options %s', device,
                mount_point, options)
    run(['mount', device, mount_point] + options)
    state.setdefault('sub_mount_points', {})[label_or_path] = sub_mount_point

    schedule_cleanup(state, unmount_filesystem, device, mount_point,
                     is_bind_mount)


def unmount_filesystem(device, mount_point, is_bind_mount):
    """Unmount a filesystem."""
    logger.info('Unmounting device %s from mount point %s', device,
                mount_point)
    if not is_bind_mount:
        run(['fuser', '-mvk', mount_point], ignore_fail=True)

    run(['umount', mount_point])


def qemu_debootstrap(state, architecture, distribution, variant, components,
                     packages, mirror):
    """Debootstrap into a mounted directory."""
    target = state['mount_point']
    logger.info('Qemu debootstraping into %s, architecture %s, '
                'distribution %s, variant %s, components %s, build mirror %s',
                target, architecture, distribution, variant, components,
                mirror)
    try:
        run([
            'qemu-debootstrap', '--arch=' + architecture,
            '--variant=' + variant, '--components=' + ','.join(components),
            '--include=' + ','.join(packages), distribution, target, mirror
        ])
    except (Exception, KeyboardInterrupt):
        logger.info(
            'Unmounting filesystems that may have been left by debootstrap')
        run(['umount', os.path.join(target, 'proc')], ignore_fail=True)
        run(['umount', os.path.join(target, 'sys')], ignore_fail=True)
        raise

    schedule_cleanup(state, qemu_remove_binary, state)


def qemu_remove_binary(state):
    """Remove Qemu binary that may have been installed by qemu-debootstrap."""
    binaries = path_in_mount(state, 'usr/bin/qemu-*-static')
    logger.info('Removing qemu binaries %s', binaries)
    run(['rm', '-f', binaries])


@contextlib.contextmanager
def no_run_daemon_policy(state):
    """Context manager to ensure daemons are not run during installs."""
    path = path_in_mount(state, 'usr/sbin/policy-rc.d')
    content = '''#!/bin/sh
exit 101
'''
    with open(path, 'w') as file_handle:
        file_handle.write(content)

    os.chmod(path, 0o755)
    yield
    os.unlink(path)


def install_package(state, package):
    """Install a package using apt."""
    logger.info('Installing package %s', package)
    with no_run_daemon_policy(state):
        run_in_chroot(state, ['apt-get', 'install', '-y', package])


def install_custom_package(state, package_path):
    """Install a custom .deb file."""
    logger.info('Install custom .deb package %s', package_path)
    sub_destination = os.path.join('tmp', os.path.basename(package_path))
    destination_path = path_in_mount(state, sub_destination)
    shutil.copyfile(package_path, destination_path)
    install_package(state, 'gdebi-core')
    package_path = os.path.join('/tmp', os.path.basename(package_path))
    with no_run_daemon_policy(state):
        run_in_chroot(state, ['gdebi', '-n', package_path])


def set_hostname(state, hostname):
    """Set the hostname inside the image."""
    logger.info('Setting hostname to %s', hostname)

    etc_hostname_path = path_in_mount(state, 'etc/hostname')
    with open(etc_hostname_path, 'w') as file_handle:
        file_handle.write(hostname + '\n')

    etc_hosts_path = path_in_mount(state, 'etc/hosts')
    with open(etc_hosts_path, 'r') as file_handle:
        lines = file_handle.readlines()
    with open(etc_hosts_path, 'w') as file_handle:
        appended = False
        for line in lines:
            if line.startswith('127.0.1.1'):
                line = line + ' ' + hostname
                appended = True

            file_handle.write(line)

        if not appended:
            file_handle.write('127.0.1.1 ' + hostname + '\n')


def get_fstab_options(filesystem_type):
    """Return options to use for a filesystem type."""
    flags = ['errors=remount-ro'] if not filesystem_type == 'btrfs' else []
    return ','.join(flags) or 'defaults'


def get_uuid_of_device(device):
    """Return the UUID of a given device."""
    output = run(['blkid', '--output=value', '--match-tag=UUID', device])
    return output.decode().strip()


def add_fstab_entry(state, label, filesystem_type, pass_number, append=True):
    """Add an entry in /etc/fstab for a disk partition."""
    file_path = path_in_mount(state, 'etc/fstab')
    device = 'UUID={}'.format(get_uuid_of_device(state['devices'][label]))
    values = {
        'device': device,
        'mount_point': '/' + (state['sub_mount_points'][label] or ''),
        'filesystem_type': filesystem_type,
        'options': get_fstab_options(filesystem_type),
        'frequency': '0',
        'pass_number': pass_number
    }
    line = '{device} {mount_point} {filesystem_type} {options} {frequency} ' \
           '{pass_number}\n'
    line = line.format(**values)
    logger.info('Adding fstab entry %s', values)

    mode = 'a' if append else 'w'
    with open(file_path, mode) as file_handle:
        file_handle.write(line)


def install_grub(state):
    """Install grub boot loader on the loop back device."""
    device = state['loop_device']
    logger.info('Installing grub boot loader on device %s', device)
    run_in_chroot(state, ['update-grub'])
    run_in_chroot(state, ['grub-install', device])


def setup_apt(state, mirror, distribution, components):
    """Setup apt sources and update the cache."""
    logger.info('Setting apt for mirror %s', mirror)
    values = {
        'mirror': mirror,
        'distribution': distribution,
        'components': ' '.join(components)
    }
    basic_template = '''
deb {mirror} {distribution} {components}
deb-src {mirror} {distribution} {components}
'''
    updates_template = '''
deb {mirror} {distribution}-updates {components}
deb-src {mirror} {distribution}-updates {components}

deb http://security.debian.org/debian-security/ {distribution}/updates {components}
deb-src http://security.debian.org/debian-security/ {distribution}/updates {components}
'''
    file_path = path_in_mount(state, 'etc/apt/sources.list')
    with open(file_path, 'w') as file_handle:
        file_handle.write(basic_template.format(**values))
        if distribution not in ('sid', 'unstable'):
            file_handle.write(updates_template.format(**values))

    run_in_chroot(state, ['apt-get', 'update'])
    run_in_chroot(state, ['apt-get', 'clean'])


def setup_flash_kernel(state, machine_name, kernel_options):
    """Setup and install flash-kernel package."""
    logger.info('Setting up flash kernel for machine %s with options %s',
                machine_name, kernel_options)
    directory_path = path_in_mount(state, 'etc/flash_kernel')
    os.makedirs(directory_path, exist_ok=True)

    file_path = path_in_mount(state, 'etc/flash_kernel/machine')
    with open(file_path, 'w') as file_handle:
        file_handle.write(machine_name)

    if kernel_options:
        stdin = 'flash-kernel flash-kernel/linux_cmdline string "{}"'.format(
            kernel_options)
        run_in_chroot(
            state, ['debconf-set-selections'], feed_stdin=stdin.encode())

    run_in_chroot(state, ['apt-get', 'install', '-y', 'flash-kernel'])
    run_in_chroot(state, ['flash-kernel'])


def install_boot_loader_part(state, path, seek, size, count=None):
    """Do a dd copy for a file onto the disk image."""
    image_file = state['image_file']
    full_path = path_in_mount(state, path)
    logger.info('Installing boot loader part %s at seek=%s, size=%s, count=%s',
                full_path, seek, size, count)
    command = [
        'dd', 'if=' + full_path, 'of=' + image_file, 'seek=' + seek,
        'bs=' + size, 'conv=notrunc'
    ]
    if count:
        command.append('count=' + count)

    run(command)


def fill_free_space_with_zeros(state):
    """Fill up the free space in the image with zeros.

    So that we can compress the image better.

    """
    zeros_path = path_in_mount(state, 'ZEROS')
    logger.info('Fill space with zeros on %s', state['mount_point'])
    run(['dd', 'if=/dev/zero', 'of=' + zeros_path, 'bs=1M'], ignore_fail=True)
    run(['rm', '-f', zeros_path])
