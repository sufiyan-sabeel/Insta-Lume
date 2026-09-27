#!/usr/bin/env python3
"""Scan an AArch64 ELF .so for MOVZ/MOVK 32-bit constant builds and report
which of the supplied values are materialised as immediates.

Used to work out how string constants living in .data are addressed.

Usage:
  python3 find_string_refs.py <lib.so> <hex value> [<hex value> ...]
"""
import struct
import sys


def elf_sections(path):
    buf = open(path, 'rb').read()
    if buf[:4] != b'\x7fELF' or buf[4] != 2:
        raise SystemExit('expected a 64-bit ELF file')
    e_phoff, e_shoff = struct.unpack_from('<QQ', buf, 32)
    e_phentsize, e_phnum, e_shentsize, e_shnum, e_shstrndx = struct.unpack_from('<HHHHH', buf, 54)
    segs = []
    for i in range(e_phnum):
        p = e_phoff + i * e_phentsize
        p_type, p_flags = struct.unpack_from('<II', buf, p)
        p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_align = struct.unpack_from('<QQQQQQ', buf, p + 8)
        segs.append((p_type, p_flags, p_offset, p_vaddr, p_filesz, p_memsz))
    shs = []
    shstr_off = struct.unpack_from('<Q', buf, e_shoff + e_shstrndx * e_shentsize + 24)[0]
    for i in range(e_shnum):
        s = e_shoff + i * e_shentsize
        name_off, sh_type, sh_flags = struct.unpack_from('<IIQ', buf, s)
        sh_addr, sh_offset, sh_size = struct.unpack_from('<QQQ', buf, s + 16)
        end = buf.index(b'\x00', shstr_off + name_off)
        shs.append((buf[shstr_off + name_off:end].decode(), sh_type, sh_addr, sh_offset, sh_size))
    return buf, segs, shs


def main():
    args = sys.argv[1:]
    tol = 0
    if '--tol' in args:
        i = args.index('--tol')
        tol = int(args[i + 1])
        del args[i:i + 2]
    if len(args) < 2:
        raise SystemExit(__doc__)
    path = args[0]
    values = [int(x, 0) for x in args[1:]]
    buf, segs, shs = elf_sections(path)

    dstart = next((a for n, t, a, o, s in shs if n == '.data'), None)
    want = {}
    for v in values:
        want[v] = ('absolute', v, 0)
        if dstart is not None:
            want[v - dstart] = ('offset-from-.data', v, 0)
            # allow small deltas: callers may add a small immediate afterwards
            for d in range(1, tol + 1):
                want.setdefault(v - dstart - d, ('offset-from-.data(-%d)' % d, v, -d))
                want.setdefault(v - dstart + d, ('offset-from-.data(+%d)' % d, v, +d))

    found = []
    for p_type, p_flags, po, pv, pf, pm in segs:
        if p_type != 1 or not (p_flags & 1):
            continue
        prev = None
        for a in range((po + 3) & ~3, po + pf - 4, 4):
            insn = struct.unpack_from('<I', buf, a)[0]
            pc = pv + (a - po)
            # MOVZ Wd/Xd  (52800000 = W, D2800000 = X)
            if (insn & 0xFF800000) in (0x52800000, 0xD2800000):
                prev = (pc, a, (insn >> 21) & 3, (insn >> 5) & 0xFFFF, insn & 0x1F)
                continue
            # MOVK Wd/Xd  (72800000 = W, F2800000 = X)
            if (insn & 0xFF800000) in (0x72800000, 0xF2800000) and prev is not None:
                ppc, pa, phw, pimm, prd = prev
                hw = (insn >> 21) & 3
                rd = insn & 0x1F
                if rd == prd and phw == 0 and hw == 1 and a - pa <= 8:
                    value = pimm | (((insn >> 5) & 0xFFFF) << 16)
                    kind = want.get(value)
                    if kind:
                        found.append((kind, value, ppc, pc, 'MOVZ+MOVK'))
                    prev = None
                    continue
            if prev is not None:
                # a MOVZ that is not completed by a MOVK still holds a 16-bit value
                ppc, pa, phw, pimm, prd = prev
                if phw == 0 and want.get(pimm):
                    found.append((want[pimm], pimm, ppc, ppc, 'MOVZ-only'))
                prev = None

    print('targets: ' + ' '.join(hex(v) for v in values))
    if not found:
        print('no MOVZ/MOVK immediate matches found')
    for kind, value, pc1, pc2, style in found:
        label, _target, delta = kind
        extra = f' delta={delta:+d}' if delta else ''
        print(f'  {label} value=0x{value:x}{extra} {style} movz@0x{pc1:x} last@0x{pc2:x}')


if __name__ == '__main__':
    main()
