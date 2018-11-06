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

from .. import library
from .arm import ARMImageBuilder


class A64ImageBuilder(ARMImageBuilder):
    """Image builder for all Allwinner A64 board targets."""
    architecture = 'arm64'
    kernel_flavor = 'arm64'
    boot_offset = '1mib'

    def __init__(self, *args, **kwargs):
        """Initialize builder object."""
        super().__init__(*args, **kwargs)
        self.packages += ['atf-allwinner', 'device-tree-compiler']

    @staticmethod
    def install_boot_loader(state):
        """Install the boot loader onto the image."""
        library.run_in_chroot(state,
                              ['u-boot-install-sunxi64', state['loop_device']])
