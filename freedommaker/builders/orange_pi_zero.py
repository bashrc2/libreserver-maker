# SPDX-License-Identifier: GPL-3.0-or-later
"""
Worker class to build Xunlong Orange Pi Zero image.
"""

from .a20 import A20ImageBuilder


class OrangePiZeroImageBuilder(A20ImageBuilder):
    """Image builder for Orange Pi Zero target."""
    machine = 'orange-pi-zero'
    flash_kernel_name = 'Xunlong Orange Pi Zero'
    u_boot_path = 'usr/lib/u-boot/orangepi_zero/u-boot-sunxi-with-spl.bin'
