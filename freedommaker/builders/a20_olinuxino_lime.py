# SPDX-License-Identifier: GPL-3.0-or-later
"""
Worker class to build Olimex A20-OLinuXino-LIME image.
"""

from .a20 import A20ImageBuilder


class A20OLinuXinoLimeImageBuilder(A20ImageBuilder):
    """Image builder for A20 OLinuXino Lime targets."""
    machine = 'a20-olinuxino-lime'
    flash_kernel_name = 'Olimex A20-OLinuXino-LIME'
    u_boot_path = 'usr/lib/u-boot/A20-OLinuXino-Lime/u-boot-sunxi-with-spl.bin'
