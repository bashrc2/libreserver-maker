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
Worker class to build LinkSprite pcDuino3 image.
"""

from .a20 import A20ImageBuilder


class PCDuino3ImageBuilder(A20ImageBuilder):
    """Image builder for PCDuino3 target."""
    machine = 'pcduino3'
    flash_kernel_name = 'LinkSprite pcDuino3'
    u_boot_path = 'usr/lib/u-boot/Linksprite_pcDuino3/u-boot-sunxi-with-spl.bin'
