#!/usr/bin/env python3

import argparse

from zorrom import mrom
from zorrom.util import parser_grcs, parse_grcs


def run(verbose, rom1_fn, rom2_fn, fn_out=None, grows=None, gcols=None):
    txt1, w1, h1 = mrom.load_txt(open(rom1_fn, "r"), None, None)
    txt2, w2, h2 = mrom.load_txt(open(rom2_fn, "r"), None, None)

    assert w1 == w2 and h1 == h2, "size mismatch: left bits %u (%uw x %uh), right bits %u (%uw x %uh)" % (
        len(txt1), w1, h1, len(txt2), w2, h2)
    l = len(txt1)
    w = w1
    h = h1
    print("0x%04X (%u) bytes, %uw x %uh" % (l, l, w, h))

    txtdict1 = mrom.txt2dict(txt1, w1, h1)
    txtdict2 = mrom.txt2dict(txt2, w2, h2)
    txtdict = mrom.txt2dict(txt1, w2, h2)

    bitd = {}
    for x in range(w2):
        for y in range(h2):
            l = txtdict1[(x, y)]
            r = txtdict2[(x, y)]
            if l == r:
                continue
            bitd[(x, y)] = (l, r)
            txtdict[(x, y)] = "?"
    print("%u bits different" % len(bitd))
    if verbose:
        for (x, y), (l, r) in sorted(bitd.items()):
            print("  %ux, %uy: %s vs %s" % (x, y, l, r))
    if fn_out:
        print("Saving %s" % fn_out)
        mrom.save_txt(open(fn_out, "w"),
                      txtdict,
                      w,
                      h,
                      gcols=gcols,
                      grows=grows)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Compute bit statistics between two .txts')
    parser.add_argument('--verbose', '-v', action='store_true', help='verbose')
    parser_grcs(parser)
    parser.add_argument('rom1', help='ROM1 .txt file name')
    parser.add_argument('rom2', help='ROM2 .txt file name')
    parser.add_argument('fn_out',
                        nargs='?',
                        help='Output .txt file name with ?s')
    args = parser.parse_args()

    grows, gcols = parse_grcs(args)

    run(verbose=args.verbose,
        rom1_fn=args.rom1,
        rom2_fn=args.rom2,
        fn_out=args.fn_out,
        grows=grows,
        gcols=gcols)
