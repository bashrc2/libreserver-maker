# SPDX-License-Identifier: GPL-3.0-or-later
"""
Base worker class to build Raspberry Pi 2 and 3 images.
"""

from .. import library
from .arm import ARMImageBuilder


class RaspberryPiWithUBoot(ARMImageBuilder):
    """Base image builder for Raspberry Pi 2 and 3 targets."""
    free = False
    uboot_variant = None
    firmware_filesystem_type = 'vfat'
    firmware_size = '64MiB'


    def install_boot_loader(self, state):
        """Install the boot loader onto the image."""
        if not self.uboot_variant:
            raise NotImplementedError

        firmware_package = 'raspi-firmware'
        if self.arguments.distribution in ['buster', 'stable']:
            firmware_package = 'raspi3-firmware'

        script = '''
set -e
set -x
set -o pipefail

apt-get install --no-install-recommends -y dpkg-dev
cd /tmp
apt-get source {firmware_package}
cp {firmware_package}*/boot/* /boot/firmware
rm -rf {firmware_package}*
cd /

# remove unneeded firmware files
rm -f /boot/firmware/fixup_*
rm -f /boot/firmware/start_*

# u-boot setup
apt-get install -y u-boot-rpi
cp /usr/lib/u-boot/{uboot_variant}/u-boot.bin /boot/firmware/kernel.img
cp /usr/lib/u-boot/{uboot_variant}/u-boot.bin /boot/firmware/kernel7.img
'''.format(firmware_package=firmware_package, uboot_variant=self.uboot_variant)
        library.run_in_chroot(state, ['bash', '-c', script])
