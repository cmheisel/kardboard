#!/usr/bin/env python
#
# Utility script to run pyflakes with the modules we care about and
# exclude errors we know to be fine.

import os
import re
import subprocess
import sys


def main():
    cur_dir = os.path.dirname(__file__)
    modules = sys.argv[1:]

    if not modules:
        modules = ['kardboard']

    p = subprocess.Popen(['pyflakes'] + modules,
                         stderr=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         close_fds=True)

    contents = p.stdout.readlines()
    # Read in the exclusions file
    exclusions = {}
    exclusion_file = os.path.join(cur_dir, "pyflakes.exclude")
    fp = open(exclusion_file, "r")

    for line in fp.readlines():
        if not line.startswith("#"):
            exclusions[line.rstrip()] = 1

    fp.close()

    exit_flag = 0
    # Now filter thin
    for line in contents:
        line = line.rstrip()
        line = line.replace('../kardboard/', '')
        test_line = re.sub(r':[0-9]+:', r':*:', line, 1)
        test_line = re.sub(r'line [0-9]+', r'line *', test_line)

        if test_line not in exclusions:
            print line
            exit_flag = -1
    return exit_flag


if __name__ == "__main__":
    sys.exit(main())
