from io import StringIO, BytesIO


def keeponly(s, keep):
    """
    py2
    table = string.maketrans('','')
    not_bits = table.translate(table, )
    return txt.translate(table, not_bits)
    """
    return ''.join([x for x in s if x in keep])


class InvalidData(Exception):
    pass


def mask_b2i(maskb):
    '''Convert bitmask to bit number'''
    return {
        0x80000000: 31,
        0x40000000: 30,
        0x20000000: 29,
        0x10000000: 28,
        0x08000000: 27,
        0x04000000: 26,
        0x02000000: 25,
        0x01000000: 24,
        0x00800000: 23,
        0x00400000: 22,
        0x00200000: 21,
        0x00100000: 20,
        0x00080000: 19,
        0x00040000: 18,
        0x00020000: 17,
        0x00010000: 16,
        0x00008000: 15,
        0x00004000: 14,
        0x00002000: 13,
        0x00001000: 12,
        0x00000800: 11,
        0x00000400: 10,
        0x00000200: 9,
        0x00000100: 8,
        0x00000080: 7,
        0x00000040: 6,
        0x00000020: 5,
        0x00000010: 4,
        0x00000008: 3,
        0x00000004: 2,
        0x00000002: 1,
        0x00000001: 0,
    }[maskb]


def mask_i2b(maski):
    '''Convert bit number to bitmask'''
    assert 0 <= maski <= 31
    return 1 << maski


def txt2dict(txt, w, h):
    ret = {}
    i = 0
    for y in range(h):
        for x in range(w):
            ret[(x, y)] = txt[i]
            i += 1
    return ret


def dict2txt(self, txtdict, w, h):
    ret = ""
    for y in range(h):
        for x in range(w):
            ret += txtdict[(x, y)]
    return ret


def td_rotate_180(txtdict, w, h):
    ret = {}
    for y in range(h):
        for x in range(w):
            ret[(x, y)] = txtdict[(w - x - 1, h - y - 1)]
    return ret


def td_rotate_90(txtdict, w, h):
    # y: x
    # x: w - y - 1
    ret = {}
    for y in range(h):
        for x in range(w):
            ret[(x, y)] = txtdict[(h - y - 1, x)]
    return ret


def td_flipx(txtdict, w, h):
    """Mirror along x axis"""
    ret = {}
    for y in range(h):
        for x in range(w):
            ret[(x, h - y - 1)] = txtdict[(x, y)]
    return ret


def td_flipy(txtdict, w, h):
    """Mirror along y axis"""
    # return txtdict
    ret = {}
    for y in range(h):
        for x in range(w):
            ret[(w - x - 1, y)] = txtdict[(x, y)]
    return ret


def td_rotate(rotate, txtdict, wtxt, htxt):
    """
    w/h referenced to output
    """
    if rotate == 180:
        txtdict = td_rotate_180(txtdict, wtxt, htxt)
    elif rotate == 90:
        txtdict = td_rotate_90(txtdict, wtxt, htxt)
        wtxt, htxt = htxt, wtxt
    elif rotate == 270:
        txtdict = td_rotate_90(txtdict, wtxt, htxt)
        wtxt, htxt = htxt, wtxt
    else:
        assert 0


class Bin2Txt(object):
    def __init__(self, mr, f_in, f_out, verbose=False):
        self.mr = mr
        self.f_in = f_in
        self.f_out = f_out
        self.verbose = verbose

    # Default impl based off of oi2rc()
    def run(self):
        # (c, r)
        bits = {}
        dbytes = bytearray(self.f_in.read())
        if self.verbose:
            print('Bytes: %d' % len(dbytes))
        if len(dbytes) != self.mr.bytes():
            raise Exception()
        cols, rows = self.mr.txtwh()
        gcols, grows = self.mr.txtgroups()
        gcols = list(gcols)
        grows = list(grows)

        # Build bit state
        for offset in range(self.mr.bytes()):
            for maski in range(8):
                c, r = self.mr.oi2cr(offset, maski)
                if c >= cols or r >= rows:
                    raise Exception('Bad c %d, r %d from off %d, maski %d' %
                                    (c, r, offset, maski))
                bit = '1' if (dbytes[offset] & (1 << maski)) else '0'
                bits[(c, r)] = bit

        # Now write it nicely formatted
        for row in range(rows):
            # Put a space between row gaps
            while row in grows:
                self.f_out.write('\n')
                grows.remove(row)
            agcols = list(gcols)
            for col in range(cols):
                while col in agcols:
                    self.f_out.write(' ')
                    agcols.remove(col)
                bit = bits.get((col, row), 'X')
                if bit == 'X':
                    # TODO: add some sort of error flag
                    # For now good for debugging
                    pass
                self.f_out.write(bit)
            # Newline afer every row
            self.f_out.write('\n')


