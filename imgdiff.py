#!/usr/bin/env python3
# backpropagate ROM into image

from PIL import Image
import argparse
import os
import json
from zorrom import archs
from zorrom import util
'''
Given byte offset and mask return image (col, row)
maskb: binary mask
maski: bitshi
'''
"""
mb old
def bit_b2i(offset, maskb=None, maski=None):
    maskin = {
        0x80: 7,
        0x40: 6,
        0x20: 5,
        0x10: 4,
        0x08: 3,
        0x04: 2,
        0x02: 1,
        0x01: 0,
    }
    if maski is None:
        maski = maskin[maskb]
    biti = offset * 8 + maski
    #print(biti)
    # Each column has 16 bytes
    # Actually starts from right of image
    col = (32 * 8 - 1) - biti / (8 * 32)
    # 0, 8, 16, ... 239, 247, 255
    row = (biti % 32) * 8 + (biti / 32) % 8
    #print row
    return (col, row)
"""


def bitmap(mrl, mrr, fn_out):
    # red on difference
    color_diff = (255, 0, 0)
    # gray on 1
    color_1 = (128, 128, 128)
    # black on 0
    color_0 = (0, 0, 0)
    # blue?
    color_null = (0, 64, 64)
    if mrl.invert():
        color_1, color_0 = color_0, color_1

    txtw, txth = mrl.txtwh()
    print("Image %uw x %uh" % (txtw, txth))
    im = Image.new("RGB", (txtw, txth), "black")
    diffs = []
    for col in range(txtw):
        for row in range(txth):
            try:
                # b1 = mrl.get_cr(col, row)
                # b2 = mrr.get_cr(col, row)
                offset, maskb = mrl.cr2ob(col, row)
                assert offset < mrl.bytes()
                assert maskb < 0x100, maskb
                b1 = bool(mrl.binary[offset] & maskb)
                b2 = bool(mrr.binary[offset] & maskb)
            except KeyError:
                # Not all positions actually map to binary
                c = color_null
            else:
                if b1 != b2:
                    c = color_diff
                    diffs.append((col, row, b1, b2))
                else:
                    if b1:
                        c = color_1
                    else:
                        c = color_0
            im.putpixel((col, row), c)
    im.save(fn_out)
    return diffs


def run(arch, rom1_fn, rom2_fn, fn_out, monkey_fn=None, annotate=None):
    mrl = archs.get_arch(arch)
    mrl.parse_bin(open(rom1_fn, 'rb').read())
    mrr = archs.get_arch(arch)
    mrr.parse_bin(open(rom2_fn, 'rb').read())

    print('Converting to image layout...')
    dir_out = 'romdiff'
    if not os.path.exists(dir_out):
        os.mkdir(dir_out)

    diffs = bitmap(mrl, mrr, fn_out)

    for diff in diffs:
        col, row, b1, b2 = diff
        print('x%d, y%d, L: %d, R: %d' % (col, row, b1, b2))
        off, maskb = mrl.cr2ob(col, row)
        print('  Offset 0x%04X, mask 0x%02X' % (off, maskb))
        vg_col = col / 8
        vl_col = col % 8
        vg_row = row / 8
        vl_row = row % 8
        if monkey_fn:
            print(
                '  http://cs.sipr0n.org/static/%s/%s_%02d_%02d.png @ col %d, row %d'
                % (monkey_fn, monkey_fn, vg_col, vg_row, vl_col, vl_row))

    if annotate:
        j = {}
        for diff in diffs:
            col, row, b1, b2 = diff
            j["%u,%u" % (col, row)] = {}
        json.dump(j,
                  open(annotate, "w"),
                  indent=4,
                  sort_keys=True,
                  separators=(',', ': '))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=
        'Visually diff two .bin in original image layout, printing differences'
    )
    parser.add_argument('--verbose', '-v', action='store_true', help='verbose')
    parser.add_argument('--arch', help='Decoder to use (required)')
    parser.add_argument('--annotate', help='Output rompar annotate JSON')
    parser.add_argument('--monkey-fn',
                        default=None,
                        help='Monkey URL reference. Ex: sega_315-5677_xpol')
    parser.add_argument('rom1', help='ROM1 file name')
    parser.add_argument('rom2', help='ROM2 file name')
    parser.add_argument('out',
                        nargs='?',
                        default=None,
                        help='Output file name')
    args = parser.parse_args()

    fn_out = args.out
    if not fn_out:
        fn_out = 'out.png'
    run(args.arch,
        rom1_fn=args.rom1,
        rom2_fn=args.rom2,
        fn_out=fn_out,
        monkey_fn=args.monkey_fn,
        annotate=args.annotate)
