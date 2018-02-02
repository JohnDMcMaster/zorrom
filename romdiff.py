# backpropagate ROM into image

from PIL import Image
import argparse
import os
from zorrom.archs import arch2mr

'''
Given byte offset and mask return image (col, row)
maskb: binary mask
maski: bitshi
'''
def bit_b2i(offset, maskb=None, maski=None):
    maskin = {
        0x80: 7,
        0x40: 6,
        0x20: 5,
        0x10: 4,
        0x08: 3,
        0x04: 2,
        0x02: 1,
        0x01: 0,
        }
    if maski is None:
        maski = maskin[maskb]
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
Given image row/col return byte (offset, binary mask)
'''
bit_i2bm = {}
for offset in xrange(8192):
    for maski in xrange(8):
        col, row = bit_b2i(offset, maski=maski)
        bit_i2bm[(col, row)] = offset, 1 << maski
def bit_i2b(col, row):
    return bit_i2bm[(col, row)]

'''
Convert a bytearray ROM file into a row/col bit dict w/ image convention
'''
def romb2romi(romb):
    if len(romb) != 8192:
        raise ValueError()
    ret = {}

    for col in xrange(32 * 8):
        for row in xrange(32 * 8):
            offset, maskb = bit_i2b(col, row)
            if maskb > 0x80:
                raise ValueError()
            byte = romb[offset]
            bit = int(bool(byte & maskb)) ^ 1
            ret[(col, row)] = bit
    return ret

def bitmap(rom1, rom2, fn_out):
    BIT_WH = 32 * 8                                                                                                                                                                                                                                        
    im = Image.new("RGB", (BIT_WH, BIT_WH), "black")
    diffs = []
    for col in xrange(BIT_WH):
        for row in xrange(BIT_WH):
            b1 = rom1[(col, row)]
            b2 = rom2[(col, row)]
            if b1 != b2:
                c = (255, 0, 0)
                diffs.append((col, row, b1, b2))
            else:
                if b1:
                    c = (128, 128, 128)
                else:
                    c = (0, 0, 0)
            im.putpixel((col, row), c)
    im.save(fn_out)
    return diffs


def run(arch, rom1_fn, rom2_fn, fn_out, monkey_fn=None):
    try:
        mrc = arch2mr[arch]
    except KeyError:
        raise Exception("Invalid architecture %s. Try --list-arch" % arch)

    rom1b = bytearray(open(rom1_fn, 'r').read())
    rom2b = bytearray(open(rom2_fn, 'r').read())
    print 'Converting to image layout...'
    rom1i = romb2romi(rom1b)
    rom2i = romb2romi(rom2b)
    dir_out = 'romdiff'
    if not os.path.exists(dir_out):
        os.mkdir(dir_out)

    diffs = bitmap(rom1i, rom2i, fn_out)

    for diff in diffs:
        col, row, b1, b2 = diff
        print 'x%d, y%d, CS: %d, C0: %d' % (col, row, b1, b2)
        off, mask = bit_i2b(col, row)
        print '  Offset 0x%04X, mask 0x%02X' % (off, mask)
        vg_col = col / 8
        vl_col = col % 8
        vg_row = row / 8
        vl_row = row % 8
        if monkey_fn:
            print '  http://cs.sipr0n.org/static/%s/%s_%02d_%02d.png @ col %d, row %d' % (monkey_fn, monkey_fn, vg_col, vg_row, vl_col, vl_row)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Visually diff two .bin in original image layout, printing differences')
    parser.add_argument('--verbose', '-v', action='store_true', help='verbose')
    parser.add_argument('--arch', help='Decoder to use (required)')
    parser.add_argument('--monkey-fn', default=None, help='Monkey URL reference. Ex: sega_315-5677_xpol')
    parser.add_argument('rom1', help='ROM1 file name')
    parser.add_argument('rom2', help='ROM2 file name')
    parser.add_argument('out', nargs='?', default=None, help='Output file name')
    args = parser.parse_args()

    if args.arch != 'mb86233':
        raise Exception("FIXME: only mb86233 supported")

    fn_out = args.out
    if not fn_out:
        fn_out = 'out.png'
    run(args.arch, rom1_fn=args.rom1, rom2_fn=args.rom2, fn_out=fn_out, args.monkey_fn)
