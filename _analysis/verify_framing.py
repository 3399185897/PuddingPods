"""Simulate Llc1;->b([B) framing, before and after the +4 patch.

Frame layout on the wire (PUDDING / GAIA v4, vendor 0x1D):
    FF 04 <len> <seq> <vendor> <feature> <cmd> <payload...>
    len  counts ONLY payload bytes, so total = 4 + 4 + len.
"""

def frame(buf, patched):
    """Return (frames, consumed_total) mirroring the smali loop."""
    buf = list(buf)
    out = []
    while True:
        # strip leading non-0xFF bytes
        while buf and (buf[0] & 0xFF) != 0xFF:
            buf.pop(0)
        if len(buf) < 4:
            return out, len(buf)

        two_byte_len = (buf[2] & 0x02) != 0
        header_len = 5 if two_byte_len else 4
        if two_byte_len:
            length = ((buf[3] & 0xFF) << 8) | (buf[4] & 0xFF)
        else:
            length = buf[3] & 0xFF

        # patch: declared length only covers payload -> add the 4 metadata bytes
        if patched:
            length += 4

        extra = 1 if (buf[2] & 0x01) else 0
        consumed = header_len + length + extra

        if consumed > 0x10004:
            return out, len(buf) - 1
        if len(buf) < consumed:
            return out, len(buf)

        body = buf[header_len:header_len + length]
        out.append(body)
        del buf[:consumed]


def parse_battery(body):
    """Scan [type][level] pairs, type 1=left 2=right 3=case, level < 101."""
    found = {}
    i = 4  # smali starts the scan at v4 == 4 (skips seq/vendor/feature/cmd)
    while i + 1 < len(body):
        t = body[i] & 0xFF
        v = body[i + 1] & 0xFF
        if 0 <= v < 0x65 and t in (1, 2, 3):
            found[t] = v
            i += 2
        else:
            i += 1
    return found


CASES = {
    "battery reply (len=6)": bytes.fromhex("FF040006001D1B0101640264035E"),
    "anc reply   (len=1)": bytes.fromhex("FF040001001D410400"),
    "gain reply  (len=1)": bytes.fromhex("FF040001001D1F0201"),
    "indicator   (len=1)": bytes.fromhex("FF040001001D270201"),
}

for name, raw in CASES.items():
    print("=" * 62)
    print(f"{name}   raw={raw.hex(' ').upper()}")
    for patched in (False, True):
        frames, leftover = frame(raw, patched)
        tag = "PATCHED " if patched else "ORIGINAL"
        body = frames[0] if frames else b""
        print(f"  {tag} frames={len(frames)} body_len={len(body):>2} "
              f"leftover={leftover} body={bytes(body).hex(' ').upper()}")
        if "battery" in name:
            got = parse_battery(body)
            pretty = {1: "left", 2: "right", 3: "case"}
            print("           battery ->",
                  {pretty[k]: f"{v}%" for k, v in sorted(got.items())} or "{}")
        else:
            # state parsers read body[4]
            val = body[4] & 0xFF if len(body) > 4 else None
            print(f"           payload[0] -> {val if val is not None else 'INDEX OUT OF BOUNDS'}")
