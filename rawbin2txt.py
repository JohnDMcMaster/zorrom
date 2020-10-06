#!/usr/bin/env python3

from zorrom import mrom

def run(fn_in, fn_out, width, height=None, bits=None, grows=None, gcols=None, lsb=False, verbose=False):
    if lsb:
        txt_raw = mrom.load_bin_lsb(open(fn_in, "rb"))
    else:
        txt_raw = mrom.load_bin_msb(open(fn_in, "rb"))
    if height is None:
        assert len(txt_raw) % width == 0
        height = len(txt_raw) // width 
    if not bits:
        bits = width * height
    bits = width * height
    txt = txt_raw[0:bits]
    print("%uw x %uh => %u bits" % (width, height, bits))
    txtdict = mrom.txt2dict(txt, width, height)

    if grows is None:
        grows = list(range(8, height, 8))

    if gcols is None:
        gcols = list(range(8, width, 8))

    mrom.save_txt(open(fn_out, "w"),
                  txtdict,
                  width,
                  height,
                  grows=grows,
                  gcols=gcols)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Convert a bit array .bin to a .txt file')
    parser.add_argument('--verbose', action='store_true', help='')
    parser.add_argument('--lsb', action='store_true', help='lsb first')
    parser.add_argument('--width', required=True, help='.txt file width')
    parser.add_argument('--bits', help='.txt file width')
    parser.add_argument('fn_in', help='.bin file in')
    parser.add_argument('fn_out', help='.txt file out')
    args = parser.parse_args()

    bits = None
    if args.bits:
        bits = int(args.bits, 0)

    run(args.fn_in,
               args.fn_out,
               width=int(args.width, 0),
               bits=bits,
               verbose=args.verbose)
