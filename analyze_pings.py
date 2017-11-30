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

#
# Roadmap
# 
# 2017-11-12 [ ] Expand handling to recognize the Linux ping
#                syntax.
# 2017-11-29 [ ] Add signatures to the output for provenance tracking.
# 2017-11-29 [ ] Add command line flag handling to __main__() ...
#

def handle_gateway_failure(line_queue, firstline, linenumber):
    """ when a line starts with '92 bytes from ' we have
    to expect four more lines:
       'Vr HL TOS  Len   ID Flg  off TTL Pro  cks      Src      Dst'
       (a bunch of numbers and data)
       (a blank line)
       'Request timeout for icmp_seq '
    """
    pattern = "Vr HL TOS  Len   ID Flg  off TTL Pro  cks      Src      Dst"
    # need to flush three lines here ...
    secondline = line_queue.get_line()
    if secondline.strip() != pattern:
        print "handle_gateway_failure(): linenumber: " + str(linenumber)
    thirdline = line_queue.get_line()
    fourthline = line_queue.get_line()
    fifthline = line_queue.get_line()
    (junk, sequence_number) = fifthline.split("icmp_seq ")
    return int(sequence_number)

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

def classify(line_queue, line, linenumber):
    """ Given a line from the pinger output, classify it. """

    # print "classify(): " + line
    if line == "ping: sendto: Network is down":
        """Get sequence number from subsequent line."""
        seq_num = handle_expected_timeout(line_queue, line, linenumber)
        return ("Down", seq_num)
    elif line.startswith("#"):
        """No sequence number."""
        return ("Comment", 0)
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
        return ("Normal", int(seq_num))
    elif line.startswith("92 bytes from "):
        # this precedes three more lines for the report
        # first push this back on the queue
        seq_num = handle_gateway_failure(line_queue, line, linenumber)
        return ("GWFailure", int(seq_num))
    else:
        # Is there anything other than '64 bytes...'?
        print "linenumber: ", str(linenumber)
        print "Unexpected: '", line, "'"
        return ("Unexpected", -1)

def main():
    """Main body."""

    # capture timing information
    cputime_0 = psutil.cpu_times()

    # Self-identification for the run
    # This gives us YYYY-MM-DDTHH:MM:SS+HH:MM
    timestamp = datetime.datetime.isoformat(\
            datetime.datetime.today())
    print "# analyze_pings.py - version 1.0"
    print "# analyze_pings.py: timestamp: " + timestamp

    parser = argparse.ArgumentParser(description='Analyze a ping log')
    parser.add_argument('-f', nargs='?',\
            default='stdin', help="input file name")
    parser.add_argument('-D', type=int, nargs='?',\
            default=0, help="Debug flag (int: default to 0)")
    args = parser.parse_args()
    input_file_name = args.f

    print "# analyze_pings.py: input_file_name: " + input_file_name

    line_queue = LineQueue(4, input_file_name)
    # LineQueue returns a comment-structured self identification
    print line_queue.signature()

    # Initialize the counters
    classifications = ["Down",
                       "Comment",
                       "GWFailure",
                       "Route",
                       "Timeout",
                       "Normal",
                       "NegativeRTT",
                       "Unexpected"]
    down_classifications = [
                       "Down",
                       "GWFailure",
                       "Route",
                       "Timeout",
                       "NegativeRTT"
                       ]
    counters = {"Down": 0,
                "Comment": 0,
                "GWFailure": 0,
                "Route": 0,
                "Timeout": 0,
                "Normal": 0,
                "NegativeRTT": 0,
                "Unexpected": 0}

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

    while line:
        linecount += 1
        # print "linecount: '" + str(linecount)
        # print "line: '" + line.strip() + "'"
        (kind, seq_num) = classify(line_queue, line.strip(), linecount)
        # print "   kind: " + kind
        if kind:
            counters[kind] += 1
            if kind == "Normal":
                (ip, num, rtt) = \
                        parse_normal_return(line.strip(), linecount)
                # result is a tuple: (ip_address, sequence_number, rtt)
                # ping sends pings once per second, so sequence_number
                # is rough count of seconds.
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
                    # print "linecount: " + str(linecount)
                else:
                    up_end = sequence_number
                network_state = "Up"

# We use the online algorithm documented in Wikipedia article:
# https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance
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
    print "Down: ", counters["Down"]
    print "GWfailure: ", counters["GWFailure"]
    print "Normal: ", counters["Normal"]
    print "NegativeRTT: ", counters["NegativeRTT"]
    print "Comment: ", counters["Comment"]
    print "Route: ", counters["Route"]
    print "Timeout: ", counters["Timeout"]
    print "Unexpected: ", counters["Unexpected"]

    print "sequence_number: " + str(sequence_number)
    print "sequence_offset: " + str(sequence_offset)
    print "normal_ping_count: " + str(normal_ping_count)
    print "Average rtt: " + str(mean_rtt)
    print "Variance: " + str(sigma_squared)
    print "Standard Deviation: " + str(sqrt(sigma_squared))

    checksum = linecount
    checksum -= counters["Down"]
    checksum -= counters["GWFailure"]
    checksum -= counters["Normal"]
    checksum -= counters["NegativeRTT"]
    checksum -= counters["Comment"]
    checksum -= counters["Route"]
    checksum -= counters["Timeout"]
    checksum -= counters["Unexpected"]

    print "checksum: " + str(checksum)

    cputime_1 = psutil.cpu_times()
    print
    # index 0 is user
    # index 1 is nice
    # index 2 is system
    # index 3 is idle
    print "User time: " + str(cputime_1[0] - cputime_0[0])
    print "System time: " + str(cputime_1[2] - cputime_0[2])

if __name__ == '__main__':
    main()
