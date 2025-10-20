import glm
from src.objects.floor import Floor
from src.objects.wall import Wall

class SceneManager:
    def __init__(self, app):
        self.app = app
        self.objects = []
        self.current_scene = "main"  # ✅ Estado de la escena actual
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
    
    def set_scene(self, scene_name):
        """
        Cambia la escena actual
        
        Args:
            scene_name (str): Nombre de la escena ("main", "products", "cart", "config")
        """
        print(f"✓ Cambiando escena a: {scene_name}")
        self.current_scene = scene_name
        
        if scene_name == "main":
            # Restaurar escena principal
            pass
        elif scene_name == "products":
            # Configurar vista de productos
            pass
        elif scene_name == "cart":
            # Configurar vista de carrito
            pass
        elif scene_name == "config":
            # Configurar vista de configuración
            pass
    
    def get_current_scene(self):
        """Retorna la escena actual"""
        return self.current_scene
    
    def render(self):
        """Render all objects in the scene"""
        for obj in self.objects:
            obj.update_matrices()
            obj.render()
    
    def cleanup(self):
        """Clean up all scene objects"""
        for obj in self.objects:
            obj.destroy()