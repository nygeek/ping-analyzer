""" SequenceStats

Class to accumulate a time series of real values and produce
relevant statistics.

"""

import TimeStamp as ts

import json
import numpy as np
import psutil
import re

#
# Roadmap
# 
# 2017-12-27 [x] Separate the SequenceStats class into its own module.
#

class SequenceStats(object):
    """Accumulate statistics on a sequence of reals."""
    def __init__(self, value, incremental=True):
        self.incremental = incremental
        # print "self.incremental: " + str(self.incremental)
        # Initialize stats structure
        # One annoying property of this construction of __init__ is that
        # we have to delay instantiating the ss object until we have
        # first value available ... we can not set everything up from
        # 'outside,' so to speak.
        self.n = 1
        self.mean = float(value)
        # We start M2 at zero because, as the total squared distance from
        # the mean, the first value is the mean and the distance is zero
        self.M2 = 0
        self.minimum = float(value)
        self.maximum = float(value)
        # non-Incremental
        if not self.incremental:
            self.history = []
            self.history.append(float(value))
            self.narray = None
            self.nstats = {}

    def accumulate(self, value):
        """Accept a data value and add them to the stats."""
        self.n += 1

        self.maximum = max(self.maximum, float(value))
        self.minimum = min(self.minimum, float(value))

# We use the online algorithm documented in Wikipedia article:
# https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance
# We start with Python code for a numerically stable algorithm that
# is reproduced in the Wikipedia article:

        # print "n: " + str(self.n)
        # print "value: " + str(value)
        delta = float(value) - self.mean
        # print "delta: " + str(delta)
        self.mean += delta / float(self.n)
        # print "mean: " + str(self.mean)
        delta2 = float(value) - self.mean
        # print "delta2: " + str(delta2)
        self.M2 += delta * delta2
        # print "self.M2: " + str(self.M2)
        # print

        # non-Incremental here ...
        if not self.incremental:
            self.history.append(value)

    def build_narray(self):
        """Construct the numpy array for non-incremental stats."""
        self.narray = np.array(self.history)
        # While we're at it, calculate the stats.
        self.nstats['mean'] = np.mean(self.narray)
        self.nstats['variance'] = np.var(self.narray)
        self.nstats['n'] = len(self.history)

    def get_mean(self):
        """Fetch the mean."""
        if not self.incremental:
            self.build_narray()
            return [self.mean, self.nstats['mean']]
        else:
            return self.mean

    def get_variance(self):
        """Fetch the variance."""
        if not self.incremental:
            self.build_narray()
            return [self.M2 / (self.n - 1), self.nstats['variance']]
        else:
            if self.n < 2:
                return float(nan)
            else:
                return self.M2 / (self.n - 1)

    def get_minimum(self):
        """Fetch the minimum."""
        return self.minimum

    def get_maximum(self):
        """Fetch the maximum."""
        return self.maximum

    def __str__(self):
        if self.incremental:
            stats = {
                    "incremental": str(self.incremental),
                    "n": self.n,
                    "len(history)": len(self.history),
                    "minimum": self.minimum,
                    "maximum": self.maximum
                    }
            return json.dumps(\
                    [stats, self.current],\
                    indent=2, separators=(',', ': '))
        else:
            stats = {
                    "incremental": str(self.incremental),
                    "n": self.n,
                    "minimum": self.minimum,
                    "maximum": self.maximum,
                    "mean": self.get_mean(),
                    "variance": self.get_variance()
                    }
            return json.dumps(\
                    [stats, self.nstats],\
                    indent=2, separators=(',', ': '))

def main():
    """Main body."""

    # capture timing information
    cputime_0 = psutil.cpu_times()

    # Self-identification for the run
    # This gives us YYYY-MM-DDTHH:MM:SS+HH:MM
    ts0 = ts.TimeStamp()
    timestamp_pattern = ts0.get_recognizer_re()

    print "# SequenceStats.py"
    print "# SequenceStats.py: start: timestamp: " + ts0.get_timestamp()

    # Some data pulled from Matt Teachout's page
    # (http://www.matt-teachout.org/data-sets-for-stats.html) page
    # ANOVA Data / Sheet 1 / Column O (Social Media Minutes - Instagram)
    #  Excel results:
    #  N: 124
    #  Mean: 83.20564516
    #  Variance(P): 6803.274242
    #  Variance(S): 6858.585415

    excel_mean = 83.20564516
    excel_variance_p = 6803.274242
    excel_variance_s = 6858.585415

    data1 = [\
        300, 60, 60, 30, 45, 60, 100, 120, 45, 30, 45, 120, 40,
        10, 180, 90, 240, 60, 3, 30, 190, 5, 60, 60, 120, 5, 60,
        45, 20, 120, 200, 180, 180, 35, 120, 120, 1.5, 120, 10, 120,
        60, 2, 120, 30, 60, 60, 120, 60, 30, 15, 90, 2, 60, 120, 60,
        30, 60, 25, 150, 90, 180, 20, 30, 3, 100, 60, 20, 60, 65, 120,
        180, 60, 120, 180, 30, 60, 30, 60, 190, 300, 25, 60, 60, 120,
        3, 200, 65, 2, 2, 2, 2, 2, 2, 2, 120, 4, 30, 1, 120, 120, 120,
        65, 60, 120, 1, 420, 90, 60, 60, 180, 300, 180, 500, 3, 3, 80,
        90, 80, 45, 5, 2, 120, 120, 120
        ]
    n1 = len(data1)

    np_data1 = np.array(data1)
    np_mean1 = np.mean(np_data1)
    np_variance1 = np.var(np_data1)

    print "n1: " + str(n1)

    print "excel_mean: " + str(excel_mean)
    print "excel_variance_p: " + str(excel_variance_p)
    print "excel_variance_s: " + str(excel_variance_s)

    print

    print "np_mean1: " + str(np_mean1)
    print "np_variance1: " + str(np_variance1)
    print "np_variance (to sample): " +\
            str(np_variance1 * float(n1) / float(n1 - 1))

    # Now we run the incremental code
    print
    ss1 = SequenceStats(data1[0])
    for j in range(1,124):
        # print "accumulate(data1[" + str(j) + "]: " + str(data1[j])
        ss1.accumulate(data1[j])
    print "incremental mean1: " + str(ss1.get_mean())
    print "incremental variance1: " + str(ss1.get_variance())

    data2 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    n2 = len(data2)
    print "n2: " + str(n2)
    np_data2 = np.array(data2)
    np_mean2 = np.mean(np_data2)
    np_variance2 = np.var(np_data2)
    print "np_mean2: " + str(np_mean2)
    print "np_variance2: " + str(np_variance2)

    print
    ss2 = SequenceStats(data2[0])
    for j in range(1,10):
        # print "accumulate(data2[" + str(j) + "]: " + str(data2[j])
        ss2.accumulate(data2[j])
    print "incremental mean2: " + str(ss2.get_mean())
    print "incremental variance2: " + str(ss2.get_variance())

    cputime_1 = psutil.cpu_times()
    print
    # index 0 is user
    # index 1 is nice
    # index 2 is system
    # index 3 is idle

    ts1 = ts.TimeStamp()
    print "# SequenceStats.py: end: timestamp: " + ts1.get_timestamp()
    print "# SequenceStats.py: User time: " +\
            str(cputime_1[0] - cputime_0[0]) + " S"
    print "# SequenceStats.py: System time: " +\
            str(cputime_1[2] - cputime_0[2]) + " S"

if __name__ == '__main__':
    main()
