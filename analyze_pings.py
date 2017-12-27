""" analyze_pings.py

Take the log of ping data output from running ping for a long
time and summarize and analyze the various errors.

"""

from LineQueue import LineQueue
import argparse
import datetime as datetime
import json
from math import sqrt
import psutil
import re
import TimeStamp as ts

#
# Roadmap
# 
# 2017-11-12 [x] Expand handling to recognize the Linux ping
#                syntax.
#                [Solved] Invoke ping with the -n flag.
# 2017-11-29 [x] Add signatures to the output for provenance tracking.
# 2017-11-29 [x] Add command line flag handling to __main__() ...
# 2017-12-25 [ ] Complete handling of timestamp information.
# 2017-12-26 [x] The five line expectation in 'handle_gateway_failure'
#                is incorrect ... the 'Request timeout ...' is actually
#                the next record.  These four records are actually part
#                of the previous record, which is also a Request timeout.
# 2017-12-26 [ ] Keep track of max and min for RTT
# 2017-12-26 [ ] Adjust the "RTTTooLong" threshold to be some sort of
#                multiple of the mean RTT (3x? 4x?).
#

def handle_gateway_failure(line_queue, firstline, linenumber):
    """ when a line starts with '92 bytes from ' we have
    to expect three more lines:
       'Vr HL TOS  Len   ID Flg  off TTL Pro  cks      Src      Dst'
       (a bunch of numbers and data)
       (a blank line)
    """
    pattern = "Vr HL TOS  Len   ID Flg  off TTL Pro  cks      Src      Dst"
    # need to flush three lines here ...
    secondline = line_queue.get_line()
    if secondline.strip() != pattern:
        print "handle_gateway_failure(): linenumber: " + str(linenumber)
    thirdline = line_queue.get_line()
    fourthline = line_queue.get_line()

def handle_expected_timeout(line_queue, firstline, linenumber):
    """When we encounter a various messages we can
        expect a 'Request timeout' message to follow immediately."""
    pattern = "Request timeout for icmp_seq "
    # need to flush one more line here ...
    secondline = line_queue.get_line()
    if not secondline.startswith(pattern):
        print "handle_down_network(): linenumber: " + str(linenumber)
    (junk, sequence_number) = secondline.split("icmp_seq ")
    return int(sequence_number)

def parse_normal_return(line, linenumber):
    """ Given a normal string, return a tuple containing IP address,
        Sequence number, and RTT.
    """
    # print "parse_normal_return(): " + line.strip()
    (front, back) = line.split(":")
    # This gets tricky.  The IP address might be there
    # or it might be in parens at the end of the line
    # e.g. 64 bytes from panix2.panix.com (166.84.1.2):
    # e.g. 64 bytes from 166.84.1.2: ...
    (junk, junk, junk, ip_address) = front.split(" ")
    (junk, seq, ttl, time, ms) = back.split(" ")
    (junk, t) = time.split("=")
    (icmp_seq, numb) = seq.split("=")
    return (ip_address, numb, t)

def classify(line_queue, line, linenumber, threshold):
    """ Given a line from the pinger output, classify it. """

    # print "classify(): " + line
    if line == "ping: sendto: Network is down":
        """Get sequence number from subsequent line."""
        seq_num = handle_expected_timeout(line_queue, line, linenumber)
        return ("Down", seq_num)
    elif line.startswith("#"):
        """No sequence number."""
        # need to parse timestamp comments
        if line.startswith("# timestamp: "):
            # this is a timestamp
            (junk, junk, junk, timestamp) = line.split(" ")
            return ("Timestamp", timestamp)
        return ("Comment", 0)
    elif line.startswith("PING "):
        """Here is our log of the initial ping commmand"""
        return ("Initialization", 0)
    elif line == "ping: sendto: No route to host":
        """Get sequence number from subsequent timeout line."""
        seq_num = handle_expected_timeout(line_queue, line, linenumber)
        return ("Route", int(seq_num))
    elif line.startswith("Request timeout for icmp_seq "):
        (junk, sequence_number) = line.split("icmp_seq ")
        return ("Timeout", int(sequence_number))
    elif line.startswith("64 bytes from "):
        # might be negative RTT, so parse the line first
        (junk, seq_num, rtt) = parse_normal_return(line.strip(), linenumber)
        if float(rtt) < 0:
            return ("NegativeRTT", int(seq_num))
        if float(rtt) > threshold:
            return ("RTTTooLong", int(seq_num))
        return ("Normal", int(seq_num))
    elif line.startswith("92 bytes from "):
        # this precedes three more lines for the report
        # first push this back on the queue
        handle_gateway_failure(line_queue, line, linenumber)
        return ("GWFailure", -1)
    else:
        # Is there anything other than '64 bytes...'?
        print "linenumber: ", str(linenumber)
        print "Unexpected: '", line, "'"
        return ("Unexpected", -1)

