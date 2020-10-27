#!/usr/bin/env python3

import argparse

from zorrom import mrom


def run(verbose, fn_ins, fn_out):
    w = None
    h = None
    txtdict = None

    for fn_in in fn_ins:
        txt1, w1, h1 = mrom.load_txt(open(fn_in, "r"), None, None)
        print("Check %s, %uw x %uh" % (fn_in, w1, h1))
        if txtdict is None:
            w = w1
            h = h1
        else:
            # strictly speaking don't need w assert, but keep for now
            assert w1 == w and h1 == h, "size mismatch: left bits %u (%uw x %uh), right bits %u (%uw x %uh)" % (
                len(txt1), w1, h1, len(w * h), w, h)

        txtdict1 = mrom.txt2dict(txt1, w1, h1)
        if txtdict is None:
            txtdict = txtdict1
        else:
            for x in range(w):
                for y in range(h):
                    l = txtdict1[(x, y)]
                    r = txtdict[(x, y)]
                    txtdict[(x, y)] = l if l == r else 'X'

    syms = dict()
    for x in range(w):
        for y in range(h):
            r = txtdict[(x, y)]
            syms[r] = syms.get(r, 0) + 1
    print("Statistics")
    for sym in "01X":
        print("  %s: %u" % (sym, syms[sym]))

    mrom.save_txt(open(fn_out, "w"), txtdict, w, h)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=
        "Compute symbol and between two files, outputting x when they don't match"
    )
    parser.add_argument('--verbose', '-v', action='store_true', help='verbose')
    parser.add_argument('--out', required=True, help='Output .txt file name')
    parser.add_argument('ins', nargs='+', help='ROM input .txt file names')
    args = parser.parse_args()

    run(verbose=args.verbose, fn_ins=args.ins, fn_out=args.out)
