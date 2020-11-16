from zorrom import mrom


class LC5800(mrom.MaskROM):
    def desc(self):
        return 'LC5800'

    def endian(self):
        return "big"

    def word_bits(self):
        return 16

    def nwords(self):
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


"""
Doesn't work, haven't diagnosed

from zorrom import solver

class LC5800(solver.SolverMaskROM):
    def desc(self):
        return 'LC5800'

    def endian(self):
        return "big"

    def word_bits(self):
        return 16

    def nwords(self):
        return ((16 * 32 * 64) // 16)

    def txtwh(self):
        # 16 groups of 32 bits across, 64 lines down.
        return (16 * 32, 64)

    def invert(self):
        return True

    def solver_params(self):
        return {
            "rotate": 0,
            "flipx": True,
            "interleaves": 2,
            "interleave-dir": "r",
            "layout-alg": "cols-left",
        }
"""
