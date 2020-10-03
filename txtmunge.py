#!/usr/bin/env python3

from zorrom import mrom
from zorrom.util import add_bool_arg


def munge_txt(txt,
              fn_out,
              win,
              hin,
              rotate=None,
              flipx=False,
              flipy=False,
              invert=False):
    '''Return contents as char array of bits (ie string with no whitespace)'''
    assert rotate in (None, 0, 90, 180, 270)
    if rotate == 90 or rotate == 270:
        wout, hout = hin, win
    else:
        wout, hout = win, hin
    txtdict = mrom.txt2dict(txt, win, hin)
    if rotate not in (None, 0):
        txtdict = mrom.td_rotate(rotate, txtdict, wout, hout)
    if flipx:
        txtdict = mrom.td_flipx(txtdict, wout, hout)
    if flipy:
        txtdict = mrom.td_flipy(txtdict, wout, hout)
    if invert:
        txtdict = mrom.td_invert(txtdict, wout, hout)
    # return mrom.dict2txt(txtdict, wout, hout)
    mrom.save_txt(open(fn_out, "w"), txtdict, wout, hout)


def run(fn_in,
        fn_out,
        invert=None,
        rotate=None,
        flipx=False,
        flipy=False,
        verbose=False):
    txtin, win, hin = mrom.load_txt(open(fn_in, "r"), None, None)
    munge_txt(txtin,
              fn_out,
              win,
              hin,
              rotate=rotate,
              flipx=flipx,
              flipy=flipy,
              invert=invert)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Raw .txt file manipulator. Whitespace is not preserved')
    add_bool_arg(parser, '--invert', default=None, help='Default: auto')
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
    parser.add_argument('--verbose', action='store_true', help='')
    parser.add_argument('fn_in', nargs='?', help='.txt file in')
    parser.add_argument('fn_out', nargs='?', help='.bin file out')
    args = parser.parse_args()

    run(args.fn_in,
        args.fn_out,
        invert=args.invert,
        rotate=args.rotate,
        flipx=args.flipx,
        flipy=args.flipy,
        verbose=args.verbose)


if __name__ == "__main__":
    main()