class Txt2Bin(object):
    def __init__(self, mr, f_in, verbose=False):
        self.mr = mr
        self.f_in = f_in
        self.buff_out = None
        self.verbose = verbose

    # todo: break out as global util?
    def txt(self, w, h):
        '''Read input file, checking format and stripping everything not 01 '''
        ret = ''
        lines = 0
        for linei, l in enumerate(self.f_in):
            l = l.strip().replace(' ', '')
            if not l:
                continue
            if len(l) != w:
                raise InvalidData('Line %s want length %d, got %d' %
                                  (linei, w, len(l)))
            if l.replace('1', '').replace('0', ''):
                raise InvalidData('Line %s unexpected char' % linei)
            ret += l
            lines += 1
        if lines != h:
            raise InvalidData('Want %d lines, got %d' % (h, lines))
        return ret

    def txtbits(self, rotate=None, flipx=False, flipy=False):
        '''Return contents as char array of bits (ie string with no whitespace)'''
        assert rotate in (None, 0, 90, 180, 270)
        w, h = self.mr.txtwh()
        wtxt, htxt = w, h
        if rotate == 90 or rotate == 270:
            wtxt, htxt = h, w
        txt = self.txt(wtxt, htxt)
        txtdict = txt2dict(txt, wtxt, htxt)
        if rotate not in (None, 0):
            txtdict = td_rotate(rotate, txtdict, wtxt, htxt)
        if flipx:
            txtdict = td_flipx(txtdict, wtxt, htxt)
        if flipy:
            txtdict = td_flipy(txtdict, wtxt, htxt)
        return txtdict

    # Default impl based off of oi2rc()
    def run(self, rotate=None, flipx=False, flipy=False):
        self.buff_out = bytearray()
        # (col, row) to "1" or "0"
        txtdict = self.txtbits(rotate=rotate, flipx=flipx, flipy=flipy)
        # Existing col, row selections
        crs = {}
        w, h = self.mr.txtwh()

        def next_word():
            byte = 0
            for maski in range(self.mr.word_bits()):
                c, r = self.mr.oi2cr(offset, maski)
                assert 0 <= c < w and 0 <= r < h, "Invalid off %u maski %u => 0 <= %u col < %u and 0 <= %u row < %u" % (
                    offset, maski, c, w, r, h)
                if (c, r) in crs:
                    offset2, maski2 = crs[(c, r)]
                    raise Exception(
                        "Duplicate c=%d, r=%d: (o %d, i %d) vs (o %d, i %d)" %
                        (c, r, offset, maski, offset2, maski2))
                bit = txtdict[(c, r)]
                if bit == '1':
                    byte |= 1 << maski
                crs[(c, r)] = (offset, maski)
            return byte

        for offset in range(self.mr.words()):
            word = next_word()
            if self.mr.invert():
                word ^= self.mr.bitmask()
            self.append_word(word)
        return self.buff_out

    # TODO: move to mr as word2bytes()
    def append_word(self, w):
        if self.mr.word_bits() <= 8:
            self.buff_out.append(w)
        elif self.mr.word_bits() <= 16:
            if self.mr.bigendian():
                self.buff_out.append((w >> 8) & 0xff)
                self.buff_out.append(w & 0xff)
            else:
                self.buff_out.append(w & 0xff)
                self.buff_out.append((w >> 8) & 0xff)
        elif self.mr.word_bits() <= 32:
            if self.mr.bigendian():
                self.buff_out.append((w >> 24) & 0xff)
                self.buff_out.append((w >> 16) & 0xff)
                self.buff_out.append((w >> 8) & 0xff)
                self.buff_out.append(w & 0xff)
            else:
                self.buff_out.append(w & 0xff)
                self.buff_out.append((w >> 8) & 0xff)
                self.buff_out.append((w >> 16) & 0xff)
                self.buff_out.append((w >> 24) & 0xff)
        else:
            assert 0, "Unsupported word size %u" % self.mr.word_bits()


