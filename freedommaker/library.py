# SPDX-License-Identifier: GPL-3.0-or-later
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
    return run(*args, **kwargs)


def run_script_in_chroot(state, script):
    """Run a script inside chroot of mount point."""
    run_in_chroot(state, ['bash', '-c', script])


def add_cron_in_chroot(state, mins, commandStr):
    """Add a cron entry inside chroot"""
    script = 'echo "*/' + str(mins) + \
        ' *   * * *   ' + \
        'root    ' + commandStr + '" >> /etc/crontab'
    run_script_in_chroot(state, script)


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


def create_ram_directory_image(state, image_file, size):
    """Create a temporary RAM directory."""
    logger.info('Create RAM directory for image: %s (%s)', image_file, size)
    directory = tempfile.TemporaryDirectory()
    run([
        'mount', '-o', 'size=' + size, '-t', 'tmpfs', 'tmpfs', directory.name
    ])

    state['ram_directory'] = directory
    temp_image_file = os.path.join(directory.name,
                                   os.path.basename(image_file))
    state['image_file'] = temp_image_file

    schedule_cleanup(state, remove_ram_directory, directory)
    schedule_cleanup(state, copy_image, state, temp_image_file, image_file)


def remove_ram_directory(directory):
    """Remove RAM directory created for temporary image path."""
    logger.info('Cleanup RAM directory %s', directory)
    run(['umount', directory.name])
    directory.cleanup()


def copy_image(state, source_image, target_image):
    """Copy from temp image to target path."""
    if not state['success']:
        target_image += '.failed'

    logger.info('Copying file: %s -> %s', source_image, target_image)
    run(['cp', '--sparse=always', source_image, target_image])


def create_temp_image(state, image_file):
    """Create a temp image for a target image file on disk."""
    temp_image_file = image_file + '.temp'
    logger.info('Creating temp image %s for image %s', temp_image_file,
                image_file)
    state['image_file'] = temp_image_file

    schedule_cleanup(state, move_image, state, temp_image_file, image_file)


def move_image(state, source_image, target_image):
    """Remove from temp image name to final image name."""
    if not state['success']:
        target_image += '.failed'

    logger.info('Moving image: %s -> %s', source_image, target_image)
    run(['mv', source_image, target_image])


def create_image(state, size):
    """Create an empty sparse file using qemu-image."""
    logger.info('Creating image %s of size %s', state['image_file'], size)
    run(['qemu-img', 'create', '-f', 'raw', state['image_file'], size])


def create_partition_table(state, partition_table_type):
    """Create an empty partition table in given device."""
    logger.info('Creating partition table on %s of type %s',
                state['image_file'], partition_table_type)
    run(['parted', '-s', state['image_file'], 'mklabel', partition_table_type])


def create_partition(state, label, start, end, filesystem_type):
    """Create a primary partition in a given device."""
    filesystem_map = {'vfat': 'fat32'}
    filesystem_type = filesystem_map.get(filesystem_type, filesystem_type)

    partition_type = 'primary'
    logger.info('Creating partition %s in %s (range %s - %s) of type %s',
                label, state['image_file'], start, end, filesystem_type)
    run([
        'parted', '-s', state['image_file'], 'mkpart', partition_type,
        filesystem_type, start, end
    ])

    state.setdefault('partitions', []).append(label)


def set_boot_flag(state, partition_number):
    """Set boot flag on a partition of a device."""
    logger.info('Setting boot flag on %s partition for %s', partition_number,
                state['image_file'])
    run([
        'parted', '-s', state['image_file'], 'set',
        str(partition_number), 'boot', 'on'
    ])


def loopback_setup(state):
    """Perform mapping to loopback devices from partitions in image file."""
    logger.info('Setting up loopback mappings for %s', state['image_file'])
    output = run(['kpartx', '-asv', state['image_file']]).decode()
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

    schedule_cleanup(state, loopback_teardown, state['image_file'])


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

    # Due to a bug, probably in udev, /dev/disk/by-uuid/<uuid> link is not
    # reliably created after the creation of the filesystem. This leads to
    # update-grub using root=/dev/mapper/loop0p1 instead of root=UUID=<uuid>
    # when creating grub.cfg. This results in an unbootable image. Force udev
    # events as a workaround.
    run(['udevadm', 'trigger', device])
    run(['udevadm', 'settle'])


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

    schedule_cleanup(state, unmount_filesystem, device, mount_point)


