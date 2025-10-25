from .base_object import BaseObject
import numpy as np

class Floor(BaseObject):
    def __init__(self, app, texture_path=None, uv_scale=(4.0, 4.0)):
        super().__init__(app, texture_path=texture_path, uv_scale=uv_scale)

    def get_vertex_data(self):
        # Plano XZ de 10x10 (de -5 a 5) en Y=0
        # Pos (x,y,z) + UV (u,v) con tiling por uv_scale
        s, t = self.uv_scale
        s, t = self.uv_scale
        vertices = [
            (-5, 0, -5, 0.0, 0.0),
            (5, 0, -5, s, 0.0),
            (5, 0, 5, s, t),
            (-5, 0, -5, 0.0, 0.0),
            (5, 0, 5, s, t),
            (-5, 0, 5, 0.0, t),
        ]
        return np.array(vertices, dtype='f4').tobytes()

    def render(self):
        if not self.use_texture and 'color' in self.shader_program:
            self.shader_program['color'].value = (0.3, 0.3, 0.3)
        super().render()
