""" pinger.py

Wrapper to run the ping program under the control of a configuration
file.

"""

import argparse
import datetime as datetime
import ConfigParser
import os
import psutil

def main():
    """main body."""

    # capture timing information
    cputime_0 = psutil.cpu_times()

    # Self-identification for the run
    # This gives us YYYY-MM-DDTHH:MM:SS+HH:MM
    timestamp = datetime.datetime.isoformat(\
                    datetime.datetime.today())
    print "# pinger.py"
    print "# pinger.py: start: timestamp: " + timestamp

    parser = argparse.ArgumentParser(\
            description='Run pings from a configuration file.')
    parser.add_argument('-c', nargs='?',\
            default='./pinger.cfg', help="configuration file name")
    parser.add_argument('-D', type=int, nargs='?',\
                    default=0, help="Debug flag (int: default to 0)")
    args = parser.parse_args()

    print "# pinger.py: args.c: " + args.c

    config = ConfigParser.ConfigParser()
    config_file_path = os.path.expanduser(args.c)

    print "# pinger.py: config_file_path: " + config_file_path
    config.read(config_file_path)

    try:
        hosts = config.get('destinations', 'hosts')
    except ConfigParser.NoOptionError:
        hosts = 'localhost'
    host_list = hosts.split(", ")

    # timer_interval us used by the insert_timestamps.py program
    #
    # try:
    #     timer_interval = config.getint('pinger', 'timer_interval')
    # except ConfigParser.NoOptionError:
    #     timer_interval = 100 

    print "# pinger.py: host_list: " + str(host_list)
    # print "# pinger.py: timer_interval: " + str(timer_interval)

    # capture timing information
    cputime_1 = psutil.cpu_times()

    # wrapping up - display timing data
    timestamp = datetime.datetime.isoformat(\
                    datetime.datetime.today())
    print "# pinger.py: end: timestamp: " + timestamp
    print "# pinger.py: User time: " +\
                    str(cputime_1[0] - cputime_0[0]) + " S"
    print "# pinger.py: System time: " +\
            str(cputime_1[2] - cputime_0[2]) + " S"

if __name__ == '__main__':
    main()