def unmount_filesystem(device, mount_point, ignore_fail=False):
    """Unmount a filesystem."""
    logger.info('Unmounting device %s from mount point %s', device,
                mount_point)
    run(['umount', mount_point], ignore_fail=ignore_fail)


def process_cleanup(state):
    """Kill all processes using a given mount point."""
    mount_point = state['mount_point']
    logger.info('Killing all processes on the mount point %s', mount_point)
    run(['fuser', '-mvk', mount_point], ignore_fail=True)
    # XXX: Twice seems to work better?
    run(['fuser', '-mvk', mount_point], ignore_fail=True)


def setup_extra_storage(state, file_system_type, size):
    """Add an extra storage device to a btrfs filesystem."""
    if file_system_type != 'btrfs':
        return

    extra_storage_file = state['image_file'] + '.extra'
    mount_point = state['mount_point']
    logger.info('Adding extra storage to file system %s', mount_point)
    run(['qemu-img', 'create', '-f', 'raw', extra_storage_file, size])
    output = run(['losetup', '--show', '--find', extra_storage_file])
    loop_device = output.decode().strip()
    run(['btrfs', 'device', 'add', loop_device, mount_point])

    schedule_cleanup(state, cleanup_extra_storage, state, loop_device,
                     extra_storage_file)


def cleanup_extra_storage(state, loop_device, extra_storage_file):
    """Remove the extra storage added to a btrfs filesystem and balance it."""
    mount_point = state['mount_point']
    logger.info('Removing extra storage from file system %s', mount_point)

    _btrfs_rebalance(mount_point)
    run(['btrfs', 'balance', 'start', '-mconvert=dup', mount_point],
        ignore_fail=True)

    # Remove the extra storage device from btrfs filesystem
    run(['btrfs', 'device', 'remove', loop_device, mount_point])
    run(['losetup', '--detach', loop_device])
    run(['rm', '-f', extra_storage_file])

    _btrfs_rebalance(mount_point)


def _btrfs_rebalance(mount_point):
    """Re-balance btrfs filesystem."""
    for usage in range(0, 100, 20):
        run(['btrfs', 'balance', 'start', f'-musage={usage}', mount_point],
            ignore_fail=True)
        run(['btrfs', 'balance', 'start', f'-dusage={usage}', mount_point],
            ignore_fail=True)


def qemu_debootstrap(state, architecture, distribution, variant, components,
                     packages, mirror):
    """Debootstrap into a mounted directory."""
    target = state['mount_point']
    logger.info(
        'Qemu debootstraping into %s, architecture %s, '
        'distribution %s, variant %s, components %s, build mirror %s', target,
        architecture, distribution, variant, components, mirror)
    try:
        run([
            'qemu-debootstrap', '--arch=' + architecture,
            '--variant=' + variant, '--components=' + ','.join(components),
            '--include=' + ','.join(packages), distribution, target, mirror
        ])
    except (Exception, KeyboardInterrupt):
        logger.info(
            'Unmounting filesystems that may have been left by debootstrap')
        for path in ('proc', 'sys', 'etc/machine-id'):
            unmount_filesystem(None,
                               os.path.join(target, path),
                               ignore_fail=True)
        raise

    schedule_cleanup(state, qemu_remove_binary, state)

    # During bootstrap, /etc/machine-id path might be bind mounted.
    schedule_cleanup(state,
                     unmount_filesystem,
                     None,
                     os.path.join(target, 'etc/machine-id'),
                     ignore_fail=True)


def qemu_remove_binary(state):
    """Remove Qemu binary that may have been installed by qemu-debootstrap."""
    binaries = path_in_mount(state, 'usr/bin/qemu-*-static')
    logger.info('Removing qemu binaries %s', binaries)
    run(['rm', '-f', binaries])


@contextlib.contextmanager
def no_run_daemon_policy(state):
    """Context manager to ensure daemons are not run during installs."""
    logger.info('Enforcing policy not to run daemons')
    path = path_in_mount(state, 'usr/sbin/policy-rc.d')
    content = '''#!/bin/sh
exit 101
'''
    with open(path, 'w') as file_handle:
        file_handle.write(content)

    os.chmod(path, 0o755)
    yield

    logger.info('Relaxing policy not to run daemons')
    os.unlink(path)


