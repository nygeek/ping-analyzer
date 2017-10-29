""" LineQueue implementation

Written by Marc Donner
Started 2017-09-10

My ping stream analyzier (analyze_pings.py) requires the ability
to look three lines ahead in order to handle certain ill-formed
error reports.

"""

import fileinput
import json
import sys

#
# TODO
#
# 2017-09-10 [ ] Make sure that we do the right thing on EOF
#


class LineQueue(object):
    """LineQueue - buffer for a file descriptor that supports pushback"""
    def __init__(self, maxDepth=4, filename="stdin"):
        self.max_depth = maxDepth
        if filename == 'stdin':
            self.file_descriptor = sys.stdin
        else:
            self.file_descriptor = open(filename, 'r')
        self.queue = []
        # I can not use a sentry to indicate EOF, since there is
        # no way I can prevent that string from appearing in an
        # arbitrary file somewhere.  So I use queue_len.  It is -1 if
        # I have not seen EOF yet.  After I have seen EOF, I have to
        # keep track of the number of lines to EOF.
        self.queue_len = -1
        self.fill_queue()

    def get_line(self):
        """get a line from the lq"""
        if self.queue_len < 0:
            result = self.queue.pop(0)
            self.queue_len = len(self.queue)
            self.fill_queue()
        elif self.queue_len > 0:
            result = self.queue.pop(0)
            self.queue_len = len(self.queue)
            # Can not call fill_queue() here, since we have seen EOF
        return result

    def fill_queue(self):
        """fill the queue as needed"""
        while len(self.queue) < self.max_depth:
            line = self.file_descriptor.readline()
            if not line:
                # we are at EOF ... note how many lines we have
                # to go
                self.queue_len = len(self.queue)
            else:
                self.queue.append(line.strip())

    def push_back(self, line):
        """Push a line back on the queue."""
        self.queue.insert(0, line)

    def __str__(self):
        return json.dumps(self.queue, indent=2, separators=(',', ': '))


def main():
    """main routine - just for testing"""
    print "begin test..."
    queue = LineQueue(4, "./lqtest.txt")
    print "queue before:"
    print str(queue)

    z = queue.get_line()
    print z

    print "queue after:"
    print str(queue)

    z1 = queue.get_line()
    z2 = queue.get_line()
    z3 = queue.get_line()
    queue.push_back(z3)
    queue.push_back(z2)
    queue.push_back(z1)

    print "queue after pushbacks:"
    print str(queue)

    # now read to the end of the file

    exit


if __name__ == '__main__':
    main()
