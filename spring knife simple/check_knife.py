"""Checks for the simple spring knife (make_knife.py). Run:  python3 check_knife.py

It walks the knife through a whole cycle, push and pull, and at every step checks that no two
parts overlap: with every part where it is drawn, and with each part pushed to the ends of its
play across (the blade, the knob bar, the sleds and the lid). Then the latch: that the block
holds at both ends with room to spare, that the cams push it clear before the knob stops, and
that it clicks in before the blade reaches its hard stop. Then rough sums for the band, the
thumb and the blade's slide, with pessimistic friction. Then printing: each part one piece,
every flat face on a layer line, everything on the bed.

Each line says ok or FAIL. The last line counts them.
"""

import math
import sys
import zipfile

import numpy as np
import manifold3d as m3

import make_knife as k

results = []


def report(ok, text):
    results.append(ok)
    print(("ok    " if ok else "FAIL  ") + text)


def vol(a, b):
    if a is None or b is None:
        return 0.0
    ba, bb = a.bounding_box(), b.bounding_box()
    if any(ba[i] >= bb[i + 3] or bb[i] >= ba[i + 3] for i in range(3)):
        return 0.0
    return (a ^ b).volume()


# ---------------------------------------------------------------- the latch block's push, from the plan shapes
def lower_y(poly, x):
    """The lowest y of a plan polygon at x (None if x is outside it)."""
    ys = []
    n = len(poly)
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        if x0 == x1:
            if abs(x - x0) < 1e-9:
                ys += [y0, y1]
            continue
        lo, hi = min(x0, x1), max(x0, x1)
        if lo - 1e-9 <= x <= hi + 1e-9:
            ys.append(y0 + (y1 - y0) * (x - x0) / (x1 - x0))
    return min(ys) if ys else None


def tooth_samples(c, dyc):
    pts = k.tooth_points()
    out = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        for t in np.linspace(0, 1, 25):
            out.append((k.C0 + c + x0 + t * (x1 - x0), y0 + t * (y1 - y0) + dyc))
    return out


def push_needed(c, s, dyc=0.0, dyb=0.0, dyl=0.0):
    """How far the catches and cams push the latch block in (from its out position)."""
    polys = [[(x, y + dyl) for x, y in p] for p in k.catch_polys()] + [[(x, y + dyb) for x, y in p] for p in k.cam_polys(s)]
    need = 0.0
    for x, y in tooth_samples(c, dyc):
        for p in polys:
            ly = lower_y(p, x)
            if ly is not None and ly < y:
                need = max(need, y - ly)
    return need


# ---------------------------------------------------------------- the cycle
def states():
    """(name, c, s, sled F front face, sled B back face) through a whole cycle. A sled pressed on by the lug or a riser
    is drawn 0.02 off it."""
    S, T, g = k.THROW, k.TRAVEL, 0.02
    out = []

    def add(name, c, s, f=None, b=None):
        ff, bb = k.sled_faces(c, s)
        out.append((name, c, s, (f if f is not None else ff) - g, (b if b is not None else bb) + g))

    for s in np.linspace(0, S + k.KNOB_OVER, 9):                       # push: the blade held closed
        add(f"push, knob at {s:.1f}", k.CREEP - 0.02, s)
    add("push, knob back past its end", 0.0, -k.KNOB_OVER)
    for c in np.linspace(k.CREEP, T + k.OVER, 12):                     # the throw out
        add(f"throw out, blade at {c:.1f}", c, S)
    add("throw out, knob past its end", T + k.OVER, S + k.KNOB_OVER)
    for s in np.linspace(S + k.KNOB_OVER, -k.KNOB_OVER, 9):            # pull: the blade held open
        add(f"pull, knob at {s:.1f}", T - k.CREEP + 0.02, s)
    for c in np.linspace(T - k.CREEP, -k.OVER, 12):                    # the throw in
        add(f"throw in, blade at {c:.1f}", c, 0.0)
    add("throw in, knob past its end", -k.OVER, -k.KNOB_OVER)
    return out


