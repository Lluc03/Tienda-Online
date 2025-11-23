from .base_object import BaseObject
import numpy as np
import glm

class Box(BaseObject):
    """
    Caja/Cubo 3D completo con 6 caras visibles desde el interior.
    Útil para crear habitaciones, supermercados, etc.
    """
    def __init__(
        self,
        app,
        position=(0.0, 0.0, 0.0),
        size=(10.0, 5.0, 10.0),  # ancho, alto, profundidad
        color=(0.9, 0.9, 0.9),
        texture_path=None,
        uv_scale=(1.0, 1.0),
        rotation_deg=(0.0, 0.0, 0.0)
    ):
        """
        Args:
            position: Centro del cubo (x, y, z)
            size: Dimensiones (ancho_x, alto_y, profundidad_z)
            color: Color RGB si no hay textura
            texture_path: Ruta a textura opcional
            uv_scale: Escala de coordenadas UV
            rotation_deg: Rotación en grados (pitch, yaw, roll)
        """
        self.position = glm.vec3(*position)
        self.size = glm.vec3(*size)
        self.color = color
        self.rotation_deg = rotation_deg
        super().__init__(app, texture_path=texture_path, uv_scale=uv_scale)

    def get_model_matrix(self):
        m_model = glm.translate(glm.mat4(), self.position)
        
        # Aplicar rotaciones (convertir grados a radianes)
        rx, ry, rz = [glm.radians(a) for a in self.rotation_deg]
        m_model = glm.rotate(m_model, rx, glm.vec3(1, 0, 0))
        m_model = glm.rotate(m_model, ry, glm.vec3(0, 1, 0))
        m_model = glm.rotate(m_model, rz, glm.vec3(0, 0, 1))
        
        m_model = glm.scale(m_model, self.size)
        return m_model

    def get_vertex_data(self):
        """
        Genera las 6 caras del cubo con normales hacia el INTERIOR.
        Esto permite ver las paredes desde dentro del supermercado.
        """
        s, t = self.uv_scale
        
        # Cada cara tiene 6 vértices (2 triángulos)
        # Formato: (x, y, z, u, v)
        
        # ===== SUELO (Y-) - mirando hacia arriba desde abajo =====
        floor = [
            (-0.5, -0.5, -0.5,  0.0, 0.0),
            ( 0.5, -0.5,  0.5,  s,   t  ),
            ( 0.5, -0.5, -0.5,  s,   0.0),
            (-0.5, -0.5, -0.5,  0.0, 0.0),
            (-0.5, -0.5,  0.5,  0.0, t  ),
            ( 0.5, -0.5,  0.5,  s,   t  ),
        ]
        
        # ===== TECHO (Y+) - mirando hacia abajo desde arriba =====
        ceiling = [
            (-0.5,  0.5, -0.5,  0.0, 0.0),
            ( 0.5,  0.5, -0.5,  s,   0.0),
            ( 0.5,  0.5,  0.5,  s,   t  ),
            (-0.5,  0.5, -0.5,  0.0, 0.0),
            ( 0.5,  0.5,  0.5,  s,   t  ),
            (-0.5,  0.5,  0.5,  0.0, t  ),
        ]
        
        # ===== PARED FRONTAL (Z+) - mirando hacia -Z =====
        front = [
            (-0.5, -0.5,  0.5,  0.0, 0.0),
            ( 0.5,  0.5,  0.5,  s,   t  ),
            ( 0.5, -0.5,  0.5,  s,   0.0),
            (-0.5, -0.5,  0.5,  0.0, 0.0),
            (-0.5,  0.5,  0.5,  0.0, t  ),
            ( 0.5,  0.5,  0.5,  s,   t  ),
        ]
        
        # ===== PARED TRASERA (Z-) - mirando hacia +Z =====
        back = [
            (-0.5, -0.5, -0.5,  0.0, 0.0),
            ( 0.5, -0.5, -0.5,  s,   0.0),
            ( 0.5,  0.5, -0.5,  s,   t  ),
            (-0.5, -0.5, -0.5,  0.0, 0.0),
            ( 0.5,  0.5, -0.5,  s,   t  ),
            (-0.5,  0.5, -0.5,  0.0, t  ),
        ]
        
        # ===== PARED IZQUIERDA (X-) - mirando hacia +X =====
        left = [
            (-0.5, -0.5, -0.5,  0.0, 0.0),
            (-0.5,  0.5,  0.5,  s,   t  ),
            (-0.5, -0.5,  0.5,  s,   0.0),
            (-0.5, -0.5, -0.5,  0.0, 0.0),
            (-0.5,  0.5, -0.5,  0.0, t  ),
            (-0.5,  0.5,  0.5,  s,   t  ),
        ]
        
        # ===== PARED DERECHA (X+) - mirando hacia -X =====
        right = [
            ( 0.5, -0.5, -0.5,  0.0, 0.0),
            ( 0.5, -0.5,  0.5,  s,   0.0),
            ( 0.5,  0.5,  0.5,  s,   t  ),
            ( 0.5, -0.5, -0.5,  0.0, 0.0),
            ( 0.5,  0.5,  0.5,  s,   t  ),
            ( 0.5,  0.5, -0.5,  0.0, t  ),
        ]
        
        # Combinar todas las caras
        vertices = floor + ceiling + front + back + left + right
        return np.array(vertices, dtype='f4').tobytes()

    def render(self):
        """Renderiza el cubo con el color especificado si no hay textura"""
        if not self.use_texture and "color" in self.shader_program:
            self.shader_program["color"].value = self.color
        super().render()