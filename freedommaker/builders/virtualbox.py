# SPDX-License-Identifier: GPL-3.0-or-later
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
