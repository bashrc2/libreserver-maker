# SPDX-License-Identifier: GPL-3.0-or-later
"""
Worker class to build Olimex A20-OLinuXino-LIME2 image.
"""

from .a20 import A20ImageBuilder


class A20OLinuXinoLime2ImageBuilder(A20ImageBuilder):
    """Image builder for A20 OLinuXino Lime2 targets."""
    machine = 'a20-olinuxino-lime2'
    flash_kernel_name = 'Olimex A20-OLinuXino-LIME2'
    u_boot_path = \
        'usr/lib/u-boot/A20-OLinuXino-Lime2/u-boot-sunxi-with-spl.bin'
