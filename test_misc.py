#!/usr/bin/env python3

import unittest
import os
import io
import warnings

from zorrom.archs import arch2mr
from zorrom import solver
from zorrom.util import hexdump


def check_bin(ref, got, msg):
    # print(type(got), len(got), type(ref), len(ref))
    if ref != got:
        if 1 and got[0:32] != ref[0:32]:
            dump_got = got[0:32]
            dump_ref = ref[0:32]
        else:
            dump_got = got
            dump_ref = ref
        hexdump(dump_ref, "Ref")
        hexdump(dump_got, "Got")
        open("test/got.bin", "wb").write(got)
        open("test/ref.bin", "wb").write(ref)
        assert 0, msg


class TestCase(unittest.TestCase):
    def setUp(self):
        """Call before every test case."""
        print("")
        print("")
        print(self._testMethodName)
        warnings.simplefilter("ignore", ResourceWarning)

    def tearDown(self):
        """Call after every test case."""
        pass

    def test_txt2bin(self):
        for arch in arch2mr.keys():
            print("arch %s" % arch)
            mrc = arch2mr[arch]
            f_in = open("test/%s.txt" % arch, 'r')
            f_out = io.BytesIO()
            mr = mrc()
            got = mr.txt2bin(f_in, f_out)
            ref = open("test/%s.bin" % arch, 'rb').read()
            check_bin(ref, got, arch)

    def test_bin2txt(self):
        for arch in arch2mr.keys():
            print("arch %s" % arch)
            mrc = arch2mr[arch]
            f_in = open("test/%s.bin" % arch, 'rb')
            f_out = io.StringIO()

            mr = mrc()
            mr.bin2txt(f_in, f_out, defchar="0")

            ref = open("test/%s.txt" % arch, 'r').read()
            got = f_out.getvalue()
            # todo: consider being more strict on formatting
            got = got.translate(str.maketrans('', '', ' \n\t\r'))
            ref = ref.translate(str.maketrans('', '', ' \n\t\r'))
            open("test/got.txt", "w").write(got)
            open("test/ref.txt", "w").write(ref)
            assert ref == got, arch

    def test_solver(self):
        """non-constrained solver test"""
        matches, _tries = solver.run(
            "test/lr35902.txt",
            ref_words=solver.parse_ref_words("0x55,0x5a,0xb4"),
            dir_out=None,
            verbose=False)
        assert len(matches) == 1, len(matches)
        for match in matches:
            assert match["bytes"] == open("test/lr35902.bin", "rb").read()

    def test_solver_interleave(self):
        """non-constrained interleave test"""
        matches, _tries = solver.run(
            "test/lc5800.txt",
            ref_words=solver.parse_ref_words("0xc5,0x5c,0xaf"),
            dir_out=None,
            interleave_force=0,
            invert_force=True,
            flipx_force=True,
            rotate_force=0,
            layout_alg_force="cols-left",
            verbose=False)
        assert len(matches) == 1, len(matches)
        for match in matches:
            assert match["bytes"] == open("test/lc5800.bin", "rb").read()

    def solver_assert(self,
                      arch,
                      ref_indexes=None,
                      txt_in=None,
                      ref_words=None,
                      **kwargs):
        ref_bin = open("test/%s.bin" % arch, "rb").read()
        if ref_words is None:
            if ref_indexes is None:
                ref_indexes = [0, 1, 2]
            ref_words = solver.parse_ref_words(",".join(
                ["%u:0x%02x" % (x, ref_bin[x]) for x in ref_indexes]))
        if txt_in is None:
            txt_in = "test/%s.txt" % arch
        matches, tries = solver.run(txt_in,
                                    ref_words=ref_words,
                                    dir_out=None,
                                    verbose=False,
                                    **kwargs)
        assert tries == 1, tries
        assert len(matches) == 1, len(matches)
        for match in matches:
            # open("1.bin", "wb").write(match["bytes"])
            # open("2.bin", "wb").write(ref_bin)
            assert match["bytes"] == ref_bin

    def test_solvers(self):
        """Use solver (with hints to make it quick) to solve known layouts"""

        # FIXME: only partially correct
        # mirrors halfway through
        if 0:
            # python3 solver.py --invert --flipx --interleave 1 --rotate 180 --layout-alg cols-downl --bytes 0:0x84,1:0xFF,1022:0x7c,1023:0x18 test/d8041ah.txt
            # Best score: 1.000, r-180_flipx-1_invert-1_inverleave-lr-1_cols-downl
            self.solver_assert(
                "d8041ah",
                # Truncate bottom rows
                txt_in="test/d8041ah_roi.txt",
                # ref_indexes=[0x00, 0x01, 1022, 1023],
                ref_indexes=[0x00, 0x01],
                rotate_force=180,
                flipx_force=True,
                invert_force=True,
                interleave_force=1,
                layout_alg_force="cols-downl",
            )

        # python3 solver.py --bytes 0xc5,0x5c --interleave 0 test/lc5800.txt
        # Best score: 1.000, r-0_flipx-1_invert-1_inverleave-lr-16_cols-left
        self.solver_assert(
            "lc5800",
            rotate_force=0,
            flipx_force=True,
            invert_force=True,
            interleave_force=2,
            interleave_dir_force="r",
            layout_alg_force="cols-left",
        )

        # python3 solver.py --bytes 0x55,0x5a test/lr35902.txt
        # Best score: 1.000, r-180_flipx-1_invert-0_inverleave-lr-1_cols-downr
        self.solver_assert(
            "lr35902",
            rotate_force=180,
            flipx_force=True,
            invert_force=False,
            interleave_force=1,
            layout_alg_force="cols-downr",
        )

        # python3 solver.py --bytes 0x1c,0xee test/m5l8042.txt
        # Best score: 1.000, r-180_flipx-0_invert-0_inverleave-lr-1_cols-left
        self.solver_assert(
            "m5l8042",
            rotate_force=180,
            flipx_force=False,
            invert_force=False,
            interleave_force=1,
            layout_alg_force="cols-left",
        )

        # python3 solver.py --bytes 0x3f,0x0b --interleave 4 test/mb8623x.txt
        # Best score: 1.000, r-270_flipx-0_invert-1_inverleave-lr-4_cols-right
        self.solver_assert(
            "mb8623x",
            rotate_force=270,
            flipx_force=False,
            invert_force=True,
            interleave_force=4,
            interleave_dir_force="r",
            layout_alg_force="cols-right",
        )

        # pic1670
        # Unsolvable, needs new algorithm

        # python3 solver.py --bytes 0xd2,0x21,0xc6 test/tms32010.txt
        # Unsolvable: obfuscated

        # python3 solver.py --layout-alg squeeze-lr --bytes 0x9c6d --no-invert --flipx --interleave 1 --rotate 0 --word-bits 16 test/tms320c15.txt
        # Best score: 1.000, r-0_flipx-1_invert-0_inverleave-lr-1_squeeze-lr
        self.solver_assert(
            "tms320c15",
            word_bits=16,
            endian_force="big",
            ref_words=solver.parse_ref_words("0:0x9c6d"),
            rotate_force=0,
            flipx_force=True,
            invert_force=False,
            interleave_force=1,
            layout_alg_force="squeeze-lr",
        )


if __name__ == "__main__":
    unittest.main()  # run all tests