def parts_at(c, s, f, b, dyc=0.0, dyb=0.0, dys=0.0, push=0.0, band_h=None):
    p = {
        "blade": k.carrier(c, with_arm=False).translate([0, dyc, 0]),
        "latch block": k.latch_block(c, push + 0.01).translate([0, dyc, 0]) if push > 0 else
        k.latch_block(c, 0.0).translate([0, dyc, 0]),
        "knob bar": k.knob_bar(s, dyb),
        "knob": k.knob(s, dyb),
        "sled F": k.sled(f, "F", dys),
        "sled B": k.sled(b, "B", dys),
    }
    h = band_h or max(k.BANDS.values())
    xa, xb = f - k.SLED_BEAR, b + k.SLED_BEAR
    zb = k.ZP + k.BAND_Z
    p["band"] = k.box(xa, xb, k.BAND_Y - k.BAND_W / 2 + dys, k.BAND_Y + k.BAND_W / 2 + dys, zb + 0.01, zb + h)
    return p


IGNORE = {frozenset(("knob bar", "knob")), frozenset(("band", "sled F")), frozenset(("band", "sled B"))}


def check_cycle():
    base = k.slab(0, k.Z1) - k.cavity() + k.rib()       # without the screws' holes and threads
    lid0 = k.slab(k.Z1, k.HT) + k.union([k.prism(p, k.CATCH_Z0, k.Z1 + 0.01) for p in k.catch_polys()]) \
        + k.union([k.cyl_z(x, y, k.BOSS_Z0, k.Z1 + 0.01, k.BOSS_D, 48) for x, y in k.screws()])
    x0, x1, y0, y1 = k.knob_slot()
    lid0 = lid0 - k.box(x0, x1, y0, y1, k.Z1 - 1, k.HT + 1)
    base = base - k.union([k.cyl_z(x, y, k.FLOOR, k.Z1 + 1, k.POST_POCKET_D, 48) for x, y in k.screws()])
    drifts = [(0, 0, 0, 0)]
    for dyc in (-0.3, 0.3):
        for dyb in (-0.3, 0.3):
            for dys in (-0.3, 0.3):
                for dyl in (-k.LID_DRIFT, k.LID_DRIFT):
                    drifts.append((dyc, dyb, dys, dyl))
    worst = {}
    n = 0
    for name, c, s, f, b in states():
        for dyc, dyb, dys, dyl in drifts:
            push = push_needed(c, s, dyc, dyb, dyl)
            parts = parts_at(c, s, f, b, dyc, dyb, dys, push)
            lid = lid0.translate([0, dyl, 0])
            fixed = {"base plate": base, "lid": lid}
            names = list(parts)
            for i, a in enumerate(names):
                for other, fx in fixed.items():
                    v = vol(parts[a], fx)
                    key_ = (a, other)
                    if v > worst.get(key_, (0, ""))[0]:
                        worst[key_] = (v, f"{name}, drift {dyc:+.2f} {dyb:+.2f} {dys:+.2f} {dyl:+.2f}")
                for bname in names[i + 1:]:
                    if frozenset((a, bname)) in IGNORE:
                        continue
                    v = vol(parts[a], parts[bname])
                    key_ = (a, bname)
                    if v > worst.get(key_, (0, ""))[0]:
                        worst[key_] = (v, f"{name}, drift {dyc:+.2f} {dyb:+.2f} {dys:+.2f} {dyl:+.2f}")
            n += 1
    bad = {kk: v for kk, v in worst.items() if v[0] > 0.002}
    report(not bad, f"no two parts overlap through the whole cycle ({n} positions, {len(drifts)} ways each part sits in its play)")
    for (a, b_), (v, where) in sorted(bad.items(), key=lambda kv: -kv[1][0]):
        print(f"        {a} into {b_}: {v:.3f} mm3 at {where}")


def check_keys():
    """Each sled always has a key under the lips somewhere, so it can't lift into the cams and catches."""
    gaps = k.key_gaps()
    free = lambda k0: any(k0 + k.KEY_LEN > g0 and k0 < g1 for g0, g1 in gaps)
    worst = []
    for c in np.linspace(-k.OVER, k.TRAVEL + k.OVER, 121):
        for s in np.linspace(-k.KNOB_OVER, k.THROW + k.KNOB_OVER, 41):
            f, b = k.sled_faces(c, s)
            for kind, x0 in (("F", f - k.SLED_L), ("B", b)):
                keys = (x0, x0 + k.SLED_L - k.KEY_LEN)
                if all(free(k0) for k0 in keys):
                    worst.append((kind, c, s))
    report(not worst, "wherever the sleds go, each keeps a key under the channel's lips" +
           (f" (both keys free: {worst[:3]})" if worst else ""))
    fi, bi = k.sled_insert()
    report(fi + k.SLED_L + 0.5 <= k.lug_x() - k.OVER - k.G_P and bi >= k.lug_x() - k.G_P + 0.5,
           f"the sleds drop in at {fi:.1f} and {bi:.1f} without meeting the blade's lug or each other")


