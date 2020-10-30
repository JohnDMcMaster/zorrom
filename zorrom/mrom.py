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


class NotImplemented(Exception):
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


def dict2txt(txtdict, w, h):
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


def td_rotate_90ccw(txtdict, wout, hout):
    """Rotate 90 CCW"""
    # y: x
    # x: w - y - 1
    ret = {}
    for y in range(hout):
        for x in range(wout):
            xin = hout - y - 1
            yin = x
            try:
                val = txtdict[(xin, yin)]
            except KeyError:
                raise KeyError(
                    "out %uw x %u h: %ux, %uy out => invalid %ux, %uy in" %
                    (wout, hout, x, y, xin, yin))
            ret[(x, y)] = val
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


def td_invert(txtdict, w, h):
    ret = {}
    for y in range(h):
        for x in range(w):
            c = txtdict[(x, y)]
            ret[(x, y)] = {"0": "1", "1": "0"}.get(c, c)
    return ret


def td_rotate(rotate, txtdict, wout, hout):
    """
    w/h referenced to output
    """
    wtxt, htxt = wout, hout
    if rotate == 180:
        txtdict = td_rotate_180(txtdict, wtxt, htxt)
    elif rotate == 90:
        txtdict = td_rotate_180(txtdict, htxt, wtxt)
        txtdict = td_rotate_90ccw(txtdict, wtxt, htxt)
        wtxt, htxt = htxt, wtxt
    elif rotate == 270:
        txtdict = td_rotate_90ccw(txtdict, wtxt, htxt)
        wtxt, htxt = htxt, wtxt
    elif rotate == 0:
        return txtdict
    else:
        assert 0, "bad rotate %s" % rotate
    return txtdict


def td_rotate2(rotate, txtdict, win, hin):
    if rotate == 90 or rotate == 270:
        wout, hout = hin, win
    else:
        wout, hout = win, hin
    txtdict = td_rotate(rotate, txtdict, wout, hout)
    return txtdict, wout, hout


def save_txt(f_out, bits, cols, rows, grows=[], gcols=[], defchar="?"):
    # Now write it nicely formatted
    for row in range(rows):
        # Put a space between row gaps
        agrows = list(grows)
        while row in agrows:
            f_out.write('\n')
            agrows.remove(row)
        agcols = list(gcols)
        for col in range(cols):
            while col in agcols:
                f_out.write(' ')
                agcols.remove(col)
            bit = bits.get((col, row), defchar)
            """
            if bit == self.defchar:
                # TODO: add some sort of error flag
                # For now good for debugging
                pass
            """
            f_out.write(bit)
        # Newline afer every row
        f_out.write('\n')


def ret_txt(*args, **kwargs):
    f = StringIO()
    save_txt(f, *args, **kwargs)
    return f.getvalue()


class Bin2Txt(object):
    def __init__(self, mr, f_in, f_out, verbose=False, defchar='X'):
        self.mr = mr
        self.f_in = f_in
        self.f_out = f_out
        self.verbose = verbose
        self.defchar = defchar

    # Default impl based off of oi2rc()
    def run(self):
        # (c, r)
        bits = {}
        dbytes = bytearray(self.f_in.read())
        if self.verbose:
            print('Bytes: %d' % len(dbytes))
        assert len(dbytes) == self.mr.bytes(), "Expect %u bytes, got %u" % (
            self.mr.bytes(), len(dbytes))
        cols, rows = self.mr.txtwh()
        gcols, grows = self.mr.txtgroups()
        gcols = list(gcols)
        grows = list(grows)

        # Build bit state
        for word in range(self.mr.nwords()):
            for maski in range(self.mr.word_bits()):
                c, r = self.mr.oi2cr(word, maski)
                if c >= cols or r >= rows:
                    raise Exception('Bad c %d, r %d from off %d, maski %d' %
                                    (c, r, word, maski))
                bit = self.mr.get_bytearray_bit(dbytes, word, maski)
                if self.mr.invert():
                    bit = {'0': '1', '1': '0'}[bit]
                bits[(c, r)] = bit

        save_txt(self.f_out,
                 bits,
                 cols,
                 rows,
                 grows=grows,
                 gcols=gcols,
                 defchar=self.defchar)


def load_bin_lsb(f_in):
    ret = ""
    for b in f_in.read():
        for maski in range(8):
            maskb = 1 << maski
            if maskb & b:
                ret += "1"
            else:
                ret += "0"
    return ret


def load_bin_msb(f_in):
    ret = ""
    for b in f_in.read():
        for maski in range(8):
            maskb = 1 << (7 - maski)
            if maskb & b:
                ret += "1"
            else:
                ret += "0"
    return ret


