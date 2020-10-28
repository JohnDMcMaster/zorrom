#!/usr/bin/env python3

from zorrom import solver
from zorrom.util import add_bool_arg

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Guess mask ROM layout based on constraints')
    parser.add_argument(
        '--bytes',
        required=True,
        help=
        'Constraints as offset:byte,offset:byte,.. offset:byte:mask is also allowed'
    )
    parser.add_argument('--verbose', action='store_true', help='')
    parser.add_argument('--all', action='store_true', help='')
    add_bool_arg(parser, '--invert', default=None, help='')
    parser.add_argument('--rotate', type=int, default=None, help='')
    add_bool_arg(parser, '--flipx', default=None, help='')
    parser.add_argument('--interleave', type=int, default=1, help='')
    parser.add_argument('--layout-alg', type=str, default=None, help='')
    parser.add_argument('--write-thresh', type=float, default=None, help='')
    parser.add_argument('--word-bits', type=int, default=8, help='')
    parser.add_argument('--words', type=int, default=None, help='')
    parser.add_argument('fn_in', help='.txt file in')
    parser.add_argument('dir_out', nargs='?', help='Write top .bin file')
    args = parser.parse_args()

    solver.run(args.fn_in,
               solver.parse_ref_words(args.bytes),
               args.dir_out,
               all=args.all,
               invert_force=args.invert,
               rotate_force=args.rotate,
               flipx_force=args.flipx,
               interleave_force=args.interleave,
               layout_alg_force=args.layout_alg,
               write_thresh=args.write_thresh,
               word_bits=args.word_bits,
               words=args.words,
               verbose=args.verbose)
