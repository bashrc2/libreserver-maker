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
Base worker class to build Raspberry Pi 2 and 3 images.
"""

from .. import library
from .arm import ARMImageBuilder


class RaspberryPiWithUBoot(ARMImageBuilder):
    """Base image builder for Raspberry Pi 2 and 3 targets."""
    free = False
    uboot_variant = None
    firmware_filesystem_type = 'vfat'
    firmware_size = '60mib'

    def install_boot_loader(self, state):
        """Install the boot loader onto the image."""
        if not self.uboot_variant:
            raise NotImplementedError

        script = '''
set -e
set -x
set -o pipefail

apt-get install --no-install-recommends -y dpkg-dev
cd /tmp
apt-get source raspi3-firmware
cp raspi3-firmware*/boot/* /boot/firmware
rm -rf raspi3-firmware*
cd /

# remove unneeded firmware files
rm -f /boot/firmware/fixup_*
rm -f /boot/firmware/start_*

# u-boot setup
apt-get install -y u-boot-rpi
cp /usr/lib/u-boot/{uboot_variant}/u-boot.bin /boot/firmware/kernel.img
'''.format(uboot_variant=self.uboot_variant)
        library.run_in_chroot(state, ['bash', '-c', script])