# todo: break out as global util?
def load_txt(f_in, w, h):
    '''Read input file, checking format and stripping everything not 01 '''
    ret = ''
    lines = 0
    for linei, l in enumerate(f_in):
        l = l.strip().replace(' ', '')
        if not l:
            continue
        if w is None:
            w = len(l)
        if len(l) != w:
            raise InvalidData('Line %s want length %d, got %d' %
                              (linei, w, len(l)))
        if l.replace('1', '').replace('0', ''):
            raise InvalidData('Unexpected char on line %u: "%s"' % (linei, l))
        ret += l
        lines += 1
    if h is None:
        h = lines
    if lines != h:
        raise InvalidData('Want %d lines, got %d' % (h, lines))
    return ret, w, h


class Txt2Words(object):
    def __init__(self, mr, f_in, verbose=False):
        self.mr = mr
        self.f_in = f_in
        self.buff_out = None
        self.verbose = verbose

    def txtbits(self, rotate=None, flipx=False, flipy=False, invert=None):
        '''Return contents as char array of bits (ie string with no whitespace)'''
        assert rotate in (None, 0, 90, 180, 270)
        w, h = self.mr.txtwh()
        wtxt, htxt = w, h
        if rotate == 90 or rotate == 270:
            wtxt, htxt = h, w
        txt, _w, _h = load_txt(self.f_in, wtxt, htxt)
        txtdict = txt2dict(txt, wtxt, htxt)
        if rotate not in (None, 0):
            txtdict = td_rotate(rotate, txtdict, wtxt, htxt)
        if flipx:
            txtdict = td_flipx(txtdict, wtxt, htxt)
        if flipy:
            txtdict = td_flipy(txtdict, wtxt, htxt)
        return txtdict

    # Default impl based off of oi2rc()
    def run(self, rotate=None, flipx=False, flipy=False, invert=None):
        # (col, row) to "1" or "0"
        txtdict = self.txtbits(rotate=rotate,
                               flipx=flipx,
                               flipy=flipy,
                               invert=invert)
        # Existing col, row selections
        crs = {}
        w, h = self.mr.txtwh()
        words = []

        def next_word():
            word = 0
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
                    word |= 1 << maski
                # if r == 0:
                #    print("tr off %u, mask %u @ %uc %ur => %s" % (offset, maski, c, r, bit))
                crs[(c, r)] = (offset, maski)
            return word

        for offset in range(self.mr.nwords()):
            word = next_word()
            if self.mr.invert():
                word ^= self.mr.bitmask()
            words.append(word)
        return words


