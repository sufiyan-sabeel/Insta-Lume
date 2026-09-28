#!/usr/bin/env python3
"""Replace whole C-strings inside the .data blob of libinstazen.so.

Safety model (why growth is allowed here, but only when balanced):

  The Dex2C string blob in `.data` is NUL-tight: strings sit back to back.
  The library addresses those strings either by index/order (a table built by
  scanning the blob) or by address.  To stay correct under BOTH models this
  tool enforces three rules:

  1. whole-string, unique matches only (never substrings),
  2. the string COUNT and ORDER inside .data never change,
  3. the total byte length of .data never changes, and every *unpatched*
     string keeps its exact offset: a grown string must be compensated by the
     very next string shrinking by the same amount.  Only the compensated
     string may move; the tool prints every moved offset so the change is
     auditable.

The file size therefore stays identical and the ELF layout is untouched.

Usage:
  python3 patch_so_blob.py <libinstazen.so> [--pad] [--dry-run]
                           --replace OLD NEW [--replace OLD NEW ...]

--pad  right-pad NEW with spaces when it is shorter than OLD (visible labels).
       Padded replacements are length-neutral and never move anything.
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
    dry = '--dry-run' in args
    if dry:
        args.remove('--dry-run')
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

    blob = bytes(buf[d_off:d_off + d_size])
    parts = blob.split(b'\x00')
    # index by exact content (whole strings only)
    index = {}
    for i, p in enumerate(parts):
        index.setdefault(p, []).append(i)

    patched = {}          # part index -> new bytes
    for old_s, new_s in pairs:
        old = old_s.encode('utf-8', 'surrogateescape')
        new = new_s.encode('utf-8', 'surrogateescape')
        if len(new) < len(old) and pad:
            # --pad keeps a visible label full width (length-neutral, safe by
            # construction).  Without --pad the shrink is intentional: it is
            # how a grown neighbour is paid for, and the balance checks below
            # prove that nothing else moves.
            new = new + b' ' * (len(old) - len(new))
        hits = index.get(old, [])
        if not hits:
            raise SystemExit(f'string not found as a whole blob entry: {old_s!r}')
        if len(hits) > 1 and not allow_multi:
            raise SystemExit(f'{len(hits)} occurrences of {old_s!r}: '
                             f'{[hex(d_off + sum(len(p) + 1 for p in parts[:i])) for i in hits]} '
                             f'(use --allow-multiple)')
        for i in hits:
            if i in patched:
                raise SystemExit(f'part {i} patched twice')
            patched[i] = new
            delta = len(new) - len(old)
            print(f'  {"DRY " if dry else ""}{old_s!r} -> {new_s!r} '
                  f'({len(old)} -> {len(new)}, delta {delta:+d})')

    if not patched:
        raise SystemExit('nothing to do')

    # --- rule 3: no unpatched string may move, total length unchanged ---
    total_old = sum(len(parts[i]) for i in patched)
    total_new = sum(len(patched[i]) for i in patched)
    if total_new != total_old:
        raise SystemExit(
            f'unbalanced length change: {total_old} -> {total_new} bytes. '
            f'Growth must be paid for by shrinking the string directly after '
            f'the grown one so that every other offset stays identical.')

    running = 0
    moved = []
    for i, p in enumerate(parts):
        if i in patched:
            if running != 0:
                moved.append((i, running))
            running += len(patched[i]) - len(p)
        else:
            if running != 0:
                raise SystemExit(
                    f'unpatched string would move by {running:+d} bytes: '
                    f'{p[:60]!r} (fix: compensate on the string directly after '
                    f'the grown one)')
    if running != 0:
        raise SystemExit(f'unbalanced trailing delta {running:+d}')

    new_parts = [patched.get(i, p) for i, p in enumerate(parts)]
    new_blob = b'\x00'.join(new_parts)
    if len(new_blob) != d_size:
        raise SystemExit(f'.data size changed: {d_size} -> {len(new_blob)}')
    if len(buf) != original_len:
        raise SystemExit('file length changed unexpectedly')

    for i, d in moved:
        off = d_off + sum(len(q) + 1 for q in parts[:i])
        print(f'  [moved] entry now at 0x{off:x} ({d:+d} bytes): {parts[i][:50]!r}')
    if not moved:
        print('  no offsets moved (all replacements length-neutral)')

    if dry:
        print('dry run: not writing')
        return
    buf[d_off:d_off + d_size] = new_blob
    open(path, 'wb').write(bytes(buf))
    print(f'patched {path} ({len(buf)} bytes, unchanged)')


if __name__ == '__main__':
    main()
