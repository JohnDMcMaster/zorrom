from zorrom import mrom


class Tutorial1(mrom.MaskROM):
    def desc(self):
        return 'Tutorial 1'

    def txtwh(self):
        # 16 columns, 8 rows
        return (16, 8)

    def calc_oi2cr(self, offset, maski):
        '''Given binary (word offset, bit index) return image col/row'''
        return offset, 7 - maski

    def invert(self):
        return True
