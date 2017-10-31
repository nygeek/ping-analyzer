""" analyze_pings.py

Take the log of ping data output from running ping for a long
time and summarize and analyze the various errors.

"""

from LineQueue import LineQueue
from datetime import datetime
import json
import re

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

def parse_normal_return(line, linenumber):
    """ Given a normal string, return a tuple containing IP address,
        Sequence number, and RTT.
    """
    # print "parse_normal_return(): " + line.strip()
    (front, back) = line.split(":")
    (junk, junk, junk, ip_address) = front.split(" ")
    (junk, seq, ttl, time, ms) = back.split(" ")
    (junk, t) = time.split("=")
    (icmp_seq, numb) = seq.split("=")
    return (ip_address, numb, t)

def classify(line_queue, line, linenumber):
    """ Given a line from the pinger output, classify it. """

    # print "classify(): " + line
    if line == "ping: sendto: Network is down":
        return "Down"
    elif line.startswith("#"):
        return "Prefix"
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

    # Initialize the counters
    counters = {"Down": 0,
                "Prefix": 0,
                "GWFailure": 0,
                "Route": 0,
                "Timeout": 0,
                "Normal": 0,
                "Unexpected": 0}

    line_queue = LineQueue(4)
    linecount = 0
    
    line = line_queue.get_line()
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
                print str(result)
            line = line_queue.get_line()
        else:
            # Failed to classify:
            print "linecount: " + str(linecount)
            print "line: '" + line.strip() + "'"
            counters["Unexpected"] += 1

    print "linecount", linecount
    print "Down: ", counters["Down"]
    print "GWfailure: ", counters["GWFailure"]
    print "Normal: ", counters["Normal"]
    print "Prefix: ", counters["Prefix"]
    print "Route: ", counters["Route"]
    print "Timeout: ", counters["Timeout"]
    print "Unexpected: ", counters["Unexpected"]

    checksum = linecount
    checksum -= counters["Down"]
    checksum -= counters["GWFailure"]
    checksum -= counters["Normal"]
    checksum -= counters["Prefix"]
    checksum -= counters["Route"]
    checksum -= counters["Timeout"]
    checksum -= counters["Unexpected"]

    print "checksum: " + str(checksum)

if __name__ == '__main__':
    main()
