#!/usr/bin/env python3

from zorrom import solver

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Guess mask ROM layout based on constraints')
    parser.add_argument('--bytes', required=True, help='Constraints as offset:byte,offset:byte,.. offset:byte:mask is also allowed')
    parser.add_argument('--verbose', action='store_true', help='')
    parser.add_argument('fn_in', help='.txt file in')
    parser.add_argument('dir_out', nargs='?', help='Write top .bin file')
    args = parser.parse_args()

    solver.run(args.fn_in,
        solver.parse_ref_words(args.bytes),
        args.dir_out,
        verbose=args.verbose)
