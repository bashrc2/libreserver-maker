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
Worker class to build Vagrant images.
"""

import os

from .. import library
from .virtualbox_amd64 import VirtualBoxAmd64ImageBuilder


class VagrantImageBuilder(VirtualBoxAmd64ImageBuilder):
    """Image builder for Vagrant package."""
    vagrant_extension = '.box'

    @classmethod
    def get_target_name(cls):
        """Return the name of the target for an image builder."""
        return 'vagrant'

    def build(self):
        """Run the image building process."""
        vm_file = self._replace_extension(self.image_file,
                                          self.vm_image_extension)
        vagrant_file = self._replace_extension(self.image_file,
                                               self.vagrant_extension)

        self.make_image()
        self.create_vm_file(self.image_file, vm_file)
        os.remove(self.image_file)
        self.vagrant_package(vm_file, vagrant_file)

    @staticmethod
    def vagrant_package(vm_file, vagrant_file):
        """Create a vagrant package from VM file."""
        library.run(
            ['sudo', 'bin/vagrant-package', '--output', vagrant_file, vm_file])



