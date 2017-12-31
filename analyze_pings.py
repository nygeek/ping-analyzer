""" analyze_pings.py

Take the log of ping data output from running ping for a long
time and summarize and analyze the various errors.

"""

from LineQueue import LineQueue

import argparse
import json
import numpy as np
import psutil
import re
import SequenceStats as ss
import TimeStamp as ts

#
# Roadmap
# 
# 2017-11-12 [x] Expand handling to recognize the Linux ping
#                syntax.
#                [Solved] Invoke ping with the -n flag.
# 2017-11-29 [x] Add signatures to the output for provenance tracking.
# 2017-11-29 [x] Add command line flag handling to __main__() ...
# 2017-12-25 [x] Complete handling of timestamp information.
# 2017-12-26 [x] The five line expectation in 'handle_gateway_failure'
#                is incorrect ... the 'Request timeout ...' is actually
#                the next record.  These four records are actually part
#                of the previous record, which is also a Request timeout.
# 2017-12-26 [x] Keep track of max and min for RTT
#                [Done] 2017-12-27
# 2017-12-26 [ ] Adjust the "RTTTooLong" threshold to be some sort of
#                multiple of the mean RTT (3x? 4x?).
# 2017-12-27 [x] Separate the SequenceStats class into its own module.
#                [Done] 2017-12-29
#

timestamp_pattern = ""

def recognize_timestamp(line):
    """Handle a timestamp comment line."""
    # This is a pukey way to handle this imported constant ...
    # I bet there's a better way.  Figure it out.
    global timestamp_pattern
    if re.match(timestamp_pattern, line):
        return True
    else:
        return False

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
    pushback = None
    if recognize_timestamp(secondline):
        pushback = secondline
        secondline = line_queue.get_line()
    if secondline.strip() != pattern:
        print "handle_gateway_failure(): linenumber: " + str(linenumber)
    thirdline = line_queue.get_line()
    if recognize_timestamp(thirdline):
        pushback = thirdline
        thirdline = line_queue.get_line()
    fourthline = line_queue.get_line()
    if recognize_timestamp(fourthline):
        pushback = fourthline
        fourthline = line_queue.get_line()
    # sweet - LineQueue to the rescue
    if pushback:
        line_queue.push_back(pushback)

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
    # 64 bytes from 166.84.1.3: icmp_seq=64539 ttl=246 time=23.707 ms
    pattern = '64 bytes from (\d+\.\d+\.\d+\.\d+): '
    pattern += 'icmp_seq=(\d+) ttl=(\d+) time=(\d+\.?\d*) ms'
    (re_ip, re_seq, re_ttl, re_rtt) = \
        [re.match(pattern, line).group(k) for k in [1,2,3,4]]
    return (re_ip, re_seq, re_rtt)

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
        handle_gateway_failure(line_queue, line, linenumber)
        return ("GWFailure", -1)
    else:
        # Is there anything other than '64 bytes...'?
        print "linenumber: ", str(linenumber)
        print "Unexpected: '", line, "'"
        return ("Unexpected", -1)

