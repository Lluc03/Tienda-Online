import glm
from src.objects.floor import Floor
from src.objects.wall import Wall

class SceneManager:
    def __init__(self, app):
        self.app = app
        self.objects = []
        self.setup_scene()
    
    def setup_scene(self):
        """Setup the basic room scene"""
        # Create floor
        self.floor = Floor(self.app)
        self.objects.append(self.floor)
        
        # Create walls
        self.walls = [
            Wall(self.app, glm.vec3(0, 2.5, -5), glm.vec3(10, 5, 0.1), (0.7, 0.7, 0.9)),
            Wall(self.app, glm.vec3(-5, 2.5, 0), glm.vec3(0.1, 5, 10), (0.9, 0.7, 0.7)),
            Wall(self.app, glm.vec3(5, 2.5, 0), glm.vec3(0.1, 5, 10), (0.7, 0.9, 0.7)),
        ]
        self.objects.extend(self.walls)
    
    def render(self):
        """Render all objects in the scene"""
        for obj in self.objects:
            obj.update_matrices()
            obj.render()
    
    def cleanup(self):
        """Clean up all scene objects"""
        for obj in self.objects:
            obj.destroy()