""" analyze_pings.py """

import fileinput
from datetime import datetime
import json
import re

def handle_gateway_failure(linenumber):
    """ when a line starts with '92 bytes from ' we have
    to expect three more lines:
       'Vr HL TOS  Len   ID Flg  off TTL Pro  cks      Src      Dst'
       (a bunch of numbers and data)
       (a blank line) """
    first = "Vr HL TOS  Len   ID Flg  off TTL Pro  cks      Src      Dst"
    # need to flush three lines here ...

def classify(linenumber, line):
    """ Given a line from the pinger output, classify it. """

    if line == "ping: sendto: Network is down":
        return "Down"
    elif line == "ping: sendto: No route to host":
        return "Route"
    elif line.startswith("Request timeout for icmp_seq "):
        return "Timeout"
    elif line.startswith("64 bytes from "):
        return "Normal"
    elif line.startswith("92 bytes from "):
        # this precedes three more lines for the report
        handle_gateway_failure(linenumber)
    else:
        # Is there anything other than '64 bytes...'?
        print "Unexpected: '", line, "'"
        print "linenumber: ", linenumber
        return "Unexpected"

# Because one of the error modes produces a four-line sequence
# I need an input reader that lets me look ahead in the input
# stream:

def main():
    """Main body."""

    # Initialize the counters
    counters = {"Down": 0,
                "Route": 0,
                "Timeout": 0,
                "Normal": 0,
                "Unexpected": 0}

    linecount = 0
    for line in fileinput.input():
        linecount += 1
        counters[classify(linecount, line.strip())] += 1

    print "linecount", linecount
    print "down: ", counters["Down"]
    print "route: ", counters["Route"]
    print "timeout: ", counters["Timeout"]
    print "normal: ", counters["Normal"]
    print "unexpected: ", counters["Unexpected"]

if __name__ == '__main__':
    main()
