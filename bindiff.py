#!/usr/bin/env python3

from PIL import Image
import argparse
import os


def run(verbose, rom1_fn, rom2_fn):
    rom1 = open(rom1_fn, "rb").read()
    rom2 = open(rom2_fn, "rb").read()
    assert len(rom1) == len(rom2)
    l = len(rom1)
    print("0x%04X (%u) bytes" % (l, l))

    byted = {}
    bitd = {}
    for addr, (l, r) in enumerate(zip(rom1, rom2)):
        if l == r:
            continue
        byted[addr] = (l, r)
        for bit in range(8):
            bit = 1 << bit
            lbit = l & bit
            rbit = r & bit
            if lbit != rbit:
                bitd[(addr, bit)] = (lbit, rbit)
    print("%u bytes different" % len(byted))
    print("%u bits different" % len(bitd))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Compute statistics between two ROMs')
    parser.add_argument('--verbose', '-v', action='store_true', help='verbose')
    parser.add_argument('rom1', help='ROM1 file name')
    parser.add_argument('rom2', help='ROM2 file name')
    args = parser.parse_args()

    run(verbose=args.verbose, rom1_fn=args.rom1, rom2_fn=args.rom2)
