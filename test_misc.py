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
        matches = solver.run("test/lr35902.txt",
            solver.parse_ref_words("0x55,0x5a,0xb4"),
            None,
            verbose=False)
        assert len(matches) == 1


if __name__ == "__main__":
    unittest.main()  # run all tests