def install_package(state, package, install_from_backports=False):
    """Install a package using apt."""
    logger.info('Installing package %s', package)

    with no_run_daemon_policy(state):
        run_in_chroot(state, ['apt-get', 'install', '-y', package])
        if install_from_backports:
            # TODO Install doc-en and doc-es packages too
            run_in_chroot(state, ['apt-get', 'install', '-y', 'gdebi-core'])
            run_in_chroot(
                state,
                ['apt-get', '-t', 'buster-backports', 'download', package])
            run_in_chroot(state, ['sh', '-c', f'gdebi -n {package}*.deb'])
            run_in_chroot(state, [
                'find', '.', '-maxdepth', '1', '-iname', f'"{package}*.deb"',
                '-delete'
            ])
            run_in_chroot(state, ['apt', 'autoremove', '-y'])


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


def install_grub(state, target=None, is_efi=False):
    """Install grub boot loader on the loop back device."""
    device = state['loop_device']
    logger.info('Installing grub boot loader on device %s', device)
    run_in_chroot(state, ['update-grub'])
    args = [f'--target={target}'] if target else []
    args += ['--no-nvram'] if is_efi else []
    run_in_chroot(state, ['grub-install', device] + args)


def setup_apt(state, mirror, distribution, components, enable_backports=False):
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
'''
    old_security_template = '''
deb http://security.debian.org/debian-security/ {distribution}/updates {components}
deb-src http://security.debian.org/debian-security/ {distribution}/updates {components}
'''
    security_template = '''
deb http://security.debian.org/debian-security/ {distribution}-security {components}
deb-src http://security.debian.org/debian-security/ {distribution}-security {components}
'''
    buster_backports_template = '''
deb http://deb.debian.org/debian buster-backports main
deb-src http://deb.debian.org/debian buster-backports main
'''
    file_path = path_in_mount(state, 'etc/apt/sources.list')
    with open(file_path, 'w') as file_handle:
        file_handle.write(basic_template.format(**values))
        if distribution not in ('sid', 'unstable'):
            file_handle.write(updates_template.format(**values))
            if enable_backports:
                file_handle.write(buster_backports_template)
            if distribution in ('bullseye', 'testing'):
                file_handle.write(security_template.format(**values))
            else:  # stable/buster
                file_handle.write(old_security_template.format(**values))

    run_in_chroot(state, ['apt-get', 'update'])
    run_in_chroot(state, ['apt-get', 'clean'])


def setup_flash_kernel(state, machine_name, kernel_options,
                       boot_filesystem_type):
    """Setup and install flash-kernel package."""
    logger.info('Setting up flash kernel for machine %s with options %s',
                machine_name, kernel_options)
    directory_path = path_in_mount(state, 'etc/flash-kernel')
    os.makedirs(directory_path, exist_ok=True)

    file_path = path_in_mount(state, 'etc/flash-kernel/machine')
    with open(file_path, 'w') as file_handle:
        file_handle.write(machine_name)

    if kernel_options:
        stdin = 'flash-kernel flash-kernel/linux_cmdline string {}'.format(
            kernel_options)
        run_in_chroot(state, ['debconf-set-selections'],
                      feed_stdin=stdin.encode())

    run_in_chroot(state, ['apt-get', 'install', '-y', 'flash-kernel'])

    # flash-kernel creates links in /boot and does not work with the filesystem
    # is vfat.
    if boot_filesystem_type != 'vfat':
        run_in_chroot(state, ['flash-kernel'])


def update_initramfs(state):
    """Update the initramfs in the disk image to make it use fstab etc."""
    logger.info('Updating initramfs')
    run_in_chroot(state, ['update-initramfs', '-u'])


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


def compress(archive_file, image_file):
    """Compress an image using xz."""
    logger.info('Compressing file %s to %s', image_file, archive_file)
    command = ['xz', '--no-warn', '--threads=0', '-9', '--force']
    run(command + [image_file])


def sign(archive):
    """Sign an image using GPG."""
    logger.info('Signing file %s with GPG', archive)
    signature = archive + '.sig'
    try:
        os.remove(signature)
    except FileNotFoundError:
        pass

    run(['gpg', '--output', signature, '--detach-sig', archive])
