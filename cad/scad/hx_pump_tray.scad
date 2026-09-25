// Drip tray that holds the heat exchanger + tank-loop pump.
// The raised rim catches small leaks so water stays away from the PC.
tray_l   = 160;   // length (mm)
tray_w   = 90;    // width (mm)
floor_t  = 3;     // floor thickness (mm)
rim_h    = 12;    // rim height (mm) – holds ~ tray_l*tray_w*rim_h/1e6 L = ~0.17 L
rim_t    = 2.4;   // rim wall thickness (mm)
slot_l   = 12;    // zip-tie slot length (mm)
slot_w   = 4;     // zip-tie slot width (mm)
screw_d  = 4.3;   // M4 mounting holes
$fn = 48;

difference() {
  cube([tray_l, tray_w, floor_t + rim_h]);
  translate([rim_t, rim_t, floor_t]) cube([tray_l - 2*rim_t, tray_w - 2*rim_t, rim_h + 1]);
  // zip-tie slots: left half = heat exchanger, right half = pump
  for (x = [30, 60, 105, 135]) for (y = [18, tray_w - 18])
    translate([x - slot_l/2, y - slot_w/2, -1]) cube([slot_l, slot_w, floor_t + 2]);
  // corner screw holes
  for (x = [10, tray_l - 10]) for (y = [10, tray_w - 10])
    translate([x, y, -1]) cylinder(d = screw_d, h = floor_t + 2);
}
