#!/usr/bin/env python3
"""Generate wiring.html for Moon72: both halves from below, to scale, with every
bus, diode and numbered wire; the nice!nano pinout for each half; a harness table,
a checklist and meter tests.

Geometry comes from case/scad/moonlander.scad itself (openscad -D part="dump" for the
numbers, "outline_body" / "outline_mod" for the plate shapes), so the drawing always
matches the printed plates.

Coordinates: "left geometry" = the left half seen from the top, mm, x toward the other
half, y away from you. The right half is the same geometry mirrored; the switches and
the nice!nano are not mirrored parts, so their pin offsets flip sign there. The drawing
shows each plate from below, back edge still away from you: left and right swap.
"""
import json
import math
import re
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCAD = HERE.parent / "case" / "scad" / "moonlander.scad"


# ---------------------------------------------------------------- geometry from the scad

def openscad(part, ext):
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / f"x.{ext}"
        subprocess.run(["openscad", "-D", f'part="{part}"', "-o", str(out), str(SCAD)],
                       check=True, capture_output=True)
        return out.read_text()


def outline(part):
    """2D export -> list of polygons, y back up (SVG has it flipped)."""
    polys = []
    for d in re.findall(r'<path d="([^"]+)"', openscad(part, "svg")):
        for sub in re.split(r"[Zz]", d):
            pts = [(float(a), -float(b)) for a, b in re.findall(r"(-?[\d.]+),(-?[\d.]+)", sub)]
            if len(pts) > 2:
                polys.append(pts)
    return polys


D = dict(json.loads(re.search(r"DUMP = (.*)", openscad("dump", "echo")).group(1)))
u, STAG, COL_ROWS = D["u"], D["stag"], D["col_rows"]
H, N, A = D["h"], D["n"], D["A"]
HINGE_ROT = math.degrees(math.atan2(H[1], H[0]))
THUMB_ROT = HINGE_ROT + D["phi"]          # thumb keys' turn, top view (left half)
NN_C, NN = D["nn_c"], D["nn"]
BODY = outline("outline_body")
MOD = [[(A[0] + x * H[0] + y * N[0], A[1] + x * H[1] + y * N[1]) for x, y in p] for p in outline("outline_mod")]


def mod_world(p):
    return (A[0] + p[0] * H[0] + p[1] * N[0], A[1] + p[0] * H[1] + p[1] * N[1])


