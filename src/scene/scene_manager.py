import glm
from src.objects.floor import Floor
from src.objects.wall import Wall
from src.objects.model_obj import ModelOBJ
from src.placement.shelf_space import ShelfSpace
from src.placement.placer import pack_grid_on_shelf


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
    
    def _register_shelves_from_models(self, models, levels=5, margin_xy=0.02, back_offset=0.02):
        """ Crea objetos ShelfSpace a partir de una lista de ModelOBJ ya colocados. """
        self.shelf_spaces = [ShelfSpace(m, levels=levels, margin_xy=margin_xy, back_offset=back_offset) for m in models]

    def _fill_shelf_with_model(self, shelf_space, obj_path, tex_path, target_longest=0.22, gap=0.04, max_items_per_level=None, y_clearance=0.001):
        """
        Rellena cada balda de shelf_space con copias de un modelo:
        - target_longest: tamaño objetivo del lado mayor del producto (m).
        - gap: separación lateral/frontal.
        - y_clearance: pequeño offset para evitar z-fighting al apoyar.
        """
        # 1) Cargar una "plantilla" del producto (se compartirá geometría por cache)
        proto = ModelOBJ(self.app, obj_path, tex_path, position=(0,0,0), scale=(1,1,1), rotation_deg=(0,0,0))
        proto.auto_scale_by_longest_side(target_longest)

        # Huella (w,d) y alto (h) del AABB ESCALADO
        sx, sy, sz = proto.aabb_local_sizes()     # tamaños en espacio local
        w = sx * proto._scale.x
        h = sy * proto._scale.y
        d = sz * proto._scale.z
        footprint = (w, d)


        spawned = []
        for lvl in shelf_space.get_levels():
            # 2) Calcular las posiciones en esta balda (centros) con el packer
            poses = pack_grid_on_shelf(lvl, footprint, gap=gap, max_items=max_items_per_level)
            # 3) Crear instancias y posicionarlas
            # La y del packer es la "altura de balda"; apoyamos elevando medio alto del producto
            for (x, y, z) in poses:
                item = proto.clone()
                # posición -> ajustar y para apoyar: y_balda + h/2 + clearance
                item.set_position((x, y + h/2.0 + y_clearance, z))
                # si quieres orientar la manzana aleatoriamente (yaw), descomenta:
                # item.set_rotation((0.0, random.uniform(0, 360), 0.0))
                spawned.append(item)
                self.objects.append(item)

        return spawned


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

        # --- Estanterías importadas (laterales) ---
        shelf_model = "assets/models/shelf01.obj"
        shelf_tex   = "assets/textures/shelf01_diffuse.jpg"

        # Crea con escala 1 para autoescalar después
        shelf_left = ModelOBJ(
            self.app, shelf_model, shelf_tex,
            position=(-3.5, 0.0, -3.0),      # lateral izquierdo
            scale=(1.0, 1.0, 1.0),
            rotation_deg=(0.0, 90.0, 0.0)    # mirando al pasillo
        )
        shelf_right = ModelOBJ(
            self.app, shelf_model, shelf_tex,
            position=( 3.5, 0.0, -3.0),      # lateral derecho
            scale=(1.0, 1.0, 1.0),
            rotation_deg=(0.0, -90.0, 0.0)
        )

        # Escala para que su lado mayor sea ~2.4 u. (ajusta 2.0–2.6 a gusto)
        for sh in (shelf_left, shelf_right):
            sh.auto_scale_by_longest_side(2.4)
            # re-coloca (x,z) y apóyala en el suelo
            # (set_position primero; align_to_floor corrige la Y)
            x, z = sh._position.x, sh._position.z
            sh.set_position((x, 0.0, z))
            sh.align_to_floor()

        self.objects += [shelf_left, shelf_right]

        # Crear los espacios de las estanterías
        self._register_shelves_from_models(
            [shelf_left, shelf_right],
            levels=5,
            margin_xy=0.03,
            back_offset=0.03
        )

        # Rellenar con manzanas
        apple_model = "assets/models/apple01.obj"
        apple_tex   = "assets/textures/apple_diffuse.jpg"

        for shelf_space in self.shelf_spaces:
            self._fill_shelf_with_model(
                shelf_space,
                obj_path=apple_model,
                tex_path=apple_tex,
                target_longest=0.22,   # 22 cm (tamaño real de una manzana grande)
                gap=0.04,              # separación lateral/frontal
                max_items_per_level=None
            )
