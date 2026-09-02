import json

BS = chr(92)
PCB = "C:/Claude/CustomMechanicalKeyboard/KiCAD/keyBoard/keyboardKiCad.kicad_pcb"
OUT = "C:/Claude/CustomMechanicalKeyboard/case/fps.json"

src = open(PCB, encoding="utf-8").read()


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


tree = parse(tokenize(src))
root = tree[0]


def nm(node):
    return node[0] if node and isinstance(node[0], str) else None


def find_all(node, key):
    return [c for c in node if isinstance(c, list) and nm(c) == key]


def find(node, key):
    r = find_all(node, key)
    return r[0] if r else None


fps = []
for fp in find_all(root, "footprint"):
    lib = fp[1] if len(fp) > 1 and isinstance(fp[1], str) else ""
    tr = find(fp, "transform")
    if tr is not None:
        tl = find(tr, "translate")
        x, y = float(tl[1]), float(tl[2])
        rr = find(tr, "rotate")
        rot = float(rr[1]) if rr else 0.0
    else:
        at = find(fp, "at")
        x, y = float(at[1]), float(at[2])
        rot = float(at[3]) if len(at) > 3 else 0.0
    ref = val = None
    for p in find_all(fp, "property"):
        if p[1] == "Reference":
            ref = p[2]
        if p[1] == "Value":
            val = p[2]
    layer = find(fp, "layer")
    layer = layer[1] if layer else "?"
    holes = []
    for pad in find_all(fp, "pad"):
        d = find(pad, "drill")
        if d:
            pat = find(pad, "at")
            holes.append([float(pat[1]), float(pat[2]), d[1:]])
    fps.append(
        dict(lib=lib, ref=ref, val=val, x=x, y=y, rot=rot, layer=layer, holes=holes)
    )

json.dump(fps, open(OUT, "w"), indent=1)
print("total footprints:", len(fps))
print()
print("=== NON-SWITCH / NON-DIODE FOOTPRINTS ===")
for f in fps:
    if "SW_Kailh" in f["lib"] or "DO-35" in f["lib"]:
        continue
    r = str(f["ref"])
    v = str(f["val"])[:26]
    l = str(f["lib"])[:42]
    print(
        "%8s | %-26s | %-42s | (%8.3f, %8.3f) rot=%-6s %s holes=%d"
        % (r, v, l, f["x"], f["y"], f["rot"], f["layer"], len(f["holes"]))
    )
