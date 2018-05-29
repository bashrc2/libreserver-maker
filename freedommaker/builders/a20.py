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
Base worker class to build all Allwinner A20 based SBC images.
"""

from .. import library
from .arm import ARMImageBuilder


class A20ImageBuilder(ARMImageBuilder):
    """Base image builder for all Allwinner A20 board based targets."""
    architecture = 'armhf'
    kernel_flavor = 'armmp-lpae'
    boot_offset = '1mib'
    u_boot_path = None

    def install_boot_loader(self, state):
        """Install the boot loader onto the image."""
        if not self.u_boot_path:
            raise NotImplementedError

        library.install_boot_loader_part(
            state, self.u_boot_path, seek='8', size='1k')
