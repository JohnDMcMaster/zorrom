#!/usr/bin/env python3

import unittest
import os
import io
import warnings

from zorrom.archs import arch2mr
from zorrom import solver


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
            # print(type(got), len(got), type(ref), len(ref))
            open("test/got.bin", "wb").write(got)
            open("test/ref.bin", "wb").write(ref)
            assert ref == got, arch

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
        matches, _tries = solver.run(
            "test/lr35902.txt",
            ref_words=solver.parse_ref_words("0x55,0x5a,0xb4"),
            dir_out=None,
            verbose=False)
        assert len(matches) == 1
        for _algo_info, guess_bin in matches:
            assert guess_bin == open("test/lr35902.bin", "rb").read()

    def test_solver_interleave(self):
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
        assert len(matches) == 1
        for _algo_info, guess_bin in matches:
            assert guess_bin == open("test/lc5800.bin", "rb").read()

    def solver_assert(self, arch, **kwargs):
        ref_bin = open("test/%s.bin" % arch, "rb").read()
        matches, tries = solver.run(
            "test/%s.txt" % arch,
            ref_words=solver.parse_ref_words(
                "0x%02x,0x%02x,0x%02x" % (ref_bin[0], ref_bin[1], ref_bin[2])),
            dir_out=None,
            verbose=False,
            **kwargs)
        assert tries == 1, tries
        assert len(matches) == 1, len(matches)
        for _algo_info, guess_bin in matches:
            open("1.bin", "wb").write(guess_bin)
            open("2.bin", "wb").write(ref_bin)
            assert guess_bin == ref_bin

    def test_solvers(self):
        """Use solver (with hints to make it quick) to solve known layouts"""

        # FIXME: only partially correct
        if 0:
            # python3 solver.py --bytes 0x84,0xFF test/d8041ah.txt
            # Best score: 1.000, r-180_flipx-1_invert-1_inverleave-lr-1_cols-downl
            self.solver_assert(
                "d8041ah",
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
            layout_alg_force="cols-right",
        )

        # pic1670
        # Unsolvable, needs new algorithm

        # python3 solver.py --bytes 0xd2,0x21,0xc6 test/tms32010.txt
        # Unsolvable: obfuscated

        # python3 solver.py --bytes 0x9c,0x6d,0xe9 test/tms320c15.txt
        # Unsolvable, needs new algorithm


if __name__ == "__main__":
    unittest.main()  # run all tests
