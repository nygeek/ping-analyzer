""" TimeStamp Operations

Written by Marc Donner
Started 2017-12-25

The insert_timestamps.py intercalates standard timestamps into the
logs.  In order to work with these timestamps reasonably, we need
some operators.  This file contains a class TimeStamp that does
that.

"""

# Roadmap
# 
# 2017-12-25 [ ] Do the right thing with differences of more than a day
#                This involves using my JDN (Julian Day Number) stuff
#                to get accurate differences between Gregorian dates.
#

import re
import datetime as datetime

class TimeStamp(object):
    """TimeStamp - timestamp object - various operations."""

    def __init__(self, ts='now'):
        # YYYY-MM-DD
        self.pattern = '([0-9]{4})-([0-9]{2})-([0-9]{2})'
        # hh:mm:ss
        self.pattern += 'T([0-9]{2}):([0-9]{2}):([0-9]{2})'
        # fraction of a second
        self.pattern += '\.([0-9]{6})'
        # initialize with the timestamp passed, or now
        if ts=='now': 
            self.timestamp = datetime.datetime.isoformat(\
                                datetime.datetime.today())
        else:
            self.timestamp = ts
        self.parsed = False

    def parse_ts(self):
        """Pick the timestamp apart into components."""
        (self.year, self.month, self.day,\
            self.hour, self.minute, self.second, self.microseconds) = \
            [int(re.match(self.pattern, self.timestamp).group(k))\
                for k in range(1,8)]
        self.parsed = True

    def get_parts(self):
        """Return all seven parts in a vector."""
        if not self.parsed:
            self.parse_ts()
        return (self.year, self.month, self.day,\
                self.hour, self.minute, self.second,\
                self.microseconds)

    def get_timestamp(self):
        """Get the raw timestamp back."""
        return self.timestamp

    def get_year(self):
        """Return the year component."""
        if not self.parsed:
            self.parse_ts()
        return self.year

    def get_month(self):
        """Return the month component."""
        if not self.parsed:
            self.parse_ts()
        return self.month

    def get_day(self):
        """Return the day component."""
        if not self.parsed:
            self.parse_ts()
        return self.day

    def get_hour(self):
        """Return the hour component."""
        if not self.parsed:
            self.parse_ts()
        return self.hour

    def get_minute(self):
        """Return the minute component."""
        if not self.parsed:
            self.parse_ts()
        return self.minute

    def get_second(self):
        """Return the second component."""
        if not self.parsed:
            self.parse_ts()
        return self.second

    def get_microseconds(self):
        """Return the microseconds component."""
        if not self.parsed:
            self.parse_ts()
        return self.microseconds

    def minus_small(self, ts):
        """Subtract one timestamp from another."""
        minuend = self.get_parts()
        subtrahend = ts.get_parts()
        difference = [minuend[i] - subtrahend[i] for i in range(7)]
        fail = difference[0] + difference[1] + difference[2]
        if not fail:
            diff = difference[3]
            # diff is in hours now
            diff = 60 * diff + difference[4]
            # diff is in minutes now
            diff = 60 * diff + difference[5]
            # diff is in seconds now
            diff += difference[6] / 1000000.0
        else:
            print "Tell Donner to implement long differences."
        return diff

    def __str__(self):
        if not self.parsed:
            self.parse_ts()
        return str([self.timestamp,\
                self.year, self.month, self.day,\
                self.hour, self.minute, self.second,\
                self.microseconds])

def main():
    """Main routine - just for testing."""

print "TimeStamp Class test...\n"

ts0 = TimeStamp('2017-12-25T12:46:18.734556')
print "ts0: " + str(ts0)

print "ts0.get_parts(): " + str(ts0.get_parts())

# Another timestamp - just now
ts1 = TimeStamp()
print "ts1: " + str(ts1)

# Difference in seconds between the two timestamps ...
# Only works if they are in the same day
print "difference ts1 - ts0: " + str(ts1.minus_small(ts0))
