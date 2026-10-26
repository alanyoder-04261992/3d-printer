// {{NAME}}
// Units: millimeters. Edit the parameters, then export:
//   openscad -o model.stl model.scad

/* [Size] */
width  = 40;
depth  = 30;
height = 10;

/* [Print tuning - see knowledge/design-rules.md] */
wall      = 1.6;   // 4 perimeters at 0.4 mm nozzle
clearance = 0.3;   // added to holes / mating parts
chamfer   = 0.5;   // bottom edge chamfer, hides elephant's foot

$fn = 64;

// Box with a chamfered bottom edge so the first layer doesn't flare out.
module chamfered_block(size, c) {
    hull() {
        translate([c, c, 0]) cube([size.x - 2 * c, size.y - 2 * c, c]);
        translate([0, 0, c]) cube([size.x, size.y, size.z - c]);
    }
}

chamfered_block([width, depth, height], chamfer);
