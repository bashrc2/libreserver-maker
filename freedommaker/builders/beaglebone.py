# SPDX-License-Identifier: GPL-3.0-or-later
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
