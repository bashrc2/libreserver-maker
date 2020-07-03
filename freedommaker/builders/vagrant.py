# SPDX-License-Identifier: GPL-3.0-or-later
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

    def vagrant_package(self, vm_file, vagrant_file):
        """Create a vagrant package from VM file."""
        library.run(['bin/vagrant-package',
                     '--distribution', self.arguments.distribution,
                     '--output', vagrant_file, vm_file])
