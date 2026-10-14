// Moonlander-style split, 36 keys per half (72 total), MX, handwired, nice!nano.
// Same key grid and matrix as ZSA's Moonlander (qmk keyboards/zsa/moonlander).
//
// Per half, printed parts:
//   plate        flat switch plate over the 32 main keys + a solid lid over the
//                electronics corner. Wired upside down on the bench, with the
//                nice!nano glued to its underside; screwed onto the tray from the top.
//   tray         floor + walls. Battery fence, USB-C and power switch notches
//                (open at the top, so the wired plate drops in), hinge knuckles, leg pivot.
//   thumb_plate  red key + 3 thumbs.
//   thumb_tray   floor + walls of the thumb module + its hinge knuckles.
//   palm         the wing: wrist rest on a free hinge along the tray's front edge.
//   leg          tenting leg: an arm on the inner wall that swings down in 15 degree steps.
//   hinge_cap    4 per half: washer under the M2 screw that closes a hinge unit.
//
// Like the Moonlander: the thumb module hangs on two hinges along its top edge and tilts
// down (thumb_tilt) in 15 degree steps. Its wires run inside the inner hinge, along the
// axis, so nothing shows and tilting only twists them. To tent, swing the leg down (raises the inner edge),
// then tilt the thumb module down until it rests on the desk: outer edge, leg and thumb
// module carry the board. The wing swings freely and lies on the desk.
//
// Every hinge unit is the same: a knuckle on each part, a printed 5 mm boss on one of them
// through the other, a cap over the boss end and one M2 into the boss. The thumb module
// and the wing each go on by sliding along their axis onto both bosses at once; every cap
// sits on an outside end, so every screw can be reached. The thumb hinge's inner unit is a
// hollow tube for the wires instead, with no screw: the outer screw pulls the whole module
// inward, which closes both sets of teeth.
// Hardware: M2 x 8 countersunk screws only.
//
// The left half is modelled; side = "right" mirrors every part.
// World: z = 0 is the desk. x toward the other half, y away from you.

include <common.scad>

part = "all";       // all | exploded | tented | plate | tray | thumb_plate | thumb_tray
                    // | palm | leg | hinge_cap | fit_plate | layout_2d | clash_*
                    // | assembly (thumb module and wing half slid off their bosses)
side = "left";      // left | right

/* [Key grid, from qmk zsa/moonlander keyboard.json] */
u = 19.05;
stag = [0.375, 0.375, 0.125, 0, 0.125, 0.25, 0.25];   // column stagger, units down from the top
col_rows = [5, 5, 5, 5, 5, 4, 3];                      // keys per column

/* [Case] */
plate_top = 18.5;   // plate top above the desk: switch zone + battery under the keys
plate_t = 3;        // clip_t at the switch + clip relief below
floor_t = 2.5;
wall_t = 2.5;
rim = 8;            // plate border outside the key squares
corner_r = 4;
sw_depth = 10.5;    // below the plate top: switch body 5, pins 3.3, diode + wire
boss_d = 6;

/* [Thumb module] */
hinge_rot = atan(1.875 / 2);   // hinge follows the staircase under cols 4-6 (key corners)
hinge_drop = 1.5;   // body edge this far outside that staircase
thumb_rot = 20;     // thumb row falls this much toward the other half
thumb_s0 = 0.35 * u; // first thumb's centre along the hinge, from col 4's corner
thumb_off = 1;      // extra gap between the red key and the hinge edge
red_w = 2;          // red key cap width (units); one switch
thumb_h = 1.5;      // thumb cap height (units)
thumb_tilt = 0;     // degrees, outer edge down
tilt_max = 45;      // clash-checked at every step up to here

/* [Hinge units (thumb module, wing, leg): knuckle | faces | knuckle, boss through both, cap + M2] */
kn_d = 11;
kn_w = 8;
kn_r_cl = 0.6;      // knuckle to the other part's wall
teeth = 24;         // 15 degree steps
tooth_h = 0.8;
tooth_cl = 0.15;    // between the meshed faces, along the axis
pin_d = 5;          // printed boss on the body knuckle, through the module knuckle
pin_cl = 0.4;       // diametral, module knuckle bore over the boss
cap_d = 10;
cap_t = 2.5;
tilt_step = 360 / teeth;

/* [Wires through the thumb hinge's inner unit: a tube on the module turning in the tray's knuckle] */
tube_od = 6.4;
tube_id = 4.4;      // 5 x 28 AWG silicone wire, bare ends threaded through
tube_cl = 0.4;      // diametral, tray knuckle bore over the tube
tube_in = 3.5;      // how far the tube reaches into the tray's knuckle; past it the wires turn out

/* [Thumb link connector: JST XH 2.54 mm 5-pin plug + socket pair with leads, flat on the tray floor] */
conn = [18, 15.5, 6.6];   // mated pair against the inside of the hinge wall: length (along the wall), width, thickness

/* [Tenting leg, Moonlander style: an arm on the inner wall, toothed pivot, 15 degree steps] */
leg_y = -8;         // pivot along the inner wall, just in front of the USB-C notch
leg_z = 8;
leg_len = 50;       // pivot to foot tip
leg_wd = 10;        // arm width
leg_w = 6;          // arm thickness, along the pivot
leg_angle = 0;      // 0 = stowed along the wall pointing forward; 90 = straight down
leg_tent_angle = 90; // used by the tented view

/* [Wing (palm rest), Moonlander style: hangs on a free hinge along the tray's front edge] */
wing_t = 3.5;       // shell thickness
wing_r = 1.5;       // edge rounding
palm_gap = 0;       // wing back face flush against the tray front wall
palm_drop = 1;      // wing top below plate top
wing_angle = 0;     // front edge down; it lies on the desk, so it follows the board
wing_max = 30;      // clash-checked swing
wing_cl = 0.3;      // knuckle pockets in the wing
face_cl = 0.3;      // between the plain (untoothed) knuckle faces of the wing hinge

