# SPDX-License-Identifier: GPL-3.0-or-later
"""
Worker class to build Pine64 LTS image.
"""

from .a64 import A64ImageBuilder


class Pine64LTSImageBuilder(A64ImageBuilder):
    """Image builder for Pine64 LTS target."""
    machine = 'pine64-lts'
    flash_kernel_name = 'Pine64 LTS'
    u_boot_target = 'pine64-lts'
