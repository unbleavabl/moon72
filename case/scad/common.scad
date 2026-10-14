// Sizes shared by every model. Values proven on the macropad
// (handwired-kb/macropad/case/scad/common.scad) are copied, not re-guessed.
// Units mm.

/* [Switch holes] */
clip_t = 1.5;         // plate thickness at the switch clips; MX clips need 1.5
switch_cut = 14.0;    // printed fine on the macropad (P1S); tune with fit_plate.stl
clip_relief = 15.0;   // hole under the clip layer, room for the clips to spring out

/* [Fasteners: M2 countersunk only] */
pilot_d = 1.8;        // M2 screws cut their own thread in this hole, no inserts. Holes print
                      // ~0.4 small, so this comes out ~1.4-1.5; open it up if the screws bind
pilot_depth = 6;      // M2 x 8 through a 3 mm plate (5 mm of bite)
screw_d = 2.4;
screw_head_d = 4.0;   // M2 flat head (3.8), 90 deg countersink

$fn = 48;

// Countersunk M3 clearance hole, head at z = 0, shank going down `len`.
module countersink(len) {
    translate([0, 0, -len]) cylinder(d = screw_d, h = len + 0.01);
    translate([0, 0, -(screw_head_d - screw_d) / 2])
        cylinder(d1 = screw_d, d2 = screw_head_d, h = (screw_head_d - screw_d) / 2 + 0.01);
    cylinder(d = screw_head_d, h = 10);
}
