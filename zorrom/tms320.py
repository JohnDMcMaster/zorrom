from zorrom.util import hexdump
from zorrom import mrom


class TMS320C15(mrom.MaskROM):
    def desc(self):
        return 'TMS320C15'

    def endian(self):
        return "big"

    def word_bits(self):
        return 16

    def words(self):
        return 4096

    def txtwh(self):
        return (128, 512)

    def invert(self):
        return False

    def calc_cr2oi(self, col, row):
        order = [0, 1, 2, 3, 4, 5, 6, 7, 7, 6, 5, 4, 3, 2, 1, 0]
        # out.print((data[i * 8 + order[j & 0xF]] & (1 << (j >> 3))) != 0 ? "1" : 0);
        i = 511 - row
        j = col
        word = i * 8 + order[j & 0xF]
        maski = j >> 3
        return (word, maski)
