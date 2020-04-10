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
        0x80: 7,
        0x40: 6,
        0x20: 5,
        0x10: 4,
        0x08: 3,
        0x04: 2,
        0x02: 1,
        0x01: 0,
    }[maskb]


def mask_i2b(maski):
    '''Convert bit number to bitmask'''
    assert 0 <= maski <= 7
    return 1 << maski


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

    @staticmethod
    def desc(self):
        return 'Unspecified'

    @staticmethod
    def txtwh(self):
        '''
        Return expected txt file width/height in the canonical orientation
        Typically this is with row/column decoding down and to the right
        '''
        raise Exception("Required")

    @staticmethod
    def txtgroups(self):
        '''Return two iterators giving the x/col and yrow break points within a row/column'''
        # Before the given entry
        # ie 1 means put a space between the first and second entry
        return (), ()

    def bytes(self):
        '''Assumes word in bytes for now. Assumes no parity bits'''
        w, h = MaskROM.txtwh()
        bits = w * h
        if bits % 8 != 0:
            raise Exception("Irregular layout")
        return bits // 8

    @staticmethod
    def invert(self):
        '''
        During visual entry, convention is usually to use brighter / more featureful as 1
        However, this is often actually 0
        Set True to default to swap 0/1 bits
        '''
        return False

    def reindex(self):
        self.map_cr2boi = {}
        for offset in range(self.bytes()):
            for maski in range(8):
                col, row = self.oi2cr(offset, maski)
                self.map_cr2boi[(col, row)] = offset, maski
        assert len(self.map_cr2boi) != 0

    def cr2ob(self, col, row):
        '''Given image row/col return binary (byte offset, binary mask)'''
        offset, maski = self.cr2oi(col, row)
        return offset, mask_i2b(maski)

    def cr2oi(self, col, row):
        '''Given image row/col return binary (byte offset, bit index)'''
        return self.map_cr2boi[(col, row)]

    # You must implement one of these
    def oi2cr(self, offset, maski):
        '''Given binary (byte offset, bit index) return image row/col'''
        return self.ob2cr(offset, mask_i2b(maski))

    def ob2cr(self, offset, maskb):
        '''Given binary (byte offset, binary mask) return image row/col '''
        return self.oi2cr(offset, mask_b2i(maskb))

    def parse_txt(self, txt):
        self.binary = self.txt2bin(StringIO(txt))

    def parse_bin(self, bin):
        assert len(bin) == self.bytes()
        self.binary = bytearray(bin)

    def get_cr(self, col, row):
        assert self.binary, "Must load binary"
        offset, maskb = self.cr2ob(col, row)
        return bool(self.binary[offset] & maskb)

    def iter_oi(self):
        for offset in range(self.bytes()):
            for maski in range(8):
                yield offset, maski

    def iter_ob(self):
        for offset in range(self.bytes()):
            for maski in range(8):
                yield offset, 1 << maski

    def txt2bin(self, buff, invert=None, rotate=None, flipx=False, flipy=False):
        t = self.Txt2Bin(self, buff, verbose=self.verbose)
        ret = t.run(rotate=rotate, flipx=flipx, flipy=flipy)
        if invert is None:
            invert = self.invert()
        if invert:
            ret = bytearray([x ^ 0xFF for x in ret])
        assert self.bytes() == len(ret), "Expected %u bytes, got %u"  % (self.bytes(), len(ret))
        return ret

    def bin2txt(self, f_in, f_out):
        t = self.Bin2Txt(self, f_in, f_out, verbose=self.verbose)
        t.run()

    class Txt2Bin(object):
        def __init__(self, mr, f_in, verbose=False):
            self.mr = mr
            self.f_in = f_in
            self.buff_out = None
            self.verbose = verbose

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

        def txt2dict(self, txt, w, h):
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

        def rotate_180(self, txtdict, w, h):
            ret = {}
            for y in range(h):
                for x in range(w):
                    ret[(x, y)] = txtdict[(w - x - 1, h - y - 1)]
            return ret

        def rotate_90(self, txtdict, w, h):
            # y: x
            # x: w - y - 1
            ret = {}
            for y in range(h):
                for x in range(w):
                    ret[(x, y)] = txtdict[(h - y - 1, x)]
            return ret

        def flipx(self, txtdict, w, h):
            """Mirror along x axis"""
            ret = {}
            for y in range(h):
                for x in range(w):
                    ret[(x, h - y - 1)] = txtdict[(x, y)]
            return ret

        def flipy(self, txtdict, w, h):
            """Mirror along y axis"""
            # return txtdict
            ret = {}
            for y in range(h):
                for x in range(w):
                    ret[(w - x - 1, y)] = txtdict[(x, y)]
            return ret

        def txtbits(self, rotate=None, flipx=False, flipy=False):
            '''Return contents as char array of bits (ie string with no whitespace)'''
            assert rotate in (None, 0, 90, 180, 270)
            w, h = self.mr.txtwh()
            wtxt, htxt = w, h
            if rotate == 90 or rotate == 270:
                wtxt, htxt = h, w
            txt = self.txt(wtxt, htxt)
            txtdict = self.txt2dict(txt, wtxt, htxt)
            if rotate not in (None, 0):
                if rotate == 180:
                    txtdict = self.rotate_180(txtdict, wtxt, htxt)
                elif rotate == 90:
                    txtdict = self.rotate_90(txtdict, wtxt, htxt)
                    wtxt, htxt = htxt, wtxt
                elif rotate == 270:
                    txtdict = self.rotate_90(txtdict, wtxt, htxt)
                    wtxt, htxt = htxt, wtxt
                else:
                    assert 0
            if flipx:
                txtdict = self.flipx(txtdict, wtxt, htxt)
            if flipy:
                txtdict = self.flipy(txtdict, wtxt, htxt)
            return txtdict

        # Default impl based off of oi2rc()
        def run(self, rotate=None, flipx=False, flipy=False):
            self.buff_out = bytearray()
            # (col, row) to "1" or "0"
            txtdict = self.txtbits(rotate=rotate, flipx=flipx, flipy=flipy)
            # Existing col, row selections
            crs = {}

            def next_byte():
                byte = 0
                for maski in range(8):
                    c, r = self.mr.oi2cr(offset, maski)
                    if (c, r) in crs:
                        offset2, maski2 = crs[(c, r)]
                        raise Exception(
                            "Duplicate c=%d, r=%d: (o %d, i %d) vs (o %d, i %d)"
                            % (c, r, offset, maski, offset2, maski2))
                    bit = txtdict[(c, r)]
                    if bit == '1':
                        byte |= 1 << maski
                    crs[(c, r)] = (offset, maski)
                return byte

            for offset in range(self.mr.bytes()):
                self.buff_out.append(next_byte())
            return self.buff_out

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
                        raise Exception(
                            'Bad c %d, r %d from off %d, maski %d' %
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
