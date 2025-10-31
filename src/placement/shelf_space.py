import glm
from collections import defaultdict
from src.utils.geometry import aabb_world_from_local

class ShelfSpace:
    """
    Representa el volumen útil de una estantería importada.
    Detecta alturas reales de baldas desde la geometría y define, para cada balda:
      - y_superficie (altura de apoyo real) en campo 'y'
      - techo inmediato 'y_top' (si existe)
      - rectángulo útil por balda en XZ: x0,x1,z0,z1
    """
    def __init__(self, model_obj, levels=5, margin_xy=0.03, back_offset=0.03,
                 y_bin=0.01, board_merge=0.03, per_level_shrink=0.01,
                 label=None, debug=False):
        self.model = model_obj
        self.levels_hint = levels
        self.margin_xy = margin_xy
        self.back_offset = back_offset
        self.y_bin = y_bin
        self.board_merge = board_merge
        self.per_level_shrink = per_level_shrink
        self.label = label or "shelf"
        self.debug = debug

        local = model_obj.aabb_local()
        world_min, world_max = aabb_world_from_local(local[0], local[1], model_obj.get_model_matrix())
        self.world_min = glm.vec3(*world_min)
        self.world_max = glm.vec3(*world_max)

        self.shelves = []
        self._build_levels_from_geometry()

    # --- utilidad: hacia dónde "mira" el +Z local del modelo en mundo ---
    def _front_axis(self):
        M = self.model.get_model_matrix()
        f = glm.vec3(M * glm.vec4(0.0, 0.0, 1.0, 0.0))  # vector (no punto)
        if abs(f.x) >= abs(f.z):
            return 'x+' if f.x >= 0.0 else 'x-'
        else:
            return 'z+' if f.z >= 0.0 else 'z-'

    # --- utilidad: cuantiles robustos para recortar outliers ---
    def _quantile(self, vals, q):
        if not vals:
            return None
        s = sorted(vals)
        i = max(0, min(len(s) - 1, int(q * (len(s) - 1))))
        return s[i]

    # --- detección por geometría + aplicación de back_offset orientado ---
    def _build_levels_from_geometry(self):
        """
        Detección robusta usando normales:
        - Tomamos triángulos cuya normal tenga componente Y alta (n.y >= normal_thresh).
        - Agrupamos por altura con bins en Y para obtener cada balda.
        - El rectángulo útil XZ se calcula SOLO con los vértices de esos triángulos (sin postes).
        """
        # 1) Triángulos + normales en mundo
        tris_norms = []
        try:
            tris_norms = self.model.get_world_triangles_and_normals()
        except Exception:
            tris_norms = []

        if not tris_norms:
            # Fallback: método anterior por cuantiles
            if self.debug:
                print(f"[ShelfSpace:{self.label}] ⚠️ Sin triángulos/normales; usando fallback.")
            return self._build_levels_from_vertices_fallback()

        normal_thresh = 0.85  # cuanto más alto, más “horizontales” (superficie superior)
        # 2) Filtrar triángulos apuntando hacia +Y
        top_tris = [tri for tri in tris_norms if tri[1].y >= normal_thresh]
        if not top_tris:
            if self.debug:
                print(f"[ShelfSpace:{self.label}] ⚠️ Sin triángulos con n.y>={normal_thresh}; fallback.")
            return self._build_levels_from_vertices_fallback()
        
        tri_infos = []
        for (p0, p1, p2), n in top_tris:
            y_mean = (p0.y + p1.y + p2.y) / 3.0
            tri_infos.append((y_mean, (p0, p1, p2)))

        # 4) Bins en Y para agrupar triángulos por balda
        inv = 1.0 / self.y_bin if self.y_bin > 0 else 100.0
        buckets = {}  # key -> lista de triángulos
        for y_mean, tri in tri_infos:
            key = round(y_mean * inv)
            buckets.setdefault(key, []).append(tri)

        # 5) Centro/techo por balda (usando medias y merge por board_merge)
        candidate_levels = sorted((sum(tri[j].y for tri in tris for j in range(3)) / (3 * len(tris)), tris)
                                for _, tris in buckets.items())
        # candidate_levels: lista de (y_media_balda, [tris...])
        # fusionamos por proximidad vertical
        merged = []
        for y_mean, tris in sorted(candidate_levels, key=lambda x: x[0]):
            if not merged:
                merged.append([y_mean, y_mean, [tris]])
            else:
                y0, y1, groups = merged[-1]
                if abs(y_mean - y1) <= self.board_merge:
                    merged[-1][1] = max(y1, y_mean)
                    groups.append(tris)
                else:
                    merged.append([y_mean, y_mean, [tris]])

        # Nos quedamos con la parte superior de cada grupo + concatenamos sus tris
        levels = []
        for y0, y1, groups in merged:
            tris = [t for group in groups for t in group]
            y_top_surface = y1
            levels.append((y_top_surface, tris))

        if not levels:
            if self.debug:
                print(f"[ShelfSpace:{self.label}] ⚠️ No se detectaron niveles; fallback.")
            return self._build_levels_from_vertices_fallback()

        # 6) Recorte a 'levels_hint'
        if len(levels) > self.levels_hint:
            # quitar tapa/peana cuando hay margen
            if len(levels) >= self.levels_hint + 2:
                levels = levels[1:-1]
            else:
                levels = levels[:-1]
        if len(levels) > self.levels_hint:
            start = (len(levels) - self.levels_hint) // 2
            levels = levels[start:start + self.levels_hint]

        # 7) Construcción de rectángulos útiles por balda SOLO con vértices de esas superficies
        self.shelves = []
        axis = self._front_axis()

        for idx, (yb, tris) in enumerate(levels):
            # puntos XZ de la superficie superior filtrada
            xs, zs = [], []
            band_lo = yb - self.board_merge * 1.2
            band_hi = yb + self.board_merge * 1.2
            for (p0, p1, p2) in tris:
                for p in (p0, p1, p2):
                    if band_lo <= p.y <= band_hi:
                        xs.append(p.x)
                        zs.append(p.z)

            if self.debug:
                print(f"[ShelfSpace:{self.label}] L{idx} (normals) pts: xs={len(xs)} zs={len(zs)}")

            if not xs or not zs:
                # fallback local para este nivel
                x0 = self.world_min.x + self.margin_xy
                x1 = self.world_max.x - self.margin_xy
                z0 = self.world_min.z + self.margin_xy
                z1 = self.world_max.z - self.margin_xy
            else:
                # Como ya excluimos postes, podemos usar min/max directos
                x_min, x_max = min(xs), max(xs)
                z_min, z_max = min(zs), max(zs)

                x0 = x_min + self.margin_xy + self.per_level_shrink
                x1 = x_max - self.margin_xy - self.per_level_shrink
                z0 = z_min + self.margin_xy + self.per_level_shrink
                z1 = z_max - (self.margin_xy + self.per_level_shrink)

            # Aplicar fondo según orientación del mueble
            if   axis == 'z+':
                z0 += self.back_offset
            elif axis == 'z-':
                z1 -= self.back_offset
            elif axis == 'x+':
                x0 += self.back_offset
            elif axis == 'x-':
                x1 -= self.back_offset

            # Normalizar
            x0, x1 = min(x0, x1), max(x0, x1)
            z0, z1 = min(z0, z1), max(z0, z1)

            # Buscar techo inmediato
            y_top = None
            for (y_next, _) in sorted(levels, key=lambda e: e[0]):
                if y_next > yb:
                    y_top = y_next
                    break

            width = max(0.0, x1 - x0)
            depth = max(0.0, z1 - z0)
            if self.debug:
                print(f"[ShelfSpace:{self.label}] axis={axis} y={yb:.3f} y_top={str(round(y_top,3)) if y_top else 'None'} "
                    f"rectXZ=({x0:.3f},{x1:.3f})x({z0:.3f},{z1:.3f}) sizeXZ=({width:.3f},{depth:.3f})")

            self.shelves.append(dict(y=yb, y_top=y_top, x0=x0, x1=x1, z0=z0, z1=z1))

        if not self.shelves:
            self._build_levels_uniform()


    # --- fallback uniforme si falla la detección ---
    def _build_levels_uniform(self):
        h = self.world_max.y - self.world_min.y
        dy = h / max(self.levels_hint, 1)
        self.shelves = []
        x0 = self.world_min.x + self.margin_xy
        x1 = self.world_max.x - self.margin_xy
        z0 = self.world_min.z + self.margin_xy
        z1 = self.world_max.z - self.margin_xy
        for i in range(self.levels_hint):
            y = self.world_min.y + dy * (i + 0.5)  # centro (fallback)
            self.shelves.append(dict(
                y=y, y_top=None,
                x0=min(x0, x1), x1=max(x0, x1),
                z0=min(z0, z1), z1=max(z0, z1)
            ))

    def get_levels(self):
        return self.shelves
    
    def _build_levels_from_vertices_fallback(self):
        """Antiguo método (cuantiles por vértices) como fallback."""
        verts_w = self.model.get_world_positions()
        if not verts_w:
            self._build_levels_uniform()
            return

        bins = defaultdict(list)
        inv = 1.0 / self.y_bin if self.y_bin > 0 else 100.0
        for v in verts_w:
            key = round(v.y * inv)
            bins[key].append(v.y)

        ys = sorted(sum(vals) / len(vals) for vals in bins.values())
        surfaces = []
        for y in ys:
            if not surfaces:
                surfaces.append([y, y])
            else:
                y0, y1 = surfaces[-1]
                if abs(y - y1) <= self.board_merge:
                    surfaces[-1][1] = max(y1, y)
                else:
                    surfaces.append([y, y])

        top_surfaces = [y1 for (y0, y1) in surfaces]
        if not top_surfaces:
            self._build_levels_uniform()
            return

        candidates = top_surfaces[:]
        if len(candidates) > self.levels_hint:
            if len(candidates) >= self.levels_hint + 2:
                candidates = candidates[1:-1]
            else:
                candidates = candidates[:-1]
        if len(candidates) > self.levels_hint:
            start = (len(candidates) - self.levels_hint) // 2
            candidates = candidates[start:start + self.levels_hint]

        self.shelves = []
        axis = self._front_axis()

        # cuantiles por eje (más laxo en X)
        qx_lo, qx_hi = 0.01, 0.99
        qz_lo, qz_hi = 0.05, 0.95

        for yb in candidates:
            band_lo = yb - self.board_merge * 1.2
            band_hi = yb + self.board_merge * 1.2
            xs, zs = [], []
            for v in verts_w:
                if band_lo <= v.y <= band_hi:
                    xs.append(v.x)
                    zs.append(v.z)

            if not xs or not zs:
                x0 = self.world_min.x + self.margin_xy
                x1 = self.world_max.x - self.margin_xy
                z0 = self.world_min.z + self.margin_xy
                z1 = self.world_max.z - self.margin_xy
            else:
                x_min = self._quantile(xs, qx_lo); x_max = self._quantile(xs, qx_hi)
                z_min = self._quantile(zs, qz_lo); z_max = self._quantile(zs, qz_hi)

                x0 = x_min + self.margin_xy + self.per_level_shrink
                x1 = x_max - self.margin_xy - self.per_level_shrink
                z0 = z_min + self.margin_xy + self.per_level_shrink
                z1 = z_max - (self.margin_xy + self.per_level_shrink)

            if   axis == 'z+':
                z0 += self.back_offset
            elif axis == 'z-':
                z1 -= self.back_offset
            elif axis == 'x+':
                x0 += self.back_offset
            elif axis == 'x-':
                x1 -= self.back_offset

            x0, x1 = min(x0, x1), max(x0, x1)
            z0, z1 = min(z0, z1), max(z0, z1)

            y_top = None
            for y_next in sorted(candidates):
                if y_next > yb:
                    y_top = y_next
                    break

            self.shelves.append(dict(y=yb, y_top=y_top, x0=x0, x1=x1, z0=z0, z1=z1))

        if not self.shelves:
            self._build_levels_uniform()

