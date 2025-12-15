import glm
import math

class Camera:
    """Cámara FPS con control por ratón y movimiento dentro del supermercado."""

    # ======================================================================
    # INITIALIZATION
    # ======================================================================

    def __init__(self, app):
        self.app = app
        self.aspect_ratio = app.WIN_SIZE[0] / app.WIN_SIZE[1]

        # --------------------------------------------------------------
        # 🏁 POSICIÓN INICIAL — Diseñada para tu supermercado
        # --------------------------------------------------------------
        # Ubicación: parte frontal-derecha del supermercado
        # Altura: 1.7 m (altura humana)
        self.position = glm.vec3(5.0, 1.7, 12.0)

        # Vectores base
        self.up = glm.vec3(0, 1, 0)
        self.right = glm.vec3(1, 0, 0)
        self.forward = glm.vec3(0, 0, -1)

        # --------------------------------------------------------------
        # 🎯 ORIENTACIÓN — Mirando hacia el interior del supermercado
        # --------------------------------------------------------------
        self.yaw = 270.0
        self.pitch = 0.0

        # Configuración general
        self.target = glm.vec3(0, 1, 0)
        self.fov = 60
        self.perspective = True

        # Velocidades
        self.move_speed = 0.05
        self.mouse_sensitivity = 0.1

        # Control del ratón
        self.first_mouse = True
        self.last_mouse_x = 0
        self.last_mouse_y = 0

        # Actualizamos vectores y matrices iniciales
        self.update_camera_vectors()
        self.m_view = self.get_view_matrix()
        self.m_proj = self.get_projection_matrix()

    # ======================================================================
    # RESET CAMERA
    # ======================================================================

    def reset_camera(self):
        """Resetea la cámara a la posición de entrada del supermercado."""
        self.position = glm.vec3(9.0, 1.7, 6.5)
        self.up = glm.vec3(0, 1, 0)
        self.right = glm.vec3(1, 0, 0)
        self.forward = glm.vec3(0, 0, -1)

        # Mirando hacia dentro del supermercado
        self.yaw = -135.0
        self.pitch = 0.0
        self.fov = 60

        self.update_camera_vectors()
        self.update_view_matrix()

        print("✓ Cámara resetada a la entrada del supermercado")

    # ======================================================================
    # MATRICES
    # ======================================================================

    def get_view_matrix(self):
        return glm.lookAt(self.position, self.position + self.forward, self.up)
    
    def get_projection_matrix(self):
        if self.perspective:
            return glm.perspective(glm.radians(self.fov), self.aspect_ratio, 0.1, 100)
        else:
            return glm.ortho(-2, 2, -2, 2, 0.1, 100)

    # ======================================================================
    # CAMERA VECTOR UPDATE
    # ======================================================================

    def update_camera_vectors(self):
        """Recalcula los vectores forward/right/up basados en yaw y pitch."""

        front = glm.vec3()
        front.x = math.cos(glm.radians(self.yaw)) * math.cos(glm.radians(self.pitch))
        front.y = math.sin(glm.radians(self.pitch))
        front.z = math.sin(glm.radians(self.yaw)) * math.cos(glm.radians(self.pitch))

        self.forward = glm.normalize(front)
        self.right = glm.normalize(glm.cross(self.forward, glm.vec3(0, 1, 0)))
        self.up = glm.normalize(glm.cross(self.right, self.forward))

    # ======================================================================
    # MOUSE INPUT
    # ======================================================================

    # En camera.py, reemplaza el método process_mouse_movement:

    def process_mouse_movement(self, x_offset, y_offset, constrain_pitch=True):
        """Procesa el movimiento del ratón para rotar la cámara."""
        
        x_offset *= -self.mouse_sensitivity
        y_offset *= -self.mouse_sensitivity
        
        self.yaw += x_offset
        self.pitch += y_offset
        
        # ✅ SOLUCIÓN 3: Permitir mirar hacia abajo correctamente
        if constrain_pitch:
            max_pitch = 89.0     # casi mirar al cielo
            min_pitch = -89.0    # permitir mirar hacia abajo (era -20.0)

            if self.pitch > max_pitch:
                self.pitch = max_pitch
            if self.pitch < min_pitch:
                self.pitch = min_pitch

        self.update_camera_vectors()
        self.update_view_matrix()

    # ======================================================================
    # MOVIMIENTO WASD
    # ======================================================================

    def move_forward(self):
        self.position += self.forward * self.move_speed
        self.update_view_matrix()

    def move_backward(self):
        self.position -= self.forward * self.move_speed
        self.update_view_matrix()

    def move_left(self):
        self.position -= self.right * self.move_speed
        self.update_view_matrix()

    def move_right(self):
        self.position += self.right * self.move_speed
        self.update_view_matrix()

    def move_up(self):
        self.position += self.up * self.move_speed
        self.update_view_matrix()

    def move_down(self):
        self.position -= self.up * self.move_speed
        self.update_view_matrix()

    # ======================================================================
    # MATRIX UPDATES
    # ======================================================================

    def update_view_matrix(self):
        self.m_view = self.get_view_matrix()

    def update_projection_matrix(self):
        """Se llama cuando cambia el tamaño de la ventana."""
        self.aspect_ratio = self.app.WIN_SIZE[0] / self.app.WIN_SIZE[1]
        self.m_proj = self.get_projection_matrix()
