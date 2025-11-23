import glm
import math

def aabb_world_from_local(local_min, local_max, model_matrix):
    """
    Transforma un AABB local por una matriz modelo arbitraria (con rotación/escala/traslación)
    generando un AABB en mundo. Se hace transformando los 8 vértices y volviendo a aabb.
    """
    mins = glm.vec3(*local_min)
    maxs = glm.vec3(*local_max)
    corners = [
        glm.vec3(mins.x, mins.y, mins.z),
        glm.vec3(mins.x, mins.y, maxs.z),
        glm.vec3(mins.x, maxs.y, mins.z),
        glm.vec3(mins.x, maxs.y, maxs.z),
        glm.vec3(maxs.x, mins.y, mins.z),
        glm.vec3(maxs.x, mins.y, maxs.z),
        glm.vec3(maxs.x, maxs.y, mins.z),
        glm.vec3(maxs.x, maxs.y, maxs.z),
    ]
    world = [glm.vec3(model_matrix * glm.vec4(c, 1.0)) for c in corners]
    min_w = glm.vec3(min(p.x for p in world), min(p.y for p in world), min(p.z for p in world))
    max_w = glm.vec3(max(p.x for p in world), max(p.y for p in world), max(p.z for p in world))
    return (min_w.x, min_w.y, min_w.z), (max_w.x, max_w.y, max_w.z)

def aabb_overlap_3d(a_min, a_max, b_min, b_max, eps=1e-6):
    """Comprueba solape de dos AABB 3D.
    Cada parámetro es una tupla (x, y, z) con min y max en cada eje.
    """
    ax0, ay0, az0 = a_min
    ax1, ay1, az1 = a_max
    bx0, by0, bz0 = b_min
    bx1, by1, bz1 = b_max

    no_overlap = (
        ax1 <= bx0 + eps or bx1 <= ax0 + eps or
        ay1 <= by0 + eps or by1 <= ay0 + eps or
        az1 <= bz0 + eps or bz1 <= az0 + eps
    )
    return not no_overlap

def ray_aabb_intersection(ray_origin, ray_dir, a_min, a_max, eps=1e-6):
    """
    Intersección rayo-AABB.
    ray_origin, ray_dir: glm.vec3 (ray_dir debe estar normalizado).
    a_min, a_max: tuplas (x,y,z) del AABB en mundo.
    Devuelve distancia t >= 0 si hay intersección, o None si no hay.
    """

    tmin = -math.inf
    tmax = math.inf

    for i in range(3):
        ro = ray_origin[i]
        rd = ray_dir[i]
        amin = a_min[i]
        amax = a_max[i]

        if abs(rd) < eps:
            # Rayo paralelo al eje: si está fuera del slab, no hay intersección
            if ro < amin or ro > amax:
                return None
        else:
            t1 = (amin - ro) / rd
            t2 = (amax - ro) / rd
            if t1 > t2:
                t1, t2 = t2, t1
            tmin = max(tmin, t1)
            tmax = min(tmax, t2)
            if tmax < tmin:
                return None

    if tmax < 0:
        return None

    # Si tmin < 0, el origen está dentro de la caja → usa tmax
    return tmin if tmin >= 0 else tmax