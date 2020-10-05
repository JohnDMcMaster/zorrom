#!/usr/bin/env python3

import os

from zorrom.util import add_bool_arg
from zorrom.archs import arch2mr
from zorrom import mrom

def check_binary(candidate, ref_words, verbose=True):
    """
    Return exact_match, score 0-1
    """
    word_bits = 8
    #bits = len(candidate) * word_bits
    checks = 0
    matches = 0
    for wordi, (expect, mask) in ref_words.items():
        got = candidate[wordi]
        for maski in range(word_bits):
            maskb = 1 << maski
            # Is this bit checked?
            if not mask & maskb:
                continue
            checks += 1
            # Does the bit match?
            if expect & maskb == got & maskb:
                matches += 1
    return checks == matches, matches / checks

def try_oi2cr(mr, func, buf):
    old = mr.oi2cr
    mr.oi2cr = func
    mr.reindex()
    ret = mr.txt2bin_buf(buf)
    mr.oi2cr = old
    return ret

def guess_layout_cols_lr(mr, buf):
    """
    Assume bits are contiguous in columns
    wrapping around at the next line
    Least significant bit at left

    Can either start in very upper left of bit colum and go right
    Or can start in upper right of bit colum and go left

    Related permutations are handled by flipx, rotate, etc
    """
    # Must be able to divide input
    txtw, _txth = mr.txtwh()
    if txtw % mr.word_bits() != 0:
        return
    bit_cols = txtw // mr.word_bits()

    # upper left
    def ul_oi2cr(offset, maski):
        bitcol = offset % bit_cols
        col = maski * bit_cols + bitcol
        row = offset // bit_cols
        return (col, row)
    yield try_oi2cr(mr, ul_oi2cr, buf), "cols_lr_ul_oi2cr"

    # upper right
    def ur_oi2cr(offset, maski):
        bitcol = bit_cols - 1 - offset % bit_cols
        col = maski * bit_cols + bitcol
        row = offset // bit_cols
        return (col, row)
    yield try_oi2cr(mr, ur_oi2cr, buf), "cols_lr_ur_oi2cr"

def guess_layout_cols_ud(mr, buf):
    # Must be able to divide input
    txtw, txth = mr.txtwh()
    if txtw % mr.word_bits() != 0:
        return
    bit_cols = txtw // mr.word_bits()

    # upper left
    def ul_oi2cr(offset, maski):
        # Start left in bit's column and work rigght
        bitcol = offset // txth
        col = maski * bit_cols + bitcol
        row = offset % txth
        return (col, row)
    yield try_oi2cr(mr, ul_oi2cr, buf), "cols_ul_oi2cr"

    # upper right
    def ur_oi2cr(offset, maski):
        # Start right in bit's column and work left
        bitcol = bit_cols - offset // txth - 1
        col = maski * bit_cols + bitcol
        row = offset % txth
        return (col, row)
    yield try_oi2cr(mr, ur_oi2cr, buf), "cols_ur_oi2cr"

def guess_layout(txtdict_raw, wraw, hraw, word_bits):
    for invert in (0, 1):
        for rotate in 0, 90, 180, 270:
            # only one flip is needed
            # Second would cancel out / redundant with rotate
            for flipx in (0, 1):
                print("rotate %u, flipx %u" % (rotate, flipx))
                txtdict, txtw, txth = mrom.td_rotate2(rotate, txtdict_raw, wraw, hraw)
                if flipx:
                    txtdict = mrom.td_flipx(txtdict, txtw, txth)
                if invert:
                    txtdict = mrom.td_invert(txtdict, txtw, txth)
                
                txtbuf = mrom.ret_txt(txtdict, txtw, txth)
                mr = gen_mr(txtw, txth, word_bits)
                for layout in guess_layout_cols_lr(mr, txtbuf):
                    yield layout
                for layout in guess_layout_cols_ud(mr, txtbuf):
                    yield layout

def gen_mr(txtw, txth, word_bits):
    class SolverMaskROM(mrom.MaskROM):
        def __init__(self, verbose=False):
            self.verbose = verbose
    
            # Actual bits of a loaded ROM
            # Canonically stored as the binary itself
            self.binary = None
            # Allows converting between txt and binary space
            self.map_cr2woi = None

        def desc(self):
            return 'Solver'
    
        def word_bits(self):
            return word_bits

        def txtwh(self):
            return txtw, txth

        def oi2cr(self, offset, maski):
            assert 0, "Required"
    return SolverMaskROM()

def run(fn_in,
        dir_out=None,
        verbose=False):
    word_bits = 8
    # address: (expect, mask)
    ref_words = {
        0x00: (0x31, 0xFF),
        0x01: (0xfe, 0xFF),
        0x02: (0xff, 0xFF),
        }

    txtin, win, hin = mrom.load_txt(open(fn_in, "r"), None, None)
    print("Loaded %ux x %u h" % (win, hin))

    txtdict = mrom.txt2dict(txtin, win, hin)
    tryi = 0
    best_score = 0.0
    best_algo_info = None
    exact_matches = []
    for guess_bin, algo_info in guess_layout(txtdict, win, hin, word_bits):
        exact_match, score = check_binary(guess_bin, ref_words)
        print("%u match %s, score %0.3f" % (tryi, exact_match, score))
        print("  %s" % algo_info)
        if score > best_score:
            best_score = score
            best_algo_info = algo_info
        if exact_match:
            exact_matches.append((algo_info, guess_bin))
        tryi += 1
    print("")
    print("Best score: %0.3f, %s" % (best_score, best_algo_info))
    print("Exact matches: %s" % len(exact_matches))

    if dir_out and len(exact_matches):
        if not os.path.exists(dir_out):
            os.mkdir(dir_out)
        for algo_info, guess_bin in exact_matches:
            fn_out = os.path.join(dir_out, algo_info + ".bin")
            print("  Writing %s" % fn_out)
            open(fn_out, "wb").write(guess_bin)

def list_arch():
    for a in arch2mr.keys():
        print(a)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Guess mask ROM layout based on constraints')
    parser.add_argument('--verbose', action='store_true', help='')
    parser.add_argument('fn_in', help='.txt file in')
    parser.add_argument('dir_out', nargs='?', help='Write top .bin file')
    args = parser.parse_args()

    run(args.fn_in,
        args.dir_out,
        verbose=args.verbose)
