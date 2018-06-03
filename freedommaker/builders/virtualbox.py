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
Base worker class to build VirtualBox images.
"""

import os

from .. import library
from .vm import VMImageBuilder


class VirtualBoxImageBuilder(VMImageBuilder):
    """Base image builder for all VirtualBox targets."""
    vm_image_extension = '.vdi'

    @classmethod
    def get_target_name(cls):
        """Return the name of the target for an image builder."""
        if getattr(cls, 'architecture', None):
            return 'virtualbox-' + cls.architecture

        return None

    def create_vm_file(self, image_file, vm_file):
        """Create a VM file from image file."""
        try:
            os.remove(vm_file)
        except FileNotFoundError:
            pass

        library.run(['VBoxManage', 'convertdd', image_file, vm_file])
