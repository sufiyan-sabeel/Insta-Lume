#!/usr/bin/env python3
"""Set versionName and bump versionCode in a binary AndroidManifest.xml.

The APK's manifest is compiled binary XML (AXML): a UTF-16 string pool
followed by resource chunks.  Changing versionName must therefore either
pad the string to its original length (ugly in Settings) or rebuild the
string pool.  This tool rebuilds the pool:

  * every existing string is copied byte-for-byte (offsets preserved
    inside the copied data),
  * the new versionName is appended as one extra pool entry,
  * the offsets array, `stringsStart`, the pool chunk size and the root
    chunk size are recomputed,
  * everything after the pool (element/attribute chunks) is copied
    verbatim and only the two manifest attributes are rewritten:
      - android:versionName -> new string index (type TYPE_STRING)
      - android:versionCode -> new integer (type TYPE_INT_DEC)

The string pool of this manifest uses UTF-16 (flags bit 0 clear) and has
no style spans; both are asserted so a surprise input fails loudly
instead of producing a broken manifest.

Usage:
  python3 tools/patch_manifest_version.py <AndroidManifest.xml> <versionName> [<versionCode>]

versionCode is optional: when omitted it is incremented by one from the
value already present in the manifest (safe bump).  When the manifest
already reports the requested versionName the tool is a no-op, so it is
safe to re-run.
"""
import struct
import sys

CHUNK_RES_XML = 0x0003
CHUNK_STRING_POOL = 0x0001
CHUNK_START_ELEMENT = 0x0102
TYPE_STRING = 0x03
TYPE_INT_DEC = 0x10

POOL_HEADER = struct.Struct("<HHIIIIII")   # type, hdrSize, size, count, styles, flags, strStart, styleStart
STRING_OFFSET = struct.Struct("<I")
ATTR = struct.Struct("<iiiHBBI")           # ns, name, rawValue, size, res0, dataType, data
ELEM_HEADER = struct.Struct("<iiHHHHHH")   # ns, name, attrStart, attrSize, attrCount, id, class, style


def fail(msg):
    raise SystemExit(f"patch_manifest_version: {msg}")


def decode_pool(data, pool_off):
    """Return (strings, raw_entries, info) for the string pool at pool_off."""
    ptype, phdr, psize, count, styles, flags, str_start, style_start = POOL_HEADER.unpack_from(data, pool_off)
    if ptype != CHUNK_STRING_POOL:
        fail(f"expected string pool at {pool_off}, found type {ptype:#x}")
    if styles != 0 or style_start != 0:
        fail("string pool has style spans; unsupported")
    utf8 = bool(flags & 1)
    offs = struct.unpack_from("<%dI" % count, data, pool_off + phdr)
    base = pool_off + str_start
    end = pool_off + psize

    strings, raws = [], []
    for i, o in enumerate(offs):
        start = base + o
        stop = base + offs[i + 1] if i + 1 < count else end
        raws.append(data[start:stop])
        p = start
        if utf8:
            # u8/u16 utf16-length, then u8/u16 byte-length, then bytes, NUL
            def u8(pos):
                v = data[pos]
                if v & 0x80:
                    v = ((v & 0x7F) << 8) | data[pos + 1]
                    return v, pos + 2
                return v, pos + 1
            _, p = u8(p)
            blen, p = u8(p)
            strings.append(data[p:p + blen].decode("utf-8", "replace"))
        else:
            clen = struct.unpack_from("<H", data, p)[0]
            p += 2
            if clen & 0x8000:
                clen = ((clen & 0x7FFF) << 16) | struct.unpack_from("<H", data, p)[0]
                p += 2
            strings.append(data[p:p + clen * 2].decode("utf-16-le", "replace"))
    info = dict(utf8=utf8, flags=flags, hdr=phdr, size=psize, count=count,
                str_start=str_start, pool_off=pool_off, raws=raws)
    return strings, info


def encode_string(text, utf8):
    if utf8:
        chars = len(text)          # UTF-16 code-unit count
        b = text.encode("utf-8")
        def put(v):
            return bytes([v]) if v < 0x80 else bytes([0x80 | (v >> 8), v & 0xFF])
        out = put(chars) + put(len(b)) + b + b"\x00\x00"
    else:
        enc = text.encode("utf-16-le")
        out = struct.pack("<H", len(text)) + enc + b"\x00\x00"
    if len(out) % 4:
        out += b"\x00" * (4 - len(out) % 4)
    return out


def align4(v):
    return (v + 3) & ~3


