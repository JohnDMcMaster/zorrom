from zorrom.archs import arch2mr
from zorrom import mrom
import os
import math


def check_binary(can_words, ref_words, word_bits, verbose=False):
    """
    Return exact_match, score 0-1
    """
    #bits = len(candidate) * word_bits
    checks = 0
    matches = 0
    for wordi, (expect, mask) in ref_words.items():
        got = can_words[wordi]
        verbose and print("word %u want 0x%04X got 0x%04X" %
                          (wordi, expect, got))
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


def try_oi2cr(mr, func, buf, verbose=False):
    old = mr.oi2cr
    mr.calc_oi2cr = func
    mr.reindex()
    words = mr.txt2words_buf(buf)
    verbose and print("got words 0x%04X" % (words[0]))
    bytes = mr.words2bytes(words)
    verbose and print("got bytes 0x%02X 0x%02X" % (bytes[0], bytes[1]))
    mr.calc_oi2cr = old
    return words, bytes


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

    # Used in TMS320C15
    # even bits start from left side, odd bits from right
    # Basically alternating cols-right and cols-left
    # they move towards each other and then start again on the next line
    if mr.word_bits() % 2 == 0:

        def squeeze_lr_oi2cr(offset, maski):
            left_bit = maski & 0xFFFE
            if maski % 2 == 0:
                # cols-right
                bitcol = offset % bit_cols
            else:
                # cols-left (offset by left_bit)
                bitcol = 2 * bit_cols - 1 - offset % bit_cols
            col = left_bit * bit_cols + bitcol
            row = offset // bit_cols
            return (col, row)

        name = "squeeze-lr"
        if layout_alg_force is None or layout_alg_force == name:
            yield try_oi2cr(mr, squeeze_lr_oi2cr, buf), alg_prefix + name


def guess_layout_cols_ud(mr,
                         buf,
                         alg_prefix,
                         layout_alg_force=None,
                         verbose=False):
    # Must be able to divide input
    txtw, txth = mr.txtwh()
    if txth % mr.word_bits() != 0:
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