def check_rest_fit():
    """The latch block in its slot and the arm: with the arm drawn, the block overlaps it by just the preload."""
    car = k.carrier(0.0, with_arm=False)
    blk = k.latch_block(0.0, 0.0)
    report(vol(car, blk) < 0.002, "the latch block sits in its T-slot without touching the carrier (out position)")
    blk_in = k.latch_block(0.0, 3.1)
    report(vol(car, blk_in) < 0.002, "and pushed in 3.1 mm, further than any cam or catch pushes it")
    arm = k.carrier(0.0) - car
    over = vol(arm, blk)
    report(over > 0, f"the arm presses the block's head (drawn {k.ARM_PRELOAD} mm into it)")


# ---------------------------------------------------------------- the latch, in numbers
def check_latch():
    dc, db, dl = 0.3, 0.3, k.LID_DRIFT
    tooth_out = k.TOOTH_Y1
    hold = tooth_out - dc - (k.CATCH_Y0 + dl)
    report(hold >= 0.9, f"the latch holds by {hold:.2f} mm at least (tooth out past the catch, every part at the worst end of its play)")
    clear = (k.CATCH_Y0 - dl) - (k.CAM_Y + db)
    report(clear >= 0.15, f"each cam pushes the tooth {clear:.2f} mm or more inside the catch")
    # when does cam A let the blade go?
    s_rel = None
    for s in np.linspace(k.THROW - 5, k.THROW + k.KNOB_OVER, 200):
        if push_needed(k.CREEP, s, -dc, db, 0.0) >= k.TOOTH_Y1 - dc - (k.CATCH_Y0 - dl) + 0.15 - 1e-6:
            s_rel = s
            break
    ok = s_rel is not None and s_rel <= k.THROW - 0.5
    report(ok, f"cam A lets the blade go with the knob {k.THROW - s_rel:.2f} mm short of the end of its push" if s_rel else
           "cam A never lets the blade go")
    s_rel = None
    for s in np.linspace(5, -k.KNOB_OVER, 200):
        if push_needed(k.TRAVEL - k.CREEP, s, -dc, db, 0.0) >= k.TOOTH_Y1 - dc - (k.CATCH_Y0 - dl) + 0.15 - 1e-6:
            s_rel = s
            break
    ok = s_rel is not None and s_rel >= 0.5
    report(ok, f"cam B lets it go with the knob {s_rel:.2f} mm short of the end of its pull" if s_rel else "cam B never lets it go")
    # clicks in before the hard stop
    out_click = k.TRAVEL - k.CREEP
    report(k.TRAVEL + k.OVER - out_click >= 1.0,
           f"going out, the latch clicks in {k.TRAVEL + k.OVER - out_click:.2f} mm before the blade's hard stop, "
           f"and {k.TRAVEL + k.G_P - out_click:.2f} mm before the lug meets sled B")
    report(k.CREEP + k.OVER >= 1.0, f"going in, it clicks in {k.CREEP + k.OVER:.2f} mm before the hard stop, "
                                    f"{k.CREEP + k.G_P:.2f} before the lug meets sled F")
    # nothing sprung rubs the blade between the ends: the tooth is free between the catches
    c0 = k.CREEP + k.CATCH_FLAT + k.CATCH_RAMP + k.TL + 0.1
    c1 = k.TRAVEL - k.CREEP - k.CATCH_FLAT - k.CATCH_RAMP - k.TL - 0.1
    free = all(push_needed(c, k.THROW, 0.3, -0.3, k.LID_DRIFT) == 0 and push_needed(c, 0.0, 0.3, -0.3, k.LID_DRIFT) == 0
               for c in np.linspace(c0, c1, 80))
    report(free, f"between the catches the latch block touches nothing: free over {c1 - c0:.0f} of the {k.TRAVEL:.0f} mm")
    # the cams never reach the catches
    a1 = k.cam_a_x(k.THROW + k.KNOB_OVER)[1]
    b0 = k.cam_b_x(-k.KNOB_OVER)[0]
    report(k.closed_catch_x() - a1 >= 0.4 and b0 - k.open_catch_x() >= 0.4,
           f"the cams stop {k.closed_catch_x() - a1:.2f} and {b0 - k.open_catch_x():.2f} mm short of the catches")
    # block push: never more than its room
    worst = max(push_needed(c, s, -0.3, -0.3, -k.LID_DRIFT) for c in (k.CREEP, k.TRAVEL - k.CREEP)
                for s in np.linspace(-k.KNOB_OVER, k.THROW + k.KNOB_OVER, 120))
    room = k.HEAD_Y0 - k.CHAMBER_Y0 - k.ARM_T - 0.2
    report(worst <= room, f"the block is pushed in {worst:.2f} mm at most, with {room:.2f} of room behind it")
    # arm strain
    L, t = k.ARM_L, k.ARM_T
    d = worst + k.ARM_PRELOAD
    strain = 1.5 * t * d / L ** 2
    kk = 3 * 3000 * (k.PART_H * t ** 3 / 12) / L ** 3
    report(strain < 0.015, f"the arm bends {100 * strain:.2f} % at most (a snap fit takes about 2 %), pushing {kk * k.ARM_PRELOAD:.2f} "
                           f"to {kk * d:.2f} N")


