# SPDX-License-Identifier: GPL-3.0-or-later
"""
Miscellaneous utilities that don't fit anywhere else.
"""

import re


def add_disk_offsets(offset1, offset2):
    """Add two disk offsets as understood by parted utility.

    Currently only adding offsets in MiB is supported. For parted 'mib' is
    different from 'MiB'. When specifying the ending sector of a partition,
    'mib' means that specified sector included like [start, end] and 'MiB'
    means that specified sector is not included like [start, end).

    """
    if not offset1.endswith('MiB') or not offset2.endswith('MiB'):
        raise NotImplementedError('Adding anything but offsets in MiB')

    result = int(offset1.rstrip('MiB')) + int(offset2.rstrip('MiB'))
    return '{}MiB'.format(result)


def parse_disk_size(input_size):
    """Return integer size for size strings like 1000M, 2G etc."""
    try:
        return int(input_size)
    except ValueError:
        pass

    if not re.fullmatch(r'\d+[bkKMGT]', input_size):
        raise ValueError('Invalid size: ' + input_size)

    size = input_size[:-1]
    unit = input_size[-1]
    size_map = {
        'b': 1,
        'k': 1024,
        'K': 1024,
        'M': 1024 * 1024,
        'G': 1024 * 1024 * 1024,
        'T': 1024 * 1024 * 1024 * 1024,
    }
    return int(size) * size_map[unit]


def format_disk_size(size):
    """Return string like 100M, 2G given size in bytes."""
    unit = 0
    while size >= 1024 and unit < 5 and int(size / 1024) * 1024 == size:
        unit += 1
        size = int(size / 1024)

    return str(size) + ['', 'K', 'M', 'G', 'T'][unit]


def add_disk_sizes(size1, size2):
    """Add two string sizes represented as 1000M, 2G, etc."""
    return format_disk_size(parse_disk_size(size1) + parse_disk_size(size2))