def td_interleave_hor(txtdict,
                      txtw,
                      txth,
                      interleaves,
                      interleave_dir,
                      word_bits=8,
                      verbose=0):
    """
    Interleave left/right
    interleaves must be 1, 2, 4, 8, etc

    Example, given:
    W0A W1A W2A W3A W0B W1B W2B W3B
    interleaves=2, wordsz=4 interleave_dir=r becomes:
    W0A W0B W1A W1B W2A W2B W3A W3B
    interleaves=2, wordsz=4 interleave_dir=l like:
    W0B W0A W1B W1A W2B W2A W3B W3A
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
                if interleave_dir == "r":
                    # lowest address at left and then moves right
                    xin = inti * word_intw + biti * bit_intw + x0
                elif interleave_dir == "l":
                    # lowest address at right and then moves left
                    xin = (interleaves - inti -
                           1) * word_intw + biti * bit_intw + x0
                else:
                    assert 0, interleave_dir

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


def interleave_param_gen(interleave_force, interleave_dir_force, txtw,
                         word_bits, verbose):
    def div2s_tmp(n):
        ret = 0
        while True:
            if n % 2 != 0:
                return ret
            else:
                n = n // 2
                ret += 1

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
        interleave_lr_gen = [1 << x for x in range(0, interleave_maxn + 1)]
    interleave_lr_gen = list(interleave_lr_gen)
    if len(interleave_lr_gen) == 0:
        verbose and print("interleave failed")
        return

    if interleave_dir_force is None:
        interleave_dir_gen = ("r", "l")
    else:
        interleave_dir_gen = (interleave_dir_force, )

    for interleave in interleave_lr_gen:
        for interleave_dir in interleave_dir_gen:
            yield (interleave, interleave_dir)
            if interleave == 1:
                break


def basic_param_gen(invert_force, rotate_force, flipx_force):
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
                yield invert, rotate, flipx


import hashlib


def hashdbg(s):
    print("Hash", hashlib.sha1(str(s).encode("ascii")).hexdigest())


def guess_layout(txtdict_raw,
                 wraw,
                 hraw,
                 word_bits=8,
                 endian_force=None,
                 words=None,
                 invert_force=None,
                 rotate_force=None,
                 flipx_force=None,
                 interleave_force=1,
                 interleave_dir_force=None,
                 layout_alg_force=None,
                 verbose=False):
    verbose and print("guess_layout()")
    # hashdbg(txtdict_raw)
    # print(txtdict_raw[(75, 4)])
    # assert 0

    if layout_alg_force:
        algs = ("cols-left", "cols-right", "cols-downl", "cols-downr",
                "squeeze-lr")
        assert layout_alg_force in algs, "Got %s, need one of %s" % (
            layout_alg_force, algs)

    for invert, rotate, flipx in basic_param_gen(invert_force, rotate_force,
                                                 flipx_force):
        verbose and print("rotate %u, flipx %u" % (rotate, flipx))

        txtdict_rotated, txtw, txth = mrom.td_rotate2(rotate, txtdict_raw,
                                                      wraw, hraw)

        if txtw % word_bits != 0:
            verbose and print("rotate %u: bad width" % rotate)
            continue

        for interleaves_hor, interleave_dir in interleave_param_gen(
                interleave_force, interleave_dir_force, txtw, word_bits,
                verbose):
            txtdict = dict(txtdict_rotated)

            # print("int %u, %u" % (interleave_lr, interleave_lr_exp))
            # assert interleave_lr <= interleave_max
            # print("interleave %u => %u" % (txtw, interleave_lr))

            if flipx:
                txtdict = mrom.td_flipx(txtdict, txtw, txth)
            if invert:
                txtdict = mrom.td_invert(txtdict, txtw, txth)

            interleave_str = ""
            if interleaves_hor != 1:
                txtdict = td_interleave_hor(txtdict,
                                            txtw,
                                            txth,
                                            interleaves=interleaves_hor,
                                            interleave_dir=interleave_dir,
                                            word_bits=word_bits,
                                            verbose=verbose)
                interleave_str = "_inverleave-%s-%u" % (interleave_dir,
                                                        interleaves_hor)

            alg_prefix = "r-%u_flipx-%u_invert-%u%s_" % (rotate, flipx, invert,
                                                         interleave_str)
            verbose and print("Trying %s" % alg_prefix)
            gcols = range(word_bits, txtw, word_bits)
            txtbuf = mrom.ret_txt(txtdict, txtw, txth, gcols=gcols)
            mr = gen_mr(txtw, txth, word_bits, endian=endian_force)
            for layout, name in guess_layout_cols_lr(mr,
                                                     txtbuf,
                                                     alg_prefix,
                                                     layout_alg_force,
                                                     verbose=verbose):
                yield layout, name, txtbuf
            for layout, name in guess_layout_cols_ud(mr,
                                                     txtbuf,
                                                     alg_prefix,
                                                     layout_alg_force,
                                                     verbose=verbose):
                yield layout, name, txtbuf


def gen_mr(txtw, txth, word_bits, endian):
    if endian is None:
        endian = "byte"

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

        def endian(self):
            return endian

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
    if argstr == "":
        return ret
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
        bin_out=None,
        txt_out=None,
        verbose=False,
        all=False,
        invert_force=None,
        rotate_force=None,
        flipx_force=None,
        interleave_force=1,
        interleave_dir_force=None,
        write_thresh=1.0,
        word_bits=8,
        endian_force=None,
        words=None,
        layout_alg_force=None):

    # verbose = True
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

    # hashdbg(txtin)
    txtdict = mrom.txt2dict(txtin, win, hin)
    tryi = 0
    best_score = 0.0
    best_algo_info = None
    keep_matches = []
    for (can_words, can_bytes), algo_info, txt_base in guess_layout(
            txtdict,
            win,
            hin,
            word_bits=word_bits,
            endian_force=endian_force,
            invert_force=invert_force,
            rotate_force=rotate_force,
            flipx_force=flipx_force,
            interleave_force=interleave_force,
            interleave_dir_force=interleave_dir_force,
            layout_alg_force=layout_alg_force,
            words=words,
            verbose=verbose):
        # assert type(can_bytes) == bytearray, type(can_bytes)
        exact_match = None
        score = None
        keep = all
        if ref_words:
            exact_match, score = check_binary(can_words, ref_words, word_bits)
            keep = keep or exact_match or write_thresh and score >= write_thresh
            if verbose or keep:
                print("%u match %s, score %0.3f" % (tryi, exact_match, score))
                print("  %s" % algo_info)
            if score > best_score:
                best_score = score
                best_algo_info = algo_info
        if keep:
            keep_matches.append({
                "algorithm": algo_info,
                "bytes": can_bytes,
                "can_words": words,
                "txt_base": txt_base
            })
        tryi += 1
    verbose and print("")
    print("Tries: %u" % tryi)
    print("Best score: %0.3f, %s" % (best_score, best_algo_info))
    print("Keep matches: %s" % len(keep_matches))

    if dir_out and len(keep_matches):
        if not os.path.exists(dir_out):
            os.mkdir(dir_out)
        for keep_match in keep_matches:
            fn_out = os.path.join(dir_out, keep_match["algorithm"] + ".bin")
            print("  Writing %s" % fn_out)
            open(fn_out, "wb").write(keep_match["bytes"])

    if bin_out is not None:
        assert len(keep_matches) == 1, len(keep_matches)
        for keep_match in keep_matches:
            print("  Writing %s" % (bin_out, ))
            open(bin_out, "wb").write(keep_match["bytes"])

    if txt_out is not None:
        assert len(keep_matches) == 1, len(keep_matches)
        for keep_match in keep_matches:
            print("  Writing %s" % (txt_out, ))
            open(txt_out, "w").write(keep_match["txt_base"])

    return keep_matches, tryi
