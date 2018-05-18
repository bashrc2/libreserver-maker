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
Basic image builder using internal implementation.
"""

import logging

from . import library, utils

logger = logging.getLogger(__name__)


class InternalBuilderBackend():
    """Build an image using internal implementation."""

    def __init__(self, builder):
        """Initialize the builder."""
        self.builder = builder
        self._temp_image_file = None
        self.state = {}

    def make_image(self):
        """Create a disk image."""
        # enable systemd resolved?
        try:
            self._create_empty_image()
            self._create_partitions()
            self._loopback_setup()
            self._create_filesystems()
            self._mount_filesystems()
            self._debootstrap()
            self._set_hostname()
            self._lock_root_user()
            self._create_sudo_user()
            self._set_freedombox_disk_image_flag()
            self._create_fstab()
            self._mount_additional_filesystems()
            self._setup_build_apt()
            self._install_freedombox_packages()
            self._remove_ssh_keys()
            self._install_boot_loader()
            self._setup_final_apt()
            self._fill_free_space_with_zeros()
        except (Exception, KeyboardInterrupt) as exception:
            logger.exception('Exception during build - %s', exception)
            raise
        finally:
            self._teardown()

        self._copy_image()

    def _create_empty_image(self):
        """Create an empty disk image to create parititions in."""
        self._temp_image_file = self.builder.get_temp_image_file()
        library.create_image(self.state, self._temp_image_file,
                             self.builder.arguments.image_size)

    def _create_partitions(self):
        """Create partition table and partitions in the image."""
        # Don't install MBR on the image file, it is not needed as we use
        # either grub or u-boot.
        library.create_partition_table(self._temp_image_file, 'msdos')

        offset = '1mib'
        if self.builder.firmware_filesystem_type:
            end = utils.add_disk_offsets(offset, self.builder.firmware_size)
            library.create_partition(self.state, 'firmware',
                                     self._temp_image_file, offset, end,
                                     self.builder.firmware_filesystem_type)
            offset = utils.add_disk_offsets(end, '1mib')

        if self.builder.boot_filesystem_type:
            end = utils.add_disk_offsets(offset, self.builder.boot_size)
            library.create_partition(self.state, 'boot', self._temp_image_file,
                                     offset, end,
                                     self.builder.boot_filesystem_type)
            offset = utils.add_disk_offsets(end, '1mib')

        library.create_partition(self.state, 'root', self._temp_image_file,
                                 offset, '100%',
                                 self.builder.root_filesystem_type)

        library.set_boot_flag(self._temp_image_file, partition_number=1)

    def _loopback_setup(self):
        """Perform mapping to loopback devices from partitions in image file."""
        library.loopback_setup(self.state, self._temp_image_file)

    def _create_filesystems(self):
        """Create file systems inside the partitions created."""
        if self.builder.firmware_filesystem_type:
            library.create_filesystem(self.state['devices']['firmware'],
                                      self.builder.firmware_filesystem_type)

        if self.builder.boot_filesystem_type:
            library.create_filesystem(self.state['devices']['boot'],
                                      self.builder.boot_filesystem_type)

        library.create_filesystem(self.state['devices']['root'],
                                  self.builder.root_filesystem_type)

    def _mount_filesystems(self):
        """Mount the filesystems in the right places."""
        library.mount_filesystem(self.state, 'root', None)

        if self.builder.boot_filesystem_type:
            library.mount_filesystem(self.state, 'boot', 'boot')

        if self.builder.firmware_filesystem_type:
            library.mount_filesystem(self.state, 'firmware', 'boot/firmware')

    def _mount_additional_filesystems(self):
        """Mount extra filesystems: dev, devpts, sys and proc."""
        library.mount_filesystem(self.state, '/dev', 'dev', is_bind_mount=True)
        library.mount_filesystem(
            self.state, '/dev/pts', 'dev/pts', is_bind_mount=True)
        library.mount_filesystem(
            self.state, '/proc', 'proc', is_bind_mount=True)
        library.mount_filesystem(self.state, '/sys', 'sys', is_bind_mount=True)

    def _get_packages(self):
        """Return the list of extra packages to install.

        XXX: Move this to builder.py.
        """
        return self._get_basic_packages() + \
            self._get_kernel_packages() + \
            self._get_boot_loader_packages() + \
            self._get_filesystem_packages() + \
            self._get_extra_packages()

    @staticmethod
    def _get_basic_packages():
        """Return a list of basic packages for all king of images."""
        return ['firmware-ath9k-htc']

    def _get_kernel_packages(self):
        """Return package needed for kernel."""
        return ['linux-image-' + self.builder.kernel_flavor]

    def _get_boot_loader_packages(self):
        """Return packaged needed by boot loader."""
        if self.builder.boot_loader == 'grub':
            return ['grub-pc']

        if self.builder.boot_loader == 'u-boot':
            return ['u-boot', 'u-boot-tools']

        raise NotImplementedError

    def _get_filesystem_packages(self):
        """Return packages required for filesystems."""
        packages = []
        if 'btrfs' in [
                self.builder.root_filesystem_type,
                self.builder.boot_filesystem_type,
                self.builder.firmware_filesystem_type
        ]:
            packages += ['btrfs-progs']

        return packages

    def _get_extra_packages(self):
        """Return extra packages passed on the command line."""
        return self.builder.arguments.package or []

    def _get_components(self):
        """Return the apt components to use."""
        components = ['main']
        if not self.builder.free:
            components += ['contrib', 'non-free']

        return components

    def _debootstrap(self):
        """Run debootstrap on the mount point."""
        variant = self.builder.debootstrap_variant or '-'
        library.qemu_debootstrap(self.state, self.builder.architecture,
                                 self.builder.arguments.distribution, variant,
                                 self._get_components(), self._get_packages(),
                                 self.builder.arguments.build_mirror)

    def _set_hostname(self):
        """Set hostname in debootstrapped file system."""
        library.set_hostname(self.state, self.builder.arguments.hostname)

    def _install_freedombox_packages(self):
        """Install custom .deb packages."""
        custom_plinth = None
        custom_setup = None
        for package in (self.builder.arguments.custom_package or []):
            if 'plinth_' in package:
                custom_plinth = package
            elif 'freedombox-setup_' in package:
                custom_setup = package

        if custom_plinth:
            library.install_custom_package(self.state, custom_plinth)

        if custom_setup:
            library.install_custom_package(self.state, custom_setup)
        else:
            library.install_package(self.state, 'freedombox-setup')

    def _lock_root_user(self):
        """Lock the root user account."""
        logger.info('Locking root user')
        library.run_in_chroot(self.state, ['passwd', '-l', 'root'])

    def _create_sudo_user(self):
        """Create a user in the image with sudo permissions."""
        username = 'fbx'
        logger.info('Creating a new sudo user %s', username)
        library.run_in_chroot(
            self.state,
            ['adduser', '--gecos', username, '--disabled-password', username])
        library.run_in_chroot(self.state, ['adduser', username, 'sudo'])

    def _set_freedombox_disk_image_flag(self):
        """Set a flag to indicate that this is a FreedomBox image.

        And that FreedomBox is not installed using a Debian package.

        """
        library.run_in_chroot(self.state,
                              ['mkdir', '-p', '/var/lib/freedombox'])
        library.run_in_chroot(
            self.state,
            ['touch', '/var/lib/freedombox/is-freedombox-disk-image'])

    def _remove_ssh_keys(self):
        """Remove SSH keys so that images don't contain known keys."""
        library.run_in_chroot(
            self.state, ['sh', '-c', 'rm -f /etc/ssh/ssh_host_*'],
            ignore_fail=True)

    def _create_fstab(self):
        """Create fstab with entries for each paritition."""
        library.add_fstab_entry(
            self.state,
            'root',
            self.builder.root_filesystem_type,
            1,
            append=False)
        if self.builder.boot_filesystem_type:
            library.add_fstab_entry(self.state, 'boot',
                                    self.builder.boot_filesystem_type, 2)

        if self.builder.firmware_filesystem_type:
            library.add_fstab_entry(self.state, 'firmware',
                                    self.builder.firmware_filesystem_type, 2)

    def _install_boot_loader(self):
        """Install grub/u-boot boot loader."""
        if self.builder.boot_loader == 'grub':
            library.install_grub(self.state)

        if hasattr(self.builder, 'flash_kernel_name') and \
                   self.builder.flash_kernel_name:
            options = getattr(self.builder, 'flash_kernel_options', None)
            library.setup_flash_kernel(self.state,
                                       self.builder.flash_kernel_name, options)

        if hasattr(self.builder, 'install_boot_loader'):
            self.builder.install_boot_loader(self.state)

    def _setup_build_apt(self):
        """Setup apt to use as the build mirror."""
        library.setup_apt(self.state, self.builder.arguments.build_mirror,
                          self.builder.arguments.distribution,
                          self._get_components())

    def _setup_final_apt(self):
        """Setup apt to use the image mirror."""
        library.setup_apt(self.state, self.builder.arguments.mirror,
                          self.builder.arguments.distribution,
                          self._get_components())

    def _fill_free_space_with_zeros(self):
        """Fill up the free space in the image with zeros.

        So that we can compress the image better.
        """
        library.fill_free_space_with_zeros(self.state)

    def _copy_image(self):
        """Copy from temp image to target path."""
        logger.info('Moving file: %s -> %s', self._temp_image_file,
                    self.builder.image_file)
        library.run([
            'sudo', 'cp', '--sparse=always', self._temp_image_file,
            self.builder.image_file
        ])

    def _teardown(self):
        """Run cleanup operations for each step that executed."""
        library.cleanup(self.state)
