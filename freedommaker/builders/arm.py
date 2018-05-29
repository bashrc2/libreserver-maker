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
Base worker class to build all ARM images.
"""

from ..builder import ImageBuilder


class ARMImageBuilder(ImageBuilder):
    """Base image builder for all ARM targets."""
    boot_loader = 'u-boot'
    boot_filesystem_type = 'ext2'
    boot_size = '128mib'

    @classmethod
    def get_target_name(cls):
        """Return the name of the target for an image builder."""
        return getattr(cls, 'machine', None)