/* [nice!nano v2, upside down under the plate in the top strip, USB-C out the inner wall] */
nn = [33.6, 18.3, 1.6];   // length (x), width, board
nn_up = 3;                // board back to plate underside: through-hole stubs + wires
usb_open = [12.5, 7.5];
usb_h = 3.3;              // USB-C receptacle below the (flipped) board

/* [Battery, LiPo pouch on the floor] */
batt = [50, 34, 5.2];     // KP-523450 (5.2 x 34 x 50 mm, ~1000 mAh real), leads out of a 34 mm end. 0.3 mm under the switch pins: nothing thicker fits. Other size: change, run build.sh (clash_tray)
batt_fence = 1.6;
batt_fence_h = 3;

/* [Power switch SS12D10G5, under the plate, lever out the top wall] */
psw = [12.7, 6.3, 6.6];   // body: length (slide direction), height (lever out of the top face), width
psw_lever = [2, 5, 2];    // lever: width along the slide, how far it sticks out of the body, thickness
psw_travel = 3;
psw_pitch = 4.7;          // 3 pins out of the bottom face, away from the wall

/* [Reset: 6x6 tact under the plate, pressed with a pin through the floor] */
rst = 6.2;

// ---------------------------------------------------------------- layout

function kpos(c, r) = [(c + 0.5) * u, -(r + stag[c] + 0.5) * u];
main_keys = [for (c = [0 : 6]) for (r = [0 : col_rows[c] - 1]) kpos(c, r)];

h = [cos(hinge_rot), sin(hinge_rot)];   // along the hinge, up toward the inner column
n = [-sin(hinge_rot), cos(hinge_rot)];  // across, toward the main keys
Q = [5 * u, -5.125 * u] - hinge_drop * n;            // body hinge edge, before the rim
gap = kn_d + 2 * kn_r_cl;
axis_z = kn_d / 2;
A = Q - (rim + gap / 2) * n;                          // hinge axis in plan

// thumb keys in their own frame: row along x, red key above the middle of t0-t1
thumb_t = [for (i = [0 : 2]) [i * u, 0]];
red_t = [0.5 * u, (thumb_h + 1) * u / 2];
// into the module frame (x along h from Q's foot, y toward the body, origin on the axis)
phi = -thumb_rot - hinge_rot;
function rot2(p, a) = [p[0] * cos(a) - p[1] * sin(a), p[0] * sin(a) + p[1] * cos(a)];
function rect_pts(c, w, hh) = [for (sx = [-1, 1]) for (sy = [-1, 1]) c + rot2([sx * w / 2, sy * hh / 2], phi)];
raw_pts = concat(rect_pts(rot2(red_t, phi), red_w * u, u),
                 [for (t = thumb_t) each rect_pts(rot2(t, phi), u, thumb_h * u)]);
t_off = [thumb_s0, -(gap / 2 + rim + thumb_off) - max([for (p = raw_pts) p[1]])];
red_c = rot2(red_t, phi) + t_off;
thumb_c = [for (t = thumb_t) rot2(t, phi) + t_off];
mod_keys = concat([red_c], thumb_c);
mod_pts = [for (p = raw_pts) p + t_off];
mod_x0 = min([for (p = mod_pts) p[0]]);
mod_x1 = max([for (p = mod_pts) p[0]]);
mod_y0 = min([for (p = mod_pts) p[1]]);
E0 = Q + mod_x0 * h;
E1 = Q + mod_x1 * h;
mod_frame = [[h[0], n[0], 0, A[0]], [h[1], n[1], 0, A[1]], [0, 0, 1, axis_z], [0, 0, 0, 1]];
function Rx(a) = [[1, 0, 0, 0], [0, cos(a), -sin(a), 0], [0, sin(a), cos(a), 0], [0, 0, 0, 1]];
function mod_mat(tilt) = mod_frame * Rx(tilt);

// electronics, plan positions (left half)
strip_top = 14;           // top strip over cols 4-6 (before the rim): nice!nano, switch, reset.
                          // Deep enough for a ~6 mm wire channel between row 0 and the nice!nano
nn_c = [7 * u + rim - wall_t - nn[0] / 2 - 0.3, strip_top + rim - wall_t - 0.8 - nn[1] / 2];   // USB end into the inner wall
batt_c = [4.0 * u, -3.1 * u];                                  // on the floor, under the keys, clear of the connector pocket
psw_c = [nn_c[0] - nn[0] / 2 - 8, strip_top + rim - wall_t - psw[1] / 2 - 0.3];   // lever out the top wall
rst_c = [psw_c[0] - 12, strip_top + rim - wall_t - rst / 2 - 0.5];   // beside the switch, against the top wall

// ---------------------------------------------------------------- 2D outlines

module key_sq(c) translate(c) square(u, center = true);

module body_fill() hull() {
    translate(kpos(4, 4)) square(1, center = true);
    translate(kpos(5, 3)) square(1, center = true);
    translate(kpos(6, 2)) square(1, center = true);
    translate([7 * u - 1, -2.25 * u]) square(1);
    translate(E0) circle(0.5);
    translate(E1) circle(0.5);
}
module strip_2d() translate([4 * u, -1]) square([3 * u, strip_top + 1]);

// straight front under cols 0-4, out to where the col 4 slope crosses it: the palm rest sits flush along all of it
module front_fill_2d() translate([0, -5.5 * u]) square([4.4 * u, 1.5 * u]);

module body_2d() {
    offset(r = corner_r) offset(delta = rim - corner_r) union() {
        for (k = main_keys) key_sq(k);
        body_fill();
        strip_2d();
        front_fill_2d();
    }
}

module mod_keys_2d() {
    translate(red_c) rotate(phi) square([red_w * u, u], center = true);
    for (t = thumb_c) translate(t) rotate(phi) square([u, thumb_h * u], center = true);
}
mod_top = -(gap / 2 + rim);   // module hinge edge, before the rim
module mod_2d() offset(r = corner_r) offset(delta = rim - corner_r)
    hull() polygon(concat(mod_pts, [[mod_x1, mod_top], [mod_x0, mod_top]]));

