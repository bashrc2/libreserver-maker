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
Miscellaneous utilities that don't fit anywhere else.
"""

import re


def add_disk_offsets(offset1, offset2):
    """Add two disk offsets as understood by parted utility.

    Currently only adding offsets in mib is supported.
    """
    if not offset1.endswith('mib') or not offset2.endswith('mib'):
        raise NotImplementedError('Adding anything but offsets in mib')

    result = int(offset1.rstrip('mib')) + int(offset2.rstrip('mib'))
    return '{}mib'.format(result)


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
