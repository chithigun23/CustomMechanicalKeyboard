#!/usr/bin/env python3
"""T10 security (tamper-resistant) Torx bit with 4 mm hex shank, for the iFixit Mako/Moray 4 mm driver.
Star-shaped lofted mesh (radius as a function of angle & z) -> watertight, no boolean needed.
Run:  python make_bit.py   (needs numpy, shapely, trimesh)
"""
import math, sys
import numpy as np
from shapely.geometry import Polygon, LineString
import trimesh

N = 720  # angular samples (divisible by 6 so hex corners / torx lobes land on samples)

def torx_polygon(A, B, re, steps=40):
    """ISO 10664 style hexalobular (male): A=tip-to-tip, B=valley-to-valley, re=lobe tip radius."""
    Rl = A / 2 - re
    # solve valley radius ri for tangency of lobe circle (at 0deg) and valley circle (at 30deg)
    def f(ri):
        Rv = B / 2 + ri
        return Rl**2 + Rv**2 - 2 * Rl * Rv * math.cos(math.radians(30)) - (re + ri) ** 2
    lo, hi = 0.01, 5.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if f(lo) * f(mid) <= 0: hi = mid
        else: lo = mid
    ri = (lo + hi) / 2
    Rv = B / 2 + ri
    pts = []
    for k in range(6):
        a = math.radians(60 * k)
        L = np.array([Rl * math.cos(a), Rl * math.sin(a)])
        Vp = np.array([Rv * math.cos(a - math.radians(30)), Rv * math.sin(a - math.radians(30))])
        Vn = np.array([Rv * math.cos(a + math.radians(30)), Rv * math.sin(a + math.radians(30))])
        Tp = L + (Vp - L) * re / (re + ri)
        Tn = L + (Vn - L) * re / (re + ri)
        a0 = math.atan2(Tp[1] - L[1], Tp[0] - L[0]); a1 = math.atan2(Tn[1] - L[1], Tn[0] - L[0])
        # convex arc around L from Tp to Tn (CCW, passing through angle a)
        while a1 < a0: a1 += 2 * math.pi
        if a1 - a0 > math.pi: a0, a1 = a0 + 2 * math.pi, a1  # safety
        for t in np.linspace(a0, a1, steps):
            pts.append((L[0] + re * math.cos(t), L[1] + re * math.sin(t)))
        # concave arc around Vn from Tn to next lobe tangent
        Ln = np.array([Rl * math.cos(a + math.radians(60)), Rl * math.sin(a + math.radians(60))])
        Tq = Vn + (Ln - Vn) * ri / (re + ri)
        b0 = math.atan2(Tn[1] - Vn[1], Tn[0] - Vn[0]); b1 = math.atan2(Tq[1] - Vn[1], Tq[0] - Vn[0])
        # go CW around Vn
        while b1 > b0: b1 -= 2 * math.pi
        for t in np.linspace(b0, b1, steps):
            pts.append((Vn[0] + ri * math.cos(t), Vn[1] + ri * math.sin(t)))
    return Polygon(pts).buffer(0), ri

THETA = np.linspace(0, 2 * math.pi, N, endpoint=False)

def radial(poly):
    far = 10.0
    out = np.empty(N)
    for i, t in enumerate(THETA):
        ray = LineString([(0, 0), (far * math.cos(t), far * math.sin(t))])
        inter = ray.intersection(poly.exterior)
        out[i] = max(g.distance(__import__('shapely.geometry', fromlist=['Point']).Point(0, 0)) for g in getattr(inter, 'geoms', [inter]))
    return out

def hex_radial(AF):
    d = (THETA % (math.pi / 3)) - math.pi / 6
    return (AF / 2) / np.cos(d)

def build(AF, tipA, tipB, hole_d, hole_depth, hex_len=12.0, neck_r=1.6, neck_len=4.0,
          tip_len=5.0, re=0.20, name='bit'):
    poly, ri = torx_polygon(tipA, tipB, re)
    rt = radial(poly)
    rh = hex_radial(AF)
    rn = np.full(N, neck_r)
    # (z, radial profile) stations, bottom->top. Equal z = vertical step (flat annulus).
    z = 0.0
    st = [(0.0, rh * 0.93), (0.4, rh), (hex_len, rh)]
    z = hex_len + 2.0; st.append((z, rn))
    z += neck_len;     st.append((z, rn))
    z += 0.9;          st.append((z, rt))
    z += tip_len - 0.3; st.append((z, rt))
    z += 0.3;          st.append((z, rt * 0.90))
    ztop = z
    V = []; F = []
    rings = []
    for zz, r in st:
        base = len(V)
        for t, rr in zip(THETA, r):
            V.append((rr * math.cos(t), rr * math.sin(t), zz))
        rings.append(base)
    def quad_strip(a, b, flip=False):
        for i in range(N):
            j = (i + 1) % N
            p, q, r_, s = a + i, a + j, b + j, b + i
            F.append((p, q, r_)); F.append((p, r_, s))
    for a, b in zip(rings[:-1], rings[1:]): quad_strip(a, b)
    # bottom cap
    c0 = len(V); V.append((0, 0, 0.0))
    for i in range(N):
        j = (i + 1) % N
        F.append((c0, rings[0] + j, rings[0] + i))
    # top: annulus (outer ring -> hole rim), hole wall, hole floor
    hole_ring_top = len(V)
    for t in THETA: V.append((hole_d / 2 * math.cos(t), hole_d / 2 * math.sin(t), ztop))
    for i in range(N):
        j = (i + 1) % N
        o0, o1 = rings[-1] + i, rings[-1] + j
        h0, h1 = hole_ring_top + i, hole_ring_top + j
        F.append((o0, h1, o1)); F.append((o0, h0, h1))
    hole_ring_bot = len(V)
    for t in THETA: V.append((hole_d / 2 * math.cos(t), hole_d / 2 * math.sin(t), ztop - hole_depth))
    for i in range(N):
        j = (i + 1) % N
        F.append((hole_ring_top + i, hole_ring_bot + j, hole_ring_top + j))
        F.append((hole_ring_top + i, hole_ring_bot + i, hole_ring_bot + j))
    cf = len(V); V.append((0, 0, ztop - hole_depth))
    for i in range(N):
        j = (i + 1) % N
        F.append((cf, hole_ring_bot + i, hole_ring_bot + j))
    m = trimesh.Trimesh(np.array(V), np.array(F), process=True)
    m.fix_normals()
    m.metadata['name'] = name
    return m, ri, ztop

VARIANTS = {  # name: (hex across-flats, torx tip-to-tip A, B)
    'A': (3.95, 2.72, 1.98),
    'B': (3.90, 2.64, 1.92),
    'C': (3.85, 2.56, 1.86),
}

if __name__ == '__main__':
    import os
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    meshes = {}
    for k, (af, a, b) in VARIANTS.items():
        m, ri, h = build(af, a, b, hole_d=1.3, hole_depth=2.5, name=k)
        print(k, 'watertight', m.is_watertight, 'volume', round(m.volume, 2), 'bounds', m.bounds.round(2).tolist(), 'ri', round(ri, 3))
        m.export(os.path.join(out, f'T10_security_torx_bit_{k}.stl'))
        meshes[k] = m
    # 3-up plate, 14 mm spacing
    plate = []
    for i, k in enumerate('ABC'):
        mm = meshes[k].copy(); mm.apply_translation([i * 14.0, 0, 0]); plate.append(mm)
    trimesh.util.concatenate(plate).export(os.path.join(out, 'T10_security_torx_bit_plate_ABC.stl'))
