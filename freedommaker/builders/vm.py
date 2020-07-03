# SPDX-License-Identifier: GPL-3.0-or-later
"""
Base worker class to build Virtual Machine images.
"""

import os

from .amd_intel import AMDIntelImageBuilder


class VMImageBuilder(AMDIntelImageBuilder):
    """Base image builder for all virtual machine targets."""
    vm_image_extension = None

    def build(self):
        """Run the image building process."""
        vm_file = self._replace_extension(self.image_file,
                                          self.vm_image_extension)
        vm_archive_file = vm_file + '.xz'

        self.make_image()
        self.create_vm_file(self.image_file, vm_file)
        os.remove(self.image_file)
        self.compress(vm_archive_file, vm_file)

        self.sign(vm_archive_file)

    def create_vm_file(self, image_file, vm_file):
        """Create a VM image from image file."""
        raise Exception('Not reached')
