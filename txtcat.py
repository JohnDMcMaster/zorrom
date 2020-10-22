#!/usr/bin/env python3

import argparse

from zorrom import mrom


def run(verbose, rom1_fn, rom2_fn, fn_out):
    txt1, w1, h1 = mrom.load_txt(open(rom1_fn, "r"), None, None)
    txt2, w2, h2 = mrom.load_txt(open(rom2_fn, "r"), None, None)

    # strictly speaking don't need w assert, but keep for now
    assert w1 == w2 and h1 == h2, "size mismatch: left bits %u (%uw x %uh), right bits %u (%uw x %uh)" % (
        len(txt1), w1, h1, len(txt2), w2, h2)
    w = w1
    h = h1
    wout = w * 2
    hout = h
    print("%uw x %uh + %uw x %uh => %uw x %uh" % (w1, h1, w1, h2, wout, hout))

    # txtdict1 = mrom.txt2dict(txt1, w1, h1)
    txtdict2 = mrom.txt2dict(txt2, w2, h2)

    txtdict = mrom.txt2dict(txt1, w1, h1)
    for x in range(w2):
        for y in range(h2):
            txtdict[(w1 + x, y)] = txtdict2[(x, y)]

    mrom.save_txt(open(fn_out, "w"), txtdict, wout, hout)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Compute bit statistics between two .txts')
    parser.add_argument('--verbose', '-v', action='store_true', help='verbose')
    parser.add_argument('rom1', help='ROM1 .txt file name')
    parser.add_argument('rom2', help='ROM2 .txt file name')
    parser.add_argument('out', help='Output .txt file name')
    args = parser.parse_args()

    run(verbose=args.verbose,
        rom1_fn=args.rom1,
        rom2_fn=args.rom2,
        fn_out=args.out)
