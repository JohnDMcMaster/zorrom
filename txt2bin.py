#!/usr/bin/env python

import os

from zorrom.util import add_bool_arg
from zorrom.archs import arch2d

# Invert bytes as they are written to file
class InvFile(object):
    def __init__(self, f):
        self.f = f

    def flush(self):
        self.f.flush()

    def write(self, s):
        data = bytearray(s)
        # invert
        for i in xrange(len(data)):
            data[i] ^= 0xFF
        self.f.write(data)

def run(arch, fn_in, fn_out, invert=None, verbose=False):
    try:
        dc = arch2d[arch]
    except KeyError:
        raise Exception("Invalid architecture %s. Try --list-arch" % arch)
    f_in = open(fn_in, 'r')
    f_out = open(fn_out, "wb")
    # TODO: maybe its better to invert the input
    # There might be partial word conventions

    if invert is None:
        invert = dc.invert()
    if invert:
        f_out = InvFile(f_out)
    d = dc(verbose=verbose)
    d.txt2bin(f_in, f_out)

def list_arch():
    for a in arch2d.keys():
        print a

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Convert Mitsubishi MSL8042 ROM physical layout to binary')
    parser.add_argument('--verbose', action='store_true', help='')
    add_bool_arg(parser, '--invert', default=None, help='Default: auto')
    parser.add_argument('--arch', help='Decoder to use (required)')
    parser.add_argument('--list-arch', action='store_true', help='Extended help')
    parser.add_argument('fn_in', nargs='?', help='.txt file in')
    parser.add_argument('fn_out', nargs='?', help='.bin file out')
    args = parser.parse_args()

    if args.list_arch:
        list_arch()
    else:
        if not args.fn_in:
            raise Exception("Require input file")
        fn_out = args.fn_out
        if not fn_out:
            prefix, postfix = os.path.splitext(args.fn_in)
            if not postfix:
                raise Exception("Can't auto name output file")
            fn_out = prefix + '.bin'
        run(args.arch, args.fn_in, fn_out, invert=args.invert, verbose=args.verbose)
