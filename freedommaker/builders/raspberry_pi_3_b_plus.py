# SPDX-License-Identifier: GPL-3.0-or-later
"""
Worker class to build Raspberry Pi 3 Model B+ image.
"""

from .raspberry_pi_3 import RaspberryPi3ImageBuilder


class RaspberryPi3BPlusImageBuilder(RaspberryPi3ImageBuilder):
    """Image builder for Raspberry Pi 3 Model B+ target."""
    machine = 'raspberry3-b-plus'
    flash_kernel_name = 'Raspberry Pi 3 Model B+'
