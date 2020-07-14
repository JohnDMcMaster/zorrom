#!/usr/bin/env python3

import os

from zorrom.util import add_bool_arg
from zorrom.archs import arch2mr


def run(arch,
        fn_in,
        fn_out,
        invert=None,
        rotate=None,
        flipx=False,
        flipy=False,
        verbose=False):
    try:
        mrc = arch2mr[arch]
    except KeyError:
        raise Exception("Invalid architecture %s. Try --list-arch" % arch)
    f_in = open(fn_in, 'r')
    # TODO: maybe its better to invert the input
    # There might be partial word conventions

    mr = mrc(verbose=verbose)
    out_buff = mr.txt2bin(f_in,
                          invert=invert,
                          rotate=rotate,
                          flipx=flipx,
                          flipy=flipy)
    open(fn_out, "wb").write(out_buff)


def list_arch():
    for a in arch2mr.keys():
        print(a)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Convert ROM physical layout to binary')
    parser.add_argument('--verbose', action='store_true', help='')
    add_bool_arg(parser, '--invert', default=None, help='Default: auto')
    parser.add_argument('--arch', help='Decoder to use (required)')
    parser.add_argument('--list-arch',
                        action='store_true',
                        help='Extended help')
    parser.add_argument('--rotate',
                        type=int,
                        default=None,
                        help='Rotate clockwise 90, 180, or 270 degrees')
    parser.add_argument('--flipx',
                        action="store_true",
                        help='Mirror along x axis')
    parser.add_argument('--flipy',
                        action="store_true",
                        help='Mirror along y axis')
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
        run(args.arch,
            args.fn_in,
            fn_out,
            invert=args.invert,
            rotate=args.rotate,
            flipx=args.flipx,
            flipy=args.flipy,
            verbose=args.verbose)
