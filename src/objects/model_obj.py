# src/objects/model_obj.py
from .base_object import BaseObject
import numpy as np
import glm

_GEOM_CACHE = {}  # path -> (vertex_bytes, aabb_min, aabb_max)

class ModelOBJ(BaseObject):
    """
    Loader robusto de OBJ:
    - Parser simple de 'v', 'vt', 'f' (triangulación por fan).
    - VBO intercalado (pos:3f, uv:2f) compatible con el shader texturizado.
    - Rotación/escala/posición dinámicas (m_model se recalcula cada frame).
    """
    def __init__(self, app, obj_path, texture_path=None,
                 position=(0.0, 0.0, 0.0),
                 scale=(1.0, 1.0, 1.0),
                 rotation_deg=(0.0, 0.0, 0.0),
                 invert_v=False):
        self.obj_path  = obj_path
        self._position = glm.vec3(*position)
        self._scale    = glm.vec3(*scale)
        self._rotation = glm.vec3(*rotation_deg)  # (pitch, yaw, roll) en grados
        self._invert_v = invert_v
        self._aabb     = None
        super().__init__(app, texture_path=texture_path, uv_scale=(1.0, 1.0))

    # ---------- Transform ----------
    def get_model_matrix(self):
        M = glm.mat4()
        M = glm.translate(M, self._position)
        M = glm.rotate(M, glm.radians(self._rotation.z), glm.vec3(0, 0, 1))
        M = glm.rotate(M, glm.radians(self._rotation.y), glm.vec3(0, 1, 0))
        M = glm.rotate(M, glm.radians(self._rotation.x), glm.vec3(1, 0, 0))
        M = glm.scale(M, self._scale)
        return M

    def set_position(self, xyz): self._position = glm.vec3(*xyz)
    def set_scale(self, xyz):    self._scale    = glm.vec3(*xyz)
    def set_rotation(self, deg): self._rotation = glm.vec3(*deg)

    # ---------- Geometría ----------
    def get_vertex_data(self):
        if self.obj_path in _GEOM_CACHE:
            vb, mn, mx = _GEOM_CACHE[self.obj_path]
            self._aabb = (mn, mx)
            print(f"[ModelOBJ] cache '{self.obj_path}': {len(vb)//20} verts, AABB {mn}..{mx}")
            return vb

        positions, texcoords = [], []
        stream = []  # [x,y,z,u,v]*N

        try:
            with open(self.obj_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if not line or line.startswith('#'):
                        continue
                    if line.startswith('v '):  # posición
                        _, x, y, z = line.strip().split()[:4]
                        positions.append((float(x), float(y), float(z)))
                    elif line.startswith('vt '):  # uv
                        parts = line.strip().split()
                        if len(parts) >= 3:
                            _, u, v = parts[:3]
                            u, v = float(u), float(v)
                            if self._invert_v: v = 1.0 - v
                            texcoords.append((u, v))
                    elif line.startswith('f '):  # cara (triangulamos por fan)
                        items = line.strip().split()[1:]  # v/vt/vn o v/vt o v//vn o v
                        idx = []
                        for it in items:
                            a = it.split('/')
                            vi = int(a[0])
                            ti = int(a[1]) if len(a) > 1 and a[1] != '' else 0
                            # índices negativos → relativos al final
                            if vi < 0: vi = len(positions) + vi + 1
                            if ti < 0: ti = len(texcoords) + ti + 1
                            idx.append((vi-1, ti-1))
                        # fan: (0, i, i+1)
                        for i in range(1, len(idx)-1):
                            for k in (0, i, i+1):
                                vi, ti = idx[k]
                                x, y, z = positions[vi]
                                if 0 <= ti < len(texcoords):
                                    u, v = texcoords[ti]
                                else:
                                    u, v = 0.0, 0.0
                                stream.extend([x, y, z, u, v])
        except Exception as e:
            raise RuntimeError(f"Error leyendo OBJ '{self.obj_path}': {e}")

        if not stream:
            raise RuntimeError(f"OBJ '{self.obj_path}' sin datos de geometría.")

        xs = [p[0] for p in positions] or [0.0]
        ys = [p[1] for p in positions] or [0.0]
        zs = [p[2] for p in positions] or [0.0]
        mn = (min(xs), min(ys), min(zs))
        mx = (max(xs), max(ys), max(zs))
        self._aabb = (mn, mx)

        vb = np.array(stream, dtype='f4').tobytes()
        _GEOM_CACHE[self.obj_path] = (vb, mn, mx)
        print(f"[ModelOBJ] loaded(fallback) '{self.obj_path}': {len(stream)//5} verts, AABB {mn}..{mx}")
        return vb

    # ---------- Utilidades ----------
    def aabb_local(self): return self._aabb

    def align_to_floor(self):
        if not self._aabb: return
        min_y = self._aabb[0][1]
        self._position.y += -min_y * self._scale.y

    def auto_scale_by_longest_side(self, target_size):
        if not self._aabb: return
        sx = self._aabb[1][0] - self._aabb[0][0]
        sy = self._aabb[1][1] - self._aabb[0][1]
        sz = self._aabb[1][2] - self._aabb[0][2]
        longest = max(sx, sy, sz) if max(sx, sy, sz) > 0 else 1.0
        factor = target_size / longest
        self._scale *= factor
        print(f"[ModelOBJ] autoscale: longest={longest:.3f} -> factor={factor:.3f}")

    # recalcular m_model antes de subir a los shaders
    def update_matrices(self):
        self.m_model = self.get_model_matrix()
        super().update_matrices()