class SequenceStats(object):
    """Accumulate statistics on a sequence of reals."""
    def __init__(self, value, incremental=True):
        # We will only use the incremental stats for now
        # The flag is a place holder for when we add global
        self.incremental = incremental
        # Initialize stats structure
        self.minimum = value
        self.maximum = value
        self.n = 1
        # Initialize previous structure
        self.previous = {}
        self.previous['value'] = None
        self.previous['variance'] = -1
        self.previous['mean'] = None
        # Set up current value
        self.current = {}
        self.current['value'] = value
        self.current['variance'] = -1
        self.current['mean'] = value

    def accumulate(self, value):
        """Accept a data value and add them to the stats."""
        self.n += 1
        self.previous['value'] = self.current['value']
        self.current['value'] = value
        self.maximum = max(self.maximum, value)
        self.minimum = min(self.minimum, value)
        # Incremental mean
        t = self.current['mean']
        if self.previous['mean']:
            self.current['mean'] = self.current['mean'] +\
                (self.current['value'] - self.previous['mean']) / self.n
        self.previous['mean'] = t
        # Now start on the incremental variance
        val_0 = self.current['value']
        # val_1 = self.previous['value']
        var_0 = self.current['variance']
        var_1 = self.previous['variance']
        mean_0 = self.current['mean']
        mean_1 = self.previous['mean']
# We use the online algorithm documented in Wikipedia article:
# https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance
        variance_new =\
            ( (self.n - 1) * var_1 +\
              (val_0 - mean_1) * (val_0 - mean_0)\
            ) / self.n
        self.previous['variance'] = var_0
        self.current['variance'] = variance_new

    def get_mean(self):
        """Fetch the mean."""
        return self.current['mean']

    def get_variance(self):
        """Fetch the variance."""
        return self.current['variance']

    def get_minimum(self):
        """Fetch the minimum."""
        return self.minimum

    def get_maximum(self):
        """Fetch the maximum."""
        return self.maximum

    def __str__(self):
        stats = {
                "n": self.n,
                "minimum": self.minimum,
                "maximum": self.maximum
                }
        return json.dumps(\
                [stats, self.current],\
                indent=2, separators=(',', ': '))

def main():
    """Main body."""

    # capture timing information
    cputime_0 = psutil.cpu_times()

    # Self-identification for the run
    # This gives us YYYY-MM-DDTHH:MM:SS+HH:MM
    ts0 = ts.TimeStamp()

    print "# analyze_pings.py"
    print "# analyze_pings.py: start: timestamp: " + ts0.get_timestamp()

    parser = argparse.ArgumentParser(description='Analyze a ping log')
    parser.add_argument('-f', nargs='?',\
            default='stdin', help="input file name")
    parser.add_argument('-v', nargs='?', default='command line',\
            help="git information about build state")
    parser.add_argument('-D', type=int, nargs='?',\
            default=0, help="Debug flag (int: default to 0)")
    args = parser.parse_args()
    input_file_name = args.f
    build_version = args.v

    print "# analyze_pings.py: build version:" + build_version
    print "# analyze_pings.py: input_file_name: " + input_file_name

    line_queue = LineQueue(4, input_file_name)
    # LineQueue returns a comment-structured self identification
    print line_queue.signature()

    # Initialize the counters
    classifications = [
                       "Comment",
                       "Down",
                       "GWFailure",
                       "Initialization",
                       "NegativeRTT",
                       "Normal",
                       "Route",
                       "RTTTooLong",
                       "Timeout",
                       "Timestamp",
                       "Unexpected"]

    down_classifications = [
                       "Down",
                       "GWFailure",
                       "NegativeRTT",
                       "Route",
                       "RTTTooLong",
                       "Timeout"
                       ]
    counters = {}
    for key in classifications:
        counters[key] = 0

    linecount = 0
    
    line = line_queue.get_line()
    recent_num = 0

    # variables used for online mean and standard deviation
    previous_rtt = -1
    mean_rtt = -1
    previous_mean_rtt = 0
    sigma_squared = -1
    previous_sigma_squared = 0
    normal_ping_count = 0

    sequence_number = -1
    sequence_offset = 0

    # duration and state variables
    network_state = "None"
    up_start = -1
    up_end = -1
    down_start = -1
    down_end = -1

    previous_time = "unknown"
    reference_time = "unknown"
    previous_timestamp = None
    reference_timestamp = None
    previous_sequence = sequence_number
    reference_sequence = sequence_number

    reference_linenumber = linecount
    rtt_stats = None
    zrtt = None

    explanation = ""
    while line:
        linecount += 1
        # print "linecount: '" + str(linecount)
        # print "line: '" + line.strip() + "'"
        # TODO threshold should be dynamically calculated
        (kind, seq_num) = classify(line_queue, line.strip(), linecount, 100)
        # print "   kind: " + kind
        if kind:
            counters[kind] += 1
            if kind == "Timestamp":
                # oops - seq_num is not a number, it's a string!
                previous_time = reference_time
                previous_timestamp = reference_timestamp
                previous_sequence = reference_sequence
                #
                reference_time = seq_num
                reference_timestamp = ts.TimeStamp(reference_time)
                reference_sequence = sequence_number
                reference_linenumber = linecount
                #
                if previous_time != "unknown":
                    delta_t = reference_timestamp.minus_small(\
                            previous_timestamp)
                    delta_r = reference_sequence - previous_sequence
                    print "# time check: delta_r: " + str(delta_r) +\
                           " delta_t: " + str(delta_t)
            elif kind == "Initialization":
                pass
            elif kind == "Normal":
                (ip, num, rtt) = \
                        parse_normal_return(line.strip(), linecount)
                # result is a tuple: (ip_address, sequence_number, rtt)
                # ping sends pings once per second, so sequence_number
                # is rough count of seconds.
                if not zrtt:
                    rtt_stats = SequenceStats(float(rtt))
                zrtt = float(rtt)
                inum = int(num)
                sequence_number = seq_num + sequence_offset

                if inum == 0 and network_state != "None":
                    # The sequence number only goes to 65535, so we
                    # will keep track of the rolls
                    sequence_offset += 65536

                # Handle network state stuff
                if network_state == "None":
                    up_start = sequence_number
                    up_end = sequence_number
                    # print "Network state initialization: Up"
                    # print "   sequence_number: " + str(sequence_number)
                elif network_state == "Down":
                    down_end = sequence_number
                    up_start = sequence_number
                    up_end = sequence_number
                    #
                    print "Down: " + str(down_start) +\
                            " - " + str(down_end) + \
                            "[ " + str(down_end - down_start - 1) + " ]"
                    print "   explanation: " + explanation
                    if reference_time != "unknown":
                        print "   reference_time: " +\
                            str(reference_time)
                        print "   plus (~seconds): " +\
                            str(sequence_number - reference_sequence)
                    # print "linecount: " + str(linecount)
                else:
                    up_end = sequence_number
                network_state = "Up"

