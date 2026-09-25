"""Builds the same parts as the .scad files and saves STLs (for people without OpenSCAD).
Run:  pip install manifold3d trimesh   then   python build_stl.py"""
import math, trimesh
from manifold3d import Manifold as M

def cyl(d, h, n=96): return M.cylinder(h, d/2, d/2, n)
def cube(x, y, z): return M.cube([x, y, z])
def T(m, x=0, y=0, z=0): return m.translate([x, y, z])

def tank_lid(tank_inner_d=120, lid_t=4, overhang=6, plug_h=8, plug_wall=3, fit_gap=0.4,
             tube_hole_d=12.5, probe_hole_d=6.5, vent_d=3):
    top = cyl(tank_inner_d + 2*overhang, lid_t)
    od = tank_inner_d - fit_gap
    ring = T(cyl(od, plug_h) - T(cyl(od - 2*plug_wall, plug_h + 2), z=-1), z=-plug_h)
    body = top + ring
    r = tank_inner_d * 0.30
    for a, d in [(0, tube_hole_d), (180, tube_hole_d), (90, probe_hole_d), (270, probe_hole_d)]:
        body -= T(cyl(d, lid_t + 2), r*math.cos(math.radians(a)), r*math.sin(math.radians(a)), -1)
    return body - T(cyl(vent_d, lid_t + 2), z=-1)

def c_ring(d, wall, width, open_frac):
    r = cyl(d + 2*wall, width, 80) - T(cyl(d, width + 2, 80), z=-1)
    return r - T(cube(d*open_frac, d, width + 2), -d*open_frac/2, 0, -1)

def tube_probe_clip(tube_od=13, probe_d=6, wall=2, width=12, open_frac=0.7):
    a = c_ring(tube_od, wall, width, open_frac)
    b = T(c_ring(probe_d, wall, width, open_frac).rotate([0, 0, 180]), y=-(tube_od/2 + probe_d/2))
    return a + b

def hx_pump_tray(L=160, W=90, floor_t=3, rim_h=12, rim_t=2.4, slot_l=12, slot_w=4, screw_d=4.3):
    b = cube(L, W, floor_t + rim_h) - T(cube(L - 2*rim_t, W - 2*rim_t, rim_h + 1), rim_t, rim_t, floor_t)
    for x in [30, 60, 105, 135]:
        for y in [18, W - 18]:
            b -= T(cube(slot_l, slot_w, floor_t + 2), x - slot_l/2, y - slot_w/2, -1)
    for x in [10, L - 10]:
        for y in [10, W - 10]:
            b -= T(cyl(screw_d, floor_t + 2, 48), x, y, -1)
    return b

def save(m, name):
    mesh = m.to_mesh()
    t = trimesh.Trimesh(mesh.vert_properties[:, :3], mesh.tri_verts)
    t.export(f"stl/{name}.stl")
    print(f"{name}: watertight={t.is_watertight}, size(mm)={t.extents.round(1)}, volume={t.volume/1000:.1f} cm3")
    return t

if __name__ == "__main__":
    parts = {"tank_lid": tank_lid(), "tube_probe_clip": tube_probe_clip(), "hx_pump_tray": hx_pump_tray()}
    meshes = {k: save(v, k) for k, v in parts.items()}
    # preview images
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    for k, t in meshes.items():
        fig = plt.figure(figsize=(5, 4)); ax = fig.add_subplot(projection="3d")
        pc = Poly3DCollection(t.triangles, facecolor="#4a90c2", edgecolor="none", alpha=1.0)
        n = t.face_normals; light = (n @ [0.4, -0.5, 0.8]).clip(0.15, 1)
        pc.set_facecolor([(0.2 + 0.6*l, 0.45 + 0.45*l, 0.65 + 0.35*l) for l in light])
        ax.add_collection3d(pc)
        mn, mx = t.bounds; c = (mn + mx)/2; s = (mx - mn).max()/2
        ax.set_xlim(c[0]-s, c[0]+s); ax.set_ylim(c[1]-s, c[1]+s); ax.set_zlim(c[2]-s, c[2]+s)
        ax.view_init(35, -60); ax.set_axis_off()
        plt.tight_layout(); plt.savefig(f"previews/{k}.png", dpi=110, transparent=True); plt.close()
