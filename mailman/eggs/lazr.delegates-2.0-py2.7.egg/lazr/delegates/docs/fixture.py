# Copyright 2009-2013 Canonical Ltd.  All rights reserved.
#
# This file is part of lazr.delegates
#
# lazr.delegates is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# lazr.delegates is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with lazr.delegates.  If not, see <http://www.gnu.org/licenses/>.

"""Doctest fixtures for running under nose."""

from __future__ import absolute_import, print_function, unicode_literals

__metaclass__ = type
__all__ = [
    'globs',
    ]


def globs(globs):
    """Set up globals for doctests."""
    # Enable future statements to make Python 2 act more like Python 3.
    globs['absolute_import'] = absolute_import
    globs['print_function'] = print_function
    globs['unicode_literals'] = unicode_literals
    # Provide a convenient way to clean things up at the end of the test.
    return globs