front_y = -5.5 * u - rim;     // tray front wall, outer face, under cols 0-4
// Wing shape, traced from ZSA's moonlander-outline.stl (zsa.io/moonlander/printables, right half,
// mirrored onto the left; its main body is 149 mm wide like ours). dy runs from the tray front (0)
// back to the tip (-121.5). Outline: x of the outer and inner edge. Profile: how far the top has
// come down, 1 at the back (palm_drop under the plate top) to 0 at the tip (wing_t: tip on the desk).
wing_outer = [[-121.5, 38.9], [-121, 27.5], [-120, 24.9], [-116, 17.6], [-112, 13.3], [-108, 9.7], [-104, 7.1],
              [-100, 5.3], [-96, 3.7], [-84, 1.0], [-72, -1.3], [-60, -3.4], [-44, -5.7], [-24, -7.6], [0, -rim]];
wing_inner = [[-121.5, 38.9], [-121, 50.3], [-120, 52.2], [-116, 59.5], [-112, 63.9], [-108, 67.6], [-104, 70.6],
              [-96, 72.2], [-84, 72.7], [-76, 72.8], [-64, 74.6], [-52, 76.4], [-44, 77.9], [-36, 79.3], [-28, 81.4], [0, 80.3]];
wing_prof = [[-121.5, 0], [-118, 0.007], [-112, 0.107], [-106, 0.236], [-98, 0.336], [-90, 0.45], [-82, 0.543],
             [-74, 0.614], [-66, 0.679], [-50, 0.821], [-26, 0.95], [-10, 0.993], [0, 1]];
wing_dys = concat([for (d = [0 : -6 : -114]) d], [-117, -119, -120, -121, -121.5]);
function wing_top(dy) = wing_t + (plate_top - palm_drop - wing_t) * lookup(dy, wing_prof);
palm_x1 = lookup(0, wing_inner);   // the wing's inner back corner
module wing_2d() polygon(concat([for (d = wing_dys) [lookup(d, wing_outer), front_y - palm_gap + d]],
                                [for (i = [len(wing_dys) - 1 : -1 : 0]) [lookup(wing_dys[i], wing_inner), front_y - palm_gap + wing_dys[i]]]));

// ---------------------------------------------------------------- switch holes

module switch_hole(top) {
    translate([0, 0, top - clip_t - 0.01]) linear_extrude(clip_t + 0.02) square(switch_cut, center = true);
    translate([0, 0, top - plate_t - 0.01]) linear_extrude(plate_t - clip_t + 0.01) square(clip_relief, center = true);
}

// red key: Cherry plate-mount stabiliser cutouts for a 2u cap
module stab_holes(top) if (red_w >= 2)
    for (s = [-1, 1]) translate([s * 11.938, -0.6, top - plate_t - 0.01])
        linear_extrude(plate_t + 0.02) square([6.75, 14], center = true);

// ---------------------------------------------------------------- body

wall_top = plate_top - plate_t;

body_screws = [
    [-4, -0.375 * u + 4], [-4, -2.9 * u], [1 * u, -5.5 * u - 4], [3.5 * u, -5.5 * u - 4],
    [3 * u, 4], [4 * u - 2, strip_top + 4], [7 * u + 4, -0.6 * u], [7 * u + 4, -2.95 * u],
    Q + 0.5 * u * h - 4 * n,
];

module plate() difference() {
    translate([0, 0, wall_top]) linear_extrude(plate_t) body_2d();
    for (k = main_keys) translate(k) switch_hole(plate_top);
    for (s = body_screws) translate([s[0], s[1], plate_top]) countersink(plate_t + 1);
}

// nice!nano mount under the plate: two end blocks, hot glue
module nn_blocks() for (sx = [-1, 1])
    translate([nn_c[0] + sx * (nn[0] / 2 - 2), nn_c[1], wall_top - nn_up + 0.05])
        translate([-2, -nn[1] / 2 + 2, 0]) cube([4, nn[1] - 4, nn_up]);

module plate_part() { plate(); difference() { nn_blocks(); translate([nn_c[0] + nn[0] / 2 - 6, nn_c[1] - 5, 0]) cube([10, 10, 50]); } }

module tray() difference() {
    union() {
        linear_extrude(floor_t) body_2d();
        linear_extrude(wall_top) difference() { body_2d(); offset(delta = -wall_t) body_2d(); }
        for (s = body_screws) translate(s) cylinder(d = boss_d, h = wall_top);
        wing_lugs();
        leg_pivot();
        // battery fence
        translate([batt_c[0], batt_c[1], floor_t]) linear_extrude(batt_fence_h) difference() {
            square([batt[0] + 2 * batt_fence + 1, batt[1] + 2 * batt_fence + 1], center = true);
            square([batt[0] + 1, batt[1] + 1], center = true);
            square([batt[0] + 4 * batt_fence, 12], center = true);   // lead exit
        }
        body_knuckles();
        conn_cradle();
    }
    for (s = body_screws) translate([s[0], s[1], wall_top - pilot_depth]) cylinder(d = pilot_d, h = pilot_depth + 1);
    wing_holes_body();
    leg_pivot_holes();
    conn_pocket();
    // inner wall: USB-C and switch notches, open at the top so the wired plate drops in
    translate([7 * u + rim - wall_t - 1, nn_c[1] - usb_open[0] / 2, usb_z() - usb_open[1] / 2]) cube([wall_t + 5, usb_open[0], 50]);
    translate([psw_c[0] - (psw_lever[0] + psw_travel) / 2 - 1, strip_top + rim - wall_t - 1, psw_z() - psw_lever[2] / 2 - 1])
        cube([psw_lever[0] + psw_travel + 2, wall_t + 5, 50]);
    // reset pin hole
    translate([rst_c[0], rst_c[1], -1]) cylinder(d = 1.8, h = floor_t + 2);
    hinge_holes_body();
}

function usb_z() = wall_top - nn_up - nn[2] - usb_h / 2;
function psw_z() = wall_top - psw[2] / 2 - 0.2;   // hangs under the plate: glue its side to the plate

