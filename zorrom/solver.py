from zorrom.archs import arch2mr
from zorrom import mrom
import os
import math


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
    mr.calc_oi2cr = func
    mr.reindex()
    ret = mr.txt2bin_buf(buf)
    mr.calc_oi2cr = old
    return ret


def guess_layout_cols_lr(mr,
                         buf,
                         alg_prefix,
                         layout_alg_force=None,
                         verbose=False):
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
        verbose and "guess_layout_cols_lr: bad width"
        return
    bit_cols = txtw // mr.word_bits()

    # upper left start moving right
    def ul_oi2cr(offset, maski):
        bitcol = offset % bit_cols
        col = maski * bit_cols + bitcol
        row = offset // bit_cols
        return (col, row)

    name = "cols-right"
    if layout_alg_force is None or layout_alg_force == name:
        yield try_oi2cr(mr, ul_oi2cr, buf), alg_prefix + name

    # upper right start moving left
    def ur_oi2cr(offset, maski):
        bitcol = bit_cols - 1 - offset % bit_cols
        col = maski * bit_cols + bitcol
        row = offset // bit_cols
        return (col, row)

    name = "cols-left"
    if layout_alg_force is None or layout_alg_force == name:
        yield try_oi2cr(mr, ur_oi2cr, buf), alg_prefix + name


def guess_layout_cols_ud(mr,
                         buf,
                         alg_prefix,
                         layout_alg_force=None,
                         verbose=False):
    # Must be able to divide input
    txtw, txth = mr.txtwh()
    if txtw % mr.word_bits() != 0:
        verbose and print("guess_layout_cols_ud: bad width")
        return
    bit_cols = txtw // mr.word_bits()

    # upper left moving down
    def ul_oi2cr(offset, maski):
        # Start left in bit's column and work right
        bitcol = offset // txth
        col = maski * bit_cols + bitcol
        row = offset % txth
        return (col, row)

    name = "cols-downl"
    if layout_alg_force is None or layout_alg_force == name:
        yield try_oi2cr(mr, ul_oi2cr, buf), alg_prefix + name

    # upper right moving down
    def ur_oi2cr(offset, maski):
        # Start right in bit's column and work left
        bitcol = bit_cols - offset // txth - 1
        col = maski * bit_cols + bitcol
        row = offset % txth
        return (col, row)

    name = "cols-downr"
    if layout_alg_force is None or layout_alg_force == name:
        yield try_oi2cr(mr, ur_oi2cr, buf), alg_prefix + name


def td_interleave_lr(txtdict, txtw, txth, interleaves, word_bits=8, verbose=0):
    """
    Interleave left/right
    
    interleaves must be 1, 2, 4, 8, etc
    
    interleaves=2, wordsz=8 like:
    B0 B1 B2 B3 B4 B5 B6 B7 B0 B1 B2 B3 B4 B5 B6 B7
    B0 B1 B2 B3 B4 B5 B6 B7 B0 B1 B2 B3 B4 B5 B6 B7
    B0 B1 B2 B3 B4 B5 B6 B7 B0 B1 B2 B3 B4 B5 B6 B7
    ...
    
    That is the first row has word and left and another distinct word at right
    where bit columns have now been split        
    """
    # Must be a boundary we can split on
    assert txtw % (interleaves * word_bits) == 0, (txtw, interleaves,
                                                   word_bits)

    # Width of each interleave section including all bits
    word_intw = txtw // interleaves
    # Width of each bit's interleave section
    bit_intw = txtw // (interleaves * word_bits)
    # No interleaving => evenly divided
    bit_dstw = txtw // word_bits

    verbose and print("in %uw x %uh" % (txtw, txth))
    verbose and print("interleaves %u, word_bits %u" %
                      (interleaves, word_bits))
    verbose and print("word_intw: %u, bit_intw: %u, bit_dstw: %u" %
                      (word_intw, bit_intw, bit_dstw))

    ret = {}
    for biti in range(word_bits):
        for inti in range(interleaves):
            for x0 in range(bit_intw):
                # Source is interleaved
                # Source moves left/right, skipping to next interleave when word_intw exhausted
                xin = inti * word_intw + biti * bit_intw + x0
                # Destination is not interleaved
                # First word from left interleave block, second word from second interleave block, etc
                # each from the first column
                # Then process repeats at second column for each interleave
                # Once all columnms are exhausted moves to next row
                # xout = biti * bit_dstw + inti * bit_intw + x0
                xout = biti * bit_dstw + x0 * interleaves + inti
                for y in range(txth):
                    assert (xout, y) not in ret, (xout, y)
                    ret[(xout, y)] = txtdict[(xin, y)]
                    if verbose and inti == 0 and x0 == 1 and y == 0:
                        print(
                            "biti=%u, inti=%u, x0=%u  (%ux, %uy) => (%ux, %uy)"
                            % (biti, inti, x0, xin, y, xout, y))

    for x in range(txtw):
        for y in range(txth):
            assert (x, y) in ret, (x, y)

    return ret


