# SPDX-License-Identifier: GPL-3.0-or-later
"""
Worker class to build Lamobo R1 (BananaPI Router v1) image.
"""

from .a20 import A20ImageBuilder


class LamoboR1ImageBuilder(A20ImageBuilder):
    """Image builder for Lamobo R1 (BananaPI Router v1) targets."""
    machine = 'lamobo-r1'
    flash_kernel_name = 'Lamobo R1'
    u_boot_path = 'usr/lib/u-boot/Lamobo_R1/u-boot-sunxi-with-spl.bin'
