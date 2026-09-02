import re

BS = chr(92)


def tokenize(s):
    toks = []
    i = 0
    n = len(s)
    while i < n:
        c = s[i]
        if c in "()":
            toks.append(c)
            i += 1
        elif c == '"':
            j = i + 1
            buf = []
            while j < n:
                if s[j] == BS:
                    buf.append(s[j + 1])
                    j += 2
                elif s[j] == '"':
                    break
                else:
                    buf.append(s[j])
                    j += 1
            toks.append(("STR", "".join(buf)))
            i = j + 1
        elif c.isspace():
            i += 1
        else:
            j = i
            while j < n and (not s[j].isspace()) and s[j] not in '()"':
                j += 1
            toks.append(("ATOM", s[i:j]))
            i = j
    return toks


def parse(toks):
    stack = [[]]
    for t in toks:
        if t == "(":
            new = []
            stack[-1].append(new)
            stack.append(new)
        elif t == ")":
            stack.pop()
        else:
            stack[-1].append(t[1])
    return stack[0]


def nm(n):
    return n[0] if n and isinstance(n[0], str) else None


def fa(n, k):
    return [c for c in n if isinstance(c, list) and nm(c) == k]


def f1(n, k):
    r = fa(n, k)
    return r[0] if r else None


def load(p):
    return parse(tokenize(open(p, encoding="utf-8").read()))[0]


def fp_info(root):
    out = []
    for fp in fa(root, "footprint"):
        lib = fp[1] if len(fp) > 1 and isinstance(fp[1], str) else ""
        tr = f1(fp, "transform")
        tl = f1(tr, "translate")
        x, y = float(tl[1]), float(tl[2])
        rr = f1(tr, "rotate")
        rot = float(rr[1]) if rr else 0.0
        lay = f1(fp, "layer")
        lay = lay[1] if lay else "?"
        ref = val = None
        for p in fa(fp, "property"):
            if p[1] == "Reference":
                ref = p[2]
            if p[1] == "Value":
                val = p[2]
        nets = {}
        for pad in fa(fp, "pad"):
            net = f1(pad, "net")
            if net:
                nets[pad[1]] = net[2] if len(net) > 2 else net[1]
        out.append(dict(lib=lib, ref=ref, val=val, x=x, y=y, rot=rot, layer=lay, nets=nets, node=fp))
    return out


mcu = load("C:/Claude/CustomMechanicalKeyboard/KiCAD/mcuBoard/mcu_DaughterBoard.kicad_pcb")
kb = load("C:/Claude/CustomMechanicalKeyboard/KiCAD/keyBoard/keyboardKiCad.kicad_pcb")

mf = fp_info(mcu)
kf = fp_info(kb)

print("=== MCU DAUGHTERBOARD FOOTPRINTS BY LAYER ===")
for f in sorted(mf, key=lambda f: (f["layer"], f["ref"] or "")):
    print("  %-6s %-10s %-38s (%7.3f,%7.3f) rot=%s" % (f["ref"], f["layer"], (f["val"] or "")[:38], f["x"], f["y"], f["rot"]))

print()
print("=== CNN1 NET COMPARISON (pin -> net) ===")
mc = [f for f in mf if f["ref"] == "CNN1"][0]
kc = [f for f in kf if f["ref"] == "CNN1"][0]
same = diff = 0
rows = []
for pin in sorted(mc["nets"], key=lambda s: int(s) if s.isdigit() else 999):
    a = mc["nets"].get(pin, "-")
    b = kc["nets"].get(pin, "-")
    ok = "SAME" if a == b else "DIFF"
    if a == b:
        same += 1
    else:
        diff += 1
    rows.append("  pin %-3s  mcu=%-14s kb=%-14s %s" % (pin, a[:14], b[:14], ok))
print("\n".join(rows))
print("  --> same=%d diff=%d" % (same, diff))
