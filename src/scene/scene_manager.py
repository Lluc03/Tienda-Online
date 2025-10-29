# scene_manager.py
import glm
import math
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
        self._prototype_cache = {}  # (obj_path, tex_path, target_longest)
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

    # --- actualizado: expone y pasa y_bin/board_merge a ShelfSpace ---
    def _register_shelves_from_models(
        self,
        models,
        levels=5,
        margin_xy=0.03,
        back_offset=0.03,
        y_bin=0.005,
        board_merge=0.045,
        per_level_shrink=0.01,
        debug = False
    ):
        """
        Crea ShelfSpace para cada ModelOBJ. Mantiene firma compatible.
        'models' es una lista de objetos ModelOBJ ya posicionados.
        """
        self.shelf_spaces = []
        for idx, m in enumerate(models):
            label = f"shelf{idx}"
            sp = ShelfSpace(
                m,
                levels=levels,
                margin_xy=margin_xy,
                back_offset=back_offset,
                y_bin=y_bin,
                board_merge=board_merge,
                per_level_shrink=per_level_shrink,
                label=label,
                debug=debug,
            )
            self.shelf_spaces.append(sp)

    def _fill_shelf_with_model(
        self,
        shelf_space,
        obj_path,
        tex_path,
        target_longest=0.22,
        gap=0.04,
        max_items_per_level=None,
        y_clearance=0.004,
    ):
        """
        Rellena cada balda con copias de un modelo.
        Usa un 'prototipo' cacheado para no recargar geometría/VAO/textura.
        """
        
        # --- prototipo cacheado ---
        key = (obj_path, tex_path, float(target_longest))
        proto = self._prototype_cache.get(key)
        if proto is None:
            proto = ModelOBJ(
                self.app,
                obj_path,
                tex_path,
                position=(0, 0, 0),
                scale=(1, 1, 1),
                rotation_deg=(0, 0, 0),
            )
            proto.auto_scale_by_longest_side(target_longest)
            self._prototype_cache[key] = proto

        # --- AABB del prototipo ---
        # aabb_local_sizes(): tamaños en espacio local (sin escala)
        sx, sy, sz = proto.aabb_local_sizes()
        # Pasar a mundo aplicando la escala actual del prototipo
        w = sx * proto._scale.x   # ancho X
        h = sy * proto._scale.y   # alto  Y
        d = sz * proto._scale.z   # fondo Z
        footprint = (w, d)

        # Mínimo Y local del modelo (para apoyarlo en la balda tras el escalado)
        min_y_local = proto.min_y_local()

        print(
            f"[Fill] item footprint w={w:.3f} d={d:.3f} h={h:.3f} "
            f"min_y_local={min_y_local:.3f} gap={gap:.3f} y_clearance={y_clearance:.3f}"
        )

        spawned = []

        for i, lvl in enumerate(shelf_space.get_levels()):
            y_balda = lvl["y"]
            y_top   = lvl.get("y_top")

            # --- headroom: comprobar holgura vertical si hay techo detectado ---
            if y_top is not None:
                headroom = y_top - y_balda
                needed   = h + y_clearance + 0.010  # +1 cm de seguridad
                if headroom < needed:
                    print(
                        f"[Fill] skip {shelf_space.label} L{i} y={y_balda:.3f}: "
                        f"headroom={headroom:.3f} < needed={needed:.3f}"
                    )
                    continue

            # --- logs de capacidad teórica (cols/rows) solo informativos ---
            x0, x1 = lvl["x0"], lvl["x1"]
            z0, z1 = lvl["z0"], lvl["z1"]
            usable_w = max(0.0, x1 - x0)
            usable_d = max(0.0, z1 - z0)
            cols = max(0, math.floor((usable_w + gap) / (w + gap)))
            rows = max(0, math.floor((usable_d + gap) / (d + gap)))
            print(
                f"[Fill] use {shelf_space.label} L{i} y={y_balda:.3f} "
                f"rect=({x0:.3f},{x1:.3f})x({z0:.3f},{z1:.3f}) "
                f"usable=({usable_w:.3f},{usable_d:.3f}) -> cols={cols} rows={rows}"
            )

            # --- packing real ---
            poses = pack_grid_on_shelf(
                level_rect=lvl,
                footprint=footprint,
                gap=gap,
                max_items=max_items_per_level,
            )

            for (x, y_level, z) in poses:
                item = proto.clone()
                # Apoyar el modelo: trasladar por el min Y local escalado + holgura
                y_item = y_level - (min_y_local * item._scale.y) + y_clearance
                item.set_position((x, y_item, z))
                spawned.append(item)
                self.objects.append(item)

        return spawned

    def setup_scene(self):
        # Rutas (ajústalas a tu repo)
        floor_tex = "assets/textures/floor_diffuse.png"
        wall_tex  = "assets/textures/wall_diffuse.png"

        # Suelo con textura (tiling 4x4)
        self.floor = Floor(self.app, texture_path=floor_tex, uv_scale=(4.0, 4.0))
        self.objects.append(self.floor)

        # Paredes con textura (tiling horizontal 2x, vertical 1x)
        self.walls = [
            Wall(
                self.app,
                glm.vec3(0, 2.5, -5),
                glm.vec3(10, 5, 0.1),
                (0.7, 0.7, 0.9),
                texture_path=wall_tex,
                uv_scale=(2.0, 1.0),
            ),
            Wall(
                self.app,
                glm.vec3(-5, 2.5, 0),
                glm.vec3(0.1, 5, 10),
                (0.9, 0.7, 0.7),
                texture_path=wall_tex,
                uv_scale=(2.0, 1.0),
            ),
            Wall(
                self.app,
                glm.vec3(5, 2.5, 0),
                glm.vec3(0.1, 5, 10),
                (0.7, 0.9, 0.7),
                texture_path=wall_tex,
                uv_scale=(2.0, 1.0),
            ),
        ]
        self.objects.extend(self.walls)

        # --- Estanterías importadas (laterales) ---
        shelf_model = "assets/models/shelf01.obj"
        shelf_tex   = "assets/textures/shelf01_diffuse.jpg"

        shelf_left = ModelOBJ(
            self.app, shelf_model, shelf_tex,
            position=(-3.5, 0.0, -3.0),
            scale=(1.0, 1.0, 1.0),
            rotation_deg=(0.0, 90.0, 0.0)   # mirando al pasillo
        )
        shelf_right = ModelOBJ(
            self.app, shelf_model, shelf_tex,
            position=( 3.5, 0.0, -3.0),
            scale=(1.0, 1.0, 1.0),
            rotation_deg=(0.0, -90.0, 0.0)  # mirando al pasillo
        )

        # Escalado y apoyo al suelo
        for sh in (shelf_left, shelf_right):
            sh.auto_scale_by_longest_side(2.4)
            x, z = sh._position.x, sh._position.z
            sh.set_position((x, 0.0, z))
            sh.align_to_floor()

        self.objects += [shelf_left, shelf_right]

        # Crear espacios (con parámetros robustos para detectar baldas)
        self._register_shelves_from_models(
            [shelf_left, shelf_right],
            levels=5,
            margin_xy=0.03,
            back_offset=0.03,
            y_bin=0.005,
            board_merge=0.045,
            per_level_shrink=0.01,
            debug=True
        )

        # Rellenar con manzanas
        apple_model = "assets/models/apple01.obj"
        apple_tex   = "assets/textures/apple_diffuse.jpg"

        for shelf_space in self.shelf_spaces:
            self._fill_shelf_with_model(
                shelf_space,
                obj_path=apple_model,
                tex_path=apple_tex,
                target_longest=0.22,  # ~22 cm
                gap=0.04,
                max_items_per_level=None,
                y_clearance=0.004,    # explícito
            )
