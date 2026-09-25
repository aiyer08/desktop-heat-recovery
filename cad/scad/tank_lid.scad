// Tank lid for the heat-recovery water tank
// Change these numbers to match YOUR container, then export to STL (F6, then F7).
tank_inner_d = 120;   // inside diameter of the tank opening (mm)
lid_t        = 4;     // lid thickness (mm)
overhang     = 6;     // how far the lid sticks out past the opening (mm)
plug_h       = 8;     // depth of the plug that sits inside the opening (mm)
plug_wall    = 3;     // wall thickness of the plug ring (mm)
fit_gap      = 0.4;   // clearance so the plug isn't too tight (mm)
tube_hole_d  = 12.5;  // hole for inlet/outlet (fits a G1/4 bulkhead or 10/13 mm tube)
probe_hole_d = 6.5;   // hole for a 6 mm DS18B20 waterproof probe
vent_d       = 3;     // small vent so the tank isn't sealed
$fn = 96;

difference() {
  union() {
    cylinder(d = tank_inner_d + 2*overhang, h = lid_t);            // top plate
    translate([0,0,-plug_h])
      difference() {                                               // plug ring
        cylinder(d = tank_inner_d - fit_gap, h = plug_h);
        translate([0,0,-1]) cylinder(d = tank_inner_d - fit_gap - 2*plug_wall, h = plug_h + 2);
      }
  }
  r = tank_inner_d * 0.30;
  for (a = [0, 180])  rotate(a)   translate([r,0,-1]) cylinder(d = tube_hole_d,  h = lid_t + 2); // IN / OUT
  for (a = [90, 270]) rotate(a)   translate([r,0,-1]) cylinder(d = probe_hole_d, h = lid_t + 2); // probes top/bottom
  translate([0,0,-1]) cylinder(d = vent_d, h = lid_t + 2);                                    // vent
}