// ---------------------------------------------------------------- hinge units
// One design for the thumb module, the wing and the leg. A unit, in its own frame hu(I, o):
// z' runs along the axis from the fixed part ("body") into the moving part, the body's face
// at z' = 0, the moving part's face at z' = s. Body knuckle z' -kn_w..0, moving knuckle
// s..s + kn_w. A 5 mm boss on one of them runs through the other; a cap goes over the
// boss end on the far outside face, and one M2 through the cap into the boss pulls the
// two faces together. Toothed (Hirth) faces lock in 15 degree steps; plain faces just
// give friction. Loosen, move, tighten.
//
// o = -1 puts the moving knuckle on the -x side. With both units of a hinge at o = -1, the
// moving part slides on along +x over both bosses at once, and backs off along -x to
// unmesh its teeth: unit 0 (boss on the body, moving knuckle outboard) and unit 1 (boss on
// the moving part, body knuckle outboard). Both caps end up on the outer ends.

s_t = tooth_h + tooth_cl;   // face gap of a toothed unit
function hu(I, o) = [[0, 0, o, I], [0, 1, 0, 0], [-o, 0, 0, 0], [0, 0, 0, 1]];
function kx_body(I, o) = o > 0 ? [I - kn_w, I] : [I, I + kn_w];
function kx_mov(I, o, s) = o > 0 ? [I + s, I + s + kn_w] : [I - s - kn_w, I - s];

module hinge_add_body(I, o, boss, s, teeth) multmatrix(hu(I, o)) {
    if (teeth) hirth();
    if (boss) translate([0, 0, -kn_w + 0.01]) cylinder(d = pin_d, h = kn_w + s + kn_w - 0.6 - 0.01);
}
module hinge_sub_body(I, o, boss, s, teeth) multmatrix(hu(I, o)) {
    if (boss) translate([0, 0, s + kn_w - 0.6 - pilot_depth]) cylinder(d = pilot_d, h = pilot_depth + 1);
    else translate([0, 0, -kn_w - 1]) cylinder(d = pin_d + pin_cl, h = kn_w + tooth_h + 1.5);
}
module hinge_add_mov(I, o, boss, s, teeth) multmatrix(hu(I, o)) {
    if (teeth) difference() { hirth_mate(); translate([0, 0, -1]) cylinder(d = kn_d + 2, h = tooth_cl + 1); }
    if (!boss) translate([0, 0, -(kn_w - 0.6)]) cylinder(d = pin_d, h = kn_w - 0.6 + s + 0.01);
}
module hinge_sub_mov(I, o, boss, s, teeth) multmatrix(hu(I, o)) {
    if (boss) translate([0, 0, -1]) cylinder(d = pin_d + pin_cl, h = 30);
    else translate([0, 0, -(kn_w - 0.6) - 1]) cylinder(d = pilot_d, h = pilot_depth + 1);
}
module hinge_cap_at(I, o, boss, s) multmatrix(hu(I, o))
    if (boss) translate([0, 0, s + kn_w + 0.05]) hinge_cap();
    else translate([0, 0, -kn_w - 0.05]) mirror([0, 0, 1]) hinge_cap();
module hinge_cap() difference() {
    cylinder(d = cap_d, h = cap_t);
    translate([0, 0, cap_t]) countersink(cap_t + 1);
}

// Hirth teeth on a face at z = 0, ridges up to tooth_h; ridge and valley lines meet on the axis
module hirth(base = 1) intersection() {
    union() for (i = [0 : teeth - 1]) {
        a0 = i * tilt_step; a1 = a0 + tilt_step; am = a0 + tilt_step / 2; R = kn_d;
        hull() for (p = [[0, 0, tooth_h / 2], [R * cos(a0), R * sin(a0), 0], [R * cos(am), R * sin(am), tooth_h],
                         [R * cos(a1), R * sin(a1), 0], [0, 0, -base], [R * cos(a0), R * sin(a0), -base],
                         [R * cos(am), R * sin(am), -base], [R * cos(a1), R * sin(a1), -base]])
            translate(p) cube(0.01, center = true);
    }
    translate([0, 0, -base]) cylinder(d = kn_d, h = base + tooth_h + 0.01);
}
// the moving face: the same teeth flipped and turned half a tooth, so ridge meets valley
module hirth_mate(base = 1) translate([0, 0, tooth_cl]) rotate(tilt_step / 2) translate([0, 0, tooth_h]) mirror([0, 0, 1]) hirth(base);

// a knuckle along x in a hinge frame (axis on x, +y toward the body), with a web down
// to the floor side and across to the wall: toward = +1 body, -1 moving part
module knuckle_x(x0, x1, toward) hull() {
    translate([x0, 0, 0]) rotate([0, 90, 0]) cylinder(d = kn_d, h = x1 - x0);
    translate([x0, toward > 0 ? 0 : -(gap / 2 + wall_t), -axis_z]) cube([x1 - x0, gap / 2 + wall_t, axis_z]);
}

// ---- thumb hinge: module frame, two toothed units at the ends of the hinge edge
// Unit 0 (outer) is a normal unit with the screw. Unit 1 (inner) is the wire tube: a hollow
// boss on the module knuckle, turning in a bore in the tray knuckle. In each knuckle a slot
// takes the wires from the axis out into its tray; both are closed at the outside face.
th_I = [mod_x0 + 3 + kn_w + s_t, mod_x1 - 3 - kn_w];
wire_xm = th_I[1] - s_t - kn_w + 1.2;   // the module knuckle's wire slot starts here
wire_xb = th_I[1] + tube_in;      // the tube's end in the tray knuckle (its wire slot)

