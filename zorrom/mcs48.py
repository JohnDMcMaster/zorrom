from zorrom.util import hexdump
from zorrom import mrom


'''
Reference ROM: decap #8, #9 (FIXME: add link)
Reference version by EdHunter with help from Haze

NEC D8041AH
'''
class D8041AH(mrom.MaskROM):
    @staticmethod
    def desc(self):
        return 'NEC D8041AH'

    @staticmethod
    def txtwh():
        '''
        Layout
        -Orientation: decode logic down/right / NEC logo left
        -128 bit wide lines
        -66 lines tall
        -Last two rows may contain a bunch of 1s
        '''
        return (128, 66)

    def bytes(self):
        return 128 * 64 // 8

    @staticmethod
    def txtgroups():
        # Take literal image layout with no extra breaks
        return (), range(1, 66, 2)

    @staticmethod
    def invert():
        '''
        Actual: bit with extra circle contact => 0
        Convention: xpol bright (ie circle => 0) recorded as 1
        Result: invert
        '''
        return True

    def oi2cr(self, offset, maski):
        '''
        Each col right % 4 adds +0x40
        Each col right +4 is sequence
            0:  0x00000300
            4:  0x00000200
            8:  0x00000100
            12: 0x00000000
        Then moves onto next bit
        First bit is 0x80, then 0x40, then 0x20, etc
        This takes 4 * 4 * 8 => 128, the row size

        Next row advances to next byte
        
        That is, offset address maps as follows
        1024 bit => 10 bits
        xx xxxx xxxx

        column 128 bits => 7 bits
        bbb rrcc
        b: bitoff
        r: colrange
        c: col40
        '''
        # mask 0xc
        colrange = {
            0x0300: 0x0,
            0x0200: 0x4,
            0x0100: 0x8,
            0x0000: 0xc,
            }[offset & 0x0300]
        bitoff = (7 - maski) * 0x10
        col40 = (offset // 0x40) % 4
        col = bitoff | colrange | col40
        row = offset % 64
        return (col, row)

'''
References
-http://caps0ff.blogspot.com/2016/12/39-rom-extracted.html
-http://siliconpr0n.org/map/taito/m-001/mz_mit20x/

Orientation
vs reference, rotate such that the main decoding circuitry / SRAM is to the right
90 CCW vs the reference image

Intersil M5L8042
'''
class M5L8042(mrom.MaskROM):
    @staticmethod
    def desc(self):
        return 'Mitsubishi M5L8042'

    @staticmethod
    def txtwh():
        return (16 * 8, 16 * 8)

    @staticmethod
    def txtgroups():
        return range(8, 16 * 8, 8), range(2, 64 * 2, 2)

    @staticmethod
    def invert():
        return False

    def oi2cr(self, offset, maski):
        _cols, rows = self.txtwh()
        '''
        Lowest address as the bottom
        One bit from each column group
        '''
        # Word 0 leftmost within groups
        # but bit 0 at right
        col = (7 - maski) * 16 + offset % 16
        # first bytes at bottom
        # each row has 16 bytes
        row = rows - 1 - (offset // 16)
        return (col, row)
