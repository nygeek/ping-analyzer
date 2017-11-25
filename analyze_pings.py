""" analyze_pings.py

Take the log of ping data output from running ping for a long
time and summarize and analyze the various errors.

"""

from LineQueue import LineQueue
from datetime import datetime
from math import sqrt
import json
import psutil
import re

#
# Roadmap
# 
# 2017-11-12 [ ] Expand handling to recognize the Linux ping
#                syntax.
#

def handle_gateway_failure(line_queue, firstline, linenumber):
    """ when a line starts with '92 bytes from ' we have
    to expect three more lines:
       'Vr HL TOS  Len   ID Flg  off TTL Pro  cks      Src      Dst'
       (a bunch of numbers and data)
       (a blank line) """
    pattern = "Vr HL TOS  Len   ID Flg  off TTL Pro  cks      Src      Dst"
    # need to flush three lines here ...
    secondline = line_queue.get_line()
    if secondline.strip() != pattern:
        print "handle_gateway_failure(): linenumber: " + str(linenumber)
    thirdline = line_queue.get_line()
    fourthline = line_queue.get_line()

def handle_down_network(line_queue, firstline, linenumber):
    """ When we encounter a 'Network is down' message we can
        expect a 'Request timeout' message to follow immediately."""
    pattern = "Request timeout for icmp_seq "
    # need to flush one more line here ...
    secondline = line_queue.get_line()
    if not secondline.startswith(pattern):
        print "handle_down_network(): linenumber: " + str(linenumber)

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
        handle_down_network(line_queue, line, linenumber)
        return "Down"
    elif line.startswith("#"):
        return "Comment"
    elif line == "ping: sendto: No route to host":
        return "Route"
    elif line.startswith("Request timeout for icmp_seq "):
        return "Timeout"
    elif line.startswith("64 bytes from "):
        return "Normal"
    elif line.startswith("92 bytes from "):
        # this precedes three more lines for the report
        # first push this back on the queue
        handle_gateway_failure(line_queue, line, linenumber)
        return "GWFailure"
    else:
        # Is there anything other than '64 bytes...'?
        print "linenumber: ", str(linenumber)
        print "Unexpected: '", line, "'"
        return "Unexpected"

def main():
    """Main body."""

    # capture timing information
    cputime_0 = psutil.cpu_times()

    # Initialize the counters
    classifications = ["Down",
                       "Comment",
                       "GWFailure",
                       "Route",
                       "Timeout",
                       "Normal",
                       "NegativeRTT",
                       "Unexpected",]
    counters = {"Down": 0,
                "Comment": 0,
                "GWFailure": 0,
                "Route": 0,
                "Timeout": 0,
                "Normal": 0,
                "NegativeRTT": 0,
                "Unexpected": 0}

    line_queue = LineQueue(4)
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
    negative_ping_count = 0
    sequence_number = -1
    sequence_offset = 0
    while line:
        linecount += 1
        # print "linecount: '" + str(linecount)
        # print "line: '" + line.strip() + "'"
        kind = classify(line_queue, line.strip(), linecount)
        # print "   kind: " + kind
        if kind:
            counters[kind] += 1
            if kind == "Normal":
                result = parse_normal_return(line.strip(), linecount)
                # result is a tuple: (ip_address, sequence_number, rtt)
                # ping sends pings once per second, so sequence_number
                # is rough count of seconds.
                (ip, num, rtt) = result
                zrtt = float(rtt)
                inum = int(num)
                if sequence_number < 0:
                    sequence_number = inum + sequence_offset
                    # when we first set sequence_number the offset
                    # should be zero, but there's no harm in adding
                else:
                    sequence_number = inum + sequence_offset
                # do this after calculating sequence_number so that
                # in the 1/65536 chance that we start at sequence==0
                # we do not incorrectly offset by one cycle.
                if inum == 0:
                    # The sequence number only goes to 65535, so we
                    # will keep track of the rolls
                    sequence_offset += 65536
                # Ick - need to redesign this
                if zrtt < 0:
                    # Oops - this is NOT normal after all
                    negative_ping_count += 1
                    counters["Normal"] -= 1
                    counters["NegativeRTT"] += 1
                else:
                    normal_ping_count += 1
# We use the online algorithm documented in Wikipedia article:
# https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance
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
            line = line_queue.get_line()
        elif kind in classifications:
            # not Normal, so a problem
            print "kind: " + kind
            print "Glitch.  sequence_number: " + str(recent_num)
        else:
            # Failed to classify:
            print "linecount: " + str(linecount)
            print "line: '" + line.strip() + "'"
            counters["Unexpected"] += 1

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