module body_knuckles() multmatrix(mod_frame) {
    for (i = [0, 1]) knuckle_x(kx_body(th_I[i], -1)[0], kx_body(th_I[i], -1)[1], 1);
    hinge_add_body(th_I[0], -1, true, s_t, true);
    multmatrix(hu(th_I[1], -1)) hirth();
}
module hinge_holes_body() multmatrix(mod_frame) {
    hinge_sub_body(th_I[0], -1, true, s_t, true);
    multmatrix(hu(th_I[1], -1)) {
        translate([0, 0, -tube_in - 0.01]) cylinder(d = tube_od + tube_cl, h = tube_in + tooth_h + 1);
        // wires out: from the tube's end, up through the web into the tray
        translate([-tube_id / 2, -tube_id / 2, -(kn_w - 1.2)]) cube([tube_id, 20 + tube_id / 2, kn_w - 1.2 - tube_in + 0.01]);
    }
}
module mod_knuckles() {
    difference() {
        union() {
            knuckle_x(kx_mov(th_I[0], -1, s_t)[0], kx_mov(th_I[0], -1, s_t)[1], -1);
            hinge_add_mov(th_I[0], -1, true, s_t, true);
        }
        hinge_sub_mov(th_I[0], -1, true, s_t, true);
    }
    difference() {
        union() {
            knuckle_x(kx_mov(th_I[1], -1, s_t)[0], kx_mov(th_I[1], -1, s_t)[1], -1);
            hinge_add_mov(th_I[1], -1, true, s_t, true);   // teeth
            multmatrix(hu(th_I[1], -1)) translate([0, 0, -tube_in]) cylinder(d = tube_od, h = tube_in + s_t + 0.01);
        }
        multmatrix(hu(th_I[1], -1)) translate([0, 0, -tube_in - 1]) cylinder(d = tube_id, h = tube_in + s_t + kn_w + 2);
        wire_slot_mod();
    }
}
// wires in: from the thumb tray, through its wall and the knuckle's web into the bore
module wire_slot_mod() multmatrix(hu(th_I[1], -1))
    translate([-tube_id / 2, -20, s_t + 1.5]) cube([tube_id, 20 + tube_id / 2, kn_w - 2.7]);
module caps_in_place() multmatrix(mod_frame) hinge_cap_at(th_I[0], -1, true, s_t);
// the 5-wire bundle (3 mm) along its path, for clash_wire: in from the thumb tray, along the axis, out into the tray
wire_d = 3;
wire_mx = th_I[1] - s_t - (kn_w + 0.3) / 2;   // middle of the module knuckle's slot
wire_bx = th_I[1] + (tube_in + kn_w - 1.2) / 2; // middle of the tray knuckle's slot
module wire_dummy(tilt) {
    multmatrix(mod_mat(tilt)) {
        translate([wire_mx, -14, 0]) rotate([-90, 0, 0]) cylinder(d = wire_d, h = 14, $fn = 16);
        translate([wire_mx, 0, 0]) sphere(d = wire_d, $fn = 16);
    }
    multmatrix(mod_frame) {
        translate([wire_mx, 0, 0]) rotate([0, 90, 0]) cylinder(d = wire_d, h = wire_bx - wire_mx, $fn = 16);
        translate([wire_bx, 0, 0]) rotate([-90, 0, 0]) cylinder(d = wire_d, h = 14, $fn = 16);
        translate([wire_bx, 0, 0]) sphere(d = wire_d, $fn = 16);
    }
}

// ---- wing hinge: axis along x in front of the tray's front wall, under the wing's top.
// Two plain units: wing knuckle outboard at the outer end, tray knuckle outboard at the inner end.
wing_y = front_y - gap / 2;
wing_z = plate_top - palm_drop - kn_d / 2 - 1.6;
wing_frame = [[1, 0, 0, 0], [0, 1, 0, wing_y], [0, 0, 1, wing_z], [0, 0, 0, 1]];
wing_inv = [[1, 0, 0, 0], [0, 1, 0, -wing_y], [0, 0, 1, -wing_z], [0, 0, 0, 1]];
function wing_pose(a) = wing_frame * Rx(a) * wing_inv;   // wing swung a degrees, front edge down
wi_I = [-rim + kn_w + face_cl, palm_x1 - kn_w - cap_t - 0.5];
wi_boss = [true, false];
wing_slide = kn_w + face_cl + 1;   // how far the wing slides along x to come off its bosses

module wing_lugs() multmatrix(wing_frame) for (i = [0, 1]) {
    knuckle_x(kx_body(wi_I[i], -1)[0], kx_body(wi_I[i], -1)[1], 1);
    hinge_add_body(wi_I[i], -1, wi_boss[i], face_cl, false);
}
module wing_holes_body() multmatrix(wing_frame) for (i = [0, 1]) hinge_sub_body(wi_I[i], -1, wi_boss[i], face_cl, false);
module wing_caps() multmatrix(wing_frame) for (i = [0, 1]) hinge_cap_at(wi_I[i], -1, wi_boss[i], face_cl);
// room in the wing for a tray lug: over the whole swing, and along x for sliding on
module wing_pocket(i) {
    k = kx_body(wi_I[i], -1);
    x0 = k[0] - wing_cl;
    x1 = i == 0 ? k[1] + wing_cl + wing_slide : palm_x1 + 10;
    module env() hull() {
        translate([x0, 0, 0]) rotate([0, 90, 0]) cylinder(d = max(kn_d, cap_d) + 2 * wing_cl, h = x1 - x0);
        translate([x0, 0, -axis_z - wing_cl]) cube([x1 - x0, 30, axis_z + wing_cl]);
    }
    for (a = [0 : 5 : wing_max - 5]) hull() { multmatrix(Rx(-a)) env(); multmatrix(Rx(-a - 5)) env(); }
}
// the wing's back, in the wing frame (y, z): flush with the wall above the axis, round
// the axis below it, so it swings front-down without touching the wall
module wing_back_2d() {
    translate([-200, 0]) square([200 + gap / 2 - palm_gap, 50]);
    translate([-200, -50]) square([200, 50]);
    circle(r = gap / 2 - 0.2);
}

// ---- leg pivot: on the inner wall, one toothed unit, arm on the outside (+x)
leg_I = 7 * u + rim + 1;   // toothed face, 1 mm proud of the wall
leg_frame = [[1, 0, 0, 0], [0, 1, 0, leg_y], [0, 0, 1, leg_z], [0, 0, 0, 1]] * hu(leg_I, 1);
function Rz(a) = [[cos(a), -sin(a), 0, 0], [sin(a), cos(a), 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]];
function leg_pose(a) = leg_frame * Rz(a);   // arm swung a degrees down from stowed
// tent from the leg angle: the board pivots on its outer bottom edge, foot tip on the desk
function tent_of(a) = let(cz = leg_z - (leg_len - leg_wd / 2) * sin(a) - leg_wd / 2,
                          x = leg_I + s_t + leg_w / 2) atan(-cz / (x + rim));

