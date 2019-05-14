#
# This file is part of Freedom Maker.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
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

        library.run_in_chroot(
            state, ['u-boot-install-sunxi64', state['loop_device']], env=env)
