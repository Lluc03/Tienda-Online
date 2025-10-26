from src.utils.geometry import rects_overlap_2d

def pack_grid_on_shelf(level_rect, footprint, gap=0.04, max_items=None):
    """
    Empaqueta greedy en rejilla sobre una balda:
      - level_rect: dict {y, x0,x1,z0,z1}
      - footprint: (w, d) tamaño en X y Z de la huella del producto (AABB local ya escalado)
      - gap: separación entre productos y bordes
      - max_items: máximo de elementos (None = ilimitado)
    Devuelve lista de poses: [(x, y, z)] centrados en cada celda.
    """
    x0, x1, z0, z1, y = level_rect['x0'], level_rect['x1'], level_rect['z0'], level_rect['z1'], level_rect['y']
    w, d = footprint
    w_eff = w + gap
    d_eff = d + gap
    placements = []

    # vamos colocando de izquierda a derecha, frente a fondo
    x = x0 + w/2.0 + gap/2.0
    while x + w/2.0 <= x1 - gap/2.0:
        z = z0 + d/2.0 + gap/2.0
        while z + d/2.0 <= z1 - gap/2.0:
            # comprobar solapes con lo ya colocado (en XZ)
            rectA = (x - w/2.0, z - d/2.0, x + w/2.0, z + d/2.0)
            ok = True
            for px, py, pz, pw, pd in placements:
                rectB = (px - pw/2.0, pz - pd/2.0, px + pw/2.0, pz + pd/2.0)
                if rects_overlap_2d(*rectA, *rectB):
                    ok = False
                    break
            if ok:
                placements.append((x, y, z, w, d))
                if max_items is not None and len(placements) >= max_items:
                    return [(px, py, pz) for (px, py, pz, _, _) in placements]
            z += d_eff
        x += w_eff

    return [(px, py, pz) for (px, py, pz, _, _) in placements]
