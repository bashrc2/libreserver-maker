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
Worker class to build TI AM335x BeagleBone Black image.
"""

from .. import library
from .arm import ARMImageBuilder


class BeagleBoneImageBuilder(ARMImageBuilder):
    """Image builder for BeagleBone target."""
    architecture = 'armhf'
    machine = 'beaglebone'
    kernel_flavor = 'armmp'
    boot_offset = '2mib'
    flash_kernel_name = 'TI AM335x BeagleBone Black'
    flash_kernel_options = 'console=ttyO0'

    @staticmethod
    def install_boot_loader(state):
        """Install the boot loader onto the image."""
        library.install_boot_loader_part(state,
                                         'usr/lib/u-boot/am335x_boneblack/MLO',
                                         seek='1',
                                         size='128k',
                                         count='1')
        library.install_boot_loader_part(
            state,
            'usr/lib/u-boot/am335x_boneblack/u-boot.img',
            seek='1',
            size='384k',
            count='2')
