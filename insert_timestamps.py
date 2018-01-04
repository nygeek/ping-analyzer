""" insert_timestamps.py

Filter to insert timestamp comments into the ping stream to 
enhance our analysis.

"""

import argparse
import datetime as datetime
import ConfigParser
import os
import psutil
import sys

def main():
    """main body."""

    # capture timing information
    cputime_0 = psutil.cpu_times()

    # Self-identification for the run
    # This gives us YYYY-MM-DDTHH:MM:SS+HH:MM
    timestamp = datetime.datetime.isoformat(\
                    datetime.datetime.today())
    print "# insert_timestamps.py"
    print "# insert_timestamps.py: start: timestamp: " + timestamp

    stream_tag = "pid-" + str(os.getpid())

    parser = argparse.ArgumentParser(\
            description='Filter a stream, inserting periodic timestamps.')
    parser.add_argument('-c', nargs='?',\
            default='./pinger.cfg', help="configuration file name")
    parser.add_argument('--notag', action='store_true',\
            help="do not insert tags at all")
    parser.add_argument('-s', nargs='?',\
            default=64, help="records to skip between timestamps")
    parser.add_argument('-t', nargs='?',\
            default=stream_tag, help="tag this stream")
    parser.add_argument('-D', type=int, nargs='?',\
                    default=0, help="Debug flag (int: default to 0)")
    args = parser.parse_args()
    stream_tag = args.t

    if args.notag:
        print "# insert_timestamps.py: no tags"
    else:
        print "# insert_timestamps.py: tag: " + str(stream_tag)

    config = ConfigParser.ConfigParser()
    config_file_path = os.path.expanduser(args.c)

    print "# insert_timestamps.py: config_file_path: " + config_file_path
    config.read(config_file_path)

    if args.s:
        timer_interval = int(args.s)
    else:
        try:
            timer_interval = config.getint('pinger', 'timer_interval')
        except ConfigParser.NoOptionError:
            timer_interval = 10

    print "# insert_timestamps.py: timer_interval: " + str(timer_interval)
    
    # now we stream STDIN to STDOUT, inserting a timestamp comment
    # every timer_interval rows

    linenumber = 0
    try:
        while True:
            if not linenumber % timer_interval:
                timestamp = datetime.datetime.isoformat(\
                    datetime.datetime.today())
                if args.notag:
                    print "# timestamp: " + str(timestamp)
                else:
                    print "# timestamp: " + stream_tag + ": " +\
                            str(timestamp)
            print sys.stdin.readline().strip()
            sys.stdout.flush()
            linenumber += 1
    except KeyboardInterrupt:
        sys.stdout.flush()
        pass

    # capture timing information
    cputime_1 = psutil.cpu_times()

    # wrapping up - display timing data
    timestamp = datetime.datetime.isoformat(\
                    datetime.datetime.today())
    print "# insert_timestamps.py: end: timestamp: " + timestamp
    print "# insert_timestamps.py: User time: " +\
                    str(cputime_1[0] - cputime_0[0]) + " S"
    print "# insert_timestamps.py: System time: " +\
            str(cputime_1[2] - cputime_0[2]) + " S"
    print "# linenumber: " + str(linenumber)

if __name__ == '__main__':
    main()
