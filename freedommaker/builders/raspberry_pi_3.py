# SPDX-License-Identifier: GPL-3.0-or-later
"""
Worker class to build Raspberry Pi 3 image.
"""

from .raspberry_pi_with_uboot import RaspberryPiWithUBoot


class RaspberryPi3ImageBuilder(RaspberryPiWithUBoot):
    """Image builder for Raspberry Pi 3 target."""
    architecture = 'armhf'
    machine = 'raspberry3'
    free = False
    boot_offset = '64mib'
    kernel_flavor = 'armmp'
    flash_kernel_name = 'Raspberry Pi 3 Model B'
    uboot_variant = 'rpi_3_32b'
