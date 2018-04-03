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

def add_disk_offsets(offset1, offset2):
    """Add two disk offsets as understood by parted utility.

    Currently only adding offsets in mib is supported.
    """
    if not offset1.endswith('mib') or not offset2.endswith('mib'):
        raise NotImplementedError('Adding anything but offsets in mib')

    result = int(offset1.rstrip('mib')) + int(offset2.rstrip('mib'))
    return '{}mib'.format(result)
