###
### analyze_pings.py
###

import fileinput
from datetime import datetime
import json
import re

def classify(line):
    """ Given a line from the pinger output, classify it. """
    """ 64 bytes from 166.84.1.3: icmp_seq=19634 ttl=246 time=18.521 ms """
    """ ping: sendto: Network is down """
    """ ping: sendto: No route to host """
    """ Request timeout for icmp_seq 20043 """

    if line == "ping: sendto: Network is down":
        return("Down")
    elif line == "ping: sendto: No route to host":
        return("Route")
    elif line.startswith("Request timeout for icmp_seq "):
        return("Timeout")
    else:
        return("Normal")

def main():
    """Main body."""

    # Initialize the counters
    counters = {"Down": 0, "Route": 0, "Timeout": 0, "Normal": 0}

    linecount = 0
    for line in fileinput.input():
        linecount += 1
        counters[classify(line.strip())] += 1

    print "linecount", linecount
    print "down: ", counters["Down"]
    print "route: ", counters["Route"]
    print "timeout: ", counters["Timeout"]
    print "normal: ", counters["Normal"]

if __name__ == '__main__':
    main()
