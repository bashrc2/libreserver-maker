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
Worker class to build Cubietech Cubieboard2 image.
"""

from .a20 import A20ImageBuilder


class Cubieboard2ImageBuilder(A20ImageBuilder):
    """Image builder for Cubieboard 2 target."""
    machine = 'cubieboard2'
    flash_kernel_name = 'Cubietech Cubieboard2'
    u_boot_path = 'usr/lib/u-boot/Cubieboard2/u-boot-sunxi-with-spl.bin'
