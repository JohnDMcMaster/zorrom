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


class TMS320C53(mrom.MaskROM):
    def desc(self):
        return 'TMS320C53'

    def endian(self):
        return "big"

    def word_bits(self):
        return 16

    def nwords(self):
        # overall: 4 pages
        # page: 2 adjacent blocks
        # block: 16 groups of 8
        return 4 * 2 * 16 * 8 * 256 // 16

    def txtwh(self):
        return (4 * 2 * 16 * 8, 256)

    def invert(self):
        return True

    def calc_oi2cr_page(self, word, maski):
        """
        top-r

        Terms:
        -col8: 8 closely packed columns
        -col8x16: 16 col8's roughly next to each other
        
        There are 2 col8x16 in this ROI and 8 in the whole die

        each col group 8
        16 of those grouped
        these two of those groups (8 in the entire die)
        """

        assert 0 <= word < 2 * 16 * 8 * 256 // 16
        assert 0 <= maski < 16

        # 16 words per row
        # 8 even address words at left
        # 8 odd addredd words at right
        row = word // (2 * 8)
        wordmod = word % (2 * 8)

        colx8w = 8
        col8x16w = 8 * 16
        if wordmod < 8:
            col = col8x16w - (15 - maski) * colx8w - colx8w + (wordmod - 0)
        else:
            col = 2 * col8x16w - (15 - maski) * colx8w - colx8w + (wordmod - 8)

        # if row == 0:
        #    print(word, maski, col, row)
        return (col, row)

    def calc_oi2cr(self, word, maski):
        page_words = 2 * 16 * 8 * 256 // 16
        page_cols = 2 * 8 * 16
        page = word // page_words

        col, row = self.calc_oi2cr_page(word % page_words, maski)
        col += [
            # Not confident on this order
            2,
            1,
            3,
            0
        ][page] * page_cols

        return (col, row)
