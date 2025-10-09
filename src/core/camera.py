import glm

class Camera:
    def __init__(self, app):
        self.app = app
        self.aspect_ratio = app.WIN_SIZE[0] / app.WIN_SIZE[1]
        self.position = glm.vec3(0, 1, 5)
        self.up = glm.vec3(0, 1, 0)
        self.right = glm.vec3(1, 0, 0)
        self.forward = glm.vec3(0, 0, -1)
        
        self.target = glm.vec3(0, 1, 0)
        self.fov = 60
        self.perspective = True
        self.move_speed = 0.05
        
        self.m_view = self.get_view_matrix()
        self.m_proj = self.get_projection_matrix()

    def get_view_matrix(self):
        return glm.lookAt(self.position, self.position + self.forward, self.up)
    
    def get_projection_matrix(self):
        if self.perspective:
            return glm.perspective(glm.radians(self.fov), self.aspect_ratio, 0.1, 100)
        else:
            return glm.ortho(-2, 2, -2, 2, 0.1, 100)
    
    def move_forward(self):
        self.position += self.forward * self.move_speed
        self.update_view_matrix()

    def move_backward(self):
        self.position -= self.forward * self.move_speed
        self.update_view_matrix()

    def update_view_matrix(self):
        self.m_view = self.get_view_matrix()