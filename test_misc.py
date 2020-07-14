#!/usr/bin/env python3

import unittest
import os
import io
import warnings

from zorrom.archs import arch2mr


class TestCase(unittest.TestCase):
    def setUp(self):
        """Call before every test case."""
        warnings.simplefilter("ignore", ResourceWarning)

    def tearDown(self):
        """Call after every test case."""
        pass

    def test_txt2bin(self):
        for arch in arch2mr.keys():
            print("")
            print("arch %s" % arch)
            if arch == "pic1670":
                print('fixme')
                continue
            mrc = arch2mr[arch]
            f_in = open("test/%s.txt" % arch, 'r')
            f_out = io.BytesIO()
            mr = mrc()
            got = mr.txt2bin(f_in, f_out)
            ref = open("test/%s.bin" % arch, 'rb').read()
            assert ref == got, arch

    def test_bin2txt(self):
        for arch in arch2mr.keys():
            print("")
            print("arch %s" % arch)
            if arch == "pic1670":
                print('fixme')
                continue
            mrc = arch2mr[arch]
            f_in = open("test/%s.bin" % arch, 'rb')
            f_out = io.StringIO()

            mr = mrc()
            mr.bin2txt(f_in, f_out, defchar="0")

            ref = open("test/%s.txt" % arch, 'r').read()
            got = f_out.getvalue()
            assert ref == got, arch


if __name__ == "__main__":
    unittest.main()  # run all tests