# ---------------------------------------------------------------- rough sums
def tpu_stress(e, scale=1.0):
    """Engineering stress (MPa) of a 95A TPU stretched e (0.5 = 50 %): a typical curve, scaled for brands."""
    pts = [(0, 0), (0.1, 2.5), (0.25, 4.5), (0.5, 6.5), (0.75, 8.0), (1.0, 9.5), (1.5, 12.0)]
    for (e0, s0), (e1, s1) in zip(pts, pts[1:]):
        if e <= e1:
            return scale * (s0 + (s1 - s0) * (e - e0) / (e1 - e0))
    return scale * pts[-1][1]


def check_sums():
    L0 = k.BAND_PRINTED
    rest = k.band_length(0, 0) - L0
    cocked = k.band_length(k.CREEP, k.THROW) - L0
    report(cocked / L0 < 0.75, f"fully cocked the band stretches {100 * cocked / L0:.0f} % of its length "
                              f"({cocked:.1f} mm; {rest:.1f} at rest)")
    rho = 1.24e-3                        # g per mm3
    m_blade = (k.carrier(0.0).volume() + k.latch_block(0.0).volume()) * rho
    m_sled = k.sled(0.0, "F").volume() * rho
    print(f"        blade {m_blade:.1f} g, sled {m_sled:.2f} g")
    for name, h in k.BANDS.items():
        a = h * k.BAND_W
        lo, hi = [], []
        for scale in (0.6, 1.0, 1.5):
            f = tpu_stress(cocked / L0, scale) * a
            es = np.linspace(rest, cocked, 200) / L0
            energy = np.trapezoid([tpu_stress(e, scale) * a for e in es], es * L0)       # mJ (N mm)
            energy *= 0.6                    # TPU gives back about 60 % (pessimistic)
            # the blade slides the rest of the way: the weight and the latch block's push on the catch, mu 0.5
            coast = k.TRAVEL - (k.THROW - k.G_P - k.CREEP)
            arm_push = 1.1
            loss = 0.5 * (m_blade * 9.81e-3 + 2 * arm_push) * (k.CATCH_FLAT + k.CATCH_RAMP) \
                + 0.5 * (m_blade + m_sled) * 9.81e-3 * k.TRAVEL + 0.5 * m_sled * 9.81e-3 * k.THROW
            ke_needed = loss
            margin = energy / max(ke_needed, 1e-9)
            lo.append(margin)
            # thumb: the band at full stretch, the cam pushing the block against the band's pull (mu 0.4) and the walls
            push_block = arm_push + 0.4 * f
            ang = math.atan2(k.CAM_OUT - k.CAM_Y, k.CAM_RAMP) + math.atan(0.4)
            thumb = f + push_block * math.tan(ang) + 0.4 * (m_blade * 9.81e-3 + 1.0)
            hi.append((f, thumb, energy))
        f_n, th_n, e_n = hi[1]
        report(min(lo) >= 3, f"{name} ({h:.2f} x {k.BAND_W} mm): pulls {hi[0][0]:.1f}-{hi[2][0]:.1f} N fully cocked "
                              f"(soft to stiff TPU), thumb {hi[0][1]:.0f}-{hi[2][1]:.0f} N at the end of the push; "
                              f"gives the blade {e_n:.0f} mJ, {min(lo):.0f} times what friction can take on the way "
                              f"(mu 0.5), with {coast:.0f} mm to slide on its own")
        if name != "band thick":            # the thick band is for a soft TPU only (the read me says so)
            report(hi[2][1] <= 33, f"        {name}: thumb at most {hi[2][1]:.0f} N (33 N is a firm push)")
        else:
            report(hi[1][1] <= 33, f"        {name}: thumb at most {hi[1][1]:.0f} N in a normal TPU "
                                   f"({hi[0][1]:.0f} in a soft one, the one it is for)")


