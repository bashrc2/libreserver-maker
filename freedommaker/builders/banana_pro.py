# SPDX-License-Identifier: GPL-3.0-or-later
"""
Worker class to build LeMaker Banana Pro image.
"""

from .a20 import A20ImageBuilder


class BananaProImageBuilder(A20ImageBuilder):
    """Image builder for Banana Pro target."""
    machine = 'banana-pro'
    flash_kernel_name = 'LeMaker Banana Pro'
    u_boot_path = 'usr/lib/u-boot/Bananapro/u-boot-sunxi-with-spl.bin'
