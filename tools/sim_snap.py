"""Offline check of the snap maths in bb_socket/bb_snap.

Ports HF's aol_rotation helpers (including their y/z swaps) to Python and
verifies, for flat and tilted foundations, that:

  * Quaternion(euler) -> to_euler_angles round-trips (pieces are stored as
    euler angles and rebuilt with Quaternion(angle) after a load)
  * a wall snapped to a foundation edge lies along that edge
  * a wall snapped to that wall's side continues along the same edge line
  * a neighbouring foundation's matching edge produces the same wall slot,
    so occupancy is detected from either side

Run: python tools/sim_snap.py
"""

import math

CELL, HALF, WALL_H, SLAB_T = 2.5, 1.25, 3.0, 0.2


class V:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x, self.y, self.z = x, y, z

    def __add__(self, o): return V(self.x + o.x, self.y + o.y, self.z + o.z)
    def __sub__(self, o): return V(self.x - o.x, self.y - o.y, self.z - o.z)
    def __mul__(self, s): return V(self.x * s, self.y * s, self.z * s)
    def dot(self, o): return self.x * o.x + self.y * o.y + self.z * o.z
    def cross(self, o):
        return V(self.y * o.z - self.z * o.y, self.z * o.x - self.x * o.z, self.x * o.y - self.y * o.x)
    def len(self): return math.sqrt(self.dot(self))
    def __repr__(self): return "(%.3f, %.3f, %.3f)" % (self.x, self.y, self.z)


def rotation_around(v, a):
    q = Q(math.cos(a / 2), V(v.x * math.sin(a / 2), v.y * math.sin(a / 2), v.z * math.sin(a / 2)))
    q.normalize()
    return q


class Q:
    def __init__(self, w=1.0, v=None):
        self.w = w
        v = v or V()
        self.x, self.y, self.z = v.x, v.y, v.z

    @staticmethod
    def from_euler(s):
        q = rotation_around(V(0, 0, 1), s.z).mul(rotation_around(V(1, 0, 0), s.x)).mul(rotation_around(V(0, 1, 0), s.y))
        return q

    def normalize(self):
        n = math.sqrt(self.w ** 2 + self.x ** 2 + self.y ** 2 + self.z ** 2)
        self.w, self.x, self.y, self.z = self.w / n, self.x / n, self.y / n, self.z / n

    def rotate(self, v):
        v = V(v.x, v.z, v.y)
        u = V(self.x, self.z, self.y)
        s = self.w
        r = u * (2.0 * u.dot(v)) + v * (s * s - u.dot(u)) + u.cross(v) * (2 * s)
        return V(r.x, r.z, r.y)

    def mul(self, q):
        qv, sv = V(q.x, q.y, q.z), V(self.x, self.y, self.z)
        w = self.w * q.w - sv.dot(qv)
        v = sv.cross(qv) + qv * self.w + sv * q.w
        return Q(w, v)

    def to_euler(self):
        x, y, z, w = self.x, self.y, self.z, self.w
        x2, y2, z2 = x + x, y + y, z + z
        xx, xy, xz = x * x2, x * y2, x * z2
        yy, yz, zz = y * y2, y * z2, z * z2
        wx, wy, wz = w * x2, w * y2, w * z2
        m11, m12 = 1 - (yy + zz), xy - wz
        m21, m22 = xy + wz, 1 - (xx + zz)
        m31, m32, m33 = xz - wy, yz + wx, 1 - (xx + yy)
        ax = math.asin(max(-1, min(1, m32)))
        if abs(m32) < 0.9999999:
            ay, az = math.atan2(-m31, m33), math.atan2(-m12, m22)
        else:
            ay, az = 0, math.atan2(m21, m11)
        return V(ax, ay, az)


UP = V(0, 1, 0)


def slot(piece_pos, piece_angle, offset, yaw_deg):
    q = Q.from_euler(piece_angle)
    pos = piece_pos + q.rotate(offset)
    # aol_rotation convention: a.mul(b) applies a first, then b
    rot = rotation_around(UP, math.radians(yaw_deg)).mul(q)
    return pos, rot.to_euler()     # stored the way HF stores it


def check(label, cond):
    print(("PASS " if cond else "FAIL ") + label)
    return cond


