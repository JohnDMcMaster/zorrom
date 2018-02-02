import mrom

'''
The row and column decode logic should be up and right

Reference
https://siliconpr0n.org/map/sega/315-5571/mz_mit20x/
Rotate 90 CW to get expected rotation

Think MB86233/MB86234 is the same layout
'''
class MB8623x(mrom.MaskROM):
    def desc(self):
        return 'Fujitsu MB86233/MB86234'

    @staticmethod
    def txtwh():
        return (32 * 8, 32 * 8)

    @staticmethod
    def txtgroups():
        # Use monkey convention breaking on groups of 8
        # Actual has no col breaks and every second row break is larger
        return xrange(8, 32 * 8, 8), xrange(8, 32 * 8, 8)

    @staticmethod
    def invert():
        return True

    def oi2cr(self, offset, maski):
        biti = offset * 8 + maski
        #print biti
        # Each column has 16 bytes
        # Actually starts from right of image
        col = (32 * 8 - 1) - biti / (8 * 32)
        # 0, 8, 16, ... 239, 247, 255
        row = (biti % 32) * 8 + (biti / 32) % 8
        #print row
        return (col, row)

    '''
    http://siliconpr0n.org/.../mz_rom_mit20x_xpol/
    last bit lower left
    leftmost column read out first
    Within each group of 8 bits, one is read out at a time across the entire column
    Then the next bit in the column is read
    
    so note that column numbering is basically inverted vs our images
    Also the bit polarity is inverted
    
    so to read out last four bytes
    Most significant bits of each byte towards top of die
    bottom bit of the topmost column byte then forms the MSB of the first byte
    then move one byte down
    Take the same bit position for the next significnt bit    
    '''
    '''
    def layout_bin2img(self):
        rom = None
        romr = None

        romb = bytearray(8192)
        for i in xrange(8192):
            for j in xrange(8):
                biti = i * 8 + j
                # Each column has 16 bytes
                # Actually starts from right of image
                col = (32 * 8 - 1) - biti / (8 * 32)
                # 0, 8, 16, ... 239, 247, 255
                row = (biti % 32) * 8 + (biti / 32) % 8
                try:
                    bit = romr(rom, col, row)
                except:
                    print i, j, biti, col, row
                    raise
                if bit is None:
                    print i, j
                    raise ValueError()
                #if biti > 8192 * 8 - 32:
                #    print i, j, biti, col, row, bit
                romb[i] |= (1 ^ bit) << j
            #if biti > 8192 * 8 - 32:
            #    print 'romb[0x%02X] = 0x%02X' % (i, romb[i])
        return romb
    '''
