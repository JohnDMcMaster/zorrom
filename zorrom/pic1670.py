from zorrom import mrom
'''

Reference
https://siliconpr0n.org/map/apple/pic1670-adb-turbo/mz_mit20x/

'''


class PIC1670(mrom.MaskROM):
    @staticmethod
    def desc(self):
        return 'PIC1670'

    @staticmethod
    def bigendian(self):
        # pic16 is little endian
        return 0

    @staticmethod
    def bitwidth(self):
        # pic16 has 13 bit words
        return 13

    @staticmethod
    def txtwh():
        # 8 groups of 8 bits across, 13 groups of 16 bits down.
        return (8*8, 13 * 16)

    @staticmethod
    def txtgroups():
        # Use monkey convention breaking on groups of 8
        # Actual has no col breaks and every second row break is larger
        return range(8, 32 * 8, 8), range(8, 32 * 8, 8)

    @staticmethod
    def invert():
        return True

    '''Given binary (byte offset, bit index) return image row/col'''
    def oi2cr(self, offset, maski):
        #logic from modemmap.cc
        b = 12-maski
        col = offset & 0x3f
        if (col & 8):
            col ^= 7
        col ^= 0x38
        row = 0 ^ (8 if (offset & 0x200) else 0) | (4 if (offset & 0x100) else 0) | (2 if(offset & 0x080) else 0) | (1 if(offset & 0x040) else 0)
        row += b*16
        return (col, row)
