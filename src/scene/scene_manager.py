import glm
from src.objects.floor import Floor
from src.objects.wall import Wall

class SceneManager:
    def __init__(self, app):
        self.app = app
        self.objects = []
        self.current_scene = "main"
        self.setup_scene()
    
    
    def render(self):
        for obj in self.objects:
            obj.update_matrices()
            obj.render()


    def cleanup(self):
        # Liberar recursos de todos los objetos
        for obj in self.objects:
            try:
                obj.destroy()
            except Exception as e:
                print(f"Error liberando objeto {obj}: {e}")

    def setup_scene(self):
        # Rutas (ajústalas a tu repo)
        floor_tex = "assets/textures/floor_diffuse.png"  # o .jpg
        wall_tex  = "assets/textures/wall_diffuse.png"

        # Suelo con textura (tiling 4x4)
        self.floor = Floor(self.app, texture_path=floor_tex, uv_scale=(4.0, 4.0))
        self.objects.append(self.floor)

        # Paredes con textura (tiling horizontal 2x, vertical 1x)
        self.walls = [
            Wall(self.app, glm.vec3(0, 2.5, -5), glm.vec3(10, 5, 0.1), (0.7, 0.7, 0.9),
                 texture_path=wall_tex, uv_scale=(2.0, 1.0)),
            Wall(self.app, glm.vec3(-5, 2.5, 0), glm.vec3(0.1, 5, 10), (0.9, 0.7, 0.7),
                 texture_path=wall_tex, uv_scale=(2.0, 1.0)),
            Wall(self.app, glm.vec3(5, 2.5, 0), glm.vec3(0.1, 5, 10), (0.7, 0.9, 0.7),
                 texture_path=wall_tex, uv_scale=(2.0, 1.0)),
        ]
        self.objects.extend(self.walls)
