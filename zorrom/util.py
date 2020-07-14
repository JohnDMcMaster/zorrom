def hexdump(src, length=16):
    FILTER = ''.join([(len(repr(chr(x))) == 3) and chr(x) or '.'
                      for x in range(256)])
    lines = []
    for c in range(0, len(src), length):
        chars = src[c:c + length]
        hex = ' '.join(["%02x" % ord(x) for x in chars])
        printable = ''.join([
            "%s" % ((ord(x) <= 127 and FILTER[ord(x)]) or '.') for x in chars
        ])
        lines.append("%04x  %-*s  %s\n" % (c, length * 3, hex, printable))
    return ''.join(lines)


def add_bool_arg(parser, yes_arg, default=False, **kwargs):
    dashed = yes_arg.replace('--', '')
    dest = dashed.replace('-', '_')
    parser.add_argument(yes_arg,
                        dest=dest,
                        action='store_true',
                        default=default,
                        **kwargs)
    parser.add_argument('--no-' + dashed,
                        dest=dest,
                        action='store_false',
                        **kwargs)


def tobytes(buff):
    if type(buff) is str:
        #return bytearray(buff, 'ascii')
        return bytearray([ord(c) for c in buff])
    elif type(buff) is bytearray or type(buff) is bytes:
        return buff
    else:
        assert 0, type(buff)


def tostr(buff):
    if type(buff) is str:
        return buff
    elif type(buff) is bytearray or type(buff) is bytes:
        return ''.join([chr(b) for b in buff])
    else:
        assert 0, type(buff)


'''
Convert a bytearray ROM file into a row/col bit dict w/ image convention
'''


def rom_bytes2txtdict(mr, romb):
    if len(romb) != mr.size():
        raise ValueError()
    ret = {}

    txtw, txth = mr.txtwh()
    for col in range(txtw):
        for row in range(txth):
            offset, maskb = mr.cr2ow(col, row)
            byte = romb[offset]
            bit = int(bool(byte & maskb)) ^ 1
            ret[(col, row)] = bit
    return ret


def keeponly(s, keep):
    """
    py2
    table = string.maketrans('','')
    not_bits = table.translate(table, )
    return txt.translate(table, not_bits)
    """
    return ''.join([x for x in s if x in keep])
