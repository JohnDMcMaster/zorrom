from util import hexdump
import mrom


'''
Reference ROM: decap #8, #9 (FIXME: add link)
Reference version by EdHunter with help from Haze
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

    @staticmethod
    def txtgroups():
        # Take literal image layout with no extra breaks
        return (), xrange(1, 66, 2)

    @staticmethod
    def invert():
        '''
        Actual: bit with extra circle contact => 0
        Convention: xpol bright (ie circle => 0) recorded as 1
        Result: invert
        '''
        return True

    # TODO: convert to oi2cr
    class Txt2Bin(mrom.MaskROM.Txt2Bin):
        def run(self):
            bits = self.txtbits()
        
            def bits2byte(s):
                b = 0
                for bit in s:
                    b = b << 1
                    b = b | int(bit)
                return chr(b)
            
            data = ""
            for a in range(0, len(bits), 128):
                s = bits[a:a+128]
                for b in range(0, 16):
                    x = ""
                    for c in range(0, 8):
                        x = x + s[(c*16)+b:(c*16)+b+1]
                    data = data + bits2byte(x)
            
            # rotate - thanks haze
            ROM = bytearray(data)
            ROM2 = bytearray(data)
            
            destaddr = 0;
            for i in range(0,4):
                for j in range(0,0x400, 4):
                    sourceaddr = j+i
                    ROM2[destaddr] = ROM[sourceaddr]
                    destaddr = destaddr + 1
        
            destaddr = 0;
            for i in range(0,4):
                for j in range(0,0x400, 4):
                    sourceaddr = j+i
                    ROM[destaddr] = ROM2[sourceaddr]
                    destaddr = destaddr + 1
            
            # rearrange
            data = str(ROM)[0x300:0x400] + str(ROM)[0x200:0x300] + str(ROM)[0x100:0x200] + str(ROM)[0x000:0x100]
            
            if self.verbose:
                print "### data invert ###"
                print hexdump(data)
                print
            
            self.f_out.write(data)

'''
References
-http://caps0ff.blogspot.com/2016/12/39-rom-extracted.html
-http://siliconpr0n.org/map/taito/m-001/mz_mit20x/

Orientation
vs reference, rotate such that the main decoding circuitry / SRAM is to the right
90 CCW vs the reference image

'''
class MSL8042(mrom.MaskROM):
    @staticmethod
    def desc(self):
        return 'Mitsubishi MSL8042'

    @staticmethod
    def txtwh():
        return (16 * 8, 16 * 8)

    @staticmethod
    def txtgroups():
        return xrange(8, 16 * 8, 8), xrange(2, 64 * 2, 2)

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
