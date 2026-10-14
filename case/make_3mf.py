#!/usr/bin/env python3
"""Pack every printable STL (both halves) into one Bambu Studio project, on as few
256 mm plates (P1S) as possible. Run by build.sh after the STLs.

    3mf/moonlander.3mf

Each part is put in its print orientation (plates flipped keycap side down, everything
dropped to z = 0), turned to its smallest footprint (convex hull, rotating calipers),
then packed largest first with maxrects (bounding boxes, 0 or 90 degree turn), 5 mm
apart, 4 mm in from the bed edge, clear of the P1S's front-left exclusion area. Printer, process and filament come from
bambu_p1s_settings.json (copied from the macropad: P1S 0.4, 0.20mm Standard, Textured
PEI 65 / 60 C, PLA Basic).
"""

import math
import uuid
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
STL = HERE / "stl"
OUT = HERE / "3mf"
SETTINGS = HERE / "bambu_p1s_settings.json"
BED = 256
EDGE = 4          # keep clear of the bed edge
GAP = 5           # between parts
PLATE_STRIDE = BED * 1.2   # Bambu Studio lays plates out on a grid, 1/5 bed apart
EXCLUDE = (18 + 6, 28 + 6)  # P1S bed_exclude_area (front left, cutter), + room for the auto brim

# per-object process settings: trays and wings have hinge bosses lying sideways
TRAY = {"enable_support": "1", "support_type": "tree(auto)", "support_on_build_plate_only": "1"}
# (stl, name, flip keycap side down)
PARTS = [(f"{side}/{part}.stl", f"{side} {part}", part in ("plate", "thumb_plate"))
         for side in ("left", "right")
         for part in ("plate", "tray", "thumb_plate", "thumb_tray", "palm")]
PARTS += [("leg.stl", f"leg {i}", False) for i in (1, 2)]
PARTS += [("hinge_cap.stl", f"hinge cap {i}", False) for i in range(1, 9)]
PARTS += [("fit-tests/fit_plate.stl", "fit plate", False)]


def read_stl(path):
    """ASCII STL (OpenSCAD's) -> (vertices, triangles), shared vertices merged."""
    verts, index, tris, cur = [], {}, [], []
    for line in open(path):
        w = line.split()
        if w and w[0] == "vertex":
            v = tuple(float(x) for x in w[1:4])
            if v not in index:
                index[v] = len(verts)
                verts.append(v)
            cur.append(index[v])
            if len(cur) == 3:
                tris.append(tuple(cur))
                cur = []
    return verts, tris


def hull(pts):
    pts = sorted(set(pts))
    if len(pts) < 3:
        return pts

    def half(ps):
        h = []
        for p in ps:
            while len(h) >= 2 and (h[-1][0] - h[-2][0]) * (p[1] - h[-2][1]) - (h[-1][1] - h[-2][1]) * (p[0] - h[-2][0]) <= 0:
                h.pop()
            h.append(p)
        return h[:-1]
    return half(pts) + half(pts[::-1])


def min_rect_angle(verts):
    """Rotation (deg) that gives the smallest-area bounding box of the footprint."""
    h = hull([(round(x, 3), round(y, 3)) for x, y, _ in verts])
    best = (math.inf, 0)
    for i in range(len(h)):
        (x0, y0), (x1, y1) = h[i], h[(i + 1) % len(h)]
        a = -math.atan2(y1 - y0, x1 - x0)
        c, s = math.cos(a), math.sin(a)
        xs = [x * c - y * s for x, y in h]
        ys = [x * s + y * c for x, y in h]
        area = (max(xs) - min(xs)) * (max(ys) - min(ys))
        if area < best[0] - 1e-6:
            best = (area, a)
    return best[1]


def place_ready(verts, flip):
    """Print orientation, smallest footprint, min corner at the origin."""
    if flip:   # 180 deg about x: keycap side down
        verts = [(x, -y, -z) for x, y, z in verts]
    a = min_rect_angle(verts)
    c, s = math.cos(a), math.sin(a)
    verts = [(x * c - y * s, x * s + y * c, z) for x, y, z in verts]
    lo = [min(v[k] for v in verts) for k in range(3)]
    verts = [(x - lo[0], y - lo[1], z - lo[2]) for x, y, z in verts]
    w, d = max(v[0] for v in verts), max(v[1] for v in verts)
    if d > w:   # long side along x; the packer may still turn it
        verts = [(y, w - x, z) for x, y, z in verts]
        w, d = d, w
    return verts, w, d


