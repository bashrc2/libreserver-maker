# SPDX-License-Identifier: GPL-3.0-or-later
"""
Worker class to build Cubietech Cubietruck image.
"""

from .a20 import A20ImageBuilder


class CubietruckImageBuilder(A20ImageBuilder):
    """Image builder for Cubietruck (Cubieboard 3) target."""
    machine = 'cubietruck'
    flash_kernel_name = 'Cubietech Cubietruck'
    u_boot_path = 'usr/lib/u-boot/Cubietruck/u-boot-sunxi-with-spl.bin'
