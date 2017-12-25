""" pinger.py

Wrapper to run the ping program under the control of a configuration
file.

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

    print "# pinger.py: cwd: " + os.getcwd()
    print "# pinger.py: config_file_path: " + config_file_path
    config.read(config_file_path)

    try:
        hosts = config.get('destinations', 'hosts')
    except ConfigParser.NoOptionError:
        hosts = 'localhost'
    host_list = hosts.split(", ")

    try:
        ping_command = config.get('pinger', 'ping_command')
    except ConfigParser.NoOptionError:
        ping_command = 'ping -n'

    # insert_timestamps program is here
    insert_timestamps_path = os.path.expanduser(\
            '~/projects/p/pinger/insert_timestamps.py')

    # construct the log file path name
    try:
        destination_directory = config.get(\
                'pinger', 'destination_directory')
    except ConfigParser.NoOptionError:
        destination_directory = '/tmp'

    destination_directory = os.path.expanduser(destination_directory)

    # timer_interval us used by the insert_timestamps.py program
    #
    # try:
    #     timer_interval = config.getint('pinger', 'timer_interval')
    # except ConfigParser.NoOptionError:
    #     timer_interval = 100 

    print "# pinger.py: host_list: " + str(host_list)
    # print "# pinger.py: timer_interval: " + str(timer_interval)

    destination_directory += "/" + timestamp
    try:
        os.mkdir(destination_directory)
    except OSError:
        (exc_type, exc_value, ex_traceback) = sys.exc_info()
        print "ABORT: mkdir(" + destination_directory + ")"
        exit

    final_command = ""

    for host in host_list:
        # now construct the command strings for the pipelines

        command = []

        # First - run ping
        command.append(ping_command + " " + host)

        # Second - pipe the ping output through insert_timestamp
        command.append("python " + insert_timestamps_path + \
                        " -c " + config_file_path)

        # filename components:
        #   date + time => this will be a directory
        #   hostname
        log_file_name = host + '.ping.log'

        # Third - tee it into the log file ...
        command.append("/usr/bin/tee " + \
                destination_directory + "/" + log_file_name)

        cmd = " | ".join(command)
        final_command += cmd + " & "

    print "====="
    print final_command
    print "====="

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