module leg_pivot() multmatrix(leg_frame) {
    hirth();   // its 1 mm base is the disc on the wall
    translate([0, 0, -1 - wall_t - 4]) cylinder(d = kn_d, h = 4 + wall_t + 0.01);   // backing inside the wall
    translate([0, 0, -1 - wall_t - 4]) cylinder(d = pin_d, h = 1 + wall_t + 4 + s_t + leg_w - 0.6);
}
module leg_pivot_holes() multmatrix(leg_frame) translate([0, 0, s_t + leg_w - 0.6 - pilot_depth]) cylinder(d = pilot_d, h = pilot_depth + 1);
module leg_arm_l() difference() {   // in the pivot frame, stowed: arm along -y
    union() {
        translate([0, 0, s_t]) linear_extrude(leg_w) hull() {
            circle(d = kn_d);
            translate([0, -(leg_len - leg_wd / 2)]) circle(d = leg_wd);
        }
        difference() { hirth_mate(); translate([0, 0, -1]) cylinder(d = kn_d + 2, h = tooth_cl + 1); }
    }
    translate([0, 0, -1]) cylinder(d = pin_d + pin_cl, h = 30);
}
module leg_in_place(a = leg_angle) {
    multmatrix(leg_pose(a)) leg_arm_l();
    multmatrix(leg_frame) translate([0, 0, s_t + leg_w + 0.05]) hinge_cap();
}

// ---------------------------------------------------------------- thumb link: connector

conn_x = wire_xb - 1 - conn[0];                 // beside the tray knuckle's wire slot
conn_y = gap / 2 + wall_t;                      // against the inside of the hinge wall
conn_sink = 1.5;                                // into a pocket in the floor, to stay clear of the switch pins
module conn_dummy() multmatrix(mod_frame)
    translate([conn_x, conn_y + 0.01, floor_t - conn_sink - axis_z + 0.01]) cube(conn - [0, 0.02, 0.02]);
module conn_pocket() multmatrix(mod_frame)
    translate([conn_x - 0.3, conn_y - 0.01, floor_t - conn_sink - axis_z]) cube([conn[0] + 0.6, conn[1] + 0.3, conn_sink + 0.01]);
module conn_cradle() multmatrix(mod_frame)      // a low rail: the pair lies in its pocket between it and the wall
    translate([conn_x, conn_y + conn[1] + 0.3, floor_t - axis_z - 0.01]) cube([conn[0], 1.2, 3]);

module yz_extrude(x0, len) translate([x0, 0, 0]) rotate([90, 0, 90]) linear_extrude(len) children();

// ---------------------------------------------------------------- thumb module (local frame, untilted)

mod_screws = [
    [mod_x0 + 2, mod_top - 4], [mod_x1 - 2, mod_top - 4],
    thumb_c[0] + rot2([-(u / 2 + 4), -(thumb_h * u / 2 + 4)], phi),
    thumb_c[2] + rot2([u / 2 + 4, -(thumb_h * u / 2 + 4)], phi)];

module thumb_plate() difference() {
    translate([0, 0, wall_top - axis_z]) linear_extrude(plate_t) mod_2d();
    for (k = mod_keys) translate(k) rotate(phi) switch_hole(plate_top - axis_z);
    translate(red_c) rotate(phi) stab_holes(plate_top - axis_z);
    for (s = mod_screws) translate([s[0], s[1], plate_top - axis_z]) countersink(plate_t + 1);
}

module thumb_tray() difference() {
    union() {
        translate([0, 0, -axis_z]) linear_extrude(floor_t) mod_2d();
        translate([0, 0, -axis_z]) linear_extrude(wall_top) difference() { mod_2d(); offset(delta = -wall_t) mod_2d(); }
        for (s = mod_screws) translate([s[0], s[1], -axis_z]) cylinder(d = boss_d, h = wall_top);
        mod_knuckles();
    }
    for (s = mod_screws) translate([s[0], s[1], wall_top - axis_z - pilot_depth]) cylinder(d = pilot_d, h = pilot_depth + 1);
    wire_slot_mod();
}

// ---------------------------------------------------------------- wing (palm rest)

// a cross-section of the wing at dy: rounded strip from z0 up to the top surface, edges from the outline
module wing_slab(dy, z0) {
    x0 = lookup(dy, wing_outer); x1 = lookup(dy, wing_inner); z1 = wing_top(dy);
    r = min(wing_r, (x1 - x0) / 2 - 0.01, (z1 - z0) / 2 - 0.01);
    translate([0, front_y - palm_gap + dy + 0.005, 0]) rotate([90, 0, 0]) linear_extrude(0.01)
        translate([x0, z0]) offset(r = r) offset(delta = -r) square([x1 - x0, z1 - z0]);
}
wing_beam = gap / 2 + kn_d / 2 + 3.5;   // solid strip along the back, round the knuckles
module palm() difference() {
    union() {
        difference() {
            intersection() {
                union() {
                    // the curved shell
                    for (i = [0 : len(wing_dys) - 2]) hull() {
                        wing_slab(wing_dys[i], wing_top(wing_dys[i]) - wing_t);
                        wing_slab(wing_dys[i + 1], wing_top(wing_dys[i + 1]) - wing_t);
                    }
                    // the hinge strip under its back edge
                    hull() { wing_slab(0, 3); wing_slab(-wing_beam, 3); }
                }
                multmatrix(wing_frame) yz_extrude(-50, 300) wing_back_2d();
            }
            multmatrix(wing_frame) for (i = [0, 1]) wing_pocket(i);
            multmatrix(wing_frame) hinge_sub_mov(wi_I[0], -1, wi_boss[0], face_cl, false);   // bore
        }
        multmatrix(wing_frame) hinge_add_mov(wi_I[1], -1, wi_boss[1], face_cl, false);       // boss
    }
    multmatrix(wing_frame) hinge_sub_mov(wi_I[1], -1, wi_boss[1], face_cl, false);           // its pilot
}

