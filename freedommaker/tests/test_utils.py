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
Tests for miscellaneous utility methods.
"""

import unittest

from freedommaker import utils


class TestUtils(unittest.TestCase):
    """Test for miscellaneous utility methods."""

    def test_add_disk_offsets(self):
        """Test disk offset addition."""
        self.assertEqual(utils.add_disk_offsets('1mib', '2mib'), '3mib')
        self.assertRaises(NotImplementedError, utils.add_disk_offsets, '1gib',
                          '1mib')
        self.assertRaises(NotImplementedError, utils.add_disk_offsets, '1mib',
                          '1gib')
        self.assertRaises(ValueError, utils.add_disk_offsets, 'xmib', '1mib')
        self.assertRaises(ValueError, utils.add_disk_offsets, 'xmib', 'xmib')
