#!/usr/bin/env bash
# Clash checks, every printable STL, preview images, 1:1 paper template.
#
#   stl/fit-tests/  print first: switch holes + M3 pilot
#   stl/left/       plate, tray, thumb_plate, thumb_tray, palm
#   stl/right/      the same, mirrored
#   stl/leg.stl x2, stl/hinge_cap.stl x8
#   layout_left.svg   print at 100 %, rest your hands on it before printing plastic
#   3mf/moonlander.3mf  everything above (both halves) packed on 4 P1S plates (make_3mf.py)
set -euo pipefail
cd "$(dirname "$0")"
S=scad/moonlander.scad
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

stl() {  # stl <side> <part> <out>
    echo "== $3"
    mkdir -p "$(dirname "stl/$3")"
    openscad -q -D "part=\"$2\"" -D "side=\"$1\"" -o "stl/$3" $S
}

check() {  # check <part>: clash tests must come out empty
    local out
    out=$(openscad -D "part=\"$1\"" -o "$TMP/check.stl" $S 2>&1 || true)
    if grep -q 'top level object is empty' <<<"$out"; then
        echo "== $1 ok"
    else
        cp "$TMP/check.stl" /tmp/moonlander-check.stl 2>/dev/null || true
        echo "== $1 FAILED: parts overlap, see /tmp/moonlander-check.stl" >&2; exit 1
    fi
}

check clash_caps     # main keycaps vs thumb keycaps, tilt 0 .. tilt_max
check clash_hinge    # thumb module vs tray / plate / wing / leg over the tilt range
check clash_tray     # electronics vs switches, walls, plate; switches vs tray
check clash_wing     # wing over its swing vs tray, plate, caps, leg, thumb module
check clash_leg      # leg arm over its whole turn vs tray, plate, caps
check clash_assembly # thumb module and wing slide on along their hinge axes
check clash_wire     # thumb wires: through the inner hinge knuckles at every tilt

stl left fit_plate fit-tests/fit_plate.stl
stl left leg leg.stl
stl left hinge_cap hinge_cap.stl
for side in left right; do
    for part in plate tray thumb_plate thumb_tray palm; do
        stl "$side" "$part" "$side/$part.stl"
    done
done

python3 make_3mf.py

echo "== layout_left.svg"
openscad -q -D 'part="layout_2d"' -o layout_left.svg $S

echo "== previews"
mkdir -p preview
png() {  # png <part> <camera> <out> [extra -D]
    openscad -q -D "part=\"$1\"" ${4:+-D "$4"} --imgsize=1200,900 --colorscheme=Tomorrow --camera="$2" -o "preview/$3" $S
}
openscad -q -D 'part="all"' --projection=o --imgsize=1200,1000 --colorscheme=Tomorrow --camera=85,-95,0,0,0,0,560 -o preview/top.png $S
png all      70,-70,0,55,0,25,450      all.png
png exploded 70,-70,-10,60,0,25,520    exploded.png
png tented   85,-90,10,70,0,330,560    tented.png
png tented   70,-60,20,90,0,0,420      tented_front.png
png assembly 60,-60,0,55,0,25,560      assembly.png
