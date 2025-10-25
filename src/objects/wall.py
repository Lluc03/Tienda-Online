from .base_object import BaseObject
import numpy as np
import glm

class Wall(BaseObject):
    def __init__(self, app, position, size, color=(0.8, 0.8, 0.8), texture_path=None, uv_scale=(2.0, 1.0)):
        self.position = position
        self.size = size
        self.color = color
        super().__init__(app, texture_path=texture_path, uv_scale=uv_scale)

    def get_model_matrix(self):
        m_model = glm.translate(glm.mat4(), self.position)
        m_model = glm.scale(m_model, self.size)
        return m_model

    def get_vertex_data(self):
        # Plano vertical centrado en el origen
        s, t = self.uv_scale
        vertices = [
            (-0.5, -0.5, 0.5, 0.0, 0.0),
            (0.5, -0.5, 0.5, s, 0.0),
            (0.5, 0.5, 0.5, s, t),
            (-0.5, -0.5, 0.5, 0.0, 0.0),
            (0.5, 0.5, 0.5, s, t),
            (-0.5, 0.5, 0.5, 0.0, t),
        ]
        return np.array(vertices, dtype='f4').tobytes()

    def render(self):
        if not self.use_texture and 'color' in self.shader_program:
            self.shader_program['color'].value = self.color
        super().render()
