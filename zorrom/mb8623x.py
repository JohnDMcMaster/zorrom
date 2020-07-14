from zorrom import mrom
'''
The row and column decode logic should be up and right

Reference
https://siliconpr0n.org/map/sega/315-5571/mz_mit20x/
Rotate 90 CW to get expected rotation

Think MB86233/MB86234 is the same layout
'''


class MB8623x(mrom.MaskROM):
    @staticmethod
    def desc(self):
        return 'Fujitsu MB86233/MB86234'

    @staticmethod
    def txtwh():
        return (32 * 8, 32 * 8)

    @staticmethod
    def txtgroups():
        # Use monkey convention breaking on groups of 8
        # Actual has no col breaks and every second row break is larger
        return range(8, 32 * 8, 8), range(8, 32 * 8, 8)

    @staticmethod
    def invert():
        return True

    def oi2cr(self, offset, maski):
        biti = offset * 8 + maski
        #print biti
        # Each column has 16 bytes
        # Actually starts from right of image
        col = (32 * 8 - 1) - biti // (8 * 32)
        # 0, 8, 16, ... 239, 247, 255
        row = (biti % 32) * 8 + (biti // 32) % 8
        #print row
        return (col, row)
