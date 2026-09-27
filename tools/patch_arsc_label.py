#!/usr/bin/env python3
"""Patch the app-label string inside a compiled Android resources.arsc.

Only the target entry of the global UTF-8 string pool is changed; the
replacement grows into the pool's trailing padding, so the file size, every
chunk size and every other offset in the file stay identical.

Usage:
  python3 patch_arsc_label.py <resources.arsc> "<old>" "<new>" [--dry-run]
"""
import struct
import sys


def read_u8_varint(buf, p):
    b = buf[p]
    if b & 0x80:
        return ((b & 0x7F) << 8) | buf[p + 1], p + 2
    return b, p + 1


def main():
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    path = sys.argv[1]
    old = sys.argv[2].encode()
    new = sys.argv[3].encode()
    dry = '--dry-run' in sys.argv

    buf = bytearray(open(path, 'rb').read())
    original_size = len(buf)

    typ, hsize, _ = struct.unpack_from('<HHI', buf, 0)
    if typ != 0x0002:
        raise SystemExit('not an Android resources.arsc (missing RES_TABLE header)')
    poff = hsize
    typ, hsize, psize = struct.unpack_from('<HHI', buf, poff)
    if typ != 0x0001:
        raise SystemExit('missing global string pool')
    pool_end = poff + psize
    strcount, stylecount, flags, strstart, stylestart = struct.unpack_from('<IIIII', buf, poff + 8)
    if not (flags & 0x100):
        raise SystemExit('global pool is not UTF-8')
    if flags & 0x1:
        raise SystemExit('pool is sorted: index order would change')
    if stylecount:
        raise SystemExit('pool has style runs (not supported)')

    offsets_at = poff + hsize
    strings_at = poff + strstart

    target = None
    for i in range(strcount):
        (so,) = struct.unpack_from('<I', buf, offsets_at + i * 4)
        hdr = strings_at + so
        u16, q = read_u8_varint(buf, hdr)
        u8, q = read_u8_varint(buf, q)
        if u8 == len(old) and bytes(buf[q:q + u8]) == old:
            if target is not None:
                raise SystemExit('multiple identical strings in pool')
            target = (i, hdr, q)
    if target is None:
        raise SystemExit('string not found in pool')

    idx, hdr, data = target
    delta = len(new) - len(old)
    print(f'index={idx} hdr@0x{hdr:x} data@0x{data:x} delta={delta}')

    # UTF-8 entry layout: [u8var utf16-len][u8var utf8-len][bytes][NUL]
    # - exactly TWO length varints, then the payload (reading a third varint
    #   would consume string data and report a bogus end position).
    (last_so,) = struct.unpack_from('<I', buf, offsets_at + (strcount - 1) * 4)
    last_hdr = strings_at + last_so
    _, p1 = read_u8_varint(buf, last_hdr)
    l8, p2 = read_u8_varint(buf, p1)
    last_end = p2 + l8 + 1
    slack = pool_end - last_end
    print(f'last string ends @0x{last_end:x}, pool ends @0x{pool_end:x}, slack={slack}')
    if delta > slack:
        raise SystemExit(f'not enough padding in pool ({slack} bytes, need {delta})')

    if len(old) >= 0x80 or len(new) >= 0x80:
        raise SystemExit('multi-byte length varints not supported')
    buf[hdr] = len(new)
    buf[hdr + 1] = len(new)

    if delta:
        tail = bytes(buf[data + len(old) + 1:pool_end - delta])
        buf[data:pool_end] = new + b'\x00' + tail
        for j in range(idx + 1, strcount):
            (so,) = struct.unpack_from('<I', buf, offsets_at + j * 4)
            struct.pack_into('<I', buf, offsets_at + j * 4, so + delta)
    else:
        buf[data:data + len(old)] = new

    if len(buf) != original_size:
        raise SystemExit('file length changed unexpectedly')

    if dry:
        print('dry run: not writing')
        return
    open(path, 'wb').write(bytes(buf))
    print(f'patched {path}')


if __name__ == '__main__':
    main()
