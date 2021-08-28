# SPDX-License-Identifier: GPL-3.0-or-later
"""
Base worker class to build all Allwinner A20 based SBC images.
"""

from .. import library
from .arm import ARMImageBuilder


class A20ImageBuilder(ARMImageBuilder):
    """Base image builder for all Allwinner A20 board based targets."""
    architecture = 'armhf'
    kernel_flavor = 'armmp-lpae'
    u_boot_path = None

    def install_boot_loader(self, state):
        """Install the boot loader onto the image."""
        if not self.u_boot_path:
            raise NotImplementedError

        library.install_boot_loader_part(state,
                                         self.u_boot_path,
                                         seek='8',
                                         size='1k')
