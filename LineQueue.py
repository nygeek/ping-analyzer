""" LineQueue implementation

Written by Marc Donner
Started 2017-09-10

My ping stream analyzer (analyze_pings.py) requires the ability
to look three lines ahead in order to handle certain ill-formed
error reports.
"""

import datetime as datetime
import json
import sys

#
# Roadmap
#
# 2017-09-10 [X] Make sure that we do the right thing on EOF
#                Done 2017-10-29
#


class LineQueue(object):
    """LineQueue - buffer for a file descriptor that supports pushback."""
    def __init__(self, maxDepth=4, filename="stdin"):
        self.max_depth = maxDepth
        self.filename = filename
        self.timestamp = datetime.datetime.isoformat(\
                datetime.datetime.today())
        self.version = "1.0"
        if filename == 'stdin':
            self.file_descriptor = sys.stdin
        else:
            self.file_descriptor = open(filename, 'r')
        self.line_queue = []
        self.fill_queue()

    def signature(self):
        result = "# LineQueue version 1.0\n"
        result += "# self.filename: " + self.filename + "\n"
        result += "# self.timestamp: " + self.timestamp + "\n"
        return result

    def get_line(self):
        """Get a line from self.line_queue."""
        result = ""
        if self.line_queue:
            result = self.line_queue.pop(0)
            self.fill_queue()
        return result

    def fill_queue(self):
        """Fill the queue as needed."""
        while len(self.line_queue) < self.max_depth:
            line = self.file_descriptor.readline()
            self.line_queue.append(line)

    def push_back(self, line):
        """Push a line back on the line_queue."""
        self.line_queue.insert(0, line)

    def __str__(self):
        return json.dumps(self.line_queue, indent=2, separators=(',', ': '))


def main():
    """Main routine - just for testing."""

    print "begin test..."
    line_queue = LineQueue(4, "./lqtest.txt")

    print line_queue.signature()

    print "line_queue before:"
    print str(line_queue)

    line = line_queue.get_line()
    print line

    print "line_queue after:"
    print str(line_queue)

    line1 = line_queue.get_line()
    line2 = line_queue.get_line()
    line3 = line_queue.get_line()
    line_queue.push_back(line3)
    line_queue.push_back(line2)
    line_queue.push_back(line1)

    print "line_queue after pushbacks:"
    print str(line_queue)

    # now read to the end of the file
    line = line_queue.get_line()
    while line:
        print "line: '" + str(line.strip()) + "'"
        line = line_queue.get_line()

if __name__ == '__main__':
    main()
