from zorrom import mrom


class LC5800(mrom.MaskROM):
    def desc(self):
        return 'LC5800'

    def endian(self):
        return "big"

    def word_bits(self):
        return 16

    def words(self):
        return ((16 * 32 * 64) // 16)

    def txtwh(self):
        # 16 groups of 32 bits across, 64 lines down.
        return (16 * 32, 64)

    def invert(self):
        return True

    '''Given binary (word offset, bit index) return image row/col'''

    def calc_oi2cr(self, offset, maski):
        row = (offset // 32) ^ 63
        col = 32 * (maski) + ((offset ^ 31) & 31)
        return (col, row)
