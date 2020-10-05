from zorrom import mrom
'''
Reference
https://www.neviksti.com/DMG/

'''


class LR35902(mrom.MaskROM):
    def desc(self):
        return 'LR35902'

    def txtwh(self):
        # 2 groups of 8 bits across, 16 groups of 8 bits down.
        return (128, 16)

    def invert(self):
        return False

    '''Given binary (word offset, bit index) return image row/col'''
    def oi2cr(self, offset, maski):
        col = ((7 - maski) * 16) + (offset % 16)
        row = offset // 16
        return (col, row)