class MaskROM(object):
    def __init__(self, txt=None, bin=None, verbose=False):
        self.verbose = verbose

        # Actual bits of a loaded ROM
        # Canonically stored as the binary itself
        self.binary = None
        # Allows converting between txt and binary space
        self.map_cr2boi = None
        self.reindex()
        if txt:
            self.parse_txt(txt)
        if bin:
            self.parse_bin(bin)

    def desc(self):
        return 'Unspecified'

    def word_bits(self):
        '''Return number of bits in a word'''
        return 8

    def word_bytes(self):
        '''Return number of bytes in a word, rounded up to nearest byte'''
        word_bits = self.word_bits()
        if word_bits % 8 == 0:
            return word_bits // 8
        else:
            return (word_bits + 7) // 8

    def bitmask(self):
        '''
        Return bitmask available for words
        '''
        mask = 0
        for i in range(self.word_bits()):
            mask |= 1 << i
        return mask

    def txtwh(self):
        '''
        Return expected txt file width/height in the canonical orientation
        Typically this is with row/column decoding down and to the right
        '''
        raise Exception("Required")

    def txtgroups(self):
        '''
        Return two iterators giving the x/col and yrow break points within a row/column
        Used for visual clues and doesn't effect binary translation
        '''
        # Before the given entry
        # ie 1 means put a space between the first and second entry
        return (), ()

    def words(self):
        w, h = self.txtwh()
        bits = w * h
        # test removed as now supports non 8 bit words.
        #if bits % 8 != 0:
        #    raise Exception("Irregular layout")
        return bits // self.word_bits()

    def bytes(self):
        '''
        Number of bytes in a byte packed .bin which may be more than if they were stored raw
        Each word rounded up to the nearest byte
        Raw firmware / parity bits are not included

        For example, 2 12 bit words:
        0: 0x0FFF
        1: 0x0FFF
        Will be stored as 4 bytes, not 3 since bytes are padded
        '''
        return self.words() * self.word_bytes()

    def invert(self):
        '''
        During visual entry, convention is usually to use brighter / more featureful as 1
        However, this is often actually 0
        Set True to default to swap 0/1 bits
        '''
        return False

    def bigendian(self):
        return self.endian() == "big"

    def littleendian(self):
        return self.endian() == "little"

    def endian(self):
        """
        Most chips are 1 byte word for which this doesn't even matter
        You must implement this if you don't have 1 byte words
        In all cases bytes are currently shifted to LSB for non-byte sized words

        Ex: a 12 bit word of all FFs is stored as 0x0FFF
        """
        return "byte"

    def reindex(self):
        self.map_cr2boi = {}
        for offset in range(self.bytes()):
            for maski in range(self.word_bits()):
                col, row = self.oi2cr(offset, maski)
                self.map_cr2boi[(col, row)] = offset, maski
        assert len(self.map_cr2boi) != 0

    def cr2ow(self, col, row):
        '''Given image row/col return binary (word offset, binary mask)'''
        offset, maski = self.cr2oi(col, row)
        return offset, mask_i2b(maski)

    def cr2oi(self, col, row):
        '''Given image row/col return binary (word offset, bit index)'''
        return self.map_cr2boi[(col, row)]

    # You must implement one of these
    def oi2cr(self, offset, maski):
        '''Given binary (byte offset, bit index) return image row/col'''
        return self.ow2cr(offset, mask_i2b(maski))

    def ow2cr(self, offset, maskb):
        '''Given binary (word offset, binary mask) return image row/col '''
        return self.oi2cr(offset, mask_b2i(maskb))

    def parse_txt(self, txt):
        self.binary = self.txt2bin(StringIO(txt))

    def parse_bin(self, bin):
        assert len(bin) == self.bytes()
        self.binary = bytearray(bin)

    def get_cr(self, col, row):
        assert self.binary, "Must load binary"
        offset, maskb = self.cr2ow(col, row)
        return bool(self.binary[offset] & maskb)

    def iter_oi(self):
        for offset in range(self.bytes()):
            for maski in range(8):
                yield offset, maski

    def iter_ow(self):
        for offset in range(self.bytes()):
            for maski in range(8):
                yield offset, 1 << maski

    def txt2bin(self,
                buff,
                invert=None,
                rotate=None,
                flipx=False,
                flipy=False):
        t = Txt2Bin(self, buff, verbose=self.verbose)
        ret = t.run(rotate=rotate, flipx=flipx, flipy=flipy)
        assert self.bytes() == len(
            ret), "Expected %u bytes, got %u" % (self.bytes(), len(ret))
        return ret

    def bin2txt(self, f_in, f_out):
        t = Bin2Txt(self, f_in, f_out, verbose=self.verbose)
        t.run()