module leg() mirror([0, 0, 1]) translate([0, 0, -(s_t + leg_w)]) leg_arm_l();   // cap face down, teeth up

// ---------------------------------------------------------------- dummies for clash checks

cap_h = [plate_top + 3, plate_top + 15];   // keycap envelope with travel
module caps_main() for (k = main_keys) translate([k[0], k[1], cap_h[0]]) linear_extrude(cap_h[1] - cap_h[0]) square(u - 0.8, center = true);
module caps_mod(tilt) multmatrix(mod_mat(tilt)) {
    translate([red_c[0], red_c[1], cap_h[0] - axis_z]) rotate(phi) linear_extrude(cap_h[1] - cap_h[0]) square([red_w * u - 0.8, u - 0.8], center = true);
    for (t = thumb_c) translate([t[0], t[1], cap_h[0] - axis_z]) rotate(phi) linear_extrude(cap_h[1] - cap_h[0]) square([u - 0.8, thumb_h * u - 0.8], center = true);
}
module switch_zone() for (k = main_keys) translate([k[0], k[1], plate_top - sw_depth]) linear_extrude(sw_depth - plate_t) square(16, center = true);

module electronics() {
    // nice!nano upside down: board, then USB-C receptacle under it, stubs above
    translate([nn_c[0], nn_c[1], wall_top - nn_up - nn[2] / 2]) cube(nn, center = true);
    translate([nn_c[0] + nn[0] / 2 - 4, nn_c[1], usb_z()]) cube([8, 9, usb_h], center = true);
    translate([nn_c[0], nn_c[1], wall_top - nn_up / 2]) cube([nn[0] - 9, nn[1] - 1, nn_up - 0.02], center = true);
    // battery
    translate([batt_c[0], batt_c[1], floor_t + batt[2] / 2 + 0.01]) cube(batt, center = true);
    // power switch, reset
    translate([psw_c[0], psw_c[1], psw_z()]) cube(psw, center = true);
    // its lever through the wall notch at both ends of the travel, and its pins + solder
    translate([psw_c[0], psw_c[1] + psw[1] / 2 + psw_lever[1] / 2, psw_z()])
        cube([psw_lever[0] + psw_travel, psw_lever[1] - 0.02, psw_lever[2]], center = true);
    translate([psw_c[0], psw_c[1] - psw[1] / 2 - 2, psw_z()]) cube([2 * psw_pitch + 2, 4, 3], center = true);
    translate([rst_c[0], rst_c[1], wall_top - 2.5]) cube([rst, rst, 5 - 0.02], center = true);
    conn_dummy();
}

module body_all() {
    color("dimgray") tray(); color("silver") plate_part();
    color("gold") { caps_in_place(); wing_caps(); multmatrix(leg_frame) translate([0, 0, s_t + leg_w + 0.05]) hinge_cap(); }
}
module mod_all(tilt) multmatrix(mod_mat(tilt)) { color("dimgray") thumb_tray(); color("silver") thumb_plate(); }

module half(tilt = thumb_tilt, palm_on = true, wing = wing_angle, leg_a = leg_angle) {
    body_all();
    mod_all(tilt);
    if (palm_on) color("gray") multmatrix(wing_pose(wing)) palm();
    color("dimgray") multmatrix(leg_pose(leg_a)) leg_arm_l();
    color("orange") electronics();
    color("darkred") caps_mod(tilt);
    color("white", 0.5) caps_main();
}

// tenting: the board pivots on its outer bottom edge
function T3(v) = [[1, 0, 0, v[0]], [0, 1, 0, v[1]], [0, 0, 1, v[2]], [0, 0, 0, 1]];
function Ry(b) = [[cos(b), 0, sin(b), 0], [0, 1, 0, 0], [-sin(b), 0, cos(b), 0], [0, 0, 0, 1]];
function tent_mat(tn) = T3([-rim, 0, 0]) * Ry(-tn) * T3([rim, 0, 0]);
function mod_inv() = [[h[0], h[1], 0, -(h * A)], [n[0], n[1], 0, -(n * A)], [0, 0, 1, -axis_z], [0, 0, 0, 1]];
// lowest point of the thumb tray (corners of its outline, square rim) when tented
function mod_low(t, tn) = min([for (p = mod_pts) for (d = [[-rim, -rim], [rim, -rim], [-rim, rim], [rim, rim]])
    (tent_mat(tn) * mod_mat(t) * [p[0] + d[0], p[1] + d[1], -axis_z, 1])[2]]);
// the thumb step that brings the module closest to the desk
function thumb_rest(tn) = let(ts = [for (t = [0 : tilt_step : tilt_max]) t], e = [for (t = ts) abs(mod_low(t, tn))])
    ts[search(min(e), e)[0]];

th_slide = kn_w + s_t + 1;   // how far the thumb module slides along its axis to come off

// ---------------------------------------------------------------- fit test

module fit_plate() difference() {
    union() {
        linear_extrude(plate_t) translate([-u, -u / 2 - 4]) square([2 * u + 14, u + 8]);
        translate([u + 3, 0, 0]) cylinder(d = boss_d, h = 10);
    }
    for (x = [-u / 2, u / 2 - 2]) translate([x, 0, 0]) switch_hole(plate_t);
    translate([u + 3, 0, 10 - pilot_depth]) cylinder(d = pilot_d, h = pilot_depth + 1);
}

// ---------------------------------------------------------------- output

module sided() if (side == "right") mirror([1, 0, 0]) children(); else children();

