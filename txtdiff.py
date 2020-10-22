#!/usr/bin/env python3

import argparse

from zorrom import mrom

def run(verbose, rom1_fn, rom2_fn):
    txt1, w1, h1 = mrom.load_txt(open(rom1_fn, "r"), None, None)
    txt2, w2, h2 = mrom.load_txt(open(rom2_fn, "r"), None, None)

    assert w1 == w2 and h1 == h2, "size mismatch: left bits %u (%uw x %uh), right bits %u (%uw x %uh)" % (len(txt1), w1, h1, len(txt2), w2, h2)
    l = len(txt1)
    w = w1
    h = h1
    print("0x%04X (%u) bytes, %uw x %uh" % (l, l, w, h))

    bitd = {}
    for biti, (l, r) in enumerate(zip(txt1, txt2)):
        if l == r:
            continue
        bitd[biti] = (l, r)
    print("%u bits different" % len(bitd))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Compute bit statistics between two .txts')
    parser.add_argument('--verbose', '-v', action='store_true', help='verbose')
    parser.add_argument('rom1', help='ROM1 .txt file name')
    parser.add_argument('rom2', help='ROM2 .txt file name')
    args = parser.parse_args()

    run(verbose=args.verbose, rom1_fn=args.rom1, rom2_fn=args.rom2)
