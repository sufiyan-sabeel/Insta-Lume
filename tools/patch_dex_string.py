#!/usr/bin/env python3
"""Replace a string constant inside a DEX file, keeping the encoded byte
length identical so no other DEX structure has to move.

After the edit the DEX header signature (SHA-1) and checksum (Adler-32) are
recomputed so the file still passes ART's DexFileVerifier checks.

Usage:
  python3 patch_dex_string.py <classes.dex> "<old string>" "<new string>" [--dry-run]
"""
import hashlib
import struct
import sys
import zlib


def uleb128(buf, p):
    result = 0
    shift = 0
    while True:
        b = buf[p]
        p += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
    return result, p


def main():
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    path = sys.argv[1]
    old = sys.argv[2].encode('utf-8')
    new = sys.argv[3].encode('utf-8')
    dry = '--dry-run' in sys.argv

    if len(old) != len(new):
        raise SystemExit(f'length mismatch: {len(old)} != {len(new)} '
                         '(in-place DEX patching requires identical length)')

    buf = bytearray(open(path, 'rb').read())
    if bytes(buf[:4]) != b'dex\n':
        raise SystemExit('not a DEX file')
    original_len = len(buf)

    (string_ids_size,) = struct.unpack_from('<I', buf, 56)
    (string_ids_off,) = struct.unpack_from('<I', buf, 60)

    hits = []
    for i in range(string_ids_size):
        (off,) = struct.unpack_from('<I', buf, string_ids_off + i * 4)
        length, p = uleb128(buf, off)
        if length != len(old):
            continue
        if bytes(buf[p:p + len(old)]) == old:
            hits.append((i, off, p))

    if len(hits) != 1:
        raise SystemExit(f'expected exactly 1 match, found {len(hits)}')

    idx, data_off, payload = hits[0]
    print(f'string_ids[{idx}] data_off=0x{data_off:x} payload@0x{payload:x}')
    print(f'  old: {old.decode()!r}')
    print(f'  new: {new.decode()!r}')

    if dry:
        print('dry run: not writing')
        return

    buf[payload:payload + len(new)] = new
    if len(buf) != original_len:
        raise SystemExit('file length changed unexpectedly')

    # DEX header: signature at 12..32 (SHA-1 of bytes[32:]),
    #              checksum at 8..12 (Adler-32 of bytes[12:])
    buf[12:32] = hashlib.sha1(buf[32:]).digest()
    struct.pack_into('<I', buf, 8, zlib.adler32(buf[12:]) & 0xFFFFFFFF)

    open(path, 'wb').write(bytes(buf))
    print(f'patched {path}')


if __name__ == '__main__':
    main()