class MaskROM(object):
    def __init__(self, txt=None, bin=None, verbose=False):
        self.verbose = verbose

        # Actual bits of a loaded ROM
        # Canonically stored as the binary itself
        self.words = None
        # Allows converting between txt and binary space
        self.map_cr2oi = None
        self.map_oi2cr = None
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

    def nwords(self):
        w, h = self.txtwh()
        bits = w * h
        # test removed as now supports non 8 bit words.
        #if bits % 8 != 0:
        #    raise Exception("Irregular layout")
        return bits // self.word_bits()

    def bits(self):
        """Number of actual usable bits in the binary"""
        return self.nwords() * self.word_bits()

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
        return self.nwords() * self.word_bytes()

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

    def calc_cr2oi(self, col, row):
        raise NotImplemented("Required")

    def calc_oi2cr(self, offset, maski):
        raise NotImplemented("Required")

    def reindex_oi2cr(self):
        cols, rows = self.txtwh()
        for offset in range(self.nwords()):
            for maski in range(self.word_bits()):
                col, row = self.calc_oi2cr(offset, maski)
                assert 0 <= col < cols and 0 <= row < rows, ("bad rc", col,
                                                             row, cols, rows)
                assert (
                    col, row
                ) not in self.map_cr2oi, "col %u, row %u already in map as %u.%u, want to add %u.%u" % (
                    col, row, self.map_cr2oi[(col, row)][0],
                    self.map_cr2oi[(col, row)][1], offset, maski)
                self.map_cr2oi[(col, row)] = (offset, maski)
                self.map_oi2cr[(offset, maski)] = (col, row)

    def reindex_cr2oi(self):
        cols, rows = self.txtwh()
        for row in range(rows):
            for col in range(cols):
                res = self.calc_cr2oi(col, row)
                # parity etc
                if res is None:
                    continue
                offset, maski = res
                assert 0 <= offset < self.nwords(
                ) and 0 <= maski < self.word_bits(
                ), "Require 0 <= offset %u < %u and 0 <= maski %u < %u" % (
                    offset, self.nwords(), maski, self.word_bits())

                assert (
                    offset, maski
                ) not in self.map_oi2cr, "offset %u, maski %u already in map at (%u col %u row)" % (
                    offset, maski, col, row)
                self.map_cr2oi[(col, row)] = (offset, maski)
                self.map_oi2cr[(offset, maski)] = (col, row)

    def has_calc_oi2cr(self):
        try:
            self.calc_oi2cr(0, 0)
            return True
        except NotImplemented:
            return False

    def has_calc_cr2oi(self):
        try:
            self.calc_cr2oi(0, 0)
            return True
        except NotImplemented:
            return False

    def reindex(self):
        self.map_cr2oi = {}
        self.map_oi2cr = {}
        if self.has_calc_oi2cr():
            self.reindex_oi2cr()
        elif self.has_calc_cr2oi():
            self.reindex_cr2oi()
        else:
            raise Exception("You must implement a conversion function")
        assert len(self.map_cr2oi) == self.bits(
        ), "Binary has %u bits but mapping has %u bits" % (self.bits(),
                                                           len(self.map_cr2oi))

    def cr2ow(self, col, row):
        '''Given image row/col return binary (word offset, binary mask)'''
        offset, maski = self.cr2oi(col, row)
        return offset, mask_i2b(maski)

    def cr2oi(self, col, row):
        '''Given image row/col return binary (word offset, bit index)'''
        return self.map_cr2oi[(col, row)]

    def oi2cr(self, offset, maski):
        '''Given binary (word offset, bit index) return image row/col'''
        return self.map_oi2cr[(offset, maski)]

    def ow2cr(self, offset, maskb):
        '''Given binary (word offset, binary mask) return image row/col '''
        return self.oi2cr(offset, mask_b2i(maskb))

    def parse_txt(self, txt):
        self.words = self.txt2words(StringIO(txt))

    def parse_bin(self, bin):
        assert len(bin) == self.bytes()
        self.words = []
        for wordi in range(self.nwords()):
            self.words.append(self.get_bytearray_word(bin, wordi))

    def get_cr(self, col, row):
        assert self.words, "Must load binary"
        offset, maskb = self.cr2ow(col, row)
        return bool(self.words[offset] & maskb)

    def iter_oi(self):
        for offset in range(self.nwords()):
            for maski in range(self.word_bits()):
                yield offset, maski

    def iter_ow(self):
        for offset in range(self.nwords()):
            for maski in range(self.word_bits()):
                yield offset, 1 << maski

    def txt2bin(self,
                f_in,
                invert=None,
                rotate=None,
                flipx=False,
                flipy=False):
        t = Txt2Words(self, f_in, verbose=self.verbose)
        words = t.run(rotate=rotate, flipx=flipx, flipy=flipy, invert=invert)
        bytes = self.words2bytes(words)
        assert self.bytes() == len(
            bytes), "Expected %u bytes, got %u" % (self.bytes(), len(ret))
        return bytes

    def txt2bin_buf(self, buf_in, *args, **kwargs):
        return self.txt2bin(StringIO(buf_in), *args, **kwargs)

    def txt2words_buf(self,
                      buf_in,
                      invert=None,
                      rotate=None,
                      flipx=False,
                      flipy=False):
        t = Txt2Words(self, StringIO(buf_in), verbose=self.verbose)
        words = t.run(rotate=rotate, flipx=flipx, flipy=flipy, invert=invert)
        assert self.nwords() == len(
            words), "Expected %u words, got %u" % (self.nwords(), len(words))
        return words

    def bin2txt(self, f_in, f_out, defchar="X"):
        t = Bin2Txt(self, f_in, f_out, verbose=self.verbose, defchar=defchar)
        t.run()

    def append_word(self, buf, w):
        """
        buf: bytearray
        w: word
        """
        if self.word_bits() <= 8:
            buf.append(w)
        elif self.word_bits() <= 16:
            if self.bigendian():
                buf.append((w >> 8) & 0xff)
                buf.append(w & 0xff)
            elif self.littleendian():
                buf.append(w & 0xff)
                buf.append((w >> 8) & 0xff)
            else:
                assert 0, "endianess not defined"
        elif self.word_bits() <= 32:
            if self.bigendian():
                buf.append((w >> 24) & 0xff)
                buf.append((w >> 16) & 0xff)
                buf.append((w >> 8) & 0xff)
                buf.append(w & 0xff)
            elif self.littleendian():
                buf.append(w & 0xff)
                buf.append((w >> 8) & 0xff)
                buf.append((w >> 16) & 0xff)
                buf.append((w >> 24) & 0xff)
            else:
                assert 0, "endianess not defined"
        else:
            assert 0, "Unsupported word size %u" % self.word_bits()

    def get_bytearray_bit(self, buf, word, maski):
        if self.word_bits() <= 8:
            bytei = word
            bmaski = maski
        elif self.littleendian():
            bytei = self.word_bytes() * word + maski // 8
            bmaski = maski % 8
        elif self.bigendian():
            if self.word_bits() <= 16:
                if maski >= 8:
                    bytei = 2 * word
                else:
                    bytei = 2 * word + 1
                bmaski = maski % 8
            else:
                assert 0, "fixme"
        else:
            assert 0, "Unsupported word size %u" % self.word_bits()

        return '1' if (buf[bytei] & (1 << bmaski)) else '0'

    def get_bytearray_word(self, buf, wordi):
        ret = 0
        for maski in range(self.word_bits()):
            if self.get_bytearray_bit(buf, wordi, maski) == '1':
                ret = ret | 1 << maski
        return ret

    def words2bytes(self, words):
        ret = bytearray()
        for word in words:
            self.append_word(ret, word)
        return ret
