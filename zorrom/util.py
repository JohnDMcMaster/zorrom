import sys


def hexdump(data,
            label=None,
            indent='',
            address_width=8,
            f=sys.stdout,
            pos_offset=0):
    def isprint(c):
        return c >= ' ' and c <= '~'

    if label:
        f.write(label + "\n")

    bytes_per_half_row = 8
    bytes_per_row = 16
    data = bytearray(data)
    data_len = len(data)

    def hexdump_half_row(start):
        left = max(data_len - start, 0)

        real_data = min(bytes_per_half_row, left)

        f.write(''.join('%02X ' % c for c in data[start:start + real_data]))
        f.write(''.join('   ' * (bytes_per_half_row - real_data)))
        f.write(' ')

        return start + bytes_per_half_row

    pos = 0
    while pos < data_len:
        row_start = pos
        f.write(indent)
        if address_width:
            f.write(('%%0%dX  ' % address_width) % (pos + pos_offset))
        pos = hexdump_half_row(pos)
        pos = hexdump_half_row(pos)
        f.write("|")
        # Char view
        left = data_len - row_start
        real_data = min(bytes_per_row, left)

        strline = data[row_start:row_start + real_data].decode(
            "ascii", "replace")
        f.write(''.join([c if isprint(c) else '.' for c in strline]))
        f.write((" " * (bytes_per_row - real_data)) + "|\n")


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


def parser_grcs(parser):
    parser.add_argument('--grows', default="")
    parser.add_argument('--grows-range', default="")
    parser.add_argument('--gcols', default="")
    parser.add_argument('--gcols-range', default="")


def parse_grcs(args):
    grows = []
    if args.grows:
        grows = [int(x) for x in args.grows.split(",")]
    gcols = []
    if args.gcols:
        gcols = [int(x) for x in args.gcols.split(",")]

    if args.gcols_range:
        gcols = range(*[int(x) for x in args.gcols_range.split(",")])
    if args.grows_range:
        grows = range(*[int(x) for x in args.grows_range.split(",")])

    return grows, gcols


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
