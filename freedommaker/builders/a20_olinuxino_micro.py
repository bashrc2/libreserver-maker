# SPDX-License-Identifier: GPL-3.0-or-later
"""
Worker class to build Olimex A20-OLinuXino Micro image.
"""

from .a20 import A20ImageBuilder


class A20OLinuXinoMicroImageBuilder(A20ImageBuilder):
    """Image builder for A20 OLinuXino Micro targets."""
    machine = 'a20-olinuxino-micro'
    flash_kernel_name = 'Olimex A20-Olinuxino Micro'
    u_boot_path = \
        'usr/lib/u-boot/A20-OLinuXino_MICRO/u-boot-sunxi-with-spl.bin'
