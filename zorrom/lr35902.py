from zorrom import mrom
'''
Reference
https://www.neviksti.com/DMG/

'''


class LR35902(mrom.MaskROM):
    def desc(self):
        return 'LR35902'

    def txtwh(self):
        # 128 bits across
        #   Physically organized in 16 groups of 8 bits
        #   Logically organized in 8 groups of 16 bits
        # 16 bits down
        return (128, 16)

    def invert(self):
        return False

    '''Given binary (word offset, bit index) return image row/col'''

    def calc_oi2cr(self, offset, maski):
        col = ((7 - maski) * 16) + (offset // 16)
        row = offset % 16
        return (col, row)
