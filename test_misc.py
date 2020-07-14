#!/usr/bin/env python3

import unittest
import os
import io

from zorrom.archs import arch2mr


class TestCase(unittest.TestCase):
    def setUp(self):
        """Call before every test case."""
        pass

    def tearDown(self):
        """Call after every test case."""
        pass

    def test_mb8623x_txt2bin(self):
        mrc = arch2mr["mb8623x"]
        f_in = open("test/mb8623x.txt", 'r')
        f_out = io.BytesIO()
        mr = mrc()
        got = mr.txt2bin(f_in, f_out)
        ref = open("test/mb8623x.bin", 'rb').read()
        assert ref == got

    def test_mb8623x_bin2txt(self):
        mrc = arch2mr["mb8623x"]
        f_in = open("test/mb8623x.bin", 'rb')
        f_out = io.StringIO()

        mr = mrc()
        mr.bin2txt(f_in, f_out)

        ref = open("test/mb8623x.txt", 'r').read()
        got = f_out.getvalue()
        assert ref == got


if __name__ == "__main__":
    unittest.main()  # run all tests
