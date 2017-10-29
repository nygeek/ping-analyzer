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

def classify(line_queue, line, linenumber):
    """ Given a line from the pinger output, classify it. """

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

# Because one of the error modes produces a four-line sequence
# I need an input reader that lets me look ahead in the input
# stream:

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

    line_queue = LineQueue(4, "./sample.txt")
    linecount = 0
    
    line = line_queue.get_line()
    while line:
        linecount += 1
        kind = classify(line_queue, line.strip(), linecount)
        # print "line: '" + line.strip() + "'"
        # print "kind: " + kind
        if kind:
            line = line_queue.get_line()
            counters[kind] += 1
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

if __name__ == '__main__':
    main()
