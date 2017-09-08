###
### analyze_pings.py
###

import fileinput
from datetime import datetime
import json
import re

linecount = 0
down = 0
route = 0
timeout = 0
normal = 0

def classify(line):
    """ Given a line from the pinger output, classify it. """
    """ 64 bytes from 166.84.1.3: icmp_seq=19634 ttl=246 time=18.521 ms """
    """ ping: sendto: Network is down """
    """ ping: sendto: No route to host """
    """ Request timeout for icmp_seq 20043 """
    global down
    global route
    global timeout
    global normal
    global linecount

    linecount += 1
    if line == "ping: sendto: Network is down":
        down += 1
    elif line == "ping: sendto: No route to host":
        route += 1
    elif line.startswith("Request timeout for icmp_seq "):
        timeout += 1
    else:
        normal += 1

def main():
    """Main body."""

    for line in fileinput.input():
        # print line.strip()
        classify(line.strip())

    print "linecount", linecount
    print "down: ", down
    print "route: ", route
    print "timeout: ", timeout
    print "normal: ", normal

if __name__ == '__main__':
    main()
