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
Worker class to build Olimex A20-OLinuXino Micro image.
"""

from .a20 import A20ImageBuilder


class A20OLinuXinoMicroImageBuilder(A20ImageBuilder):
    """Image builder for A20 OLinuXino Micro targets."""
    machine = 'a20-olinuxino-micro'
    flash_kernel_name = 'Olimex A20-Olinuxino Micro'
    u_boot_path = \
        'usr/lib/u-boot/A20-OLinuXino_MICRO/u-boot-sunxi-with-spl.bin'
