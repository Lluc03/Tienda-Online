from .base_object import BaseObject
import numpy as np
import glm

class Wall(BaseObject):
    """
    🧱 Pared optimizada con opción de renderizar solo una cara.
    
    Parámetros:
    -----------
    app : GraphicsEngine
        Instancia de la aplicación
    position : glm.vec3
        Posición en el mundo 3D
    size : glm.vec3
        Dimensiones (ancho, alto, profundidad)
    color : tuple
        Color RGB (0-1) cuando no hay textura
    texture_path : str, optional
        Ruta a la textura
    uv_scale : tuple
        Escala de coordenadas UV (repetición de textura)
    rotation_deg : tuple
        Rotación en grados (X, Y, Z)
    single_face : str, optional
        "front" = solo cara frontal (+Z local)
        "back" = solo cara trasera (-Z local)
        None = ambas caras (default para compatibilidad)
    """
    
    def __init__(
        self,
        app,
        position,
        size,
        color=(0.8, 0.8, 0.8),
        texture_path=None,
        uv_scale=(2.0, 1.0),
        rotation_deg=(0.0, 0.0, 0.0),
        single_face=None
    ):
        self.position = position
        self.size = size
        self.color = color
        self.rotation_deg = rotation_deg
        self.single_face = single_face  # 👈 Nuevo parámetro
        super().__init__(app, texture_path=texture_path, uv_scale=uv_scale)

    def get_model_matrix(self):
        """
        Construye la matriz de transformación del modelo.
        Orden: Traslación → Rotación (X→Y→Z) → Escala
        """
        m_model = glm.translate(glm.mat4(), self.position)
        
        # Aplicar rotaciones en orden XYZ
        rx, ry, rz = [glm.radians(a) for a in self.rotation_deg]
        m_model = glm.rotate(m_model, rx, glm.vec3(1, 0, 0))
        m_model = glm.rotate(m_model, ry, glm.vec3(0, 1, 0))
        m_model = glm.rotate(m_model, rz, glm.vec3(0, 0, 1))
        
        m_model = glm.scale(m_model, self.size)
        return m_model

    def get_vertex_data(self):
        """
        Genera la geometría de la pared.
        
        Comportamiento según single_face:
        - "front": Solo genera cara frontal (normal +Z)
        - "back": Solo genera cara trasera (normal -Z)
        - None: Genera ambas caras (compatibilidad legacy)
        
        Cada cara tiene 6 vértices (2 triángulos).
        Formato: (x, y, z, u, v) por vértice
        """
        s, t = self.uv_scale
        vertices = []
        
        # ===== CARA FRONTAL (+Z local) =====
        if self.single_face in ["front", None]:
            front = [
                # Triángulo inferior-izquierdo → inferior-derecho → superior-derecho
                (-0.5, -0.5,  0.5,  0.0, 0.0),
                ( 0.5, -0.5,  0.5,  s,   0.0),
                ( 0.5,  0.5,  0.5,  s,   t),
                # Triángulo inferior-izquierdo → superior-derecho → superior-izquierdo
                (-0.5, -0.5,  0.5,  0.0, 0.0),
                ( 0.5,  0.5,  0.5,  s,   t),
                (-0.5,  0.5,  0.5,  0.0, t),
            ]
            vertices.extend(front)
        
        # ===== CARA TRASERA (-Z local) =====
        if self.single_face in ["back", None]:
            # Orden de vértices invertido para que la normal apunte correctamente
            back = [
                # Triángulo 1
                (-0.5, -0.5, -0.5,  0.0, 0.0),
                ( 0.5,  0.5, -0.5,  s,   t),
                ( 0.5, -0.5, -0.5,  s,   0.0),
                # Triángulo 2
                (-0.5, -0.5, -0.5,  0.0, 0.0),
                (-0.5,  0.5, -0.5,  0.0, t),
                ( 0.5,  0.5, -0.5,  s,   t),
            ]
            vertices.extend(back)
        
        return np.array(vertices, dtype='f4').tobytes()

    def render(self):
        """
        Renderiza la pared.
        Aplica el color si no hay textura y llama al render base.
        """
        if not self.use_texture and "color" in self.shader_program:
            self.shader_program["color"].value = self.color
        super().render()