# We use the online algorithm documented in Wikipedia article:
# https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance

                # Use the new stats class to accumulate the data
                rtt_stats.accumulate(zrtt)

                normal_ping_count += 1
                if previous_rtt > 0.0:
                    mean_rtt += \
                        (zrtt - previous_mean_rtt) /\
                        float(normal_ping_count)
                    previous_mean_rtt = mean_rtt
                previous_rtt = zrtt
                # This works because the first time through 
                # previous_sigma_squared is zero
                sigma_squared = \
                    ( (normal_ping_count - 1) * previous_sigma_squared + \
                      (zrtt - previous_mean_rtt) * \
                      (zrtt - mean_rtt)
                    ) / normal_ping_count
                previous_sigma_squared = sigma_squared

            elif kind in down_classifications:
                # Handle network state stuff
                explanation = kind
                if network_state == "None":
                    down_start = sequence_number
                    down_end = sequence_number
                    # print "Network state initialization: Down"
                    # print "   sequence_number: " + str(sequence_number)
                elif network_state == "Up":
                    up_end = sequence_number
                    down_start = sequence_number
                    down_end = sequence_number
                    #
                    print "Up:   " + str(up_start) +\
                            " - " + str(up_end) + \
                            " [ " + str(up_end - up_start - 1) + " ]"
                    if reference_time != "unknown":
                        print "   reference_time: " +\
                            str(reference_time)
                        print "   plus (~seconds): " +\
                            str(sequence_number - reference_sequence)
                else:
                    down_end = sequence_number
                network_state = "Down"
                # print "kind: " + kind
            elif kind == "Comment":
                pass
            else:
                # Failed to classify:
                print "Failed to classify:"
                print "   kind: " + kind
                print "   linecount: " + str(linecount)
                print "   line: '" + line.strip() + "'"
                counters["Unexpected"] += 1
        line = line_queue.get_line()

    print "linecount", linecount
    for key in classifications:
        print key + ": " + str(counters[key])

    print "sequence_number: " + str(sequence_number)
    print "sequence_offset: " + str(sequence_offset)
    print "normal_ping_count: " + str(normal_ping_count)
    print "Average RTT: " + str(mean_rtt)
    print "Variance: " + str(sigma_squared)
    print "Standard Deviation: " + str(sqrt(sigma_squared))
    print "rtt_stats: " + str(rtt_stats)

    checksum = linecount
    for key in classifications:
        checksum -= counters[key]
    print "checksum: " + str(checksum)

    cputime_1 = psutil.cpu_times()
    print
    # index 0 is user
    # index 1 is nice
    # index 2 is system
    # index 3 is idle

    ts1 = ts.TimeStamp()
    print "# analyze_pings.py: end: timestamp: " + ts1.get_timestamp()
    print "# analyze_pings.py: User time: " +\
            str(cputime_1[0] - cputime_0[0]) + " S"
    print "# analyze_pings.py: User time per record: " +\
            str(1e6 * (cputime_1[0] - cputime_0[0]) / linecount) +\
            " uS"
    print "# analyze_pings.py: System time: " +\
            str(cputime_1[2] - cputime_0[2]) + " S"
    print "# analyze_pings.py: System time per record: " +\
            str(1e6 * (cputime_1[2] - cputime_0[2]) / linecount) +\
            " uS"

if __name__ == '__main__':
    main()
