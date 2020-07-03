# SPDX-License-Identifier: GPL-3.0-or-later
"""
Worker class to build Raspberry Pi 2 image.
"""

from .raspberry_pi_with_uboot import RaspberryPiWithUBoot


class RaspberryPi2ImageBuilder(RaspberryPiWithUBoot):
    """Image builder for Raspberry Pi 2 target."""
    architecture = 'armhf'
    machine = 'raspberry2'
    boot_offset = '64mib'
    kernel_flavor = 'armmp'
    flash_kernel_name = 'Raspberry Pi 2 Model B'
    uboot_variant = 'rpi_2'
