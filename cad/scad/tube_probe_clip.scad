// Snap-on clip that holds a DS18B20 probe tight against a tube.
// Use 4 of these: in/out of the heat exchanger on BOTH loops.
tube_od   = 13;   // outside diameter of your tubing (mm)  (10/13 soft tube = 13)
probe_d   = 6;    // DS18B20 probe diameter (mm)
wall      = 2;    // plastic thickness (mm)
width     = 12;   // clip length along the tube (mm)
open_frac = 0.7;  // opening width as a fraction of diameter (snap-fit)
$fn = 80;

module c_ring(d) {
  difference() {
    cylinder(d = d + 2*wall, h = width);
    translate([0,0,-1]) cylinder(d = d, h = width + 2);
    translate([-d*open_frac/2, 0, -1]) cube([d*open_frac, d, width + 2]);  // snap opening
  }
}
c_ring(tube_od);
// probe ring sits touching the tube wall on the opposite side from the opening
translate([0, -(tube_od/2 + probe_d/2), 0]) rotate(180) c_ring(probe_d);