def guess_layout(txtdict_raw,
                 wraw,
                 hraw,
                 word_bits=8,
                 words=None,
                 invert_force=None,
                 rotate_force=None,
                 flipx_force=None,
                 interleave_force=1,
                 layout_alg_force=None,
                 verbose=False):
    verbose and print("guess_layout()")

    if layout_alg_force:
        algs = ("cols-left", "cols-right", "cols-downl", "cols-downr")
        assert layout_alg_force in algs, "Got %s, need one of %s" % (
            layout_alg_force, algs)

    if invert_force is not None:
        invert_gen = (invert_force, )
    else:
        invert_gen = (0, 1)
    for invert in invert_gen:
        if rotate_force is not None:
            rotate_gen = (rotate_force, )
        else:
            rotate_gen = (0, 90, 180, 270)
        for rotate in rotate_gen:
            # only one flip is needed
            # Second would cancel out / redundant with rotate
            if flipx_force is not None:
                flipx_force_gen = (flipx_force, )
            else:
                flipx_force_gen = (0, 1)
            for flipx in flipx_force_gen:
                verbose and print("rotate %u, flipx %u" % (rotate, flipx))
                txtdict, txtw, txth = mrom.td_rotate2(rotate, txtdict_raw,
                                                      wraw, hraw)

                def div2s_tmp(n):
                    ret = 0
                    while True:
                        if n % 2 != 0:
                            return ret
                        else:
                            n = n // 2
                            ret += 1

                if txtw % word_bits != 0:
                    verbose and print("rotate %u: bad width" % rotate)
                    continue
                if interleave_force:
                    # assert interleave_force <= interleave_maxn
                    interleave_lr_gen = (interleave_force, )
                # Default 1 => don't interleave
                else:
                    # interleave_max = txtw // word_bits
                    # interleave_maxn = int(math.log(interleave_max, 2))
                    interleave_maxn = div2s_tmp(txtw // word_bits)
                    # print(txtw, interleave_maxn)
                    # print("interleave %u => %u max " % (txtw, interleave_maxn))
                    # print("txtw=%u, interleave_max: %u (n=%u)" % (txtw, interleave_max, interleave_maxn))
                    interleave_lr_gen = [
                        1 << x for x in range(0, interleave_maxn + 1)
                    ]
                interleave_lr_gen = list(interleave_lr_gen)
                if len(interleave_lr_gen) == 0:
                    verbose and print("interleave failed")
                    continue
                for interleave_lr in interleave_lr_gen:
                    # print("int %u, %u" % (interleave_lr, interleave_lr_exp))
                    # assert interleave_lr <= interleave_max
                    # print("interleave %u => %u" % (txtw, interleave_lr))

                    if flipx:
                        txtdict = mrom.td_flipx(txtdict, txtw, txth)
                    if invert:
                        txtdict = mrom.td_invert(txtdict, txtw, txth)

                    if interleave_lr != 1:
                        txtdict = td_interleave_lr(txtdict,
                                                   txtw,
                                                   txth,
                                                   interleave_lr,
                                                   word_bits=word_bits,
                                                   verbose=verbose)

                    alg_prefix = "r-%u_flipx-%u_invert-%u_inverleave-lr-%u_" % (
                        rotate, flipx, invert, interleave_lr)
                    verbose and print("Trying %s" % alg_prefix)
                    txtbuf = mrom.ret_txt(txtdict, txtw, txth)
                    mr = gen_mr(txtw, txth, word_bits)
                    for layout, name in guess_layout_cols_lr(mr,
                                                             txtbuf,
                                                             alg_prefix,
                                                             layout_alg_force,
                                                             verbose=verbose):
                        yield layout, name
                    for layout, name in guess_layout_cols_ud(mr,
                                                             txtbuf,
                                                             alg_prefix,
                                                             layout_alg_force,
                                                             verbose=verbose):
                        yield layout, name


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

        def get_oi2cr(self, offset, maski):
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


def run(fn_in,
        ref_words,
        dir_out=None,
        verbose=False,
        all=False,
        invert_force=None,
        rotate_force=None,
        flipx_force=None,
        interleave_force=1,
        write_thresh=1.0,
        word_bits=8,
        words=None,
        layout_alg_force=None):

    txtin, win, hin = mrom.load_txt(open(fn_in, "r"), None, None)

    txtbits = win * hin
    print("Loaded %ux x %u h => %u bits (%u words)" %
          (win, hin, txtbits, txtbits // word_bits))
    if txtbits % word_bits != 0:
        print("Invalid geometery: got %uw x %uh => %u bits w/ word size %u" %
              (win, hin, txtbits, word_bits))
        return
    if words is not None and txtbits // word_bits != words:
        print("Invalid geometery: need %u words but txt has %u words" %
              (word_bits, txtbits // word_bits))
        return

    txtdict = mrom.txt2dict(txtin, win, hin)
    tryi = 0
    best_score = 0.0
    best_algo_info = None
    keep_matches = []
    for guess_bin, algo_info in guess_layout(txtdict,
                                             win,
                                             hin,
                                             word_bits=word_bits,
                                             invert_force=invert_force,
                                             rotate_force=rotate_force,
                                             flipx_force=flipx_force,
                                             interleave_force=interleave_force,
                                             layout_alg_force=layout_alg_force,
                                             words=words,
                                             verbose=verbose):
        exact_match = None
        score = None
        keep = all
        if ref_words:
            exact_match, score = check_binary(guess_bin, ref_words)
            keep = keep or exact_match or write_thresh and score >= write_thresh
            if verbose or keep:
                print("%u match %s, score %0.3f" % (tryi, exact_match, score))
                print("  %s" % algo_info)
            if score > best_score:
                best_score = score
                best_algo_info = algo_info
        if keep:
            keep_matches.append((algo_info, guess_bin))
        tryi += 1
    verbose and print("")
    print("Tries: %u" % tryi)
    print("Best score: %0.3f, %s" % (best_score, best_algo_info))
    print("Keep matches: %s" % len(keep_matches))

    if dir_out and len(keep_matches):
        if not os.path.exists(dir_out):
            os.mkdir(dir_out)
        for algo_info, guess_bin in keep_matches:
            fn_out = os.path.join(dir_out, algo_info + ".bin")
            print("  Writing %s" % fn_out)
            open(fn_out, "wb").write(guess_bin)

    return keep_matches, tryi