if (part == "all") sided() half();
else if (part == "exploded") sided() {
    translate([0, 0, -25]) color("dimgray") tray();
    color("silver") plate_part();
    color("orange") translate([0, 0, -12]) electronics();
    multmatrix(mod_mat(0)) { translate([0, 0, -25]) color("dimgray") thumb_tray(); color("silver") thumb_plate(); }
    translate([0, -30, -25]) color("gray") palm();
    translate([30, 0, -25]) color("dimgray") multmatrix(leg_pose(0)) leg_arm_l();
}
// assembly: thumb module and wing slid off along their axes, caps and screws out
else if (part == "assembly") sided() {
    color("dimgray") tray(); color("silver") plate_part();
    multmatrix(mod_frame * T3([-th_slide - 6, 0, 0]) * mod_inv()) mod_all(0);
    color("gray") translate([-wing_slide - 6, 0, 0]) palm();
    color("dimgray") multmatrix(leg_frame * T3([0, 0, 12])) leg_arm_l();
    color("gold") {
        multmatrix(mod_frame) multmatrix(hu(th_I[0], -1)) translate([0, 0, 22]) hinge_cap();
        multmatrix(wing_frame) for (i = [0, 1]) multmatrix(hu(wi_I[i], -1)) translate([0, 0, wi_boss[i] ? 22 : -22]) hinge_cap();
        multmatrix(leg_frame) translate([0, 0, 30]) hinge_cap();
    }
}
else if (part == "tented") sided() {
    tn = tent_of(leg_tent_angle);
    tt = thumb_rest(tn);
    echo(TENT = tn, THUMB_TILT = tt, THUMB_LOW = mod_low(tt, tn));
    multmatrix(tent_mat(tn)) half(tilt = tt, leg_a = leg_tent_angle);
    color("#d8d0c0") translate([-60, -220, -1.01]) cube([280, 290, 1]);   // the desk
}
else if (part == "plate") sided() plate_part();
else if (part == "tray") sided() tray();
else if (part == "thumb_plate") sided() thumb_plate();
else if (part == "thumb_tray") sided() thumb_tray();
else if (part == "palm") sided() translate([0, 0, front_y]) rotate([-90, 0, 0]) palm();   // standing on its back edge; the shell rises near vertical
else if (part == "leg") leg();
else if (part == "hinge_cap") hinge_cap();
else if (part == "fit_plate") fit_plate();
else if (part == "layout_2d") sided() {   // 1:1 paper template: print and rest your hands on it
    difference() { body_2d(); for (k = main_keys) key_sq(k); }
    multmatrix(mod_mat(0)) difference() { mod_2d(); mod_keys_2d(); }
    for (k = main_keys) translate(k) difference() { square(u - 1, center = true); square(u - 1.6, center = true); }
    multmatrix(mod_mat(0)) difference() { mod_keys_2d(); offset(delta = -0.6) mod_keys_2d(); }
    difference() { wing_2d(); offset(delta = -1) wing_2d(); }
}
// numbers for wiring/build.py (openscad -o x.echo -D part="dump")
else if (part == "dump") {
    echo(DUMP = [["u", u], ["stag", stag], ["col_rows", col_rows], ["rim", rim], ["wall_t", wall_t],
                 ["strip_top", strip_top], ["nn_c", nn_c], ["nn", nn], ["batt_c", batt_c], ["batt", batt],
                 ["psw_c", psw_c], ["psw", psw], ["psw_pitch", psw_pitch], ["rst_c", rst_c], ["A", A], ["h", h], ["n", n], ["phi", phi],
                 ["gap", gap], ["red_c", red_c], ["thumb_c", thumb_c], ["red_w", red_w], ["thumb_h", thumb_h],
                 ["wire_xm", wire_xm], ["wire_xb", wire_xb], ["conn_x", conn_x], ["conn_y", conn_y], ["conn", conn],
                 ["mod_top", mod_top], ["body_screws", body_screws], ["mod_screws", mod_screws]]);
    cube(1);
}
else if (part == "outline_body") body_2d();
else if (part == "outline_mod") mod_2d();
// clash checks: each must render empty
else if (part == "clash_caps") union() {
    for (t = [0 : tilt_step : tilt_max]) {
        intersection() { caps_main(); caps_mod(t); }
    }
}
else if (part == "clash_hinge") union() {
    for (t = [0 : tilt_step : tilt_max]) intersection() {
        union() {
            tray(); plate_part(); palm(); caps_in_place(); wing_caps();
            leg_in_place(0); leg_in_place(90);
        }
        multmatrix(mod_mat(t)) union() { thumb_tray(); thumb_plate(); }
    }
}
// wing over its swing vs everything on the board, thumb module flat and fully down
else if (part == "clash_wing") union() {
    for (a = [0 : 5 : wing_max]) intersection() {
        multmatrix(wing_pose(a)) palm();
        union() {
            tray(); plate_part(); caps_in_place(); wing_caps(); leg_in_place(0);
            for (t = [0, tilt_max]) multmatrix(mod_mat(t)) union() { thumb_tray(); thumb_plate(); }
        }
    }
}
// leg over its whole turn vs the board
else if (part == "clash_leg") union() {
    for (a = [0 : tilt_step : 180]) intersection() {
        multmatrix(leg_pose(a)) leg_arm_l();
        union() { tray(); plate_part(); caps_in_place(); wing_caps(); }
    }
}
// assembly: the thumb module and the wing slide on along +x from fully off
else if (part == "clash_assembly") union() {
    for (d = [0.5 : 1.5 : th_slide + 0.5]) intersection() {
        union() { tray(); plate_part(); wing_caps(); }
        multmatrix(mod_frame * T3([-d, 0, 0]) * mod_inv()) multmatrix(mod_mat(0)) union() { thumb_tray(); thumb_plate(); }
    }
    for (d = [0.5 : 1.5 : wing_slide + 0.5]) intersection() {
        union() { tray(); plate_part(); }
        translate([-d, 0, 0]) palm();
    }
}
// the wire bundle clears both hinge knuckles at every tilt
else if (part == "clash_wire") union() {
    for (t = [0 : tilt_step : tilt_max]) intersection() {
        wire_dummy(t);
        union() { tray(); plate_part(); conn_dummy(); multmatrix(mod_mat(t)) union() { thumb_tray(); thumb_plate(); } }
    }
}
else if (part == "clash_tray") union() {
    intersection() { electronics(); union() { switch_zone(); tray(); plate_part(); } }
    intersection() { switch_zone(); union() { tray(); } }
}