# ---------------------------------------------------------------- printing
def horizontal_z(man):
    mesh = man.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3]
    tri = np.asarray(mesh.tri_verts)
    a, b, c = v[tri[:, 0]], v[tri[:, 1]], v[tri[:, 2]]
    n = np.cross(b - a, c - a)
    ln = np.linalg.norm(n, axis=1)
    flat = ln > 1e-9
    nz = np.zeros(len(n))
    nz[flat] = n[flat, 2] / ln[flat]
    sel = np.abs(nz) > 0.999
    return sorted(set(np.round(a[sel, 2], 3)))


def on_grid(z):
    if abs(z) < 1e-3:
        return True
    n = (z - 0.05) / 0.2
    return abs(n - round(n)) < 0.01 and round(n) >= 0


def check_print():
    p = k.print_parts()
    for name, man in p.items():
        parts = len(man.decompose())
        bad = [z for z in horizontal_z(man) if not on_grid(z)]
        bb = man.bounding_box()
        fits = bb[3] - bb[0] <= 215 and bb[4] - bb[1] <= 215
        ok = parts == 1 and not bad and fits
        report(ok, f"{name}: one piece, every flat face on a layer line, fits the bed" + ("" if ok else
               f"  (pieces {parts}, off-grid faces {bad[:6]}, size {bb[3]-bb[0]:.1f} x {bb[4]-bb[1]:.1f})"))
    # thin walls in the places that matter, from the numbers
    walls = {
        "carrier strip outside the arm (upper layer)": k.CAR_Y1_UP - (k.HEAD_Y0 + k.ARM_PRELOAD + k.ARM_GAP),
        "lips over the block's head (upper layer)": k.CAR_Y1_UP - k.HEAD_Y1,
        "carrier lip outside its groove": (k.RIB_Y0 - k.RIB_GAP_LOOSE - k.FOOT) - k.CAR_Y0,
        "wall between the front screw's pocket and the mouth": (k.screws()[2][1] - k.POST_POCKET_D / 2) - k.MOUTH_HW,
        "wall between the front screw's pocket and the bar's lane": (k.screws()[2][0] - k.POST_POCKET_D / 2)
        - (k.bar_x(k.THROW + k.KNOB_OVER)[1] + k.SIDE),
        "base plate behind the rear screws' pockets": 5.7 - k.POST_POCKET_D / 2,
        "wall between the rear screws' pockets and the channel": k.channel_x()[0] - (5.7 + k.POST_POCKET_D / 2),
        "the knob bar each side of the knob's socket": (k.BAR_Y1 - k.BAR_Y0 - k.SOCKET_W) / 2,
        "the arm": k.ARM_T,
        "the lid each side of the knob's slot (outer)": k.HW_Y1 - k.knob_slot()[3],
        "lid between the front U cut-out and the front screw's post": (k.screws()[2][1] - k.BOSS_D / 2) - k.THUMB_U_R,
    }
    for what, w in walls.items():
        report(w >= 0.8 - 1e-6, f"{what}: {w:.2f} mm (two lines is 0.8)")


def check_projects():
    for name in ("1 slide test.3mf", "2 knife plates.3mf", "3 bands TPU.3mf"):
        with zipfile.ZipFile(k.os.path.join(k.HERE, name)) as z:
            names = z.namelist()
            model = z.read("3D/3dmodel.model").decode()
            ok = "Metadata/project_settings.config" in names and 'OrcaSlicer">2.4.2' in model
        report(ok, f"{name} carries Flash Studio's settings and version tags")


def main():
    check_keys()
    check_rest_fit()
    check_latch()
    check_sums()
    check_print()
    check_projects()
    check_cycle()
    n_ok = sum(results)
    print(f"\n{n_ok} ok, {len(results) - n_ok} FAIL")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
