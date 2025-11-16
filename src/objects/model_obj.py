from .base_object import BaseObject
import numpy as np
import glm

_GEOM_CACHE = {}  # path -> (vertex_bytes, aabb_min, aabb_max)
_TRI_CACHE = {}  # path -> {'positions': list[(x,y,z)], 'tri_idx': list[(i0,i1,i2)]}

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
        self._texture_path = texture_path
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
    def get_position(self): return self._position


    # ---------- Geometría ----------

    # ---------- Geometría ----------
    def get_vertex_data(self):
        """
        Genera los datos de vértices del OBJ.
        - Si self.use_texture == True  -> (x, y, z, u, v)  (5 floats)
        - Si self.use_texture == False -> (x, y, z)        (3 floats, sin UV)
        El caché se separa por (obj_path, use_texture) para evitar mezclar formatos.
        """
        # --- clave de caché diferenciando si usamos textura o no ---
        use_tex = bool(getattr(self, "use_texture", False))
        cache_key = (self.obj_path, use_tex)

        # Intentar leer de caché de geometría
        if cache_key in _GEOM_CACHE:
            vb, mn, mx = _GEOM_CACHE[cache_key]
            self._aabb = (mn, mx)
            # Recuperar posiciones/triángulos (comparten clave solo por path, da igual UV)
            extra = _TRI_CACHE.get(self.obj_path)
            if extra:
                self._raw_positions = extra.get("positions")
                self._triangles_idx = extra.get("tri_idx")
            print(
                f"[ModelOBJ] cache '{self.obj_path}' use_tex={use_tex}: "
                f"{len(vb) // (20 if use_tex else 12)} verts, AABB {mn}..{mx}"
            )
            return vb

        positions = []
        texcoords = []
        faces = []      # cada cara: lista de (vi, ti) en indices de positions/texcoords
        tri_idx = []    # lista de triángulos en índices de positions

        # --- parseo del OBJ ---
        try:
            with open(self.obj_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if not line or line.startswith("#"):
                        continue

                    if line.startswith("v "):
                        _, x, y, z = line.strip().split()[:4]
                        positions.append((float(x), float(y), float(z)))

                    elif line.startswith("vt "):
                        parts = line.strip().split()
                        if len(parts) >= 3:
                            _, u, v = parts[:3]
                            u, v = float(u), float(v)
                            if self._invert_v:
                                v = 1.0 - v
                            texcoords.append((u, v))

                    elif line.startswith("f "):
                        items = line.strip().split()[1:]
                        idx = []
                        for it in items:
                            a = it.split("/")
                            vi = int(a[0])
                            ti = int(a[1]) if len(a) > 1 and a[1] != "" else 0
                            if vi < 0:
                                vi = len(positions) + vi + 1
                            if ti < 0:
                                ti = len(texcoords) + ti + 1
                            idx.append((vi - 1, ti - 1))
                        faces.append(idx)
        except Exception as e:
            raise RuntimeError(f"Error leyendo OBJ '{self.obj_path}': {e}")

        if not positions:
            raise RuntimeError(f"OBJ '{self.obj_path}' sin datos de geometría.")

        # --- construir stream y triángulos con triangulación tipo fan ---
        stream = []
        for idx in faces:
            if len(idx) < 3:
                continue
            # fan: (0,i,i+1)
            for i in range(1, len(idx) - 1):
                fan = (0, i, i + 1)
                v_indices = []
                for k in fan:
                    vi, ti = idx[k]
                    v_indices.append(vi)
                    x, y, z = positions[vi]

                    if use_tex and 0 <= ti < len(texcoords):
                        u, v = texcoords[ti]
                        stream.extend([x, y, z, u, v])
                    else:
                        stream.extend([x, y, z])
                # guardar triángulo en índices de positions
                tri_idx.append((v_indices[0], v_indices[1], v_indices[2]))

        if not stream:
            raise RuntimeError(f"OBJ '{self.obj_path}' sin triángulos válidos.")

        # --- AABB local ---
        xs = [p[0] for p in positions]
        ys = [p[1] for p in positions]
        zs = [p[2] for p in positions]
        mn = (min(xs), min(ys), min(zs))
        mx = (max(xs), max(ys), max(zs))
        self._aabb = (mn, mx)

        # Guardar datos locales para ShelfSpace / colisiones
        self._raw_positions = positions
        self._triangles_idx = tri_idx
        _TRI_CACHE[self.obj_path] = {"positions": positions, "tri_idx": tri_idx}

        # --- empaquetar a bytes ---
        import numpy as np
        vb = np.array(stream, dtype="f4").tobytes()
        _GEOM_CACHE[cache_key] = (vb, mn, mx)

        print(
            f"[ModelOBJ] loaded '{self.obj_path}' use_tex={use_tex}: "
            f"{len(stream) // (5 if use_tex else 3)} verts, AABB {mn}..{mx}"
        )
        return vb

    
    # ---------- Utilidades ----------

    def get_world_triangles(self):
        """
        Devuelve lista de triángulos en mundo: [(p0, p1, p2), ...]
        donde p* son glm.vec3. Requiere _raw_positions y _triangles_idx.
        """
        if not hasattr(self, '_raw_positions') or self._raw_positions is None:
            return []
        if not hasattr(self, '_triangles_idx') or self._triangles_idx is None:
            return []
        M = self.get_model_matrix()
        wp = [glm.vec3(M * glm.vec4(x, y, z, 1.0)) for (x, y, z) in self._raw_positions]
        tris = []
        for i0, i1, i2 in self._triangles_idx:
            tris.append((wp[i0], wp[i1], wp[i2]))
        return tris

    def get_world_triangles_and_normals(self):
        """
        Devuelve lista de tuplas: [((p0,p1,p2), n), ...] en espacio mundo,
        con n = normal unitaria del tri (orientación por producto cruzado).
        """
        tris = self.get_world_triangles()
        out = []
        for (p0, p1, p2) in tris:
            e1 = p1 - p0
            e2 = p2 - p0
            n = glm.normalize(glm.cross(e1, e2)) if glm.length(glm.cross(e1, e2)) > 1e-9 else glm.vec3(0, 1, 0)
            out.append(((p0, p1, p2), n))
        return out
    
    def get_world_positions(self):
        """Devuelve lista de glm.vec3 de los vértices en mundo (con m_model actual)."""
        if not hasattr(self, '_raw_positions') or self._raw_positions is None:
            return []
        M = self.get_model_matrix()
        return [glm.vec3(M * glm.vec4(x, y, z, 1.0)) for (x, y, z) in self._raw_positions]

    def min_y_local(self):
        """min_y del AABB local del modelo (sin escala)."""
        if not self._aabb:
            return 0.0
        return self._aabb[0][1]

    def height_width_depth_scaled(self):
        """Tamaños escalados del AABB local."""
        if not self._aabb:
            return 0.0, 0.0, 0.0
        mn, mx = self._aabb
        sx = (mx[0] - mn[0]) * self._scale.x
        sy = (mx[1] - mn[1]) * self._scale.y
        sz = (mx[2] - mn[2]) * self._scale.z
        return sx, sy, sz

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
    
    def aabb_local_sizes(self):
        if not self._aabb:
            return 0.0, 0.0, 0.0
        sx = self._aabb[1][0] - self._aabb[0][0]
        sy = self._aabb[1][1] - self._aabb[0][1]
        sz = self._aabb[1][2] - self._aabb[0][2]
        return sx, sy, sz

    def clone(self):
        """ Crea otra instancia que comparte geometría/texture (usa la caché del loader). """
        return type(self)(
            self.app, self.obj_path, self._texture_path if self._texture_path else None,
            position=(self._position.x, self._position.y, self._position.z),
            scale=(self._scale.x, self._scale.y, self._scale.z),
            rotation_deg=(self._rotation.x, self._rotation.y, self._rotation.z),
            invert_v=self._invert_v
        )

