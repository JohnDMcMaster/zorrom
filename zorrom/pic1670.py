from zorrom import mrom
'''
Reference
https://siliconpr0n.org/map/apple/pic1670-adb-turbo/mz_mit20x/

'''


class PIC1670(mrom.MaskROM):
    def desc(self):
        return 'PIC1670'

    def endian(self):
        return "little"

    def word_bits(self):
        return 13

    def txtwh(self):
        # 8 groups of 8 bits across, 13 groups of 16 bits down.
        return (8 * 8, 13 * 16)

    def invert(self):
        return True

    '''Given binary (word offset, bit index) return image row/col'''

    def oi2cr(self, offset, maski):
        #logic from modemmap.cc
        b = 12 - maski
        col = offset & 0x3f
        if (col & 8):
            col ^= 7
        col ^= 0x38
        row = 0 ^ (8 if (offset & 0x200) else 0) | (4 if (
            offset & 0x100) else 0) | (2 if (offset & 0x080) else
                                       0) | (1 if (offset & 0x040) else 0)
        row += b * 16
        return (col, row)
