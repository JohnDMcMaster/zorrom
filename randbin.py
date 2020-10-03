#!/usr/bin/env python3

import os
import random

from zorrom.util import add_bool_arg
from zorrom.archs import arch2mr


def run(arch, fn_out, verbose=False, onebit=False):
    try:
        mrc = arch2mr[arch]
    except KeyError:
        raise Exception("Invalid architecture %s. Try --list-arch" % arch)

    mr = mrc(verbose=verbose)
    out_buf = bytearray()
    if onebit:
        for wordi in range(mr.words()):
            if wordi == 0:
                word = 0x1FF
            else:
                word = 0
            mr.append_word(out_buf, word)
    else:
        for _wordi in range(mr.words()):
            word = random.randint(0, mr.bitmask())
            mr.append_word(out_buf, word)
    open(fn_out, "wb").write(out_buf)


def list_arch():
    for a in arch2mr.keys():
        print(a)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Create a random .bin (ie for testing)')
    parser.add_argument('--verbose', action='store_true', help='')
    add_bool_arg(parser, '--invert', default=None, help='Default: auto')
    parser.add_argument('--arch', help='Decoder to use (required)')
    parser.add_argument('--list-arch',
                        action='store_true',
                        help='Extended help')
    parser.add_argument('fn_out', nargs='?', help='.bin file out')
    args = parser.parse_args()

    if args.list_arch:
        list_arch()
        return

    run(args.arch, args.fn_out, verbose=args.verbose)


if __name__ == "__main__":
    main()
