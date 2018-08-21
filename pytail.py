#!/usr/bin/env python
# https://agrrh.com/2018/tail-follow-in-python

import sys
import time

def tailf(fname):
    try:
        fp = open(fname, 'r')
    except IOError:
        print('Could not open file')
        sys.exit(1)

    fp.seek(0, 2)
    while True:
        line = fp.readline()
        if line:
            yield line.strip()
        time.sleep(0.1)

if __name__ == '__main__':
    try:
        fname = sys.argv[1]
    except IndexError:
        print('File not specified')
        sys.exit(1)

    for line in tailf(fname):
        print(line)