def run(angle):
    print("\nfoundation angle", angle)
    ok = True
    f_pos = V(10, 5, -3)
    qf = Q.from_euler(angle)

    # round trip
    q2 = Q.from_euler(qf.to_euler())
    for t in (V(1, 0, 0), V(0, 1, 0), V(0, 0, 1)):
        ok &= check("euler round trip " + repr(t), (qf.rotate(t) - q2.rotate(t)).len() < 1e-6)

    # wall on east edge
    w_pos, w_ang = slot(f_pos, angle, V(HALF, SLAB_T, 0), 90)
    qw = Q.from_euler(w_ang)
    edge_dir = qf.rotate(V(0, 0, 1))
    wall_width = qw.rotate(V(1, 0, 0))
    ok &= check("east wall width parallel to edge", abs(abs(edge_dir.dot(wall_width)) - 1) < 1e-6)
    ok &= check("east wall up matches foundation up", (qw.rotate(UP) - qf.rotate(UP)).len() < 1e-6)

    # wall on north edge
    n_pos, n_ang = slot(f_pos, angle, V(0, SLAB_T, HALF), 0)
    qn = Q.from_euler(n_ang)
    ok &= check("north wall width parallel to x edge",
                abs(abs(qf.rotate(V(1, 0, 0)).dot(qn.rotate(V(1, 0, 0)))) - 1) < 1e-6)

    # wall continuing the east wall to the right
    r_pos, _ = slot(w_pos, w_ang, V(CELL, 0, 0), 0)
    neighbour_north = f_pos + qf.rotate(V(0, 0, CELL))
    neighbour_south = f_pos + qf.rotate(V(0, 0, -CELL))
    exp_n, _ = slot(neighbour_north, angle, V(HALF, SLAB_T, 0), 90)
    exp_s, _ = slot(neighbour_south, angle, V(HALF, SLAB_T, 0), 90)
    ok &= check("side wall lands on a neighbour foundation's east edge",
                min((r_pos - exp_n).len(), (r_pos - exp_s).len()) < 1e-6)

    # shared edge: foundation to the east, its west edge slot == our east edge slot
    east_f = f_pos + qf.rotate(V(CELL, 0, 0))
    shared, _ = slot(east_f, angle, V(-HALF, SLAB_T, 0), -90)
    ok &= check("shared edge gives identical wall slot", (shared - w_pos).len() < 1e-6)

    # roof on top of the east wall, inside side
    roof_pos, roof_ang = slot(w_pos, w_ang, V(0, WALL_H, -HALF), 0)
    roof_pos2, _ = slot(w_pos, w_ang, V(0, WALL_H, HALF), 0)
    above = f_pos + qf.rotate(V(0, SLAB_T + WALL_H, 0))
    ok &= check("one roof slot is directly above the foundation",
                min((roof_pos - above).len(), (roof_pos2 - above).len()) < 1e-6)
    return ok


def upright(q):
    """Port of bb_piece.upright_rotation: keep only the heading of q."""
    fwd = q.rotate(V(0, 0, 1))
    fwd.y = 0
    n = fwd.len()
    if n < 1e-4:
        return Q()
    fwd = fwd * (1 / n)
    h = math.atan2(fwd.x, fwd.z)
    q_up = rotation_around(UP, h)
    if q_up.rotate(V(0, 0, 1)).dot(fwd) < 0.999:
        q_up = rotation_around(UP, -h)
    return q_up


def run_upright(angle):
    print("\nupright from tilted angle", angle)
    q = Q.from_euler(angle)
    u = upright(q)
    fwd = q.rotate(V(0, 0, 1))
    fwd.y = 0
    fwd = fwd * (1 / fwd.len())
    ok = check("upright keeps heading", (u.rotate(V(0, 0, 1)) - fwd).len() < 1e-6)
    ok &= check("upright is level", (u.rotate(UP) - UP).len() < 1e-6)
    e = u.to_euler()
    ok &= check("upright euler is yaw-only", abs(e.x) < 1e-6 and abs(e.z) < 1e-6)
    return ok


if __name__ == "__main__":
    results = [run(a) for a in (V(0, 0, 0), V(0, math.radians(30), 0), V(0.1, 0.7, -0.05), V(0, math.pi, 0))]
    results += [run_upright(a) for a in (V(0.08, 0.7, -0.05), V(-0.1, -2.5, 0.12), V(0.05, math.pi, 0.0), V(0, 0, 0))]
    print("\nALL PASS" if all(results) else "\nSOME FAILED")
