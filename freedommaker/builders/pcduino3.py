# SPDX-License-Identifier: GPL-3.0-or-later
"""
Worker class to build LinkSprite pcDuino3 image.
"""

from .a20 import A20ImageBuilder


class PCDuino3ImageBuilder(A20ImageBuilder):
    """Image builder for PCDuino3 target."""
    machine = 'pcduino3'
    flash_kernel_name = 'LinkSprite pcDuino3'
    u_boot_path = \
        'usr/lib/u-boot/Linksprite_pcDuino3/u-boot-sunxi-with-spl.bin'
