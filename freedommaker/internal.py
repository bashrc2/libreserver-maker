# SPDX-License-Identifier: GPL-3.0-or-later
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
        self.state = {'success': True}

    def make_image(self):
        """Create a disk image."""
        # enable systemd resolved?
        try:
            self._get_temp_image_file()
            self._create_empty_image()
            self._create_partitions()
            self._loopback_setup()
            self._create_filesystems()
            self._mount_filesystems()
            self._setup_extra_storage()
            self._debootstrap()
            self._set_hostname()
            # self._lock_root_user()
            self._create_sudo_user()
            self._set_freedombone_disk_image_flag()
            self._create_fstab()
            self._mount_additional_filesystems()
            self._setup_build_apt()
            self._install_freedombone_packages()
            self._remove_ssh_keys()
            self._generate_keys_on_first_boot()
            self._install_boot_loader()
            self._setup_final_apt()
            self._enable_eth0()
            self._install_webserver()
            self._fill_free_space_with_zeros()
        except (Exception, KeyboardInterrupt) as exception:
            logger.exception('Exception during build - %s', exception)
            self.state['success'] = False
            raise
        finally:
            self._teardown()

    def _get_temp_image_file(self):
        """Get the temporary path to where the image should be built.

        If building to RAM is enabled, create a temporary directory, mount
        tmpfs in it and return a path in that directory. This is so that builds
        that happen in RAM will be faster.

        If building to RAM is disabled, append .temp to the final file name and
        return it.

        """
        if not self.builder.arguments.build_in_ram:
            return library.create_temp_image(self.state,
                                             self.builder.image_file)

        size = utils.add_disk_sizes(self.builder.arguments.image_size,
                                    self.builder.extra_storage_size)
        size = utils.add_disk_sizes(size, '100M')  # Buffer
        return library.create_ram_directory_image(self.state,
                                                  self.builder.image_file,
                                                  size)

    def _create_empty_image(self):
        """Create an empty disk image to create parititions in."""
        library.create_image(self.state, self.builder.arguments.image_size)

    def _create_partitions(self):
        """Create partition table and partitions in the image."""
        # Don't install MBR on the image file, it is not needed as we use
        # either grub, u-boot or UEFI.
        library.create_partition_table(self.state,
                                       self.builder.partition_table_type)
        boot_partition_number = 1

        offset = '1mib'
        if self.builder.efi_filesystem_type:
            end = utils.add_disk_offsets(offset, self.builder.efi_size)
            library.create_partition(self.state, 'efi', offset, end,
                                     self.builder.efi_filesystem_type)
            offset = utils.add_disk_offsets(end, '1mib')

        if self.builder.firmware_filesystem_type:
            end = utils.add_disk_offsets(offset, self.builder.firmware_size)
            library.create_partition(self.state, 'firmware', offset, end,
                                     self.builder.firmware_filesystem_type)
            offset = utils.add_disk_offsets(end, '1mib')
            boot_partition_number += 1

        if self.builder.boot_filesystem_type:
            end = utils.add_disk_offsets(offset, self.builder.boot_size)
            library.create_partition(self.state, 'boot', offset, end,
                                     self.builder.boot_filesystem_type)
            offset = utils.add_disk_offsets(end, '1mib')

        library.create_partition(self.state, 'root', offset, '100%',
                                 self.builder.root_filesystem_type)

        library.set_boot_flag(self.state,
                              partition_number=boot_partition_number)

    def _loopback_setup(self):
        """Perform mapping to loopback devices from partitions in image file."""
        library.loopback_setup(self.state)

    def _create_filesystems(self):
        """Create file systems inside the partitions created."""
        if self.builder.firmware_filesystem_type:
            library.create_filesystem(self.state['devices']['firmware'],
                                      self.builder.firmware_filesystem_type)

        if self.builder.efi_filesystem_type:
            library.create_filesystem(self.state['devices']['efi'],
                                      self.builder.efi_filesystem_type)

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

        if self.builder.efi_filesystem_type:
            library.mount_filesystem(self.state, 'efi', 'boot/efi')

        if self.builder.firmware_filesystem_type:
            library.mount_filesystem(self.state, 'firmware', 'boot/firmware')

    def _setup_extra_storage(self):
        """Setup some extra storage for root filesystem.

        btrfs runs out of space even when the data stored is not even half of
        the available space. This is due to it needing re-balance operation. It
        may not be possible to run the re-balance during a heavy operation such
        as installing a package with lot of dependencies. Adding
        an additional disk is a good work around for that. The additional
        device will be removed during cleanup and filesystem will be
        re-balanced.

        """
        library.setup_extra_storage(self.state,
                                    self.builder.root_filesystem_type,
                                    self.builder.extra_storage_size)

    def _mount_additional_filesystems(self):
        """Mount extra filesystems: dev, devpts, sys and proc."""
        library.mount_filesystem(self.state, '/dev', 'dev', is_bind_mount=True)
        library.mount_filesystem(self.state, '/dev/pts', 'dev/pts',
                                 is_bind_mount=True)
        library.mount_filesystem(self.state, '/proc', 'proc',
                                 is_bind_mount=True)
        library.mount_filesystem(self.state, '/sys', 'sys', is_bind_mount=True)

        # Kill all the processes on the / filesystem before attempting to
        # unmount /dev/pts. Otherwise, unmounting /dev/pts will fail.
        library.schedule_cleanup(self.state, library.process_cleanup,
                                 self.state)

    def _get_packages(self):
        """Return the list of extra packages to install.

        XXX: Move this to builder.py.
        """
        return self._get_basic_packages() + \
            self._get_kernel_packages() + \
            self._get_boot_loader_packages() + \
            self._get_filesystem_packages() + \
            self._get_extra_packages()

    def _get_basic_packages(self):
        """Return a list of basic packages for all king of images."""
        return self.builder.packages

    def _get_kernel_packages(self):
        """Return package needed for kernel."""
        if not self.builder.kernel_flavor:
            return []

        return ['linux-image-' + self.builder.kernel_flavor]

    def _get_boot_loader_packages(self):
        """Return packaged needed by boot loader."""
        if not self.builder.boot_loader:
            return []

        if self.builder.boot_loader == 'grub':
            return ['grub-pc']

        if self.builder.boot_loader == 'u-boot':
            if self.builder.architecture == 'arm64':
                return ['u-boot-sunxi', 'u-boot-tools']

            return ['u-boot', 'u-boot-tools']

        raise NotImplementedError

    def _get_filesystem_packages(self):
        """Return packages required for filesystems."""
        packages = []
        if 'btrfs' in [
                self.builder.root_filesystem_type,
                self.builder.boot_filesystem_type,
                self.builder.efi_filesystem_type,
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
            components += ['contrib']

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

    def _should_use_backports(self):
        """Return whether backports is in use."""
        stable = self.builder.arguments.distribution in ['stable', 'buster']
        return stable and not self.builder.arguments.disable_backports

    def _install_webserver(self):
        """Setup webserver."""
        library.install_package(self.state, 'nginx')
        script = 'echo -e ' + \
            "'<html><head><title>Freedombone</title>" + \
            "</head><body bgcolor=\"linen\" text=\"black\">" + \
            "<div style=\"font-size: 100px; text-align: center;\">" + \
            "Freedombone</div>" + \
            "<div style=\"font-size: 38px; text-align: center;\">" + \
            "To begin installation login with:</div>" + \
            "<div style=\"font-size: 38px; " + \
            "text-align: center;\"><p role=\"alert\">" + \
            "<b>ssh admin@192.168.x.y</b>" + \
            "</p></div>" + \
            "<div style=\"font-size: 38px; text-align: center;\">" + \
            "<p>The initial password is <b>freedombone</b>. " + \
            "After changing your password ssh back in again " + \
            "with your chosen password.</p>" + \
            "<p>When the install is complete <i>ssh access " + \
            "will not be available</i> unless you turn it on " + \
            "via the settings screen.</p>" + \
            "</div></body></html>'" + \
            ' > /var/www/html/index.nginx-debian.html'
        library.run_script_in_chroot(self.state, script)

    def _install_freedombone_packages(self):
        """Setup freedombone repo."""
        library.install_package(self.state, 'git')
        library.install_package(self.state, 'build-essential')
        library.install_package(self.state, 'dialog')
        library.install_package(self.state, 'man')
        library.install_package(self.state, 'openssh-server')

        freedombone_repo = 'https://gitlab.com/bashrc2/freedombone.git'
        library.run_in_chroot(self.state, [
            'git', 'clone', '--depth=1', '--branch', 'bullseye',
            '--single-branch', freedombone_repo, '/root/freedombone'
        ])

        script = '''cd /root/freedombone;
make install'''
        library.run_script_in_chroot(self.state, script)
        script = 'echo -e "# start firstboot\necho -e ' + \
            "'\n==Freedombone Installation==\n\n" + \
            "Run:\n\n  sudo freedombone menuconfig\n\nor\n\n" + \
            "  sudo freedombone menuconfig-onion\n\n" + \
            "to begin installation.\n\n" + \
            "For more info:\n\n  man freedombone\n'" + \
            '\n# end firstboot" >> /home/admin/.bashrc'
        library.run_script_in_chroot(self.state, script)

    def _enable_eth0(self):
        """Enable eth0 interface."""
        library.run_in_chroot(self.state,
                              ['ln', '-sf', '/dev/null',
                               '/etc/systemd/network/99-default.link'])
        library.update_initramfs(self.state)
        script = 'echo -e ' + \
            "'auto eth0\nallow-hotplug eth0\niface eth0 inet dhcp'" + \
            ' > /etc/network/interfaces.d/dynamic'
        library.run_script_in_chroot(self.state, script)

    def _lock_root_user(self):
        """Lock the root user account."""
        logger.info('Locking root user')
        library.run_in_chroot(self.state, ['passwd', '-l', 'root'])

    def _create_sudo_user(self):
        """Create a user in the image with sudo permissions."""
        library.install_package(self.state, 'sudo')
        username = 'admin'
        logger.info('Creating a new sudo user %s', username)
        library.run_in_chroot(
            self.state,
            ['adduser', '--gecos', username, '--disabled-password', username])

        library.run_in_chroot(self.state, ['adduser', username, 'sudo'])
        script = 'chpasswd <<<"' + username + ':freedombone"'
        library.run_script_in_chroot(self.state, script)
        # password should be changed on first login
        library.run_in_chroot(self.state, ['chage', '-d0', 'admin'])

    def _set_freedombone_disk_image_flag(self):
        """Set a flag to indicate that this is a Freedombone image.

        And that Freedombone is not installed using a Debian package.

        """
        library.run_in_chroot(
            self.state, ['mkdir', '-p', '-m', '755', '/var/lib/freedombone'])
        library.run_in_chroot(
            self.state,
            ['touch', '/var/lib/freedombone/is-freedombone-disk-image'])

    def _remove_ssh_keys(self):
        """Remove SSH keys so that images don't contain known keys."""
        library.run_in_chroot(self.state,
                              ['sh', '-c', 'rm -f /etc/ssh/ssh_host_*'],
                              ignore_fail=True)

    def _generate_keys_on_first_boot(self):
        """Generates keys on first boot."""
        script = 'echo -e "#!/bin/bash\n' + \
            'if [ ! -f /etc/ssh/ssh_host_ed25519_key.pub ]; then\n' + \
            '  dpkg-reconfigure openssh-server\nfi"' + \
            ' > /usr/bin/firstboot_generate_keys'
        library.run_script_in_chroot(self.state, script)
        library.run_in_chroot(self.state,
                              ['chmod', '+x',
                               '/usr/bin/firstboot_generate_keys'])
        script = '/usr/bin/bash -c /usr/bin/firstboot_generate_keys'
        library.add_cron_in_chroot(self.state, 1, script)

    def _create_fstab(self):
        """Create fstab with entries for each paritition."""
        library.add_fstab_entry(self.state, 'root',
                                self.builder.root_filesystem_type, 1,
                                append=False)
        if self.builder.boot_filesystem_type:
            library.add_fstab_entry(self.state, 'boot',
                                    self.builder.boot_filesystem_type, 2)

        if self.builder.efi_filesystem_type:
            library.add_fstab_entry(self.state, 'efi',
                                    self.builder.efi_filesystem_type, 2)

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
                                       self.builder.flash_kernel_name, options,
                                       self.builder.boot_filesystem_type)

        if hasattr(self.builder, 'install_boot_loader'):
            self.builder.install_boot_loader(self.state)

        library.update_initramfs(self.state)

    def _setup_build_apt(self):
        """Setup apt to use as the build mirror."""
        use_backports = self._should_use_backports()
        library.setup_apt(self.state, self.builder.arguments.build_mirror,
                          self.builder.arguments.distribution,
                          self._get_components(),
                          enable_backports=use_backports)

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

    def _teardown(self):
        """Run cleanup operations for each step that executed."""
        library.cleanup(self.state)
