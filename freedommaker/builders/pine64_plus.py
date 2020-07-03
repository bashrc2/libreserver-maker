# SPDX-License-Identifier: GPL-3.0-or-later
"""
Worker class to build Pine64+ image.
"""

from .a64 import A64ImageBuilder


class Pine64PlusImageBuilder(A64ImageBuilder):
    """Image builder for Pine64+ target."""
    machine = 'pine64-plus'
    flash_kernel_name = 'Pine64+'
    u_boot_target = 'pine64_plus'
