# src/utils/geometry.py
import glm

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

