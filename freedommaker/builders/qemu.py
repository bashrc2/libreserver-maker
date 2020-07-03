# SPDX-License-Identifier: GPL-3.0-or-later
"""
Base worker class to build all Qemu images.
"""

from .. import library
from .vm import VMImageBuilder


class QemuImageBuilder(VMImageBuilder):
    """Base image builder for all Qemu targets."""
    vm_image_extension = '.qcow2'

    @classmethod
    def get_target_name(cls):
        """Return the name of the target for an image builder."""
        if getattr(cls, 'architecture', None):
            return 'qemu-' + cls.architecture

        return None

    def create_vm_file(self, image_file, vm_file):
        """Create a VM image file from image file."""
        library.run(
            ['qemu-img', 'convert', '-O', 'qcow2', image_file, vm_file])
