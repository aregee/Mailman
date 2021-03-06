# Copyright (C) 1998-2012 by Barry A. Warsaw
#
# This file is part of flufl.bounce
#
# flufl.bounce is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, version 3 of the License.
#
# flufl.bounce is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with flufl.bounce.  If not, see <http://www.gnu.org/licenses/>.

"""Parse bounce messages generated by qmail.

Qmail actually has a standard, called QSBMF (qmail-send bounce message
format), as described in

    http://cr.yp.to/proto/qsbmf.txt

This module should be conformant.

"""

from __future__ import absolute_import, unicode_literals

__metaclass__ = type
__all__ = [
    'Qmail',
    ]


import re

from email.iterators import body_line_iterator
from flufl.enum import Enum
from zope.interface import implementer

from flufl.bounce.interfaces import IBounceDetector, NoTemporaryFailures


# Other (non-standard?) intros have been observed in the wild.
introtags = [
    "We're sorry. There's a problem",
    'Check your send e-mail address.',
    'Hi. The MTA program at',
    'Hi. This is the',
    'This is the mail delivery agent at',
    'Unfortunately, your mail was not delivered',
    'Your mail message to the following',
    ]
acre = re.compile(r'<(?P<addr>[^>]*)>:')


class ParseState(Enum):
    start = 0
    intro_paragraph_seen = 1
    recip_paragraph_seen = 2



@implementer(IBounceDetector)
class Qmail:
    """Parse QSBMF format bounces."""

    def process(self, msg):
        """See `IBounceDetector`."""
        addresses = set()
        state = ParseState.start
        for line in body_line_iterator(msg):
            line = line.strip()
            if state is ParseState.start:
                for introtag in introtags:
                    if line.startswith(introtag):
                        state = ParseState.intro_paragraph_seen
                        break
            elif state is ParseState.intro_paragraph_seen and not line:
                # Looking for the end of the intro paragraph.
                state = ParseState.recip_paragraph_seen
            elif state is ParseState.recip_paragraph_seen:
                if line.startswith('-'):
                    # We're looking at the break paragraph, so we're done.
                    break
                # At this point we know we must be looking at a recipient
                # paragraph.
                mo = acre.match(line)
                if mo:
                    addresses.add(mo.group('addr').encode('us-ascii'))
                # Otherwise, it must be a continuation line, so just ignore it.
            else:
                # We're not looking at anything in particular.
                pass
        return NoTemporaryFailures, addresses
