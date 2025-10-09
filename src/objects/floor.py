from .base_object import BaseObject
import numpy as np

class Floor(BaseObject):
    def __init__(self, app):
        super().__init__(app)
        
    def get_vertex_data(self):
        vertices = [
            (-5, 0, -5), (5, 0, -5), (5, 0, 5),
            (-5, 0, -5), (5, 0, 5), (-5, 0, 5)
        ]
        return np.array(vertices, dtype='f4')
    
    def render(self):
        self.shader_program['color'].value = (0.3, 0.3, 0.3)
        super().render()