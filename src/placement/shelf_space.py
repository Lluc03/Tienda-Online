# src/placement/shelf_space.py
import glm
from src.utils.geometry import aabb_world_from_local

class ShelfSpace:
    """
    Representa el volumen útil de una estantería importada.
    A partir del AABB del modelo en mundo, define N niveles (baldas) con:
      - y_balda (altura)
      - rectángulo útil en XZ (con márgenes)
    """
    def __init__(self, model_obj, levels=5, margin_xy=0.02, back_offset=0.02):
        """
        model_obj: instancia de ModelOBJ ya colocada/rotada/escalada en la escena.
        levels: número de baldas (aprox. 5 en tu estantería polyhaven).
        margin_xy: margen hacia izquierda/derecha y frente para no tocar bordes.
        back_offset: margen extra hacia el fondo (pegado a pared/rieles).
        """
        self.model = model_obj
        # obtener AABB en mundo a partir del local + m_model actual
        local = model_obj.aabb_local()
        world_min, world_max = aabb_world_from_local(local[0], local[1], model_obj.get_model_matrix())
        self.world_min = glm.vec3(*world_min)
        self.world_max = glm.vec3(*world_max)
        self.levels = levels
        self.margin_xy = margin_xy
        self.back_offset = back_offset

        self._build_levels()

    def _build_levels(self):
        h = self.world_max.y - self.world_min.y
        dy = h / max(self.levels, 1)
        self.shelves = []  # lista de dicts: { y, x0,x1,z0,z1 }
        # definimos rectángulo útil con márgenes
        x0 = self.world_min.x + self.margin_xy
        x1 = self.world_max.x - self.margin_xy
        z0 = self.world_min.z + self.margin_xy
        z1 = self.world_max.z - (self.margin_xy + self.back_offset)
        # Las baldas suelen estar abiertas hacia "frente" (menor/ mayor z depende de tu orientación).
        # En tu escena el pasillo mira a -Z; si quieres reservar más margen frontal, ajusta z0 o z1.
        for i in range(self.levels):
            y = self.world_min.y + dy * (i + 0.5)  # altura central aproximada de cada balda
            self.shelves.append(dict(y=y, x0=min(x0, x1), x1=max(x0, x1), z0=min(z0, z1), z1=max(z0, z1)))

    def get_levels(self):
        return self.shelves
