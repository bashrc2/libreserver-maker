# SPDX-License-Identifier: GPL-3.0-or-later
"""
Worker class to build Cubietech Cubieboard2 image.
"""

from .a20 import A20ImageBuilder


class Cubieboard2ImageBuilder(A20ImageBuilder):
    """Image builder for Cubieboard 2 target."""
    machine = 'cubieboard2'
    flash_kernel_name = 'Cubietech Cubieboard2'
    u_boot_path = 'usr/lib/u-boot/Cubieboard2/u-boot-sunxi-with-spl.bin'
