from .base_object import BaseObject
import numpy as np
import glm

class Wall(BaseObject):
    def __init__(self, app, position, size, color=(0.8, 0.8, 0.8)):
        self.position = position
        self.size = size
        self.color = color
        super().__init__(app)
        
    def get_model_matrix(self):
        m_model = glm.translate(glm.mat4(), self.position)
        m_model = glm.scale(m_model, self.size)
        return m_model
        
    def get_vertex_data(self):
        # Create a wall (vertical plane)
        vertices = [
            # Front face
            (-0.5, -0.5, 0.5), (0.5, -0.5, 0.5), (0.5, 0.5, 0.5),
            (-0.5, -0.5, 0.5), (0.5, 0.5, 0.5), (-0.5, 0.5, 0.5),
        ]
        return np.array(vertices, dtype='f4')
    
    def render(self):
        self.shader_program['color'].value = self.color
        super().render()