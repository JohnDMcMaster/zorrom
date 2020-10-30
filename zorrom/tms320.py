from zorrom.util import hexdump
from zorrom import mrom


class TMS32010(mrom.MaskROM):
    def desc(self):
        return 'TMS32010'

    def endian(self):
        return "big"

    def word_bits(self):
        # return 16
        return 8

    def nwords(self):
        return 1536 * 2

    def txtwh(self):
        return (192, 128)

    def invert(self):
        return False

    def calc_cr2oi(self, col, row):
        #  data[((col & 0xFFC) | colorder[col & 3]) * 16 + 2 * order[(lineno & 0x7)] + (lineno >> 6)] |= ((c == '0' ? 0 : 1) << (7 - ((lineno >> 3) & 7)));
        lineno = row
        order = [7, 2, 6, 3, 5, 4, 0, 1]
        colorder = [0, 1, 3, 2]
        word = ((col & 0xFFC) | colorder[col & 3]) * 16 + 2 * order[
            (lineno & 0x7)] + (lineno >> 6)
        maski = 7 - ((lineno >> 3) & 7)
        return (word, maski)


class TMS320C15(mrom.MaskROM):
    def desc(self):
        return 'TMS320C15'

    def endian(self):
        return "big"

    def word_bits(self):
        return 16

    def nwords(self):
        return 4096

    def txtwh(self):
        return (128, 512)

    def invert(self):
        return False

    def calc_cr2oi(self, col, row):
        order = [0, 1, 2, 3, 4, 5, 6, 7, 7, 6, 5, 4, 3, 2, 1, 0]
        word = (511 - row) * 8 + order[col & 0xF]
        maski = col >> 3
        return (word, maski)