def rot(p, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def kpos(c, r):
    return ((c + 0.5) * u, -(r + STAG[c] + 0.5) * u)


# ---------------------------------------------------------------- the matrix, pins, names

ROW_PIN = ["D4", "D5", "D6", "D7", "D8", "D9"]
COL_PIN = ["D21", "D20", "D19", "D18", "D15", "D14", "D1"]
HDR_A = ["D1", "D0", "GND", "GND", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9"]      # from the USB end
HDR_B = ["B+", "GND", "RST", "3V3", "D21", "D20", "D19", "D18", "D15", "D14", "D16", "D10"]
AVOID = {"D16": "NFC pin, needs config", "D10": "NFC pin, needs config"}
FINGER = ["pinky outer", "pinky", "ring", "middle", "index", "index inner", "innermost"]

# base-layer legends (firmware/zmk-config/config/moon72.keymap), [row][finger column]
LEG = {
    "left": [["=", "1", "2", "3", "4", "5", "←"], ["Del", "Q", "W", "E", "R", "T", "Sym"],
             ["Bksp", "A", "S", "D", "F", "G", "Hyp"], ["Shift", "Z", "X", "C", "V", "B"],
             ["`", "—", "A⇧", "←", "→"]],
    "right": [["-", "0", "9", "8", "7", "6", "→"], ["\\", "P", "O", "I", "U", "Y", "Sym"],
              ["'", ";", "L", "K", "J", "H", "Meh"], ["Shift", "/", ".", ",", "M", "N"],
              ["Sym", "]", "[", "↓", "↑"]],
}
# thumb module: red key on col 3, thumbs (outermost first) on cols 4-6
THUMB_LEG = {"left": ["App", "Space", "Bksp", "Gui"], "right": ["Esc", "Enter", "Tab", "Alt"]}
MOD_COLS = [3, 4, 5, 6]
CONN_PIN = ["row5", "col3", "col4", "col5", "col6"]     # connector pin 1-5

MX_COL = (-3.81, 2.54)        # switch pins, seen from the top, LED window toward you
MX_DIODE = (2.54, 5.08)
BUS_UP = 8.5                  # row bus above the key centre (in the gap between switch rows)


# ---------------------------------------------------------------- drawing helpers

S = 5.0                       # px per mm
PAD = 70


def f(v):
    return f"{v:.1f}"


def text(x, y, s, cls="lbl", anchor="middle", extra=""):
    return f'<text x="{f(x)}" y="{f(y)}" class="{cls}" text-anchor="{anchor}"{extra}>{s}</text>'


def badge(x, y, n, kind):
    return (f'<circle cx="{f(x)}" cy="{f(y)}" r="9.5" class="badge badge-{kind}"/>'
            + text(x, y + 3.6, str(n), f"badgetxt tt-{kind}"))


def grp(owner, net, items, w=None):
    if not items:
        return []
    wa = f' data-w="{w}"' if w else ""
    return [f'<g data-o="{owner}" data-n="{net}"{wa}>'] + items + ["</g>"]


class View:
    """mm (left geometry) -> px, plate seen from below. side: left / right."""

    def __init__(self, side):
        self.side = side
        self.s = 1 if side == "left" else -1
        pts = [p for poly in BODY + MOD for p in poly]
        self.x0, self.x1 = min(p[0] for p in pts), max(p[0] for p in pts)
        self.y1 = max(p[1] for p in pts)
        self.y0 = min(p[1] for p in pts)

    def px(self, p):
        x = (self.x1 - p[0]) if self.side == "left" else (p[0] - self.x0)
        return (PAD + x * S, PAD + 30 + (self.y1 - p[1]) * S)

    def size(self):
        return (2 * PAD + (self.x1 - self.x0) * S, 2 * PAD + 60 + (self.y1 - self.y0) * S)

    def pin_off(self, o, deg=0.0):
        """A switch pin offset in left geometry: the switch is the same part on both halves."""
        return rot((o[0] * self.s, o[1]), deg)

    def poly(self, pts, cls):
        return f'<polyline points="{" ".join(f"{f(a)},{f(b)}" for a, b in map(self.px, pts))}" class="{cls}"/>'

    def path(self, polys, cls):
        d = " ".join("M" + " L".join(f"{f(a)} {f(b)}" for a, b in map(self.px, p)) + " Z" for p in polys)
        return f'<path d="{d}" class="{cls}" fill-rule="evenodd"/>'

    def dot(self, p, cls):
        x, y = self.px(p)
        return f'<circle cx="{f(x)}" cy="{f(y)}" r="3.2" class="{cls}"/>'

    def wire(self, pts, kind):
        return [self.poly(pts, "halo"), self.poly(pts, f"w w-{kind}")]

    def rail(self, pts, kind):
        return [self.poly(pts, f"bus bus-{kind}"), self.poly(pts, "bus-core")]

    def sleeve(self, p):
        x, y = self.px(p)
        return f'<rect x="{f(x - 5)}" y="{f(y - 9)}" width="10" height="18" rx="3" class="sleeve"/>'

    def box(self, c, w, hgt, deg, cls, rx=3):
        """Rectangle centred at c (mm), w x hgt mm, turned deg in the top view."""
        corners = [add(c, rot((sx * w / 2, sy * hgt / 2), deg)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        return f'<polygon points="{" ".join(f"{f(a)},{f(b)}" for a, b in map(self.px, corners))}" class="{cls}"/>'

    def diode(self, p_pin, p_bus):
        """1N4148 from a switch pin to the row bus, black band at the bus."""
        (x0, y0), (x1, y1) = self.px(p_pin), self.px(p_bus)
        ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
        L = math.hypot(x1 - x0, y1 - y0)
        w = min(3.6 * S, L - 6)
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        t = f'transform="rotate({f(ang)} {f(mx)} {f(my)})"'
        return [f'<line x1="{f(x0)}" y1="{f(y0)}" x2="{f(x1)}" y2="{f(y1)}" class="w w-row"/>',
                f'<rect x="{f(mx - w / 2)}" y="{f(my - 5)}" width="{f(w)}" height="10" rx="2" class="diode" {t}/>',
                f'<rect x="{f(mx + w / 2 - 0.4 * w)}" y="{f(my - 5)}" width="{f(0.4 * w)}" height="10" class="band" {t}/>',
                f'<rect x="{f(mx - w / 2)}" y="{f(my - 5)}" width="{f(w)}" height="10" rx="2" class="diode-edge" {t}/>']


# ---------------------------------------------------------------- one half

def nn_pins(side):
    """Header pin positions (left geometry). The board lies component side down, USB-C at the
    inner wall; seen from below (as you wire it) the components face you. On the left half the
    D1-D9 header faces the keys, on the right half it faces the back wall."""
    s = 1 if side == "left" else -1
    pins = {}
    for i in range(12):
        x = NN_C[0] + NN[0] / 2 - 2.83 - 2.54 * i
        pins[("A", i)] = (x, NN_C[1] - 7.62 * s)
        pins[("B", i)] = (x, NN_C[1] + 7.62 * s)
    return pins


def pin_xy(side, name, which=0):
    """Where a named pin is; `which` picks between the two GND pads of header A."""
    pins = nn_pins(side)
    if name in HDR_A and not (name == "GND" and which == 2):
        idx = [i for i, n in enumerate(HDR_A) if n == name][min(which, HDR_A.count(name) - 1)]
        return pins[("A", idx)]
    return pins[("B", HDR_B.index(name))]


def half(side):
    v = View(side)
    s = v.s
    base, buses, over, dots, numbered = [], [], [], [], []
    front_y = NN_C[1] - 7.62                  # the header nearer the keys, either half
    back_y = NN_C[1] + 7.62
    nn_bottom = NN_C[1] - NN[1] / 2

    def ch(k):                                # channel lanes between row 0 and the nice!nano
        return nn_bottom - 0.8 - 0.55 * k

    def ob(k):                                # lanes over the board, between its two headers
        return front_y + 2.2 + 0.66 * k       # 0-4 cols 0-4, 5-6 cols 5-6, 7 bat-, 8 row 5, 9-13 rows 0-4, 14 B+, 15-16 reset

    def rim(k):                               # lanes up the inner edge, past column 6
        return 7 * u + 0.8 + 0.62 * k

    def mid(x):                               # nearest gap between two header pins
        x0 = NN_C[0] + NN[0] / 2 - 2.83
        i = round((x0 - x) / 2.54 - 0.5)
        i = min(max(i, 0), 10)
        return x0 - 2.54 * (i + 0.5)

    def into_pin(pts, P, lane_ch, lane_ob):
        """Finish a path that is at channel height (below the board) onto pin P."""
        if abs(P[1] - front_y) < 0.1:
            return pts + [(P[0], lane_ch), P]
        xm = mid(P[0])
        return pts + [(xm, lane_ch), (xm, lane_ob), (P[0], lane_ob), P]

    # ---- plates and keep-outs ----
    base.append(v.path(BODY, "case"))
    base.append(v.path(MOD, "case"))
    title_y = v.px((0, v.y1))[1] - 26
    base.append(text(v.size()[0] / 2, title_y, f"{side.upper()} HALF · PLATES FROM BELOW · BACK EDGE AWAY FROM YOU · TO SCALE", "edge"))
    bx, by = D["batt_c"], D["batt"]
    base += grp("Battery", "body", [v.box(bx, by[0], by[1], 0, "keepout", 6)])

    # ---- main keys: switch, pins, diode, labels ----
    rows_pts = {}
    for c in range(7):
        for r in range(COL_ROWS[c]):
            k = kpos(c, r)
            name = f"{side[0].upper()} {LEG[side][r][c]}"
            base += grp(f"key {r}.{c}", "body", [v.box(k, 14, 14, 0, "part"),
                                                 text(*add(v.px(k), (0, 2)), LEG[side][r][c], "keyname"),
                                                 text(*add(v.px(k), (0, 16)), f"r{r} c{c}", "pinmini")])
            pc, pd = add(k, v.pin_off(MX_COL)), add(k, v.pin_off(MX_DIODE))
            pb = (pd[0], k[1] + BUS_UP)
            over += grp(f"key {r}.{c}", f"row{r}", v.diode(pd, pb) + [v.dot(pb, "joint j-row")])
            dots += grp(f"key {r}.{c}", f"row{r}", [v.dot(pd, "joint j-row")])
            dots += grp(f"key {r}.{c}", f"col{c}", [v.dot(pc, "joint j-col")])
            rows_pts.setdefault(r, []).append((c, k[1] + BUS_UP))

    # ---- row buses: bare copper, stepping with the column stagger ----
    row_end = {}
    for r, segs in rows_pts.items():
        pts = [(segs[0][0] * u + 2, segs[0][1])]
        for i, (c, y) in enumerate(segs):
            if i:
                pts += [(c * u, segs[i - 1][1]), (c * u, y)]
        pts.append(((segs[-1][0] + 1) * u - 2, segs[-1][1]))
        lx, ly = v.px(pts[0])
        buses += grp("bus", f"row{r}", v.rail(pts, "row") + [text(lx + (8 if s > 0 else -8), ly + 4, f"ROW {r}", "busname", "start" if s > 0 else "end")])
        row_end[r] = pts[-1]

    # ---- column buses: bare copper down each column, switch pins soldered straight on; sleeves where rows cross ----
    col_top, col_bot = {}, {}
    for c in range(7):
        top = add(kpos(c, 0), v.pin_off(MX_COL))
        bot = add(kpos(c, COL_ROWS[c] - 1), v.pin_off(MX_COL))
        col_top[c], col_bot[c] = top, bot
        buses += grp("bus", f"col{c}", v.rail([top, bot], "col")
                     + [text(*v.px((bot[0], bot[1] - 14.5)), f"COL {c}", "busname")])
        for r in range(1, COL_ROWS[c]):
            buses += grp("bus", f"row{r} col{c}", [v.sleeve((top[0], kpos(c, r)[1] + BUS_UP))])

    # ---- nice!nano ----
    pins = nn_pins(side)
    usb_x = NN_C[0] + NN[0] / 2
    nn = [v.box(NN_C, NN[0], NN[1], 0, "board", 2),
          v.box((usb_x - 3.5, NN_C[1]), 7, 9, 0, "usb", 1),
          text(*add(v.px((usb_x - 3.5, NN_C[1])), (0, 4)), "USB", "usblbl"),
          text(*add(v.px((NN_C[0] - 4, NN_C[1])), (0, 4)), "nice!nano · components up", "port")]
    used = set(ROW_PIN + COL_PIN + ["B+", "RST", "GND"])
    for (hdr, i), p in pins.items():
        name = (HDR_A if hdr == "A" else HDR_B)[i]
        cls = "pad pad-avoid" if name in AVOID else ("pad pad-used" if name in used else "pad pad-off")
        x, y = v.px(p)
        nn.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="3.6" class="{cls}"/>')
        dy = 13 if abs(p[1] - front_y) > 0.1 else -8     # names inside the board
        nn.append(text(x, y + (dy if v.px((0, back_y))[1] > v.px((0, front_y))[1] else -dy + 5), name, "padmini", extra=f' transform="rotate(-90 {f(x)} {f(y + (dy if v.px((0, back_y))[1] > v.px((0, front_y))[1] else -dy + 5))})"'))
    base += grp("nice!nano", "body", nn)

    # ---- power switch, reset ----
    psw, rst = D["psw_c"], D["rst_c"]
    pw, pp = D["psw"], D["psw_pitch"]                                  # SS12D10G5: body, pin pitch
    sw_pins = [add(psw, (dx * s, -pw[1] / 2)) for dx in (-pp, 0.0, pp)]   # outer, common, outer
    base += grp("Power switch", "body", [v.box(psw, pw[0], pw[1], 0, "part", 1),
                                         text(*add(v.px(psw), (0, -14)), "power switch", "pinmini")]
                + [v.dot(p, "joint j-pwr") for p in sw_pins[:2]])
    rst_pins = [add(rst, (-3.25 * s, -2.25)), add(rst, (3.25 * s, 2.25))]   # two diagonal legs
    base += grp("Reset", "body", [v.box(rst, 6, 6, 0, "part", 1), text(*add(v.px(rst), (0, 3)), "RST", "pinmini")]
                + [v.dot(p, "joint j-rst") for p in rst_pins])

    # ---- thumb module: switches, diodes, row 5 bus; its 5 wires to the connector ----
    ang = THUMB_ROT                                        # top-view turn in left geometry, both halves
    mod_keys = [mod_world(D["red_c"])] + [mod_world(t) for t in D["thumb_c"]]
    caps = [(D["red_w"] * u, u)] + [(u, D["thumb_h"] * u)] * 3
    bus5 = []
    for i, k in enumerate(mod_keys):
        c = MOD_COLS[i]
        leg = THUMB_LEG[side][i]
        kang = ang + (180 if i == 0 else 0)               # the red key's switch sits turned round, pins toward the thumbs
        base += grp(f"thumb {leg}", "body", [v.box(k, 14, 14, ang, "part"),
                                             text(*add(v.px(k), (0, 2)), leg, "keyname"),
                                             text(*add(v.px(k), (0, 16)), f"r5 c{c}", "pinmini")])
        pd = add(k, v.pin_off(MX_DIODE, kang))
        pb = add(k, v.pin_off((MX_DIODE[0], BUS_UP), kang))
        over += grp(f"thumb {leg}", "row5", v.diode(pd, pb) + [v.dot(pb, "joint j-row")])
        dots += grp(f"thumb {leg}", "row5", [v.dot(pd, "joint j-row")])
        bus5.append(pb)
    bus5 = [bus5[3], bus5[2], bus5[0], bus5[1]]            # innermost thumb, middle, red key, outermost
    buses += grp("bus", "row5", v.rail(bus5, "row") + [text(*add(v.px(bus5[0]), (0, 18)), "ROW 5", "busname")])

    # connector (JST XH pair in its floor pocket: tray-side half to the harness, module-side half's leads through the hinge) and the two wire slots
    cx0, cy0, (cl, ct, _) = D["conn_x"], D["conn_y"], D["conn"]
    conn_c = mod_world((cx0 + cl / 2, cy0 + ct / 2))
    conn_pin = [mod_world((cx0 + 2.5 + i * 2.5, cy0)) for i in range(5)]
    base += grp("Connector", "body", [v.box(conn_c, cl, ct + 1, HINGE_ROT, "jst", 1),
                                      text(*add(v.px(conn_c), (0, -12)), "JST XH 5-pin", "pinmini")])
    # the wires run along the hinge axis inside the inner hinge unit; these are its two slots
    slot_m = [mod_world((D["wire_xm"] + 0.5 + i * 0.6, -D["gap"] / 2 - 3.5 - 1.1 * i)) for i in range(5)]
    slot_b = [mod_world((D["wire_xb"] + 0.3 + i * 0.6, D["gap"] / 2 + 1.5)) for i in range(5)]

    # ---- numbered wires ----
    def number(w, pts, kind, owner, net, frm, to, badge_at=(0,)):
        items = v.wire(pts, kind)
        for end in badge_at:
            a, b = (pts[0], pts[1]) if end == 0 else (pts[-1], pts[-2])
            d = math.hypot(b[0] - a[0], b[1] - a[1]) or 1
            t = min(4.5, d / 2) if end == 0 else min(4.5, d * 0.6)
            q = (a[0] + (b[0] - a[0]) * t / d, a[1] + (b[1] - a[1]) * t / d)
            items.append(badge(*v.px(q), w, kind))
        numbered.append(dict(w=w, kind=kind, owner=owner, net=net, frm=frm, to=to, items=items))

    # rows 0-4: inner end of the bus, up the inner edge, along the channel, onto the pin
    for r in range(5):
        e = row_end[r]
        pts = [e, (rim(r), e[1]), (rim(r), ch(r))]
        number(r + 1, into_pin(pts, pin_xy(side, ROW_PIN[r]), ch(r), ob(9 + r)), "row", "bus", f"row{r}",
               f"Row {r} bus, inner end", ROW_PIN[r])
    # row 5: male lead from the connector
    p0 = conn_pin[0]
    pts = [p0, (p0[0], p0[1] - 2.5), (rim(5), p0[1] - 2.5), (rim(5), ch(5))]
    number(6, into_pin(pts, pin_xy(side, ROW_PIN[5]), ch(5), ob(8)), "row", "Connector", "row5",
           "Connector pin 1 (tray-side half)", ROW_PIN[5], badge_at=())

    # columns 0-4: up from the top of the bus, along the top rim, into the strip and over the board
    def floor_y(k):
        return -(STAG[k] + 0.5) * u + BUS_UP + 1.0

    for c in range(5):
        top = col_top[c]
        lane = lambda k: ob(c) if k >= 4 else floor_y(k) + 0.9 + 0.9 * c
        pts = [top, (top[0], lane(c))]
        for k in range(c + 1, 5):
            pts += [(k * u, lane(k - 1)), (k * u, lane(k))]
        P = pin_xy(side, COL_PIN[c])
        pts += [(P[0], lane(4)), P]
        number(7 + c, pts, "col", "bus", f"col{c}", f"Column {c} bus ({FINGER[c]}), top end", COL_PIN[c])
    # columns 5, 6: straight up through the channel
    for c in (5, 6):
        top = col_top[c]
        lane_ch = ch(6 + c - 5)
        number(7 + c, into_pin([top, (top[0], lane_ch)], pin_xy(side, COL_PIN[c]), lane_ch, ob(5 + c - 5)),
               "col", "bus", f"col{c}", f"Column {c} bus ({FINGER[c]}), top end", COL_PIN[c])

    # thumb link, tray side: male leads 2-5 to the bottom ends of column buses 3-6
    for i, c in enumerate(MOD_COLS):
        p0, t = conn_pin[i + 1], col_bot[c]
        y_run = p0[1] - 2.5 - 0.9 * (i + 1)
        number(14 + i, [p0, (p0[0], y_run), (t[0], y_run), t], "col", "Connector", f"col{c}",
               f"Connector pin {i + 2} (tray-side half)", f"Column {c} bus, bottom end", badge_at=(-1,))
    # thumb link, module side: the module-side half's leads from the row 5 bus and each key's column pin, out through the slots
    ends = [bus5[0]] + [add(k, v.pin_off(MX_COL, ang + (180 if i == 0 else 0))) for i, k in enumerate(mod_keys)]
    labels = ["Row 5 bus, innermost thumb end"] + [f"{THUMB_LEG[side][i]} key, column pin" for i in range(4)]
    for i in range(5):
        kind = "row" if i == 0 else "col"
        net = CONN_PIN[i]
        owner = "Thumb module"
        if i:
            dots.extend(grp(owner, net, [v.dot(ends[i], "joint j-col")]))
        lx = (ends[i][0] - A[0]) * H[0] + (ends[i][1] - A[1]) * H[1]          # module frame x of the pin
        run = mod_world((lx, -D["gap"] / 2 - 3.5 - 1.1 * i))
        number(18 + i, [ends[i], run, slot_m[i], slot_b[i], conn_pin[i]], kind, owner, net,
               labels[i], f"Connector pin {i + 1} (module-side half)")

    # power: battery + to the switch, switch to B+, battery - to GND; reset to RST and GND
    plug = (D["batt_c"][0] + D["batt"][0] / 2 + 6, D["batt_c"][1])
    base += grp("Battery", "body", [v.box(plug, 6, 5, 0, "jst", 1), text(*add(v.px(plug), (0, -10)), "JST-PH", "pinmini")])
    x_gap = 5 * u                                # between columns 4 and 5
    sp = sw_pins[1]
    number(23, [add(plug, (0, 1.2)), (x_gap, plug[1] + 1.2), (x_gap, sp[1] - 1.5), (sp[0], sp[1] - 1.5), sp],
           "pwr", "Battery", "bat", "Battery JST-PH pigtail, red", "Power switch, middle pin", badge_at=(0, -1))
    so = sw_pins[0]
    bp = pin_xy(side, "B+")
    number(24, [so, (so[0], ob(14)), (bp[0], ob(14)), bp], "pwr", "Power switch", "bplus",
           "Power switch, outer pin", "B+")
    g = pin_xy(side, "GND", 1)
    pts = [add(plug, (0, -1.2)), (rim(6), plug[1] - 1.2), (rim(6), ch(8))]
    number(25, into_pin(pts, g, ch(8), ob(7)), "gnd", "Battery", "gnd", "Battery JST-PH pigtail, black", "GND (D1-D9 header)")
    rp, rg = pin_xy(side, "RST"), pin_xy(side, "GND", 2)
    for w, p0, P, to, lane in ((26, rst_pins[0], rp, "RST", ob(15)), (27, rst_pins[1], rg, "GND (B+ header)", ob(16))):
        number(w, [p0, (p0[0], lane), (P[0], lane), P], "rst", "Reset", "rst" if w == 26 else "gnd", f"Reset button, leg {w - 25}", to)

    wires = []
    for e in numbered:
        wires += grp(e["owner"], e["net"], e["items"], e["w"])
    W, Hh = v.size()
    return base + buses + over + wires + dots, W, Hh, numbered


HALF_GAP = 90                 # px between the two halves in the combined drawing


def both_svg():
    """Both halves side by side in one drawing: left half on the left, right half on the right,
    each plate seen from below as it lies while you wire it."""
    li, wl, hl, numbered = half("left")
    ri, wr, hr, _ = half("right")
    W, Hh = wl + HALF_GAP + wr, max(hl, hr)
    x = wl + HALF_GAP / 2
    sep = f'<line x1="{f(x)}" y1="40" x2="{f(x)}" y2="{f(Hh - 40)}" class="cutline"/>'
    svg = (f'<svg class="wiring" viewBox="0 0 {f(W)} {f(Hh)}" role="img" '
           f'aria-label="Wiring of both halves, plates seen from below: left half on the left, right half on the right">\n'
           + '<g class="half-left">\n' + "\n".join(li) + "\n</g>\n" + sep + "\n"
           + f'<g class="half-right" transform="translate({f(wl + HALF_GAP)} 0)">\n' + "\n".join(ri) + "\n</g>\n</svg>")
    return svg, numbered


# ---------------------------------------------------------------- the nice!nano pin figure

def pinout_svg():
    """Both halves' boards as they lie when you wire them (plate upside down, components up)."""
    k = 9.0
    out = []
    for j, side in enumerate(("left", "right")):
        ox = 40 + j * 470
        bw, bl = NN[1] * k, NN[0] * k                      # drawn USB-C up
        bx, by = ox + 60, 90
        out.append(text(bx + bw / 2, 30, f"{side.upper()} HALF", "edge"))
        out.append(text(bx + bw / 2, 48, "USB-C toward the " + ("left" if side == "left" else "right") + " edge when you wire it (the inner wall)", "hingesub"))
        out.append(f'<rect x="{f(bx)}" y="{f(by)}" width="{f(bw)}" height="{f(bl)}" rx="8" class="board"/>')
        out.append(f'<rect x="{f(bx + bw / 2 - 4.5 * k)}" y="{f(by - 10)}" width="{f(9 * k)}" height="{f(3 * k)}" rx="5" class="usb"/>')
        # drawn turned so USB is up: on the left half the D1-D9 header is then on the left, on the right half on the right
        a_left = side == "left"
        for hdr, names in (("A", HDR_A), ("B", HDR_B)):
            on_left = (hdr == "A") == a_left
            x = bx + (14 if on_left else bw - 14)
            for i, name in enumerate(names):
                y = by + 2.83 * k + 2.54 * k * i
                use = (f"row {ROW_PIN.index(name)}" if name in ROW_PIN else f"col {COL_PIN.index(name)}" if name in COL_PIN
                       else {"B+": "switch", "RST": "reset", "GND": "bat − / reset"}.get(name, AVOID.get(name, "")))
                kind = ("row" if name in ROW_PIN else "col" if name in COL_PIN else "pwr" if name == "B+" else
                        "gnd" if name == "GND" else "rst" if name == "RST" else None)
                cls = f"pad pad-{kind}" if kind else ("pad pad-avoid" if name in AVOID else "pad pad-off")
                out.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="7" class="{cls}"/>')
                tx = x - 16 if on_left else x + 16
                out.append(text(tx, y + 4.5, name, "padname", "end" if on_left else "start"))
                if use:
                    out.append(text(tx + (-46 if on_left else 46), y + 4.5, use, f"pinlabel tt-{kind}" if kind else "pinlabel",
                                    "end" if on_left else "start"))
    return ('<svg viewBox="0 0 940 440" role="img" aria-label="nice!nano pinout for each half as it lies while wiring: '
            'rows 0 to 5 on D4 to D9, columns pinky outer to innermost on D21, D20, D19, D18, D15, D14, D1, '
            'battery through the switch to B+, reset to RST and GND.">\n' + "\n".join(out) + "\n</svg>")


def diode_key_svg():
    cx = 200
    o = [f'<line x1="{cx}" y1="20" x2="{cx}" y2="80" class="w w-row"/>', f'<line x1="{cx}" y1="240" x2="{cx}" y2="300" class="w w-plain"/>',
         f'<rect x="{cx - 22}" y="80" width="44" height="160" rx="8" class="diode"/>',
         f'<rect x="{cx - 22}" y="80" width="44" height="48" rx="8" class="band"/>',
         f'<rect x="{cx - 22}" y="104" width="44" height="24" class="band"/>',
         f'<rect x="{cx - 22}" y="80" width="44" height="160" rx="8" class="diode-edge"/>',
         text(cx + 40, 108, "black band", "note", "start"), text(cx + 40, 190, "red glass body", "note", "start"),
         text(cx + 40, 34, "band end → row bus", "note", "start"), text(cx + 40, 294, "plain end → switch pin", "note", "start"),
         text(470, 140, "Current flows column → switch → row", "note", "start"),
         text(470, 158, "(col2row), so the black band is", "note", "start"), text(470, 176, "always on the row side.", "note", "start")]
    return ('<svg viewBox="0 0 820 320" role="img" aria-label="A 1N4148 diode: black band end to the row bus, plain end to the switch pin.">\n'
            + "\n".join(o) + "\n</svg>")


# ---------------------------------------------------------------- page

def harness_html(numbered):
    groups = [("Plate to nice!nano", range(1, 14)), ("Thumb link, tray side (tray-side half of the JST XH pair)", range(14, 18)),
              ("Thumb link, module side (module-side half's leads)", range(18, 23)), ("Power and reset", range(23, 28))]
    by_w = {e["w"]: e for e in numbered}
    out = []
    for g, ws in groups:
        out.append(f'<tr class="grouprow"><th colspan="4">{g}</th></tr>')
        for w in ws:
            e = by_w[w]
            out.append(f'<tr data-w="{w}" data-o="{e["owner"]}" data-n="{e["net"]}" tabindex="0">'
                       f'<td><span class="numbadge nb-{e["kind"]}">{w}</span></td><td>{e["frm"]}</td><td class="to">{e["to"]}</td>'
                       f'<td><input type="checkbox" aria-label="Wire {w} done" data-done="{w}"></td></tr>')
    return "\n".join(out)


CHECKLIST = [
    ("Plate", "Switches clipped into both plates, all with the pins toward the back (LED window toward you); 2u stabiliser on the red key", "plate"),
    ("Buses", "Column buses: bare copper down each column on the pin nearer the outer edge (right one from below on the left half), switch pins soldered on", "col"),
    ("Buses", "Row buses 0-4: bare copper across, in the gap above each switch row, stepping with the stagger; sleeve every column crossing", "row"),
    ("Keys", "A diode from each switch's other pin to its row bus, black band at the bus (64 on the main plates)", "row"),
    ("Thumbs", "Thumb plates: diodes, then the row 5 bus from the innermost thumb to the red key", "row"),
    ("Thumbs", "Module-side half of the JST XH pair (wires 18-22): leave its leads loose for now. They run inside the inner thumb hinge and get soldered to the thumb plate (pin 1 to row 5, pins 2-5 to the red key and the thumbs' column pins) after the module is on: see Assembly", "col"),
    ("nice!nano", "nice!nano hot-glued component side up between its two blocks, USB-C at the inner edge; Kapton under it", "plate"),
    ("Harness", "Wires 1-13: rows and columns to the nice!nano (harness table)", "row"),
    ("Harness", "Wires 14-17 and 6: tray-side half of the JST XH pair, leads to the bottom of columns 3-6 and to D9", "col"),
    ("Power", "Power switch and reset button glued in the top strip; wires 23-27; battery JST-PH pigtail", "pwr"),
    ("Test", "Meter tests below, both halves, before the plates go on", "rst"),
]


def checklist_html():
    return "\n".join(f'<li><label><input type="checkbox" id="chk{i}"><span class="swatch sw-{kind}"></span>'
                     f'<span class="grp">{g}</span><span class="what">{what}</span></label></li>'
                     for i, (g, what, kind) in enumerate(CHECKLIST))


# ---------------------------------------------------------------- bill of materials, assembly

M2_PER_HALF = [("plate to tray", 9), ("thumb plate to thumb tray", 4), ("thumb hinge", 1), ("wing hinge", 2), ("tenting leg", 1)]
M2_HALF = sum(n for _, n in M2_PER_HALF)

ROBU = "https://robu.in/product/"
STOCK_CHECKED = "2026-10-14"   # every robu.in link was in stock on this day
BOM = [   # (part, qty, notes, [(link text, url), ...])
    ("Electronics", [
        ("nice!nano v2", "2", "already have. One per half. If you ever need another: the linked board is a Pro Micro-format nRF52840 (the usual nice!nano v2 clone), but its listing doesn't say nice!nano: before soldering, check it has B+ and B− battery pads and that its pin labels match the pinout below (ZMK board <code>nice_nano_v2</code>)",
         [("robu.in: Promicro nRF52840", ROBU + "promicro-nrf52840-development-board/")]),
        ("MX switches (3-pin or 5-pin)", "72", "36 per half. 5-pin ones: clip the two plastic legs (plate mount)",
         [("StacksKB: switches", "https://stackskb.com/product-category/switches/"), ("Meckeys: switches", "https://meckeys.com/category/accessories/keyboard-accessories/key-switches/")]),
        ("1N4148 diode, through-hole (DO-35)", "72", "one per key. Not the SMD (SOD-323/SOD-123) ones",
         [("robu.in: 1N4148 DO-35", ROBU + "1n4148pf-semtech-do-35-switching-diodes-rohs/")]),
        ("LiPo KP-523450 (5.2 × 34 × 50 mm), with connector", "2", "sold as 2000 mAh; a cell this size really holds ~1000 mAh. Lies on the tray floor under the keys, in a fence sized for it, 0.3 mm under the switch pins: nothing thicker fits. The listing doesn't mention a protection circuit: check for a small board under the tape at the lead end and don't use a cell without one. The connector type isn't stated (probably JST-PH 2.0): the harness end needs the mating half. Check polarity before plugging in. Your HCY-502030 also fits: set <code>batt = [30, 20, 5]</code>",
         [("Amazon.in: KP-523450 with connector", "https://www.amazon.in/dp/B0GQSXK3YX")]),
        ("SS12D10G5 slide switch", "2", "already have. In battery +; hangs under the plate's top strip, lever out of the top wall",
         [("robu.in: SS12D10G5", ROBU + "ss12d10g5-shou-han-direct-insert-2a-single-pole-double-throw-spdt-125v-3000-times-plugin-slide-switches-rohs/")]),
        ("6 × 6 × 5 mm tact switch, through-hole", "2", "reset, pressed with a pin through the floor",
         [("robu.in: 6×6×5 mm tact switch", ROBU + "6x6x5-tactile-push-button-switch/")]),
        ("Thumb link: JST XH 2.54 mm 5-pin plug + socket, both with 300 mm 26 AWG leads", "2 pairs", "one pair per half. Lies flat in a pocket in the tray floor against the hinge wall. The socket's leads are the 5 wires through the hinge tube (cut to length); the plug's leads go to the harness. One pack is 4 pieces: if that means 2 plugs + 2 sockets it's exactly enough, else get 2",
         [("robu.in: 5-pin JST XH plug + socket with cable (4 pcs)", ROBU + "5-pin-jst-xh-2-54mm-pitch-plug-and-socket-with-cable-4-pcs/")]),
    ]),
    ("Keys", [
        ("Keycaps", "64 × 1u, 6 × 1.5u, 2 × 2u", "1.5u on the thumbs, 2u on the red keys. Or 1u everywhere: set <code>thumb_h = 1</code>, <code>red_w = 1</code>",
         [("StacksKB: keycaps", "https://stackskb.com/"), ("Meckeys: keycaps", "https://meckeys.com/category/accessories/keyboard-accessories/keycaps/")]),
        ("2u plate-mount stabiliser", "2", "red keys; not needed with a 1u cap there",
         [("StacksKB: Cherry plate-mount 2u", "https://stackskb.com/store/genuine-cherry-mx-plate-mount-stabilizers-2u/")]),
    ]),
    ("Wire and sundries", [
        ("Solid copper wire, 24 AWG (0.5 mm)", "~4 m", "row and column buses. Bare tinned is easiest; solid-core PVC wire with the insulation stripped off works the same",
         [("robu.in: 24 AWG solid core (strip it)", ROBU + "24-awg-solid-core-insulated-wire-pvc/")]),
        ("Silicone wire, 28 AWG, stranded, 2 colours", "~6 m total", "harness to the nice!nano, power, reset: 27 wires per half, ~10 cm each. Two colours (rows / columns) make it much easier to trace",
         [("robu.in: 28 AWG black", ROBU + "high-quality-ultra-flexible-28awg-silicone-wire-1000-m-black/"),
          ("blue", ROBU + "high-quality-ultra-flexible-28awg-silicone-wire-1000m-blue/"),
          ("white", ROBU + "high-quality-ultra-flexible-28awg-silicone-wire-1000m-white/")]),
        ("Heat-shrink, 2.5 mm", "~1 m", "already have. Cut into ~5 mm sleeves wherever a row bus crosses a column bus (~50 crossings)",
         [("robu.in: 2.5 mm black heat-shrink", ROBU + "heat-shrink-sleeve-2-5mm-black-industrial-grade-woer-hst/")]),
        ("Insulating tape (Kapton or PVC)", "1 roll", "under and around the nice!nano. Not copper-foil \"high temperature\" tape: it conducts",
         [("robu.in: PVC insulation tape 19 mm", ROBU + "electrical-insulation-multicomp-pro-pvc-tape-1920bl-pvc-polyvinyl-chloride-blue-19-mm-x-20-m/")]),
        ("Hot glue", "", "already have. nice!nano, switch, reset button; strain relief at the hinge slots",
         [("robu.in: glue sticks", ROBU + "all-purpose-hot-melt-glue-sticks-for-glue-gun-5pcs/")]),
        ("Rubber feet, self-adhesive", "~8", "under the trays and the leg foot (any small bumpers)", []),
    ]),
    ("Hardware", [
        ("M2 × 8 countersunk screw", str(2 * M2_HALF), f"{M2_HALF} per half: " + ", ".join(f"{n} {w}" for w, n in M2_PER_HALF)
         + ". They cut their own thread in 1.8 mm printed pilots: no inserts, no nuts. 2 packs of 25",
         [("robu.in: M2 × 8 CSK, 25 pcs", ROBU + "easymech-ss-304-csk-countersunk-philips-head-m2-x-8-mm-bolt-25-pcs/")]),
    ]),
    ("Printed (case/3mf/moonlander.3mf, PLA)", [
        ("plate, tray, thumb_plate, thumb_tray", "1 each per half", "trays with supports (hinge bosses lie sideways)", []),
        ("palm (the wing)", "1 per half", "prints standing on its back edge, with a brim and supports", []),
        ("leg (tenting arm)", "2", "same part for both halves", []),
        ("hinge_cap", "8", "4 per half: 1 thumb hinge, 2 wing, 1 leg", []),
        ("fit_plate", "1", "print first: switch fit and M2 bite", []),
    ]),
    ("Tools", [
        ("Soldering iron, flush cutters, multimeter, glue gun", "", "", []),
        ("Screwdriver for your M2 heads", "", "already have. PH0 for the Phillips ones linked above (1.3 mm hex key for hex-socket ones)",
         [("robu.in: Stanley PH0 screwdriver", ROBU + "stanley-stmt60802-8-cushion-grip-screwdriver/")]),
    ]),
]


def bom_html():
    out = []
    for g, rows in BOM:
        out.append(f'<tr class="grouprow"><th colspan="4">{g}</th></tr>')
        for a, q, n, links in rows:
            ls = "<br>".join(f'<a href="{u}" target="_blank" rel="noopener">{t}</a>' for t, u in links)
            out.append(f'<tr><td>{a}</td><td class="qty">{q}</td><td>{n}</td><td class="buy">{ls}</td></tr>')
    return "\n".join(out)


PREVIEW = "../case/preview"
ASSEMBLY = [
    ("Before you print", None, [
        "Print <code>case/layout_left.svg</code> at 100 % (mirror it for the right hand), rest your hands on it and check the thumb reach. Tune <code>thumb_rot</code>, <code>thumb_s0</code>, <code>thumb_off</code>, <code>hinge_drop</code> in <code>moonlander.scad</code> and re-run <code>case/build.sh</code>.",
        "Print <code>fit_plate</code> on its own: switches must click in firmly (else <code>switch_cut</code>) and an M2 must bite in the pilot (else <code>pilot_d</code>).",
        "Print the rest from <code>case/3mf/moonlander.3mf</code> (every part already in its print orientation).",
    ]),
    ("Wire the plates", None, [
        "Switches into both plates, all pins toward the back edge; the 2u stabiliser on the red key.",
        "Follow the drawing above and the checklist below: buses, diodes, then wires 1-17 and 23-27 per half.",
        "Tray-side half of the thumb link (JST XH) on the main harness (wires 6, 14-17). The module-side half's leads stay loose at the thumb end: they go through the hinge first.",
        "nice!nano hot-glued between its blocks under the top strip, USB-C toward the inner edge.",
        "Flash, then do the meter tests at the bottom of this page.",
    ]),
    ("Thumb wires through the hinge", f"{PREVIEW}/assembly.png", [
        "Plates off. Plug the two halves of the JST XH pair together and lay the pair flat in its pocket in the tray floor, against the hinge wall.",
        "Push the module-side half's 5 leads (cut to length, ends bared) out through the slot in the tray's inner hinge knuckle, so they come out of the knuckle's bore. The plug stays in the tray: it can't pass the tube.",
        "Thread them into the end of the thumb tray's tube, along it, and out through the slot in its knuckle into the thumb tray.",
    ]),
    ("Thumb module on", None, [
        "Hold the thumb tray level with the tray, off to the outer side along the hinge, and slide it in along the hinge, taking up the leads' slack. Its outer knuckle goes onto the tray's boss and its tube into the tray's inner knuckle, both at once.",
        "Push until the teeth mesh at the angle you want (0, 15, 30 or 45°). One cap on the outer end, 1 × M2 into the boss. This one screw clamps both hinge units.",
        "Solder the 5 leads to the thumb plate: pin 1 to row 5, pins 2-5 to the red key and the thumbs' column pins (wires 18-22). Tilt through the full range once: the leads only twist.",
        "Thumb plate onto the thumb tray, 4 × M2.",
    ]),
    ("Close the main half", None, [
        "Battery in its fence, JST-PH plugged in, switch off.",
        "Plate into the tray (the USB-C, switch and reset notches are open at the top), 9 × M2.",
    ]),
    ("Wing and leg", f"{PREVIEW}/all.png", [
        "Wing: hold it in front of the tray, off to the outer side, and slide it in along the front edge. Its outer knuckle goes onto the tray's boss and its own boss into the tray's inner lug. A cap on each end, 1 × M2 each. Tighten until it swings stiffly but still drops under its own weight.",
        "Leg: arm onto the boss on the inner wall, teeth meshed, stowed (pointing forward along the wall). Cap, 1 × M2.",
    ]),
    ("Using it", f"{PREVIEW}/tented_front.png", [
        "Thumb angle: loosen the thumb hinge's one M2 about two turns, slide the module ~1 mm outward so the teeth come apart, tilt it a step, push back, tighten.",
        "Tenting: loosen the leg's M2, pull the arm out so its teeth come apart, swing it down and tighten. Then tilt the thumb module down until it rests on the desk. Leg 15° / 30° / 45° / 60° / 75° / 90° gives about 3° / 7° / 11° / 13° / 15° / 15° of tent; at 90° the thumb module rests on its 30° step.",
        "The wing swings freely: it lies on the desk flat, and tents with the board.",
        "To take the thumb module off: plate off, unplug the JST XH pair, take out the thumb hinge screw and slide it out toward the outer side; the leads come with it through the tube.",
    ]),
]


def assembly_html():
    out = []
    for i, (title, img, steps) in enumerate(ASSEMBLY, 1):
        fig = (f'<img src="{img}" alt="" loading="lazy">' if img else "")
        lis = "".join(f"<li>{t}</li>" for t in steps)
        out.append(f'<div class="astep{" withimg" if img else ""}"><div><h3><span class="anum">{i}</span>{title}</h3>'
                   f'<ol class="steps">{lis}</ol></div>{fig}</div>')
    return "\n".join(out)


PICK_PARTS = ["nice!nano", "Thumb module", "Connector", "Power switch", "Reset", "Battery"]
PICK_BUSES = [(f"row{r}", f"Row {r}") for r in range(6)] + [(f"col{c}", f"Col {c}") for c in range(7)]


def bom_markdown():
    def md(h):   # page HTML -> markdown
        return re.sub(r"</?code>", "`", h).replace("<br>", " ")
    out = ["| Part | Qty | Notes | Buy |", "|---|---|---|---|"]
    for g, rows in BOM:
        out.append(f"| **{g}** | | | |")
        for a, q, n, links in rows:
            out.append(f"| {md(a)} | {q} | {md(n)} | {' · '.join(f'[{t}]({u})' for t, u in links)} |")
    return "\n".join(out)


def write_readme_bom():
    p = HERE.parent / "README.md"
    s = p.read_text()
    s = re.sub(r"(<!-- BOM:[^\n]*-->\n).*?(<!-- /BOM -->)", lambda m: m.group(1) + bom_markdown() + "\n" + m.group(2), s, flags=re.S)
    p.write_text(s)


def main():
    write_readme_bom()
    both, numbered = both_svg()
    parts = "".join(f'<button type="button" data-pick="{p}" aria-pressed="false">{p}</button>' for p in PICK_PARTS)
    buses = "".join(f'<button type="button" data-bus="{n}" aria-pressed="false">{lab}</button>' for n, lab in PICK_BUSES)
    html = ((HERE / "template.html").read_text()
            .replace("{{BOTH}}", both).replace("{{BOM}}", bom_html()).replace("{{ASSEMBLY}}", assembly_html())
            .replace("{{HARNESS}}", harness_html(numbered)).replace("{{HARNESS_N}}", str(len(numbered)))
            .replace("{{PINOUT}}", pinout_svg()).replace("{{DIODE}}", diode_key_svg())
            .replace("{{CHECKLIST}}", checklist_html()).replace("{{CHECK_N}}", str(len(CHECKLIST)))
            .replace("{{PICK_PARTS}}", parts).replace("{{PICK_BUSES}}", buses))
    (HERE / "wiring.html").write_text(html)
    print(f"== wiring/wiring.html: {len(numbered)} wires per half")


if __name__ == "__main__":
    main()