def find_manifest_element(data, pool_end, strings):
    """Return (elem_off, attrs) where attrs are (offset_in_file, name, raw, type, data)."""
    pos = pool_end
    while pos + 8 <= len(data):
        ctype, chdr, csize = struct.unpack_from("<HHI", data, pos)
        if csize < 8:
            break
        if ctype == CHUNK_START_ELEMENT:
            ns, name, astart, asize, acount, _i, _c, _s = ELEM_HEADER.unpack_from(data, pos + 16)
            if strings[name] == "manifest":
                attrs = []
                for a in range(acount):
                    ap = pos + 16 + astart + a * asize
                    _ns, aname, raw, _sz, _res, dtype, dval = ATTR.unpack_from(data, ap)
                    attrs.append((ap, strings[aname], raw, dtype, dval))
                return pos, attrs
        pos += csize
    fail("manifest element not found")


def main():
    if len(sys.argv) not in (3, 4):
        raise SystemExit(__doc__)
    path, want_name = sys.argv[1], sys.argv[2]
    want_code = int(sys.argv[3]) if len(sys.argv) == 4 else None

    data = bytearray(open(path, "rb").read())
    root_type, root_hdr, root_size = struct.unpack_from("<HHI", data, 0)
    if root_type != CHUNK_RES_XML or root_hdr != 8 or root_size != len(data):
        fail(f"not an AXML file (type={root_type:#x} hdr={root_hdr} size={root_size} file={len(data)})")

    strings, info = decode_pool(data, 8)
    pool_off = 8
    pool_end = pool_off + info["size"]
    elem_off, attrs = find_manifest_element(data, pool_end, strings)

    cur_name, cur_code = None, None
    for _ap, aname, _raw, dtype, dval in attrs:
        if aname == "versionName" and dtype == TYPE_STRING:
            cur_name = strings[dval]
        if aname == "versionCode" and dtype == TYPE_INT_DEC:
            cur_code = dval
    if cur_name is None:
        fail("versionName attribute not found")

    if cur_name == want_name and (want_code is None or want_code == cur_code):
        print(f"manifest already {want_name} ({cur_code}); nothing to do")
        return

    if want_code is None:
        want_code = cur_code + 1
    if not (0 < want_code < 2 ** 31 - 1):
        fail(f"refusing versionCode {want_code}")

    # --- rebuild the string pool with the new versionName appended ---
    new_index = info["count"]
    raws = list(info["raws"])
    new_raw = encode_string(want_name, info["utf8"])
    data_end = len(raws)  # offset of the appended string == current data length
    raws.append(new_raw)
    new_data = b"".join(raws)
    new_count = info["count"] + 1
    new_str_start = info["hdr"] + 4 * new_count
    new_chunk_size = align4(new_str_start + len(new_data))
    new_data += b"\x00" * (new_chunk_size - new_str_start - len(new_data))

    offsets = []
    run = 0
    for r in raws:
        offsets.append(run)
        run += len(r)

    pool = POOL_HEADER.pack(CHUNK_STRING_POOL, info["hdr"], new_chunk_size,
                            new_count, 0, info["flags"], new_str_start, 0)
    pool += struct.pack("<%dI" % new_count, *offsets)
    pool += new_data
    assert len(pool) == new_chunk_size, (len(pool), new_chunk_size)

    delta = new_chunk_size - info["size"]
    out = bytearray()
    out += struct.pack("<HHI", CHUNK_RES_XML, root_hdr, root_size + delta)
    out += pool
    out += data[pool_end:]

    # --- rewrite the two manifest attributes (offsets shifted by delta) ---
    changed = []
    # find_manifest_element() walks `out`, so the attribute offsets it
    # returns are already in the rebuilt file's coordinates.
    for ap, aname, raw, dtype, dval in find_manifest_element(
            out, 8 + new_chunk_size, strings + [want_name])[1]:
        p = ap
        if aname == "versionName":
            _ns, _n, _r, _sz, _res, _ty, _d = ATTR.unpack_from(out, p)
            ATTR.pack_into(out, p, _ns, _n, new_index, _sz, _res, TYPE_STRING, new_index)
            changed.append("versionName")
        elif aname == "versionCode":
            _ns, _n, _r, _sz, _res, _ty, _d = ATTR.unpack_from(out, p)
            ATTR.pack_into(out, p, _ns, _n, _r, _sz, _res, TYPE_INT_DEC, want_code)
            changed.append("versionCode")

    if "versionName" not in changed or "versionCode" not in changed:
        fail(f"failed to patch attributes (patched: {changed})")

    struct.pack_into("<I", out, 4, len(out))
    open(path, "wb").write(bytes(out))
    print(f"{path}: versionName {cur_name!r} -> {want_name!r}, "
          f"versionCode {cur_code} -> {want_code} ({len(out)} bytes)")


if __name__ == "__main__":
    main()
