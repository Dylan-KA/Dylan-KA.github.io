"""Procedurally builds a stylised bust of Dylan from the profile photo's proportions.

Run headless from the repo root:
    blender -b --factory-startup --python blender/build_bust.py -- [--preview DIR] [--no-export]

Units are metres, Z up, the face looks down -Y and eye level sits at Z = 0.
Each part is sculpted on a dense voxel mesh, retopologised to even quads with QuadriFlow, then
exported twice: as faces (used to hide back lines) and as loose edges (the visible wireframe).
Writes Images/Model/dylan-bust.glb and blender/dylan-bust.blend.
"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GLB_PATH = os.path.join(ROOT, "Images", "Model", "dylan-bust.glb")
BLEND_PATH = os.path.join(ROOT, "blender", "dylan-bust.blend")
MIRROR = np.array([-1.0, 1.0, 1.0])
UP = np.array([0.0, 0.0, 1.0])


# ---------------------------------------------------------------------------
# Mesh plumbing
# ---------------------------------------------------------------------------

def link_mesh(name, me):
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def obj_from_data(name, verts, faces):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in np.asarray(verts, float)], [], [tuple(f) for f in faces])
    me.validate()
    me.update()
    return link_mesh(name, me)


def obj_from_bmesh(name, bm):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return link_mesh(name, me)


def hull_obj(name, pts):
    bm = bmesh.new()
    for p in pts:
        bm.verts.new(p)
    res = bmesh.ops.convex_hull(bm, input=bm.verts[:], use_existing_faces=False)
    bmesh.ops.delete(bm, geom=[v for v in res["geom_interior"] if isinstance(v, bmesh.types.BMVert)], context="VERTS")
    return obj_from_bmesh(name, bm)


def ellipsoid_obj(name, center, radii, segs=32):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=segs // 2, radius=1.0)
    for v in bm.verts:
        v.co = Vector(np.array(v.co) * radii + center)
    return obj_from_bmesh(name, bm)


def with_mirror(pts):
    pts = np.asarray(pts, float)
    side = pts[np.abs(pts[:, 0]) > 1e-6] * MIRROR
    return np.vstack([pts, side])


def get_co(me):
    a = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", a)
    return a.reshape(-1, 3)


def set_co(me, P):
    me.vertices.foreach_set("co", np.ascontiguousarray(P, dtype=np.float32).ravel())
    me.update()


def get_normals(me):
    a = np.empty(len(me.vertices) * 3)
    me.vertex_normals.foreach_get("vector", a)
    return a.reshape(-1, 3)


def get_edges(me):
    a = np.empty(len(me.edges) * 2, np.int64)
    me.edges.foreach_get("vertices", a)
    return a.reshape(-1, 2)


def join(name, objs):
    verts, faces, off = [], [], 0
    for ob in objs:
        me = ob.data
        verts.append(get_co(me))
        for p in me.polygons:
            faces.append([i + off for i in p.vertices])
        off += len(me.vertices)
        bpy.data.objects.remove(ob)
    return obj_from_data(name, np.vstack(verts), faces)


def apply_modifiers(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    old = ob.data
    ob.modifiers.clear()
    ob.data = me
    me.name = ob.name
    bpy.data.meshes.remove(old)


def voxel_remesh(ob, size):
    m = ob.modifiers.new("remesh", "REMESH")
    m.mode = "VOXEL"
    m.voxel_size = size
    m.adaptivity = 0.0
    apply_modifiers(ob)


def soften(ob, coarse, iters, fine):
    """Melts a faceted blockout: remesh coarse, smooth hard, remesh fine."""
    voxel_remesh(ob, coarse)
    s = Sculpt(ob)
    s.smooth(iters)
    s.done()
    voxel_remesh(ob, fine)


def quadriflow(ob, faces, symmetric):
    # QuadriFlow rejects edges shorter than 1e-4 as degenerate, so work at centimetre scale.
    set_co(ob.data, get_co(ob.data) * 100)
    for o in bpy.context.scene.objects:
        o.select_set(o == ob)
    bpy.context.view_layer.objects.active = ob
    with bpy.context.temp_override(active_object=ob, object=ob, selected_objects=[ob],
                                   selected_editable_objects=[ob]):
        res = bpy.ops.object.quadriflow_remesh(target_faces=faces, use_mesh_symmetry=symmetric,
                                               use_preserve_sharp=False, use_preserve_boundary=True,
                                               smooth_normals=False, seed=7)
    if "FINISHED" not in res:
        raise RuntimeError(f"QuadriFlow failed on {ob.name}")
    set_co(ob.data, get_co(ob.data) / 100)


def bisect_below(ob, z):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, z),
                           plane_no=(0, 0, 1), clear_inner=True)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()


def delete_verts(ob, mask):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.verts[i] for i in np.nonzero(mask)[0]], context="VERTS")
    bmesh.ops.delete(bm, geom=[e for e in bm.edges if e.is_wire], context="EDGES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_edges], context="VERTS")
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()


def bvh_of(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    tree = BVHTree.FromBMesh(bm)
    bm.free()
    return tree


def project(tree, pts, offset=0.0):
    """Snap points to the nearest surface, then push them `offset` along its normal."""
    locs, nrms = [], []
    for p in pts:
        loc, n, _, _ = tree.find_nearest(Vector(p))
        locs.append(np.array(loc) + np.array(n) * offset)
        nrms.append(np.array(n))
    return np.array(locs), np.array(nrms)


# ---------------------------------------------------------------------------
# Sculpting helpers (numpy "brushes" displacing vertices along their normals)
# ---------------------------------------------------------------------------

def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def ell(P, c, r):
    """Smooth ellipsoidal falloff: 1 at the centre, 0 at the boundary."""
    q = np.sum(((P - np.asarray(c)) / np.asarray(r)) ** 2, 1)
    return np.clip(1 - q, 0, None) ** 2


def catmull(ctrl, n=24, closed=False):
    C = np.asarray(ctrl, float)
    if closed:
        C = np.vstack([C[-1], C, C[0], C[1]])
    else:
        C = np.vstack([2 * C[0] - C[1], C, 2 * C[-1] - C[-2]])
    out = []
    for i in range(1, len(C) - 2):
        p0, p1, p2, p3 = C[i - 1], C[i], C[i + 1], C[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    if not closed:
        out.append(C[-2])
    return np.array(out)


def curve_falloff(P, ctrl, width, n=24):
    """Falloff around a Catmull-Rom curve (tube of radius `width`)."""
    S = catmull(ctrl, n)
    lo, hi = S.min(0) - width, S.max(0) + width
    sel = np.all((P > lo) & (P < hi), 1)
    out = np.zeros(len(P))
    if sel.any():
        Q = P[sel]
        d = np.full(len(Q), np.inf)
        for chunk in np.array_split(S, max(1, len(S) // 64)):
            d = np.minimum(d, np.min(np.linalg.norm(Q[:, None, :] - chunk[None], axis=2), 1))
        out[sel] = np.clip(1 - (d / width) ** 2, 0, None) ** 2
    return out


class Sculpt:
    def __init__(self, ob):
        self.ob, self.me = ob, ob.data
        self.P = get_co(self.me)
        self.E = get_edges(self.me)
        self.deg = np.bincount(self.E.ravel(), minlength=len(self.P)).astype(float)
        self.refresh()

    def refresh(self):
        set_co(self.me, self.P)
        self.N = get_normals(self.me)

    def push(self, f, amount):
        self.P += self.N * (f * amount)[:, None]

    def blob(self, c, r, amount, sym=True):
        f = ell(self.P, c, r)
        if sym and abs(c[0]) > 1e-9:
            f = f + ell(self.P * MIRROR, c, r)
        self.push(f, amount)

    def crease(self, ctrl, width, amount, sym=True):
        f = curve_falloff(self.P, ctrl, width)
        if sym:
            f = np.maximum(f, curve_falloff(self.P * MIRROR, ctrl, width))
        self.push(f, amount)

    def lap(self, P):
        S = np.stack([np.bincount(self.E[:, 0], P[self.E[:, 1], k], len(P)) +
                      np.bincount(self.E[:, 1], P[self.E[:, 0], k], len(P)) for k in range(3)], 1)
        return S / np.maximum(self.deg, 1)[:, None] - P

    def smooth(self, iters, mask=None, lam=0.5, mu=-0.53):
        m = np.ones(len(self.P)) if mask is None else mask
        for _ in range(iters):
            self.P += lam * m[:, None] * self.lap(self.P)
            self.P += mu * m[:, None] * self.lap(self.P)

    def done(self):
        self.refresh()
        return self.ob


def sweep(name, C, U, rw, rh, nseg=12, closed=False, caps=True):
    """Sweeps an elliptical cross-section (rw across, rh along U) along centreline C."""
    C = np.asarray(C, float)
    n = len(C)
    rw = np.broadcast_to(np.asarray(rw, float), (n,))
    rh = np.broadcast_to(np.asarray(rh, float), (n,))
    T = (np.roll(C, -1, 0) - np.roll(C, 1, 0)) if closed else np.gradient(C, axis=0)
    T /= np.linalg.norm(T, axis=1)[:, None]
    U = np.broadcast_to(np.asarray(U, float), (n, 3)).copy()
    U -= (U * T).sum(1)[:, None] * T
    U /= np.linalg.norm(U, axis=1)[:, None]
    W = np.cross(T, U)
    a = np.linspace(0, 2 * math.pi, nseg, endpoint=False)
    V = (C[:, None] + np.cos(a)[None, :, None] * rw[:, None, None] * W[:, None]
         + np.sin(a)[None, :, None] * rh[:, None, None] * U[:, None])
    verts = list(V.reshape(-1, 3))
    faces = []
    for i in range(n if closed else n - 1):
        j = (i + 1) % n
        for k in range(nseg):
            k2 = (k + 1) % nseg
            faces.append((i * nseg + k, j * nseg + k, j * nseg + k2, i * nseg + k2))
    if caps and not closed:
        for ring, centre, flip in ((0, C[0], True), (n - 1, C[-1], False)):
            verts.append(centre)
            c = len(verts) - 1
            for k in range(nseg):
                tri = (ring * nseg + k, ring * nseg + (k + 1) % nseg, c)
                faces.append(tri[::-1] if flip else tri)
    return obj_from_data(name, np.array(verts), faces)


# ---------------------------------------------------------------------------
# Head
# ---------------------------------------------------------------------------

EYE_X, EYE_Y, EYE_R = 0.033, -0.0725, 0.0125


def head_blockout():
    face = [
        # forehead
        (0, -0.086, 0.065), (0.03, -0.08, 0.065), (0.05, -0.064, 0.062),
        (0, -0.092, 0.04), (0.03, -0.088, 0.04), (0.052, -0.07, 0.04), (0.064, -0.045, 0.035),
        # brow
        (0, -0.094, 0.015), (0.02, -0.096, 0.016), (0.04, -0.091, 0.016), (0.055, -0.076, 0.012),
        (0.065, -0.05, 0.01),
        # cheekbones
        (0.05, -0.076, -0.018), (0.062, -0.056, -0.02), (0.066, -0.03, -0.02),
        (0.04, -0.084, -0.045), (0.054, -0.066, -0.05), (0.06, -0.04, -0.05),
        # muzzle / mouth
        (0, -0.098, -0.045), (0.02, -0.094, -0.048),
        (0, -0.1, -0.064), (0.02, -0.096, -0.064), (0.035, -0.084, -0.062),
        # chin
        (0, -0.097, -0.078), (0.021, -0.09, -0.08), (0, -0.094, -0.092), (0, -0.096, -0.102),
        (0.018, -0.092, -0.104), (0.023, -0.086, -0.108), (0, -0.086, -0.112), (0.014, -0.079, -0.113),
        (0, -0.07, -0.114),
        # jaw line
        (0.033, -0.074, -0.099), (0.043, -0.057, -0.09), (0.051, -0.032, -0.078),
        (0.056, -0.007, -0.066), (0.06, 0.015, -0.045),
        # base of skull
        (0, 0.095, -0.04), (0.04, 0.08, -0.05), (0, 0.07, -0.07),
    ]
    pts = list(with_mirror(face))
    c, r = np.array([0, 0.012, 0.0]), np.array([0.068, 0.095, 0.087])
    for th in np.linspace(0, math.pi, 18):
        for ph in np.linspace(0, 2 * math.pi, 36, endpoint=False):
            d = np.array([math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th)])
            d /= np.sum(np.abs(d) ** 2.6) ** (1 / 2.6)  # superellipsoid: fuller at the temples and crown
            p = c + r * d
            if p[2] > -0.045:
                pts.append(p)
    skull = hull_obj("skull", pts)

    nose = hull_obj("nose", with_mirror([
        (0, -0.088, 0.008), (0.008, -0.084, 0.006),
        (0, -0.095, -0.008), (0.008, -0.09, -0.01),
        (0, -0.104, -0.022), (0.009, -0.097, -0.022),
        (0, -0.115, -0.034), (0.008, -0.111, -0.035), (0, -0.111, -0.041), (0.007, -0.106, -0.042),
        (0.017, -0.095, -0.036), (0.019, -0.091, -0.04), (0.016, -0.088, -0.044),
        (0, -0.099, -0.044), (0.007, -0.1, -0.044),
        (0, -0.08, -0.04), (0.014, -0.08, -0.03), (0, -0.078, 0.0),
    ]))

    neck_ring = []
    for z, yc, rx in ((-0.05, 0.004, 0.051), (-0.27, 0.04, 0.054)):
        for a in np.linspace(0, 2 * math.pi, 32, endpoint=False):
            neck_ring.append((rx * math.cos(a), yc + 0.056 * math.sin(a), z))
    neck = hull_obj("neck", neck_ring)
    return [skull, nose, neck]


EAR_C = np.array([0.069, 0.014, -0.027])


def ear_frame():
    w = np.array([math.cos(math.radians(28)), -math.sin(math.radians(28)), 0.0])  # outward face
    u = np.array([0.0, math.sin(math.radians(14)), math.cos(math.radians(14))])  # up, tilted back
    u -= w * u.dot(w)
    u /= np.linalg.norm(u)
    v = np.cross(u, w)
    if v[1] < 0:
        v = -v
    return u, v, w


def ears():
    u, v, w = ear_frame()
    pts = []
    for a in np.linspace(0, 2 * math.pi, 40, endpoint=False):
        s = math.sin(a)
        hu = 0.03 * s
        hv = (0.017 + 0.003 * s) * math.cos(a) * (0.75 if s < -0.4 else 1.0)
        for depth, k in ((-0.006, 0.7), (0.011, 1.0)):
            pts.append(EAR_C + u * hu * k + v * (hv * k + 0.004) + w * depth)
    pts = np.array(pts)
    return [hull_obj("ear_l", pts), hull_obj("ear_r", pts * MIRROR)]


def ear_local(P):
    u, v, w = ear_frame()
    Q = np.column_stack([np.abs(P[:, 0]), P[:, 1], P[:, 2]]) - EAR_C
    return np.column_stack([Q @ u, Q @ v, Q @ w])


def mouth_upper(x):
    return -0.0605 + 0.0065 * (x / 0.035) ** 2


def mouth_lower(x):
    return -0.0775 + 0.021 * (x / 0.035) ** 2


def sculpt_head(ob):
    s = Sculpt(ob)
    # eye sockets, brow ridge, temples
    s.blob((EYE_X, -0.09, 0.001), (0.021, 0.026, 0.0125), -0.0135)
    s.blob((0.03, -0.097, 0.018), (0.026, 0.012, 0.007), 0.0015)
    s.blob((0.064, -0.045, 0.03), (0.012, 0.025, 0.02), -0.003)
    s.blob((0.0, -0.092, 0.006), (0.011, 0.012, 0.01), -0.003, sym=False)  # nasion dip
    # cheeks pushed up by the smile, hollow beneath the cheekbone
    s.blob((0.044, -0.078, -0.033), (0.022, 0.02, 0.02), 0.0045)
    s.blob((0.055, -0.05, -0.06), (0.012, 0.03, 0.016), -0.0025)
    s.blob((0.0, -0.096, -0.1), (0.018, 0.02, 0.012), 0.002, sym=False)  # chin
    s.blob((0.0, -0.05, -0.135), (0.014, 0.016, 0.022), 0.004, sym=False)  # Adam's apple
    s.refresh()
    s.smooth(4)
    s.refresh()

    # Eyelids: a ridge over the top of the eyeball and a smiling, raised lower lid.
    def eye_arc(z0, rise, x0=0.019, x1=0.049, y=-0.083):
        xs = np.linspace(x0, x1, 7)
        t = (xs - EYE_X) / ((x1 - x0) / 2)
        return [(x, y + 0.006 * tt * tt, z0 + rise * (1 - tt * tt)) for x, tt in zip(xs, t)]

    s.crease(eye_arc(0.008, 0.004), 0.004, 0.0016)  # upper lid
    s.crease(eye_arc(0.014, 0.004, 0.017, 0.052, -0.087), 0.003, -0.0012)  # lid fold
    s.crease(eye_arc(-0.009, -0.002), 0.004, 0.0018)  # lower lid
    s.refresh()
    # almond-shaped opening between the lids, narrowed by the smile
    for sx in (1, -1):
        q = ((s.P[:, 0] - sx * EYE_X) / 0.0135) ** 2 + ((s.P[:, 2] - 0.001) / 0.0052) ** 2
        s.push(smoothstep(1.0, 0.55, q) * (s.P[:, 1] < -0.065), -0.006)
    s.refresh()

    # Nose details
    s.blob((0.008, -0.106, -0.043), (0.005, 0.006, 0.003), -0.0025)  # nostrils
    s.crease([(0.012, -0.096, -0.031), (0.018, -0.094, -0.034), (0.02, -0.09, -0.039),
              (0.017, -0.087, -0.045)], 0.002, -0.0015)  # alar groove
    s.blob((0.0, -0.113, -0.036), (0.009, 0.006, 0.007), 0.0012, sym=False)  # bulb of the tip
    s.refresh()

    # Mouth: lips, smile lines and an open grin
    P = s.P
    x = P[:, 0]
    s.blob((0.0, -0.098, -0.064), (0.04, 0.02, 0.016), 0.003, sym=False)
    s.crease([(0.019, -0.096, -0.043), (0.031, -0.091, -0.052), (0.04, -0.085, -0.062),
              (0.044, -0.079, -0.072)], 0.004, -0.002)  # nasolabial fold
    lower = mouth_lower(np.clip(x, -0.035, 0.035))
    s.push(np.exp(-((P[:, 2] - (lower - 0.004)) / 0.004) ** 2) * smoothstep(0.034, 0.02, np.abs(x))
           * (P[:, 1] < -0.07), 0.002)  # fuller lower lip
    s.refresh()
    P = s.P
    x = np.clip(P[:, 0], -0.035, 0.035)
    inside = smoothstep(-0.001, 0.003, np.minimum(mouth_upper(x) - P[:, 2], P[:, 2] - mouth_lower(x)))
    inside *= smoothstep(0.036, 0.028, np.abs(P[:, 0])) * (P[:, 1] < -0.07)
    s.push(inside, -0.0055)
    s.refresh()
    s.smooth(6, mask=ell(s.P, (0.0, -0.1, -0.067), (0.05, 0.03, 0.03)))
    s.smooth(2)
    return s.done()


def sculpt_ears(ob):
    s = Sculpt(ob)
    L = ear_local(s.P)
    outward = L[:, 2] > 0.002
    concha = np.clip(1 - ((L[:, 0] + 0.006) / 0.013) ** 2 - ((L[:, 1] - 0.003) / 0.008) ** 2, 0, None) ** 2
    rim_d = np.sqrt((L[:, 0] / 0.027) ** 2 + ((L[:, 1] - 0.004) / 0.015) ** 2)
    scapha = np.exp(-((rim_d - 0.78) / 0.08) ** 2) * (L[:, 0] > -0.01)
    s.push(outward * (concha * 0.0075 + scapha * 0.0025), -1.0)
    s.refresh()
    s.smooth(2)
    return s.done()


def eyes():
    """Eyeballs with their poles facing forward, so latitude rings trace the pupil and iris."""
    rings = [8, 22, 27, 45, 70, 100, 135, 180]
    segs = 16
    obs = []
    for sx in (1, -1):
        c = np.array([sx * EYE_X, EYE_Y, 0.0])
        verts = [c + np.array([0, -EYE_R - 0.0007, 0])]
        for deg in rings[:-1]:
            t = math.radians(deg)
            r = EYE_R + (0.0007 if deg <= 22 else 0.0)  # cornea bulge
            for k in range(segs):
                a = 2 * math.pi * k / segs
                verts.append(c + r * np.array([math.sin(t) * math.cos(a), -math.cos(t), math.sin(t) * math.sin(a)]))
        verts.append(c + np.array([0, EYE_R, 0]))
        faces = [(0, 1 + (k + 1) % segs, 1 + k) for k in range(segs)]
        for i in range(len(rings) - 2):
            a0, b0 = 1 + i * segs, 1 + (i + 1) * segs
            faces += [(a0 + k, a0 + (k + 1) % segs, b0 + (k + 1) % segs, b0 + k) for k in range(segs)]
        last, tip = 1 + (len(rings) - 2) * segs, len(verts) - 1
        faces += [(last + k, last + (k + 1) % segs, tip) for k in range(segs)]
        obs.append(obj_from_data("eye", verts, faces))
    return join("Eyes", obs)


# ---------------------------------------------------------------------------
# Hair, brows, moustache, teeth
# ---------------------------------------------------------------------------

HAIRLINE = np.array([
    (0.0, 0.061), (0.34, 0.067), (0.62, 0.056), (0.85, 0.036), (1.02, 0.02), (1.14, -0.006), (1.28, -0.01),
    (1.4, 0.01), (1.85, 0.01), (2.1, -0.016), (2.5, -0.05), (math.pi, -0.068),
])
PART_X = -0.044


def hair(head):
    me = head.data
    P, N = get_co(me), get_normals(me)
    theta = np.abs(np.arctan2(P[:, 0], -(P[:, 1] - 0.015)))
    above = P[:, 2] - np.interp(theta, HAIRLINE[:, 0], HAIRLINE[:, 1])

    on_top = smoothstep(0.02, 0.07, P[:, 2])
    front = smoothstep(0.06, -0.06, P[:, 1])
    right_of_part = smoothstep(PART_X - 0.004, PART_X + 0.014, P[:, 0])
    top = 0.008 + 0.014 * right_of_part * (0.55 + 0.45 * front) + 0.003 * (1 - right_of_part)
    part = 1 - 0.45 * np.exp(-((P[:, 0] - PART_X) / 0.008) ** 2) * smoothstep(0.05, 0.0, P[:, 1]) * on_top
    thick = (0.0035 + (top - 0.0035) * on_top) * part
    # combed locks: broad ridges running back and across from the part
    flow = np.array([0.45, 1.0]) / np.linalg.norm([0.45, 1.0])
    across = P[:, 0] * flow[1] - P[:, 1] * flow[0]
    thick += 0.0016 * np.sin(across * 2 * math.pi / 0.024) * on_top * smoothstep(0.004, 0.012, thick)
    # Past the hairline the shell dips under the skin, so the visible edge is a clean contour.
    rise = 0.005 + 0.006 * on_top * front
    thick = -0.003 + (thick + 0.003) * smoothstep(-0.004, rise, above)

    ob = bpy.data.objects.new("Hair", me.copy())
    bpy.context.scene.collection.objects.link(ob)
    set_co(ob.data, P + N * thick[:, None])
    delete_verts(ob, above < -0.004)
    s = Sculpt(ob)
    s.smooth(3)
    return s.done()


def brows(tree):
    ctrl = [(0.011, -0.098, 0.009), (0.022, -0.1, 0.0135), (0.036, -0.097, 0.0155), (0.05, -0.088, 0.013),
            (0.058, -0.079, 0.009)]
    C, _ = project(tree, catmull(ctrl, 3), 0.0004)
    n = len(C)
    t = np.linspace(0, 1, n)
    rh = 0.0036 - 0.0018 * t ** 1.5
    rw = np.full(n, 0.0011)
    a = sweep("brow_l", C, np.tile(UP, (n, 1)), rw, rh, nseg=6)
    b = sweep("brow_r", C * MIRROR, np.tile(UP, (n, 1)), rw, rh, nseg=6)
    b.data.flip_normals()
    return join("Brows", [a, b])


def moustache(tree):
    half = [(0.0, -0.106, -0.0495), (0.012, -0.104, -0.05), (0.024, -0.099, -0.052),
            (0.034, -0.091, -0.0545), (0.041, -0.083, -0.059)]
    ctrl = [p * MIRROR for p in np.array(half[:0:-1])] + [np.array(p) for p in half]
    C, _ = project(tree, catmull(ctrl, 3), 0.002)
    n = len(C)
    t = np.abs(np.linspace(-1, 1, n))
    rh = (0.0036 + 0.0036 * np.sin(math.pi * 0.85 * t)) * np.sqrt(np.clip(1 - t ** 6, 0.04, 1))
    rw = 0.0028 * (1 - 0.4 * t ** 2)
    return sweep("Moustache", C, np.tile(UP, (n, 1)), rw, rh, nseg=8)


def teeth(tree):
    xs = np.linspace(-0.03, 0.03, 11)
    front, _ = project(tree, [(x, -0.11, mouth_upper(x) - 0.004) for x in xs], 0.0)
    C = front + np.array([0, 0.0003, 0])
    C[:, 2] = mouth_upper(xs) - 0.0052
    rh = 0.0062 * (1 - 0.35 * np.abs(xs / 0.03) ** 2)
    return sweep("Teeth", C, np.tile(UP, (len(C), 1)), 0.0022, rh, nseg=6)


# ---------------------------------------------------------------------------
# Hoodie
# ---------------------------------------------------------------------------

BUST_BOTTOM = -0.36


def hoodie():
    low = BUST_BOTTOM - 0.02
    body = hull_obj("body", with_mirror([
        (0.07, 0.0, -0.185), (0.05, -0.058, -0.2), (0.0, -0.072, -0.215), (0.05, 0.06, -0.178), (0.0, 0.08, -0.175),
        (0.12, 0.03, -0.2), (0.165, 0.025, -0.216), (0.2, 0.015, -0.238), (0.222, 0.005, -0.266),
        (0.232, 0.0, -0.3), (0.236, 0.0, low), (0.2, -0.06, -0.262), (0.2, 0.065, -0.262),
        (0.1, -0.105, -0.255), (0.0, -0.11, -0.265), (0.12, -0.112, low), (0.0, -0.116, low),
        (0.2, -0.075, -0.31), (0.205, -0.078, low),
        (0.1, 0.12, -0.25), (0.0, 0.125, -0.26), (0.12, 0.125, low), (0.0, 0.126, low),
        (0.2, 0.08, -0.31), (0.205, 0.082, low),
    ]))

    # Hood: a fat roll lying around the neck, highest at the sides, crossing in a V at the front.
    phi = np.linspace(-math.pi, math.pi, 24, endpoint=False)
    cc = np.cos(phi)  # 1 = front, -1 = back
    R = np.interp(cc, [-1, 0, 1], [0.09, 0.092, 0.068])
    C = np.column_stack([R * np.sin(phi), 0.022 - R * cc,
                         np.interp(cc, [-1, -0.3, 0.3, 0.75, 1], [-0.148, -0.152, -0.162, -0.192, -0.222])])
    C = catmull(C, 3, closed=True)
    ph = np.arctan2(C[:, 0], -(C[:, 1] - 0.022))
    cc = np.cos(ph)
    rw = np.interp(cc, [-1, 0, 0.5, 1], [0.04, 0.034, 0.026, 0.019])
    rh = np.interp(cc, [-1, 0, 0.5, 1], [0.046, 0.04, 0.027, 0.016])
    hood = sweep("hood", C, np.tile(UP, (len(C), 1)), rw, rh, nseg=14, closed=True)
    drape = ellipsoid_obj("drape", np.array([0.0, 0.105, -0.215]), np.array([0.1, 0.045, 0.07]))
    ob = join("Hoodie", [body, hood, drape])
    soften(ob, 0.007, 12, 0.0035)

    s = Sculpt(ob)
    s.smooth(6)
    s.refresh()
    # raglan seams and a few soft folds
    s.crease([(0.08, -0.06, -0.21), (0.12, -0.087, -0.26), (0.165, -0.087, -0.32), (0.18, -0.083, -0.38)],
             0.004, -0.0025)
    s.crease([(0.08, 0.065, -0.195), (0.12, 0.092, -0.25), (0.165, 0.088, -0.32), (0.18, 0.088, -0.38)],
             0.004, -0.0025)
    s.crease([(0.06, -0.106, -0.29), (0.1, -0.109, -0.33), (0.13, -0.106, -0.36)], 0.012, -0.003)
    s.crease([(0.14, -0.1, -0.26), (0.17, -0.09, -0.3)], 0.01, -0.0025)
    s.refresh()
    s.smooth(2)
    return s.done()


def drawstrings(tree):
    obs = []
    for sx, drift in ((-1, 0.009), (1, 0.006)):
        ctrl = [(sx * 0.03, -0.12, -0.2), (sx * 0.032 + drift * 0.3, -0.13, -0.245),
                (sx * 0.034 + drift * 0.6, -0.14, -0.3), (sx * 0.034 + drift, -0.14, BUST_BOTTOM + 0.03)]
        C, _ = project(tree, catmull(ctrl, 5), 0.0045)
        C[0] += np.array([0, 0.003, 0.003])
        n = len(C)
        side = np.tile([1.0, 0, 0], (n, 1))
        obs.append(sweep("string", C, side, 0.0032, 0.0032, nseg=6))
        tip = C[-1] + (C[-1] - C[-2]) / np.linalg.norm(C[-1] - C[-2]) * 0.014
        obs.append(sweep("aglet", np.linspace(C[-1], tip, 3), side[:3], 0.0042, 0.0042, nseg=6))
        ring = [C[0] + np.array([0.0055 * math.cos(a), -0.002, 0.0055 * math.sin(a)])
                for a in np.linspace(0, 2 * math.pi, 12, endpoint=False)]
        obs.append(sweep("eyelet", ring, np.tile([0, -1.0, 0], (12, 1)), 0.0016, 0.0016, nseg=4, closed=True))
    return join("Drawstrings", obs)


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

QUADS = {"Head": 4000, "Ears": 360, "Hair": 1000, "Hoodie": 1900}


def build(retopo=True):
    bpy.ops.wm.read_factory_settings(use_empty=True)

    head = join("Head", head_blockout())
    soften(head, 0.004, 25, 0.0014)
    sculpt_head(head)

    ear_obj = join("Ears", ears())
    soften(ear_obj, 0.0025, 4, 0.001)
    sculpt_ears(ear_obj)

    tree = bvh_of(head)
    parts = {
        "Hair": hair(head),
        "Brows": brows(tree),
        "Moustache": moustache(tree),
        "Teeth": teeth(tree),
        "Eyes": eyes(),
        "Hoodie": hoodie(),
    }
    parts["Head"] = head
    parts["Ears"] = ear_obj
    parts["Drawstrings"] = drawstrings(bvh_of(parts["Hoodie"]))

    for name, faces in QUADS.items() if retopo else ():
        quadriflow(parts[name], faces, symmetric=name != "Hair")
    bisect_below(parts["Hoodie"], BUST_BOTTOM)
    bisect_below(parts["Head"], -0.24)
    for name, ob in parts.items():
        ob.data.name = name
    return parts


def line_copy(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.delete(bm, geom=bm.faces[:], context="FACES_ONLY")
    return obj_from_bmesh(ob.name + "_lines", bm)


def export(parts):
    os.makedirs(os.path.dirname(GLB_PATH), exist_ok=True)
    lines = [line_copy(ob) for ob in parts.values()]
    names = set(parts) | {ob.name for ob in lines}
    for ob in bpy.context.scene.objects:
        ob.select_set(ob.name in names)
    bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format="GLB", use_selection=True, export_apply=True,
                              export_normals=False, export_texcoords=False, export_materials="NONE",
                              use_mesh_edges=True, export_yup=True)
    for ob in lines:
        bpy.data.objects.remove(ob)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parts = build(retopo="--dense" not in argv)
    for name, ob in parts.items():
        print("PART", name, len(ob.data.vertices), "verts", len(ob.data.polygons), "faces")
    if "--no-export" not in argv:
        export(parts)
    if "--preview" in argv:
        out_dir = argv[argv.index("--preview") + 1]
        sys.path.insert(0, out_dir)
        import preview_render
        preview_render.render_all(parts, out_dir)
