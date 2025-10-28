def pack_grid_on_shelf(level_rect, footprint, gap=0.04, max_items=None):
    """
    Devuelve una lista de posiciones (x, y, z) centradas para colocar cajas de huella 'footprint'
    sobre una balda 'level_rect' (dict con x0,x1,z0,z1,y).
    Usa un grid con separación 'gap'. Con 'max_items' limita el número total.
    """
    x0, x1 = level_rect["x0"], level_rect["x1"]
    z0, z1 = level_rect["z0"], level_rect["z1"]
    y = level_rect["y"]

    w, d = footprint  # ancho (X) y fondo (Z) del objeto
    poses = []
    eps = 1e-6  # evita perder la última columna/fila por acumulación flotante

    x = x0 + w / 2.0 + gap / 2.0
    while x + w / 2.0 <= (x1 - gap / 2.0 - eps):
        z = z0 + d / 2.0 + gap / 2.0
        while z + d / 2.0 <= (z1 - gap / 2.0 - eps):
            poses.append((x, y, z))
            if max_items is not None and len(poses) >= max_items:
                print(f"[Packer] capped at max_items={max_items} (placed={len(poses)})")
                return poses
            z += d + gap
        x += w + gap

    # Log de diagnóstico
    print(f"[Packer] level y={y:.3f} placed={len(poses)} "
          f"(w={w:.3f},d={d:.3f},gap={gap:.3f}) "
          f"within x[{x0:.3f},{x1:.3f}] z[{z0:.3f},{z1:.3f}]")
    return poses