class MaxRects:
    def __init__(self, size):
        self.free = [(0.0, 0.0, size, size)]

    def insert(self, w, h):
        """Best short side fit; returns (x, y, turned) or None."""
        best = None
        for fx, fy, fw, fh in self.free:
            for rw, rh, turned in ((w, h, False), (h, w, True)):
                if rw <= fw and rh <= fh:
                    score = (min(fw - rw, fh - rh), max(fw - rw, fh - rh))
                    if best is None or score < best[0]:
                        best = (score, fx, fy, rw, rh, turned)
        if best is None:
            return None
        _, x, y, rw, rh, turned = best
        self._split(x, y, rw, rh)
        return x, y, turned

    def _split(self, x, y, w, h):
        out = []
        for fx, fy, fw, fh in self.free:
            if x >= fx + fw or x + w <= fx or y >= fy + fh or y + h <= fy:
                out.append((fx, fy, fw, fh))
                continue
            if x > fx:
                out.append((fx, fy, x - fx, fh))
            if x + w < fx + fw:
                out.append((x + w, fy, fx + fw - x - w, fh))
            if y > fy:
                out.append((fx, fy, fw, y - fy))
            if y + h < fy + fh:
                out.append((fx, y + h, fw, fy + fh - y - h))
        self.free = [r for r in out if not any(
            r != o and r[0] >= o[0] and r[1] >= o[1] and r[0] + r[2] <= o[0] + o[2] and r[1] + r[3] <= o[1] + o[3]
            for o in out)]


def pack(items):
    """items: [(name, verts, tris, w, d)] -> plates: [[(name, verts, tris)]] in bed coords."""
    size = BED - 2 * EDGE + GAP   # every part reserves GAP on its far sides
    plates, bins = [], []
    for name, verts, tris, w, d in sorted(items, key=lambda it: -it[3] * it[4]):
        for i, b in enumerate(bins + [None]):
            if b is None:
                b = MaxRects(size)
                b._split(0, 0, EXCLUDE[0] - EDGE, EXCLUDE[1] - EDGE)
                bins.append(b)
                plates.append([])
            spot = b.insert(w + GAP, d + GAP)
            if spot:
                break
        x, y, turned = spot
        if turned:
            verts = [(d - vy, vx, vz) for vx, vy, vz in verts]
        verts = [(vx + x + EDGE, vy + y + EDGE, vz) for vx, vy, vz in verts]
        plates[i].append((name, verts, tris))
    return plates


