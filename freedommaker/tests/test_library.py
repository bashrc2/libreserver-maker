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
Tests for checking Freedom Maker's internal library of actions.
"""

import contextlib
import os
import random
import stat
import string
import tempfile
import unittest
from unittest.mock import Mock, call, patch

from .. import library


class TestLibrary(unittest.TestCase):
    """Test all internal library methods used for building image."""

    def setUp(self):
        """Common setup for each test."""
        self.args = ['1', '2', '3']
        self.kwargs = {'a': 'x', 'b': 'y'}
        self.method = self.random_string()
        self.image = self.random_string()

        self.mount_point_directory = tempfile.TemporaryDirectory()
        os.makedirs(self.mount_point_directory.name + '/usr/sbin/')
        os.makedirs(self.mount_point_directory.name + '/tmp/')
        os.makedirs(self.mount_point_directory.name + '/etc/apt')
        self.state = {
            'image_file': self.image,
            'mount_point': self.mount_point_directory.name,
            'success': True,
        }

    def tearDown(self):
        """Cleanup the test case."""
        self.mount_point_directory.cleanup()

    @staticmethod
    def random_string():
        """Generate a random string."""
        return ''.join(
            [random.choice(string.ascii_lowercase) for _ in range(8)])

    @contextlib.contextmanager
    def assert_file_change(self, path, content, expected_content):
        """Context manager to verify that file contents changed as expected."""
        if content is not None:
            with open(path, 'w') as file_handle:
                file_handle.write(content)

        yield

        with open(path, 'r') as file_handle:
            changed_content = file_handle.read()

        self.assertEqual(expected_content, changed_content)

    @patch('cliapp.runcmd')
    def test_run(self, runcmd):
        """Test the run utility."""
        library.run(*self.args, **self.kwargs)
        assert runcmd.called
        self.assertEqual(list(runcmd.call_args[0]), self.args)
        for key, value in self.kwargs.items():
            self.assertEqual(runcmd.call_args[1][key], value)

        environ = {
            'LC_ALL': 'C',
            'LANGUAGE': 'C',
            'LANG': 'C',
            'DEBIAN_FRONTEND': 'noninteractive',
            'DEBCONF_NONINTERACTIVE_SEEN': 'true'
        }
        for key, value in environ.items():
            runcmd.call_args[1]['env'][key] = value

    @patch('freedommaker.library.run')
    def test_run_in_chroot(self, run):
        """Test executing inside a chroot environment."""
        library.run_in_chroot(self.state, self.args, **self.kwargs)
        expected_args = ['chroot', self.state['mount_point']] + self.args
        self.assertEqual(run.call_args, call(expected_args, **self.kwargs))

    def test_path_in_mount(self):
        """Test returning a sub-directory in mount point."""
        output = library.path_in_mount(self.state, 'boot')
        self.assertEqual(output, self.state['mount_point'] + '/boot')

        output = library.path_in_mount(self.state, '/boot')
        self.assertEqual(output, '/boot')

    def test_schedule_clean(self):
        """Test scheduling cleanup jobs."""
        cleanup = Mock()
        library.schedule_cleanup(self.state, cleanup, 2, b=3)
        self.assertEqual(self.state['cleanup'][-1], [cleanup, (2, ), {'b': 3}])

    def test_cleanup(self):
        """Test the cleanup works."""
        method = Mock()
        library.schedule_cleanup(self.state, method, 1, a=1)
        library.schedule_cleanup(self.state, method, 2, a=2)
        library.schedule_cleanup(self.state, method, 3, a=3)
        library.cleanup(self.state)
        self.assertEqual(method.call_args_list, [((3, ), {
            'a': 3
        }), ((2, ), {
            'a': 2
        }), ((1, ), {
            'a': 1
        })])

    @patch('freedommaker.library.run')
    def test_create_ram_directory_image(self, run):
        """Test that RAM directory is properly created."""
        library.create_ram_directory_image(self.state, self.image, '4G')
        run.assert_called_once_with([
            'mount', '-o', 'size=4G', '-t', 'tmpfs', 'tmpfs',
            self.state['ram_directory'].name
        ])
        self.assertEqual(self.state['image_file'],
                         self.state['ram_directory'].name + '/' + self.image)
        self.assertEqual(
            self.state['cleanup'],
            [[
                library.remove_ram_directory,
                (self.state['ram_directory'], ), {}
            ],
             [
                 library.copy_image,
                 (self.state, self.state['image_file'], self.image), {}
             ]])
        self.state['ram_directory'].cleanup()

    @patch('freedommaker.library.run')
    def test_remove_ram_directory(self, run):
        """Test removing a RAM directory."""
        directory = Mock(name=self.random_string())
        library.remove_ram_directory(directory)
        run.assert_called_once_with(['umount', directory.name])
        directory.cleanup.assert_called()

    @patch('freedommaker.library.run')
    def test_copy_image(self, run):
        """Test copying temp image to final image."""
        temp_image = self.random_string()
        library.copy_image(self.state, temp_image, self.image)
        run.assert_called_once_with(
            ['cp', '--sparse=always', temp_image, self.image])

        run.reset_mock()
        self.state['success'] = False
        library.copy_image(self.state, temp_image, self.image)
        run.assert_called_once_with(
            ['cp', '--sparse=always', temp_image, self.image + '.failed'])

    def test_create_temp_image(self):
        """Test creating a temporary image file on disk."""
        library.create_temp_image(self.state, self.image)
        self.assertEqual(self.state['image_file'], self.image + '.temp')
        self.assertEqual(self.state['cleanup'], [[
            library.move_image,
            (self.state, self.image + '.temp', self.image), {}
        ]])

    @patch('freedommaker.library.run')
    def test_move_image(self, run):
        """Test moving temp image to final image."""
        source_image = self.random_string()
        library.move_image(self.state, source_image, self.image)
        run.assert_called_once_with(['mv', source_image, self.image])

        run.reset_mock()
        self.state['success'] = False
        library.move_image(self.state, source_image, self.image)
        run.assert_called_once_with(
            ['mv', source_image, self.image + '.failed'])

    @patch('freedommaker.library.run')
    def test_create_image(self, run):
        """Test creating an image."""
        library.create_image(self.state, '4G')
        run.assert_called_once_with(
            ['qemu-img', 'create', '-f', 'raw', self.image, '4G'])

    @patch('freedommaker.library.run')
    def test_create_partition_table(self, run):
        """Test creating a partition table."""
        library.create_partition_table(self.state, 'msdos')
        run.assert_called_once_with(
            ['parted', '-s', self.image, 'mklabel', 'msdos'])

    @patch('freedommaker.library.run')
    def test_create_partition(self, run):
        """Test creating a partition table."""
        library.create_partition(self.state, 'root', '10mib', '50%', 'f2fs')
        run.assert_called_once_with([
            'parted', '-s', self.image, 'mkpart', 'primary', 'f2fs', '10mib',
            '50%'
        ])

        self.assertEqual(self.state['partitions'], ['root'])

        library.create_partition(self.state, 'root', '10mib', '50%', 'vfat')
        run.assert_called_with([
            'parted', '-s', self.image, 'mkpart', 'primary', 'fat32', '10mib',
            '50%'
        ])

    @patch('freedommaker.library.run')
    def test_set_boot_flag(self, run):
        """Test that boot flag is properly set."""
        library.set_boot_flag(self.state, 3)
        run.assert_called_with(
            ['parted', '-s', self.image, 'set', '3', 'boot', 'on'])

    @patch('freedommaker.library.run')
    def test_loopback_setup(self, run):
        """Test that loopback device is properly setup."""
        self.state['partitions'] = ['firmware', 'boot', 'root']

        run.return_value = b'''remove x x
add x loop99p1
add x loop99p2
add x loop99p3
modify x x
'''
        library.loopback_setup(self.state)
        run.assert_called_with(['kpartx', '-asv', self.image])
        self.assertEqual(
            self.state['devices'], {
                'firmware': '/dev/mapper/loop99p1',
                'boot': '/dev/mapper/loop99p2',
                'root': '/dev/mapper/loop99p3'
            })
        self.assertEqual(self.state['loop_device'], '/dev/loop99')
        self.assertEqual(
            self.state['cleanup'],
            [[library.force_release_loop_device, ('/dev/loop99', ), {}],
             [
                 library.force_release_partition_loop,
                 ('/dev/mapper/loop99p1', ), {}
             ],
             [
                 library.force_release_partition_loop,
                 ('/dev/mapper/loop99p2', ), {}
             ],
             [
                 library.force_release_partition_loop,
                 ('/dev/mapper/loop99p3', ), {}
             ], [library.loopback_teardown, (self.image, ), {}]])

    @staticmethod
    @patch('freedommaker.library.run')
    def test_force_release_partition_loop(run):
        """Test loop device is forcefully released."""
        library.force_release_partition_loop('/dev/test/loop99')
        run.assert_called_with(['dmsetup', 'remove', '/dev/test/loop99'],
                               ignore_fail=True)

    @staticmethod
    @patch('freedommaker.library.run')
    def test_force_release_loop_device(run):
        """Test loop device is forcefully released."""
        library.force_release_partition_loop('/dev/test/loop99')
        run.assert_called_with(['dmsetup', 'remove', '/dev/test/loop99'],
                               ignore_fail=True)

    @staticmethod
    @patch('freedommaker.library.run')
    def test_loopback_teardown(run):
        """Test tearing down of loopback."""
        library.loopback_teardown('/dev/test/loop99')
        run.assert_called_with(['kpartx', '-dsv', '/dev/test/loop99'])

    @patch('freedommaker.library.run')
    def test_create_filesystem(self, run):
        """Test creating filesystem."""
        library.create_filesystem('/dev/test/loop99p1', 'btrfs')
        self.assertEqual(run.call_args_list, [
            call(['mkfs', '-t', 'btrfs', '/dev/test/loop99p1']),
            call(['udevadm', 'trigger', '/dev/test/loop99p1']),
            call(['udevadm', 'settle'])
        ])

    @patch('freedommaker.library.run')
    def test_mount_filesystem(self, run):
        """Test mounting a filesystem and setting proper state."""
        self.state['devices'] = {
            'root': '/dev/test/loop99p1',
            'firmware': '/dev/test/loop99p2'
        }
        library.mount_filesystem(self.state, 'root', None)
        run.assert_called_with(
            ['mount', '/dev/test/loop99p1', self.state['mount_point']])

        library.mount_filesystem(self.state, 'firmware', 'boot/firmware')
        run.assert_called_with([
            'mount', '/dev/test/loop99p2',
            self.state['mount_point'] + '/boot/firmware'
        ])

        library.mount_filesystem(
            self.state, '/dev/pts', 'dev/pts', is_bind_mount=True)
        run.assert_called_with([
            'mount', '/dev/pts', self.state['mount_point'] + '/dev/pts', '-o',
            'bind'
        ])

        sub_mount_points = {
            'root': None,
            'firmware': 'boot/firmware',
            '/dev/pts': 'dev/pts'
        }
        self.assertEqual(self.state['sub_mount_points'], sub_mount_points)

    @patch('freedommaker.library.run')
    def test_unmount_filesystem(self, run):
        """Test unmounting a filesystem."""
        library.unmount_filesystem('/dev/', self.state['mount_point'], False)
        self.assertEqual(
            run.call_args_list,
            [call(['umount', self.state['mount_point']], ignore_fail=False)])

    @patch('freedommaker.library.run')
    def test_process_cleanup(self, run):
        """Test cleaning up processes."""
        library.process_cleanup(self.state)
        self.assertEqual(run.call_args_list, [
            call(['fuser', '-mvk', self.state['mount_point']],
                 ignore_fail=True),
            call(['fuser', '-mvk', self.state['mount_point']],
                 ignore_fail=True)
        ])

    @patch('freedommaker.library.run')
    def test_setup_extra_storage(self, run):
        """Test that setting up extra storage works."""
        extra_storage_file = self.image + '.extra'
        size = '100M'
        mount_point = self.state['mount_point']
        loop_device = self.random_string()
        run.return_value = f'{loop_device}\n'.encode()

        library.setup_extra_storage(self.state, 'ext4', '100M')
        run.assert_not_called()

        library.setup_extra_storage(self.state, 'btrfs', '100M')
        run.assert_has_calls([
            call(['qemu-img', 'create', '-f', 'raw', extra_storage_file,
                  size]),
            call(['losetup', '--show', '--find', extra_storage_file]),
            call(['btrfs', 'device', 'add', loop_device, mount_point])
        ])

        self.assertEqual(self.state['cleanup'], [[
            library.cleanup_extra_storage,
            (self.state, loop_device, extra_storage_file), {}
        ]])

    @patch('freedommaker.library.run')
    def test_cleanup_extra_storage(self, run):
        """Test that extra storage will be cleaned properly."""
        extra_storage_file = self.image + '.extra'
        loop_device = self.random_string()
        mount_point = self.state['mount_point']

        library.cleanup_extra_storage(self.state, loop_device,
                                      extra_storage_file)

        run.assert_has_calls([
            call(['btrfs', 'balance', 'start', '-musage=0', mount_point],
                 ignore_fail=True),
            call(['btrfs', 'balance', 'start', '-dusage=0', mount_point],
                 ignore_fail=True),
            call(['btrfs', 'balance', 'start', '-musage=20', mount_point],
                 ignore_fail=True),
            call(['btrfs', 'balance', 'start', '-dusage=20', mount_point],
                 ignore_fail=True),
            call(['btrfs', 'balance', 'start', '-musage=40', mount_point],
                 ignore_fail=True),
            call(['btrfs', 'balance', 'start', '-dusage=40', mount_point],
                 ignore_fail=True),
            call(['btrfs', 'balance', 'start', '-musage=60', mount_point],
                 ignore_fail=True),
            call(['btrfs', 'balance', 'start', '-dusage=60', mount_point],
                 ignore_fail=True),
            call(['btrfs', 'balance', 'start', '-musage=80', mount_point],
                 ignore_fail=True),
            call(['btrfs', 'balance', 'start', '-dusage=80', mount_point],
                 ignore_fail=True),
            call(['btrfs', 'balance', 'start', '-mconvert=dup', mount_point],
                 ignore_fail=True),
            call(['btrfs', 'device', 'remove', loop_device, mount_point]),
            call(['losetup', '--detach', loop_device]),
            call(['rm', '-f', extra_storage_file]),
            call(['btrfs', 'balance', 'start', '-musage=0', mount_point],
                 ignore_fail=True),
            call(['btrfs', 'balance', 'start', '-dusage=0', mount_point],
                 ignore_fail=True),
            call(['btrfs', 'balance', 'start', '-musage=20', mount_point],
                 ignore_fail=True),
            call(['btrfs', 'balance', 'start', '-dusage=20', mount_point],
                 ignore_fail=True),
            call(['btrfs', 'balance', 'start', '-musage=40', mount_point],
                 ignore_fail=True),
            call(['btrfs', 'balance', 'start', '-dusage=40', mount_point],
                 ignore_fail=True),
            call(['btrfs', 'balance', 'start', '-musage=60', mount_point],
                 ignore_fail=True),
            call(['btrfs', 'balance', 'start', '-dusage=60', mount_point],
                 ignore_fail=True),
            call(['btrfs', 'balance', 'start', '-musage=80', mount_point],
                 ignore_fail=True),
            call(['btrfs', 'balance', 'start', '-dusage=80', mount_point],
                 ignore_fail=True),
        ])

    @patch('freedommaker.library.run')
    def test_qemu_debootstrap(self, run):
        """Test debootstrapping using qemu."""
        library.qemu_debootstrap(self.state, 'i386', 'stretch', 'minbase',
                                 ['main', 'contrib'], ['p1', 'p2'],
                                 'http://deb.debian.org/debian')
        run.assert_called_with([
            'qemu-debootstrap', '--arch=i386', '--variant=minbase',
            '--components=main,contrib', '--include=p1,p2', 'stretch',
            self.state['mount_point'], 'http://deb.debian.org/debian'
        ])

        self.assertEqual(
            self.state['cleanup'],
            [[library.qemu_remove_binary, (self.state, ), {}],
             [
                 library.unmount_filesystem,
                 (None, self.state['mount_point'] + '/etc/machine-id'),
                 {
                     'ignore_fail': True
                 }
             ]])

    @patch('freedommaker.library.run')
    def test_qemu_remove_binary(self, run):
        """Test removing the qemu binary within the mount point."""
        library.qemu_remove_binary(self.state)
        run.assert_called_with(
            ['rm', '-f', self.state['mount_point'] + '/usr/bin/qemu-*-static'])

    def test_no_daemon_policy(self):
        """Test that no daemon run policy is properly set."""
        file_path = self.state['mount_point'] + '/usr/sbin/policy-rc.d'
        with library.no_run_daemon_policy(self.state):
            with open(file_path, 'r') as file_handle:
                contents = file_handle.read()

            self.assertEqual(contents, '#!/bin/sh\nexit 101\n')
            self.assertEqual(oct(os.stat(file_path)[stat.ST_MODE])[-3:], '755')

        self.assertFalse(os.path.isfile(file_path))

    @patch('freedommaker.library.run_in_chroot')
    def test_install_package(self, run):
        """Test installing a package."""
        library.install_package(self.state, 'nmap')
        run.assert_called_with(self.state,
                               ['apt-get', 'install', '-y', 'nmap'])

    @patch('freedommaker.library.install_package')
    @patch('freedommaker.library.run_in_chroot')
    def test_install_custom_package(self, run, install_package):
        """Test installing a custom package."""
        with tempfile.NamedTemporaryFile() as file_path:
            library.install_custom_package(self.state, file_path.name)
            install_package.assert_called_with(self.state, 'gdebi-core')

            run.assert_called_with(
                self.state,
                ['gdebi', '-n', '/tmp/' + os.path.basename(file_path.name)])

    def test_set_hostname(self):
        """Test that hostname is properly set."""
        hosts_path = self.state['mount_point'] + '/etc/hosts'
        hostname_path = self.state['mount_point'] + '/etc/hostname'

        content = '''127.0.0.1 localhost
::1     localhost ip6-localhost ip6-loopback
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
'''
        expected_content = content + '''127.0.1.1 fbx\n'''
        with self.assert_file_change(hosts_path, content, expected_content):
            with self.assert_file_change(hostname_path, 'test', 'fbx\n'):
                library.set_hostname(self.state, 'fbx')

    def test_get_fstab_options(self):
        """Test getting fstab options for a file system."""
        options = library.get_fstab_options('ext4')
        self.assertEqual(options, 'errors=remount-ro')

        options = library.get_fstab_options('btrfs')
        self.assertEqual(options, 'defaults')

    @patch('freedommaker.library.run', return_value=b'test-uuid')
    def test_get_uuid_of_device(self, run):
        """Test retrieving UUID of device."""
        response = library.get_uuid_of_device('/dev/test/loop99p1')
        run.assert_called_with([
            'blkid', '--output=value', '--match-tag=UUID', '/dev/test/loop99p1'
        ])
        self.assertEqual(response, 'test-uuid')

    @patch('freedommaker.library.get_uuid_of_device')
    def test_add_fstab_entry(self, get_uuid):
        """Test adding entries to /etc/fstab."""
        fstab_path = self.state['mount_point'] + '/etc/fstab'
        self.state['devices'] = {
            'root': '/dev/test/loop99p1',
            'boot': '/dev/test/loop99p2'
        }
        self.state['sub_mount_points'] = {'root': None, 'boot': 'boot'}

        expected_content = 'UUID=root-uuid / btrfs defaults 0 1\n'
        get_uuid.return_value = 'root-uuid'
        with self.assert_file_change(fstab_path, 'initial-trash',
                                     expected_content):
            library.add_fstab_entry(
                self.state, 'root', 'btrfs', 1, append=False)

        expected_content += 'UUID=boot-uuid /boot ext4 errors=remount-ro 0 2\n'
        get_uuid.return_value = 'boot-uuid'
        with self.assert_file_change(fstab_path, None, expected_content):
            library.add_fstab_entry(self.state, 'boot', 'ext4', 2, append=True)

    @patch('freedommaker.library.run_in_chroot')
    def test_install_grub(self, run):
        """Test installing grub boot loader."""
        self.state['loop_device'] = '/dev/test/loop99'
        library.install_grub(self.state)
        self.assertEqual(run.call_args_list, [
            call(self.state, ['update-grub']),
            call(self.state, ['grub-install', '/dev/test/loop99'])
        ])

    @patch('freedommaker.library.run_in_chroot')
    def test_setup_apt(self, run):
        """Test setting up apt."""
        sources_path = self.state['mount_point'] + '/etc/apt/sources.list'

        stable_content = '''
deb http://deb.debian.org/debian stretch main
deb-src http://deb.debian.org/debian stretch main

deb http://deb.debian.org/debian stretch-updates main
deb-src http://deb.debian.org/debian stretch-updates main

deb http://security.debian.org/debian-security/ stretch/updates main
deb-src http://security.debian.org/debian-security/ stretch/updates main
'''
        with self.assert_file_change(sources_path, None, stable_content):
            library.setup_apt(self.state, 'http://deb.debian.org/debian',
                              'stretch', ['main'])

        self.assertEqual(run.call_args_list, [
            call(self.state, ['apt-get', 'update']),
            call(self.state, ['apt-get', 'clean'])
        ])

        unstable_content = '''
deb http://ftp.us.debian.org/debian unstable main contrib non-free
deb-src http://ftp.us.debian.org/debian unstable main contrib non-free
'''
        with self.assert_file_change(sources_path, None, unstable_content):
            library.setup_apt(self.state, 'http://ftp.us.debian.org/debian',
                              'unstable', ['main', 'contrib', 'non-free'])

    @patch('freedommaker.library.run_in_chroot')
    def test_setup_flash_kernel(self, run):
        """Test setting up flash kernel."""
        machine_path = self.state['mount_point'] + '/etc/flash-kernel/machine'
        expected_content = 'test-machine'
        with self.assert_file_change(machine_path, None, expected_content):
            library.setup_flash_kernel(self.state, 'test-machine', None,
                                       'ext2')

        self.assertEqual(run.call_args_list, [
            call(self.state, ['apt-get', 'install', '-y', 'flash-kernel']),
            call(self.state, ['flash-kernel'])
        ])

        run.reset_mock()
        with self.assert_file_change(machine_path, None, expected_content):
            library.setup_flash_kernel(self.state, 'test-machine', 'debug',
                                       'vfat')

        selection = b'flash-kernel flash-kernel/linux_cmdline string debug'
        self.assertEqual(run.call_args_list, [
            call(self.state, ['debconf-set-selections'], feed_stdin=selection),
            call(self.state, ['apt-get', 'install', '-y', 'flash-kernel']),
        ])

    @patch('freedommaker.library.run_in_chroot')
    def test_update_initramfs(self, run):
        """Test updating initramfs."""
        library.update_initramfs(self.state)

        self.assertEqual(run.call_args_list,
                         [call(self.state, ['update-initramfs', '-u'])])

    @patch('freedommaker.library.run')
    def test_install_boot_loader_path(self, run):
        """Test installing boot loader components using dd."""
        path = 'u-boot/path'
        full_path = self.state['mount_point'] + '/' + path
        library.install_boot_loader_part(self.state, path, '533', '515')
        run.assert_called_with([
            'dd', 'if=' + full_path, 'of=' + self.image, 'seek=533', 'bs=515',
            'conv=notrunc'
        ])

        library.install_boot_loader_part(self.state, path, '533', '515', '90')
        run.assert_called_with([
            'dd', 'if=' + full_path, 'of=' + self.image, 'seek=533', 'bs=515',
            'conv=notrunc', 'count=90'
        ])

    @patch('freedommaker.library.run')
    def test_fill_free_space_with_zeros(self, run):
        """Test filling free space with zeros."""
        zeros_path = self.state['mount_point'] + '/ZEROS'
        library.fill_free_space_with_zeros(self.state)
        self.assertEqual(run.call_args_list, [
            call(['dd', 'if=/dev/zero', 'of=' + zeros_path, 'bs=1M'],
                 ignore_fail=True),
            call(['rm', '-f', zeros_path])
        ])

    @patch('freedommaker.library.run')
    def test_compress(self, run):
        """Test compressing an image."""
        archive_file = self.random_string()
        image_file = self.random_string()

        library.compress(archive_file, image_file)
        run.assert_called_with(
            ['xz', '--no-warn', '--threads=0', '-9', '--force', image_file])

    @patch('os.remove')
    @patch('freedommaker.library.run')
    def test_sign(self, run, remove):
        """Test running signing with GPG."""
        archive = self.random_string()
        signature = archive + '.sig'
        remove.side_effect = FileNotFoundError
        library.sign(archive)
        run.assert_called_with(
            ['gpg', '--output', signature, '--detach-sig', archive])