def main():
    """Main body."""
    global timestamp_pattern

    # capture timing information
    cputime_0 = psutil.cpu_times()

    # Self-identification for the run
    # This gives us YYYY-MM-DDTHH:MM:SS+HH:MM
    ts0 = ts.TimeStamp()
    timestamp_pattern = ts0.get_recognizer_re()

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
    current = {}
    previous = {}
    
    previous['rtt'] = None
    current['rtt'] = None

    previous['mean'] = 0.0
    current['mean'] = 0.0

    previous['variance'] = 0.0
    current['variance'] = 0.0

    normal_ping_count = 0

    sequence_number = -1
    sequence_offset = 0

    # duration and state variables
    network_state = "None"
    up_start = -1
    up_end = -1
    down_start = -1
    down_end = -1

    previous['time'] = "unknown"
    current['time'] = "unknown"

    previous['timestamp'] = None
    current['timestamp'] = None

    previous['sequence'] = sequence_number
    current['sequence'] = sequence_number

    current['linenumber'] = linecount

    # reference_linenumber = linecount
    
    rtt_stats = None
    zrtt = None

    explanation = ""
    while line:
        linecount += 1
        # print "linecount: '" + str(linecount)
        # print "line: '" + line.strip() + "'"
        # TODO threshold should be dynamically calculated
        (kind, seq_num) = classify(line_queue, line.strip(), linecount, 250)
        # print "   kind: " + kind
        if kind:
            counters[kind] += 1
            if kind == "Timestamp":
                # oops - seq_num is not a number, it's a string!
                previous['time'] = current['time']
                previous['timestamp'] = current['timestamp']
                previous['sequence'] = current['sequence']
                # 
                current['time'] = seq_num
                current['timestamp'] = ts.TimeStamp(current['time'])
                current['sequence'] = sequence_number
                current['linenumber'] = linecount
                #
                # if previous_time != "unknown":
                if previous['time'] != "unknown":
                    delta_t = current['timestamp'].minus_small(\
                            previous['timestamp'])
                    delta_r = current['sequence'] - previous['sequence']
                    print "# time check: delta_r: " + str(delta_r) +\
                           " delta_t: " + str(delta_t)
            elif kind == "Initialization":
                pass
            elif kind == "Normal":
                (ip, num, rtt) = \
                        parse_normal_return(line.strip(), linecount)

                # result is a tuple of strings:
                #     (ip_address, sequence_number, rtt)
                # ping sends pings once per second, so sequence_number
                # is roughly a count of seconds.

                if not zrtt:
                    rtt_stats = ss.SequenceStats(float(rtt), False)
                    current['mean'] = float(rtt)
                zrtt = float(rtt)

                inum = int(num)
                if inum == 0 and network_state != "None":
                    # The sequence number only goes to 65535, so we
                    # will keep track of the rolls
                    sequence_offset += 65536
                sequence_number = inum + sequence_offset

                # Handle network state stuff
                if network_state == "None":
                    up_start = sequence_number
                    up_end = sequence_number
                    # print "Network state initialization: Up"
                    # print "   sequence_number: " + str(sequence_number)
                elif network_state == "Down":
                    down_end = sequence_number - 1
                    up_start = sequence_number
                    up_end = sequence_number
                    #
                    print "Down: " + str(down_start) +\
                            " - " + str(down_end) + \
                            "[ " + str(down_end - down_start - 1) + " ]"
                    if explanation == "RTTTooLong":
                        explanation += " RTT: " + str(zrtt)
                    print "   explanation: " + explanation
                    if current['time'] != "unknown":
                        print "   current['time']: " +\
                            str(current['time'])
                        print "   plus (~seconds): " +\
                            str(sequence_number - current['sequence'])
                    # print "linecount: " + str(linecount)
                else:
                    up_end = sequence_number
                network_state = "Up"

# We use the online algorithm documented in Wikipedia article:
# https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance

                # Use the new stats class to accumulate the data
                rtt_stats.accumulate(zrtt)

                normal_ping_count += 1
                if previous['rtt'] > 0.0:
                    temp = current['mean']
                    current['mean'] += \
                        (zrtt - previous['mean']) /\
                        float(normal_ping_count)
                    previous['mean'] = temp
                previous['rtt'] = zrtt
                # previous_rtt = zrtt
                # This works because the first time through 
                # previous_variance is zero
                # this is the population variance
                temp = current['variance']
                current['variance'] = \
                    ( (normal_ping_count - 1) * previous['variance'] + \
                      (zrtt - previous['mean']) * \
                      (zrtt - current['mean'])
                    ) / normal_ping_count
                previous['variance'] = temp

            elif kind in down_classifications:
                # Handle network state stuff
                explanation = kind
                if network_state == "None":
                    down_start = sequence_number
                    down_end = sequence_number
                    # print "Network state initialization: Down"
                    # print "   sequence_number: " + str(sequence_number)
                elif network_state == "Up":
                    up_end = sequence_number - 1
                    down_start = sequence_number
                    down_end = sequence_number
                    #
                    print "Up:   " + str(up_start) +\
                            " - " + str(up_end) + \
                            " [ " + str(up_end - up_start - 1) + " ]"
                    if current['time'] != "unknown":
                        print "   current['time']: " +\
                            str(current['time'])
                        print "   plus (~seconds): " +\
                            str(sequence_number - current['sequence'])
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
    print "Mean: " + str(current['mean'])
    print "Mean RTT (two ways): " + str(rtt_stats.get_mean())
    print "Variance: " + str(current['variance'])
    print "Variance RTT (two ways): " + str(rtt_stats.get_variance())
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