def write_3mf(path, plates):
    cols = math.ceil(math.sqrt(len(plates)))
    ns = ('xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
          'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
          'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p"')
    z = zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED)
    z.writestr("[Content_Types].xml", """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
 <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
 <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
 <Default Extension="png" ContentType="image/png"/>
 <Default Extension="gcode" ContentType="text/x.gcode"/>
</Types>
""")
    z.writestr("_rels/.rels", """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>
""")
    res, build, rels, settings, plate_xml = [], [], [], [], []
    next_id, n = 1, 0
    for p, objs in enumerate(plates):
        ox, oy = (p % cols) * PLATE_STRIDE, -(p // cols) * PLATE_STRIDE
        inst = []
        for name, verts, tris in objs:
            n += 1
            cx = (min(v[0] for v in verts) + max(v[0] for v in verts)) / 2
            cy = (min(v[1] for v in verts) + max(v[1] for v in verts)) / 2
            obj_file = f"3D/Objects/object_{n}.model"
            pid, oid = next_id, next_id + 1
            next_id += 2
            vx = "\n".join(f'     <vertex x="{x - cx:.4f}" y="{y - cy:.4f}" z="{zz:.4f}"/>' for x, y, zz in verts)
            tx = "\n".join(f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in tris)
            z.writestr(obj_file, f'<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" {ns}>\n'
                                 f' <metadata name="BambuStudio:3mfVersion">1</metadata>\n <resources>\n'
                                 f'  <object id="{pid}" p:UUID="{uuid.uuid4()}" type="model">\n   <mesh>\n    <vertices>\n{vx}\n    </vertices>\n'
                                 f'    <triangles>\n{tx}\n    </triangles>\n   </mesh>\n  </object>\n </resources>\n <build/>\n</model>\n')
            rels.append(f' <Relationship Target="/{obj_file}" Id="rel-{n}" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>')
            res.append(f'  <object id="{oid}" p:UUID="{uuid.uuid4()}" type="model">\n   <components>\n'
                       f'    <component p:path="/{obj_file}" objectid="{pid}" p:UUID="{uuid.uuid4()}" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>\n'
                       '   </components>\n  </object>')
            build.append(f'  <item objectid="{oid}" p:UUID="{uuid.uuid4()}" transform="1 0 0 0 1 0 0 0 1 {cx + ox:.4f} {cy + oy:.4f} 0" printable="1"/>')
            extra = "".join(f'    <metadata key="{k}" value="{v}"/>\n' for k, v in (TRAY.items() if name.endswith(("tray", "palm")) else []))
            settings.append(f'  <object id="{oid}">\n    <metadata key="name" value="{name}"/>\n    <metadata key="extruder" value="1"/>\n{extra}'
                            f'    <part id="{pid}" subtype="normal_part">\n      <metadata key="name" value="{name}"/>\n'
                            '      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>\n'
                            f'      <mesh_stat face_count="{len(tris)}" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>\n'
                            '    </part>\n  </object>')
            inst.append(f'    <model_instance>\n      <metadata key="object_id" value="{oid}"/>\n      <metadata key="instance_id" value="0"/>\n'
                        f'      <metadata key="identify_id" value="{100 + n}"/>\n    </model_instance>')
        plate_xml.append(f'  <plate>\n    <metadata key="plater_id" value="{p + 1}"/>\n'
                         f'    <metadata key="plater_name" value="plate {p + 1}"/>\n    <metadata key="locked" value="false"/>\n'
                         + "\n".join(inst) + '\n  </plate>')
    z.writestr("3D/3dmodel.model", f'<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" {ns}>\n'
                                   ' <metadata name="Application">BambuStudio-02.08.03.66</metadata>\n'
                                   ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n'
                                   f' <metadata name="Title">{path.stem}</metadata>\n'
                                   ' <resources>\n' + "\n".join(res) + '\n </resources>\n'
                                   f' <build p:UUID="{uuid.uuid4()}">\n' + "\n".join(build) + '\n </build>\n</model>\n')
    z.writestr("3D/_rels/3dmodel.model.rels", '<?xml version="1.0" encoding="UTF-8"?>\n'
               '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n' + "\n".join(rels) + '\n</Relationships>\n')
    z.writestr("Metadata/project_settings.config", SETTINGS.read_text())
    z.writestr("Metadata/model_settings.config", '<?xml version="1.0" encoding="UTF-8"?>\n<config>\n' + "\n".join(settings) + "\n"
               + "\n".join(plate_xml) + '\n</config>\n')
    z.close()


def main():
    OUT.mkdir(exist_ok=True)
    cache, items = {}, []
    for stl, name, flip in PARTS:
        if stl not in cache:
            cache[stl] = read_stl(STL / stl)
        verts, tris = cache[stl]
        verts, w, d = place_ready(verts, flip)
        if min(w, d) > BED - 2 * EDGE or max(w, d) > BED - 2 * EDGE:
            raise SystemExit(f"{name} ({w:.0f} x {d:.0f}) does not fit the bed")
        items.append((name, verts, tris, w, d))
    plates = pack(items)
    path = OUT / "moonlander.3mf"
    write_3mf(path, plates)
    print(f"== 3mf/{path.name}: {len(items)} parts on {len(plates)} plates")
    for p, objs in enumerate(plates):
        print(f"   plate {p + 1}: " + ", ".join(o[0] for o in objs))


if __name__ == "__main__":
    main()
