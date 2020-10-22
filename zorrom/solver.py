from zorrom.archs import arch2mr
from zorrom import mrom
import os


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


def guess_layout_cols_lr(mr, buf, alg_prefix):
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

    yield try_oi2cr(mr, ul_oi2cr, buf), alg_prefix + "cols-right"

    # upper right
    def ur_oi2cr(offset, maski):
        bitcol = bit_cols - 1 - offset % bit_cols
        col = maski * bit_cols + bitcol
        row = offset // bit_cols
        return (col, row)

    yield try_oi2cr(mr, ur_oi2cr, buf), alg_prefix + "cols-left"


def guess_layout_cols_ud(mr, buf, alg_prefix):
    # Must be able to divide input
    txtw, txth = mr.txtwh()
    if txtw % mr.word_bits() != 0:
        return
    bit_cols = txtw // mr.word_bits()

    # upper left
    def ul_oi2cr(offset, maski):
        # Start left in bit's column and work right
        bitcol = offset // txth
        col = maski * bit_cols + bitcol
        row = offset % txth
        return (col, row)

    yield try_oi2cr(mr, ul_oi2cr, buf), alg_prefix + "cols-downl"

    # upper right
    def ur_oi2cr(offset, maski):
        # Start right in bit's column and work left
        bitcol = bit_cols - offset // txth - 1
        col = maski * bit_cols + bitcol
        row = offset % txth
        return (col, row)

    yield try_oi2cr(mr, ur_oi2cr, buf), alg_prefix + "cols-downr"


def guess_layout(txtdict_raw, wraw, hraw, word_bits, verbose=False):
    for invert in (0, 1):
        for rotate in 0, 90, 180, 270:
            # only one flip is needed
            # Second would cancel out / redundant with rotate
            for flipx in (0, 1):
                verbose and print("rotate %u, flipx %u" % (rotate, flipx))
                txtdict, txtw, txth = mrom.td_rotate2(rotate, txtdict_raw,
                                                      wraw, hraw)
                if flipx:
                    txtdict = mrom.td_flipx(txtdict, txtw, txth)
                if invert:
                    txtdict = mrom.td_invert(txtdict, txtw, txth)

                alg_prefix = "r-%u_flipx-%u_invert-%u_" % (rotate, flipx,
                                                           invert)
                txtbuf = mrom.ret_txt(txtdict, txtw, txth)
                mr = gen_mr(txtw, txth, word_bits)
                for layout in guess_layout_cols_lr(mr, txtbuf, alg_prefix):
                    yield layout
                for layout in guess_layout_cols_ud(mr, txtbuf, alg_prefix):
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


def parse_ref_words(argstr):
    # address: (expect, mask)
    """
    All three of thse are equivilent:
    ./solver.py --bytes 0x31,0xfe,0xff dmg-cpu/rom.txt
    ./solver.py --bytes 0x00:0x31,0x01:0xfe,0x02:0xff dmg-cpu/rom.txt
    ./solver.py --bytes 0x00:0x31:0xFF,0x01:0xfe:0xFF,0x02:0xff:0xFF dmg-cpu/rom.txt

    Which maps to:
    ref_words = {
        0x00: (0x31, 0xFF),
        0x01: (0xfe, 0xFF),
        0x02: (0xff, 0xFF),
        }
    """

    ret = {}
    auto_addr = 0
    for constraint in argstr.split(","):
        parts = constraint.split(":")
        assert len(parts) <= 3
        # One arg: assume offset and just use value
        if len(parts) == 1:
            offset = auto_addr
            value = int(parts[0], 0)
        # two arg: offset:value
        else:
            offset = int(parts[0], 0)
            value = int(parts[1], 0)
        mask = 0xFF
        # three arg: allow masking value
        if len(parts) >= 3:
            mask = int(parts[2], 0)
        ret[offset] = (value, mask)
        auto_addr += 1
    return ret


def run(fn_in, ref_words, dir_out=None, verbose=False, all=False):
    word_bits = 8

    if all:
        ref_words = {}

    txtin, win, hin = mrom.load_txt(open(fn_in, "r"), None, None)
    verbose and print("Loaded %ux x %u h" % (win, hin))

    txtdict = mrom.txt2dict(txtin, win, hin)
    tryi = 0
    best_score = 0.0
    best_algo_info = None
    keep_matches = []
    for guess_bin, algo_info in guess_layout(txtdict,
                                             win,
                                             hin,
                                             word_bits,
                                             verbose=verbose):
        exact_match = None
        if not all:
            exact_match, score = check_binary(guess_bin, ref_words)
            verbose and print("%u match %s, score %0.3f" %
                              (tryi, exact_match, score))
            verbose and print("  %s" % algo_info)
            if score > best_score:
                best_score = score
                best_algo_info = algo_info
        if exact_match or all:
            keep_matches.append((algo_info, guess_bin))
        tryi += 1
    verbose and print("")
    print("Best score: %0.3f, %s" % (best_score, best_algo_info))
    print("Keep matches: %s" % len(keep_matches))

    if dir_out and len(keep_matches):
        if not os.path.exists(dir_out):
            os.mkdir(dir_out)
        for algo_info, guess_bin in keep_matches:
            fn_out = os.path.join(dir_out, algo_info + ".bin")
            print("  Writing %s" % fn_out)
            open(fn_out, "wb").write(guess_bin)

    return keep_matches
