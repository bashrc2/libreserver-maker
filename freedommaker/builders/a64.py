# SPDX-License-Identifier: GPL-3.0-or-later
"""
Base worker class to build all ARM64 images.
"""

import os

from .. import library
from .arm import ARMImageBuilder


class A64ImageBuilder(ARMImageBuilder):
    """Image builder for all Allwinner A64 board targets."""
    architecture = 'arm64'
    kernel_flavor = 'arm64'
    boot_offset = '1mib'
    u_boot_target = None

    def __init__(self, *args, **kwargs):
        """Initialize builder object."""
        super().__init__(*args, **kwargs)
        self.packages += ['arm-trusted-firmware', 'device-tree-compiler']

    @classmethod
    def install_boot_loader(cls, state):
        """Install the boot loader onto the image."""
        if not cls.u_boot_target:
            raise ValueError('U-boot target must be provided.')

        u_boot_target_path = '/usr/lib/u-boot/{}'.format(cls.u_boot_target)
        env = os.environ.copy()
        env['TARGET'] = u_boot_target_path

        library.run_in_chroot(state,
                              ['u-boot-install-sunxi64', state['loop_device']],
                              env=env)
