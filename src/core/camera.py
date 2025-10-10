import glm
import math

class Camera:
    def __init__(self, app):
        self.app = app
        self.aspect_ratio = app.WIN_SIZE[0] / app.WIN_SIZE[1]
        
        # Position and orientation
        self.position = glm.vec3(0, 1, 5)
        self.up = glm.vec3(0, 1, 0)
        self.right = glm.vec3(1, 0, 0)
        self.forward = glm.vec3(0, 0, -1)
        
        # Rotation
        self.yaw = -90.0   # Horizontal angle (left/right)
        self.pitch = 0.0   # Vertical angle (up/down)
        
        # Configuration
        self.target = glm.vec3(0, 1, 0)
        self.fov = 60
        self.perspective = True
        
        # Speeds - Adjusted for dragging
        self.move_speed = 0.05
        self.mouse_sensitivity = 0.08  # Slightly more sensitive for dragging
        
        # Mouse control
        self.first_mouse = True
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        
        # Matrices
        self.m_view = self.get_view_matrix()
        self.m_proj = self.get_projection_matrix()
        
        self.update_camera_vectors()

    def get_view_matrix(self):
        return glm.lookAt(self.position, self.position + self.forward, self.up)
    
    def get_projection_matrix(self):
        if self.perspective:
            return glm.perspective(glm.radians(self.fov), self.aspect_ratio, 0.1, 100)
        else:
            return glm.ortho(-2, 2, -2, 2, 0.1, 100)
    
    def update_camera_vectors(self):
        # Calculate new forward, right and up vectors based on yaw and pitch
        front = glm.vec3()
        front.x = math.cos(glm.radians(self.yaw)) * math.cos(glm.radians(self.pitch))
        front.y = math.sin(glm.radians(self.pitch))
        front.z = math.sin(glm.radians(self.yaw)) * math.cos(glm.radians(self.pitch))
        
        self.forward = glm.normalize(front)
        self.right = glm.normalize(glm.cross(self.forward, glm.vec3(0, 1, 0)))
        self.up = glm.normalize(glm.cross(self.right, self.forward))

    def process_mouse_movement(self, x_offset, y_offset, constrain_pitch=True):
        x_offset *= self.mouse_sensitivity
        y_offset *= self.mouse_sensitivity
        
        self.yaw += x_offset
        self.pitch += y_offset
        
        # Limit pitch to prevent camera flipping
        if constrain_pitch:
            if self.pitch > 89.0:
                self.pitch = 89.0
            if self.pitch < -89.0:
                self.pitch = -89.0
        
        self.update_camera_vectors()

    # Keyboard movement
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

    def update_view_matrix(self):
        self.m_view = self.get_view_matrix()