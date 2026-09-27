#!/usr/bin/env python3
"""Replace whole C-strings inside libinstazen.so WITHOUT changing any length.

Why same-length only: the Dex2C-compiled native library addresses its global
string blob positionally (base + offset / array index). Growing, shrinking or
moving a string would silently corrupt every reference after it, so this tool
refuses any edit that is not an exact in-place byte substitution of the same
size. String content is not hashed anywhere in the library (verified: no
Java-hash / FNV / CRC32 hits), so same-length content swaps are safe.

Matching is on whole strings (NUL-delimited), never substrings, and every
match count must be exactly 1 unless --allow-multiple is given.

Usage:
  python3 patch_so_strings.py <libinstazen.so> --replace OLD NEW [--replace OLD NEW ...]
                              [--pad] [--dry-run]

--pad  right-pads NEW with spaces when it is shorter than OLD (for visible
       labels/toasts). With --pad, URLs that are too short would also be
       padded, so only pass exact-length values for links.
"""
import struct
import sys


def find_data_section(buf):
    e_shoff = struct.unpack_from('<Q', buf, 40)[0]
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from('<HHH', buf, 58)
    shstr_off = e_shoff + e_shstrndx * e_shentsize
    strtab_off = struct.unpack_from('<Q', buf, shstr_off + 24)[0]
    for i in range(e_shnum):
        o = e_shoff + i * e_shentsize
        name_off = struct.unpack_from('<I', buf, o)[0]
        end = buf.find(b'\x00', strtab_off + name_off)
        name = bytes(buf[strtab_off + name_off:end])
        if name == b'.data':
            sh_addr = struct.unpack_from('<Q', buf, o + 16)[0]
            sh_off = struct.unpack_from('<Q', buf, o + 24)[0]
            sh_size = struct.unpack_from('<Q', buf, o + 32)[0]
            return sh_addr, sh_off, sh_size
    return None


def main():
    args = sys.argv[1:]
    if '--dry-run' in args:
        dry = True
        args.remove('--dry-run')
    else:
        dry = False
    pad = '--pad' in args
    if pad:
        args.remove('--pad')
    allow_multi = '--allow-multiple' in args
    if allow_multi:
        args.remove('--allow-multiple')

    it = iter(args)
    path = next(it, None)
    if not path:
        raise SystemExit(__doc__)
    pairs = []
    while True:
        try:
            flag = next(it)
        except StopIteration:
            break
        if flag != '--replace':
            raise SystemExit(f'unexpected argument: {flag}')
        pairs.append((next(it), next(it)))

    buf = bytearray(open(path, 'rb').read())
    original_len = len(buf)
    info = find_data_section(buf)
    if info is None:
        raise SystemExit('ELF .data section not found')
    d_addr, d_off, d_size = info
    print(f'.data: va=0x{d_addr:x} off=0x{d_off:x} size=0x{d_size:x}')

    for old_s, new_s in pairs:
        old = old_s.encode()
        new = new_s.encode()
        if len(new) > len(old):
            raise SystemExit(f'refusing (longer): {old_s!r} -> {new_s!r} '
                             f'({len(old)} -> {len(new)})')
        if len(new) < len(old):
            if not pad:
                raise SystemExit(f'refusing (shorter, no --pad): {old_s!r} -> {new_s!r} '
                                 f'({len(old)} -> {len(new)})')
            new = new + b' ' * (len(old) - len(new))

        needle = b'\x00' + old + b'\x00'
        hits = []
        start = 0
        while True:
            i = buf.find(needle, start)
            if i < 0:
                break
            hits.append(i + 1)          # payload offset (skip leading NUL)
            start = i + 1
        if not hits:
            raise SystemExit(f'string not found (or not NUL-bounded): {old_s!r}')
        if len(hits) > 1 and not allow_multi:
            raise SystemExit(f'{len(hits)} occurrences of {old_s!r}: '
                             f'{[hex(h) for h in hits]} (use --allow-multiple)')

        for h in hits:
            if not (d_off <= h < d_off + d_size):
                raise SystemExit(f'occurrence at 0x{h:x} is outside .data')
            buf[h:h + len(old)] = new
        locs = ', '.join(f'0x{h:x}' for h in hits)
        print(f'  {"DRY " if dry else ""}{old_s!r} -> {bytes(new).decode()!r} '
              f'({len(old)} bytes) at {locs}')

    if len(buf) != original_len:
        raise SystemExit('file length changed unexpectedly')
    if dry:
        print('dry run: not writing')
        return
    open(path, 'wb').write(bytes(buf))
    print(f'patched {path}')


if __name__ == '__main__':
    main()
