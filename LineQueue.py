""" LineQueue implementation

Written by Marc Donner
Started 2017-09-10

My ping stream analyzier (analyze_pings.py) requires the ability
to look three lines ahead in order to handle certain ill-formed
error conditions.

"""

import fileinput
import json
import sys

#
# TODO
#
# I should parameterize the input so that I can do a better job of
# testing.  Right now I depend on the fileinput machinery, which I
# do not fully understand.
#

class LineQueue:
    def __init__(self, maxDepth=4, filename="stdin"):
        self.MAXDEPTH = maxDepth
        if filename == 'stdin':
            self.fd = sys.stdin
        else:
            self.fd = open(filename)
        self.queue = []
        self.fillQueue()

    def getLine(self):
        result = self.queue.pop(0)
        self.fillQueue()
        return result

    def fillQueue(self):
        while len(self.queue) < self.MAXDEPTH:
            line = self.fd.readline().strip()
            self.queue.append(line)

    def pushBack(self, line):
        self.queue.insert(0, line) 

    def __str__(self):
        return json.dumps(self.queue, indent=2, separators=(',', ': '))

def main():
    print "begin test..."
    lQ = LineQueue(4, "./lqtest.txt")
    print "lQ before:"
    print str(lQ)

    z = lQ.getLine()
    print z

    print "lQ after:"
    print str(lQ)

    z1 = lQ.getLine()
    z2= lQ.getLine()
    z3= lQ.getLine()
    lQ.pushBack(z3)
    lQ.pushBack(z2)
    lQ.pushBack(z1)

    print "lQ after pushbacks:"
    print str(lQ)

    exit

if __name__ == '__main__':
    main()
