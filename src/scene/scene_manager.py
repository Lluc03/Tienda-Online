import glm
import math
from src.objects.Model3D import Model3D
from src.objects.model_obj import ModelOBJ
from src.objects.floor import Floor
from src.objects.wall import Wall
from src.objects.InstancedModel3D import InstancedModel3D
from src.objects.Model3DMultiMaterial import Model3DMultiMaterial
from src.objects.coordenates.shelves_positions import SHELVES
from src.objects.coordenates.water_positions import WATER_PACKS
from src.objects.coordenates.chips_positions import CHIPS
from src.objects.coordenates.milk_positions import MILK
from src.objects.coordenates.apple_positions import APPLE
from src.objects.coordenates.cereals_positions import CEREALS
from src.objects.coordenates.wine_positions import WINE
from src.objects.coordenates.cocacola_positions import COCACOLA
from src.objects.coordenates.cava_positions import CAVA
from src.objects.coordenates.whiskey_positions import WHISKEY
from src.objects.coordenates.paper_positions import PAPER
from src.objects.coordenates.shampoo_positions import SHAMPOO
from src.objects.coordenates.sponge_positions import SPONGE
from src.objects.coordenates.candle_positions import CANDLE
from src.objects.coordenates.jarron_positions import JARRON
from src.objects.coordenates.mug_positions import MUG
from src.objects.coordenates.orange_positions import ORANGE
from src.objects.coordenates.kinder_positions import KINDER
from src.objects.coordenates.tuna_positions import TUNA

# ===== GEOMETRÍA IMPORTADA =====
from src.utils.geometry import (
    aabb_world_from_local,
    aabb_overlap_3d,
    ray_aabb_intersection
)


class SceneManager:
    """
    🏗️ Gestor de escenas con sistema de habitación tipo cubo perfecto.
    """

    def __init__(self, app):
        self.app = app
        self.objects = []
        self.current_scene = "main"

        # Para colisiones y raycast (añadido)
        self.static_colliders = []     # lista de (min, max)
        self.product_items = []        # objetos clicables

        # Configuración de la sala
        self.room_config = {
            "width": 20.0,
            "height": 5.0,
            "depth": 15.0,
            "wall_thickness": 0.3,
            "door_width": 3.0,
            "door_height": 2.8
        }

        self.scene_objects = {
            "main": [],
            "products": [],
            "cart": [],
            "config": []
        }

        self.shelves = []

        # ===== Construcción escena =====
        self._create_imported_scene()
        self.setup_main_room()
        self.setup_cash_registers()
        self._create_shelves()
        self._create_water_packs()
        self._create_chips()
        self._create_milk()
        self._create_apples()
        self._create_orange()
        self._create_kinder()
        self._create_cereals()
        self._create_wine()
        self._create_cocacola()
        self._create_cava()
        self._create_whiskey()
        self._create_paper()
        self._create_shampoo()
        self._create_sponge()
        self._create_candle()
        self._create_jarron()
        self._create_mug()
        self._create_tuna()
        self._create_avatar()

        # Regeneramos colliders
        self.rebuild_static_colliders()

        print(f"\n📋 RESUMEN DE ESCENA:")
        print(f"   Total objetos: {len(self.objects)}")
        print(f"   Objetos en 'main': {len(self.scene_objects['main'])}")
        for i, obj in enumerate(self.objects):
            obj_type = type(obj).__name__
            pos = getattr(obj, 'position', 'N/A')
            print(f"   [{i}] {obj_type} en {pos}")

    # ======================================================================
    #                   📦 FUNCIONES IMPORTADAS DEL OTRO SCENEMANAGER
    # ======================================================================

    def rebuild_static_colliders(self):
        self.static_colliders = []

        avatar = getattr(self, "avatar", None)

        for obj in self.objects:

            if obj is avatar:
                continue

            # ⛔ NO colisionan
            if getattr(obj, "is_walkable", False):
                continue

            # ⛔ NO colisionan (productos)
            if isinstance(obj, InstancedModel3D):
                continue

            if not hasattr(obj, "get_model_matrix"):
                continue

            if not hasattr(obj, "aabb_local") or not callable(obj.aabb_local):
                continue

            local_min, local_max = obj.aabb_local()

            wmin, wmax = aabb_world_from_local(
                local_min, local_max,
                obj.get_model_matrix()
            )

            self.static_colliders.append(
                (glm.vec3(*wmin), glm.vec3(*wmax), obj)
            )

        print(f"✓ Colliders estáticos: {len(self.static_colliders)}")


    def get_entity_aabb_world(self, entity):
        """Devuelve AABB global del entity como glm.vec3, compatible con try_move()."""

        fn = getattr(entity, "aabb_local", None)
        if not callable(fn):
            return None

        local = fn()
        if not local:
            return None

        local_min, local_max = local

        wmin_t, wmax_t = aabb_world_from_local(
            local_min, local_max,
            entity.get_model_matrix()
        )

        return glm.vec3(*wmin_t), glm.vec3(*wmax_t)


    def try_move(self, entity, delta, keep_on_ground=True):
        """Intenta mover y detecta colisiones AABB."""
        if delta is None:
            return True

        if isinstance(delta, tuple):
            delta = glm.vec3(*delta)

        if glm.length(delta) == 0:
            return True

        if not hasattr(entity, "set_position") or not hasattr(entity, "position"):
            return False

        old_pos = glm.vec3(entity.position)
        new_pos = old_pos + delta

        if keep_on_ground and new_pos.y < 0:
            new_pos.y = 0

        entity.position = new_pos

        aabb = self.get_entity_aabb_world(entity)
        if aabb is None:
            return True

        a_min, a_max = aabb

        for b_min, b_max, obj in self.static_colliders:

            if aabb_overlap_3d(
                (a_min.x, a_min.y, a_min.z),
                (a_max.x, a_max.y, a_max.z),
                (b_min.x, b_min.y, b_min.z),
                (b_max.x, b_max.y, b_max.z)
            ):
                obj_name = getattr(obj, "name", type(obj).__name__)
                obj_pos = getattr(obj, "position", None)

                print(
                    f"🚫 COLISIÓN con {obj_name} "
                    f"| pos={obj_pos} "
                    f"| avatar_pos={new_pos}"
                )

                entity.position = old_pos
                return False


        return True

    def raycast_pick_product(self, ray_origin, ray_dir):
        """Raycast contra productos GLTF con detección por instancia."""
        best = None
        best_instance_id = -1
        best_t = None
        best_instance_data = None

        for item in self.product_items:

            from src.objects.InstancedModel3D import InstancedModel3D

            # --- Si és un model amb instàncies ---
            if isinstance(item, InstancedModel3D):

                local_aabb = item.aabb_local()
                if local_aabb is None:
                    continue

                local_min, local_max = local_aabb

                for inst_id, inst_data in enumerate(item.instances):

                    pos = inst_data.get("pos", (0, 0, 0))
                    rot = inst_data.get("rot", (0, 0, 0))
                    scale = inst_data.get("scale", (1, 1, 1))

                    # --- Normalitzar pos/rot/scale sempre a tuples de 3 ---
                    def ensure_vec3(v, default):
                        if isinstance(v, (int, float)):
                            return (v, v, v)
                        if hasattr(v, "__iter__") and len(v) == 3:
                            return tuple(v)
                        return default

                    pos = ensure_vec3(pos, (0, 0, 0))
                    rot = ensure_vec3(rot, (0, 0, 0))
                    scale = ensure_vec3(scale, (1, 1, 1))

                    # Matriu de transformació
                    m = glm.mat4(1.0)
                    m = glm.translate(m, glm.vec3(*pos))
                    m = glm.rotate(m, glm.radians(rot[0]), glm.vec3(1,0,0))
                    m = glm.rotate(m, glm.radians(rot[1]), glm.vec3(0,1,0))
                    m = glm.rotate(m, glm.radians(rot[2]), glm.vec3(0,0,1))
                    m = glm.scale(m, glm.vec3(*scale))

                    from src.utils.geometry import aabb_world_from_local, ray_aabb_intersection
                    wmin, wmax = aabb_world_from_local(local_min, local_max, m)

                    t = ray_aabb_intersection(ray_origin, ray_dir,
                                            glm.vec3(*wmin), glm.vec3(*wmax))

                    if t is None or t < 0:
                        continue

                    # ⭐ NUEVO: Verificar si está visible (no bloqueado por estanterías)
                    product_pos = glm.vec3(*pos)
                    if self.is_product_occluded_by_shelf(ray_origin, product_pos):
                        continue

                    if best_t is None or t < best_t:
                        best_t = t
                        best = item
                        best_instance_id = inst_id
                        best_instance_data = inst_data

            # --- Si l'objecte NO és instàncies ---
            else:
                aabb = self.get_entity_aabb_world(item)
                if aabb is None:
                    continue

                a_min, a_max = aabb
                from src.utils.geometry import ray_aabb_intersection
                t = ray_aabb_intersection(ray_origin, ray_dir, a_min, a_max)

                if t is None or t < 0:
                    continue

                # ⭐ NUEVO: Verificar visibilidad
                product_center = (a_min + a_max) * 0.5
                if self.is_product_occluded_by_shelf(ray_origin, product_center):
                    continue

                if best_t is None or t < best_t:
                    best_t = t
                    best = item
                    best_instance_id = -1
                    best_instance_data = None

        # === TEST DE OCLUSIÓN POR PAREDES ===
        if best is not None:
            if self.is_occluded_by_walls(ray_origin, ray_dir, best_t):
                return None, -1, None, None

        # RETORNAR 4 VALORS
        return best, best_instance_id, best_t, best_instance_data


    def is_product_occluded_by_shelf(self, ray_origin, product_pos):
        """
        Verifica si una estantería bloquea la línea de visión al producto.
        Retorna True si el producto está oculto detrás de una estantería.
        """
        ray_dir = glm.normalize(product_pos - ray_origin)
        distance_to_product = glm.length(product_pos - ray_origin)
        
        for shelf in self.shelves:
            if not hasattr(shelf, "aabb_local") or not callable(shelf.aabb_local):
                continue
                
            local = shelf.aabb_local()
            if not local:
                continue
                
            local_min, local_max = local
            
            try:
                wmin, wmax = aabb_world_from_local(local_min, local_max, shelf.get_model_matrix())
            except:
                continue
            
            from src.utils.geometry import ray_aabb_intersection
            t = ray_aabb_intersection(
                ray_origin,
                ray_dir,
                glm.vec3(*wmin),
                glm.vec3(*wmax)
            )
            
            if t is None or t < 0:
                continue
            
            # Si la estantería está entre la cámara y el producto
            # Usar margen de 0.3 para permitir productos EN la estantería
            if 0.5 < t < distance_to_product - 0.1:
                return True
        
        return False


    def is_occluded_by_walls(self, ray_origin, ray_dir, hit_point_dist):
        """
        Verifica si alguna PARED bloquea la línea de visión.
        Solo comprueba paredes y objetos sólidos, NO estanterías.
        """
        for obj in self.objects:

            # Ignorar avatar
            if obj is getattr(self, "avatar", None):
                continue

            # ⭐ Ignorar estanterías (se comprueban en is_product_occluded_by_shelf)
            if obj in self.shelves:
                continue
            
            # ⭐ Ignorar productos (solo queremos paredes/objetos sólidos)
            if obj in self.product_items:
                continue

            # Objectes sense AABB local → ignorar
            if not hasattr(obj, "aabb_local") or not callable(obj.aabb_local):
                continue

            local = obj.aabb_local()
            if not local:
                continue

            local_min, local_max = local

            # Obtenir AABB en món
            try:
                wmin, wmax = aabb_world_from_local(local_min, local_max, obj.get_model_matrix())
            except:
                continue

            # Test ray–AABB
            from src.utils.geometry import ray_aabb_intersection
            t = ray_aabb_intersection(
                ray_origin,
                ray_dir,
                glm.vec3(*wmin),
                glm.vec3(*wmax)
            )

            if t is None or t < 0:
                continue

            # Si el objeto (pared) está ENTRE cámara y producto → bloqueado
            if 0 < t < hit_point_dist - 0.001:
                return True

        return False
    
    
    def is_occluded(self, ray_origin, ray_dir, hit_point_dist, ignore_obj=None):
        """
        Retorna True si ALGUNA cosa tapa la línia de visió.
        Només compten objectes del món (parets, prestatgeries) que
        tinguin AABB vàlid.
        """
        for obj in self.objects:

            # Ignorar el producte que hem col·lisionat
            if obj is ignore_obj:
                continue

            # Ignorar l’avatar
            if obj is getattr(self, "avatar", None):
                continue

            # Objectes sense AABB local → ignorar
            if not hasattr(obj, "aabb_local") or not callable(obj.aabb_local):
                continue

            local = obj.aabb_local()
            if not local:
                continue

            local_min, local_max = local

            # Obtenir AABB en món
            try:
                wmin, wmax = aabb_world_from_local(local_min, local_max, obj.get_model_matrix())
            except:
                continue

            # Test ray–AABB
            t = ray_aabb_intersection(
                ray_origin,
                ray_dir,
                glm.vec3(*wmin),
                glm.vec3(*wmax)
            )

            if t is None or t < 0:
                continue

            # Si l'objecte està ENTRE càmera i producte → està ocultat
            if 0 < t < hit_point_dist - 0.001:
                return True

        return False




    # ======================================================================
    #                       ⬇️ CÓDIGO ORIGINAL COMPLETO
    # ======================================================================
    def _create_imported_scene(self):
        scene = Model3D(
            self.app,
            model_path="assets/models/escena1.glb",
            position=glm.vec3(1.0, -0.1, 0.0),
            scale=glm.vec3(0.75),
            rotation=(0.0, 90.0, 0.0)
        )

        scene.is_walkable = True      # ⛔ NO colisiona
        scene.name = "StoreStructure"

        self._add_object(scene)


    def setup_main_room(self):
        print("🏗️ Construyendo sala del supermercado...")

        cfg = self.room_config
        w = cfg["width"]
        h = cfg["height"]
        d = cfg["depth"]
        t = cfg["wall_thickness"]

        floor_tex = "assets/textures/floor_prove1.jpg"
        wall_tex = "assets/textures/wall_white.jpg"


        # Suelo central
        self._create_floor_at(floor_tex, w, d, x=0, z=0)

        # Suelo derecho
        self._create_floor_at(floor_tex, w*0.75, d, x=-10.33, z=-10.0)

        # Suelo izquierdo
        self._create_floor_at(floor_tex, w, d, x=-6.5, z=0)

        # ===== PAREDES =====
        # self._create_wall(
        #     texture_path=wall_tex,
        #     position=glm.vec3(0, h/2, -d/2 - t/2),
        #     size=glm.vec3(w + 2*t, h, t),
        #     uv_scale=(w/4, h/4),
        #     rotation=(0, 0, 0),
        #     face="front",
        #     name="Pared trasera"
        # )

        # self._create_wall(
        #     texture_path=wall_tex,
        #     position=glm.vec3(-w/2 - t/2 + 1.0, h/2, 0),
        #     size=glm.vec3(d, h, t),
        #     uv_scale=(d/4, h/4),
        #     rotation=(0, 90, 0),
        #     face="back",
        #     name="Pared izquierda"
        # )

        # self._create_wall(
        #     texture_path=wall_tex,
        #     position=glm.vec3(w/2 + t/2, h/2, 0),
        #     size=glm.vec3(d, h, t),
        #     uv_scale=(d/4, h/4),
        #     rotation=(0, -90, 0),
        #     face="front",
        #     name="Pared derecha"
        # )

        #self._create_front_wall_with_door(wall_tex, w, h, d, t, cfg)

        # self._create_wall(
        #     texture_path=wall_tex,
        #     position=glm.vec3(0, h + t/2, 0),
        #     size=glm.vec3(w + 2*t, t, d + 2*t),
        #     uv_scale=(w/4, d/4),
        #     rotation=(90, 0, 0),
        #     face="back",
        #     name="Techo"
        # )

        print(f"   → Sala lista.")

        asphalt = Floor(
            self.app,
            texture_path="assets/textures/asphalt_grey.jpg",
            uv_scale=(100, 100)
        )
        asphalt.get_model_matrix = lambda: glm.scale(glm.mat4(), glm.vec3(200, 1, 200))

        # ===== MARCAR COMO NO COLISIONABLE =====
        asphalt.is_walkable = True  # Flag para identificarlo

        self._add_object(asphalt)

    # -----------------------------------------------------------
    
    def _create_floor_at(self, texture_path, width, depth, x=0.0, y=0.01, z=0.0):
        floor = Floor(
            self.app,
            texture_path=texture_path,
            uv_scale=(width / 2.0, depth / 2.0)
        )

        floor.get_model_matrix = lambda: glm.translate(
            glm.scale(glm.mat4(), glm.vec3(width / 10.0, 1.0, depth / 10.0)),
            glm.vec3(x, y, z)
        )

        # ===== MARCAR COMO NO COLISIONABLE =====
        floor.is_walkable = True

        self._add_object(floor)

    
    def _create_floor(self, texture_path, width, depth):
        floor = Floor(
            self.app,
            texture_path=texture_path,
            uv_scale=(width / 2.0, depth / 2.0)
        )
        floor.get_model_matrix = lambda: glm.translate(
            glm.scale(glm.mat4(), glm.vec3(width/10.0, 1.0, depth/10.0)),
            glm.vec3(0.0, 0.005, 0.0)
        )
        
        # ===== MARCAR COMO NO COLISIONABLE =====
        floor.is_walkable = True
        
        self._add_object(floor)

    def _create_floor_offset(self, texture_path, width, depth, offset_x=0.0, offset_z=0.0):
        floor = Floor(
            self.app,
            texture_path=texture_path,
            uv_scale=(width / 2.0, depth / 2.0)
        )

        floor.get_model_matrix = lambda: glm.translate(
            glm.scale(glm.mat4(), glm.vec3(width / 10.0, 1.0, depth / 10.0)),
            glm.vec3(offset_x, 0.005, offset_z)
        )

        floor.is_walkable = True
        self._add_object(floor)


    # -----------------------------------------------------------
    def _create_wall(self, texture_path, position, size, uv_scale, rotation, face, name):
        wall = Wall(
            self.app,
            position=position,
            size=size,
            color=(0.85, 0.85, 0.85),
            texture_path=texture_path,
            uv_scale=uv_scale,
            rotation_deg=rotation,
            single_face=face
        )
        self._add_object(wall)

    # -----------------------------------------------------------
    def _create_front_wall_with_door(self, texture_path, w, h, d, t, cfg):
        door_w = cfg["door_width"]
        door_h = cfg["door_height"]
        margin = 0.5
        z_pos = d/2 + t/2

        door_center_x = w/2 - margin - door_w/2
        left_part_width = w - door_w - margin
        right_part_width = margin

        self._create_wall(
            texture_path=texture_path,
            position=glm.vec3(-w/2 + left_part_width/2, h/2, z_pos),
            size=glm.vec3(left_part_width, h, t),
            uv_scale=(left_part_width/4, h/4),
            rotation=(0, 180, 0),
            face="front",
            name="Pared frontal izquierda"
        )

        lintel_h = h - door_h
        if lintel_h > 0.1:
            self._create_wall(
                texture_path=texture_path,
                position=glm.vec3(door_center_x, h - lintel_h/2, z_pos),
                size=glm.vec3(door_w, lintel_h, t),
                uv_scale=(door_w/4, lintel_h/4),
                rotation=(0, 180, 0),
                face="front",
                name="Dintel sobre puerta"
            )

        self._create_wall(
            texture_path=texture_path,
            position=glm.vec3(w/2 - right_part_width/2, h/2, z_pos),
            size=glm.vec3(right_part_width, h, t),
            uv_scale=(right_part_width/4, h/4),
            rotation=(0, 180, 0),
            face="front",
            name="Pared frontal derecha"
        )

    # ======================================================================
    #                         OBJETOS DE LA ESCENA
    # ======================================================================
    def setup_cash_registers(self):
        self.checkout1 = Model3DMultiMaterial(
            self.app,
            "assets/models/Supermarket_Checkout.glb",
            position=glm.vec3(4.0, 0.0, -4.0),
            scale=glm.vec3(0.4),
            rotation=(0, -90, 0)
        )

        self._add_object(self.checkout1)

        self.checkout2 = Model3DMultiMaterial(
            self.app,
            "assets/models/Supermarket_Checkout.glb",
            position=glm.vec3(4.0, 0.0, 2.0),
            scale=glm.vec3(0.4),
            rotation=(0, -90, 0)
        )

        self._add_object(self.checkout2)

        # self.register1 = Model3D(
        #     self.app,
        #     model_path="assets/models/supermarket_checkout.glb",
        #     position=glm.vec3(4.0, 0.0, -4.0),
        #     scale=glm.vec3(0.4, 0.4, 0.4),
        #     rotation=(0.0, -90.0, 0.0)
        # )
        # self._add_object(self.register1)

        # self.register2 = Model3D(
        #     self.app,
        #     model_path="assets/models/Supermarket_Checkout.glb",
        #     position=glm.vec3(4.0, 0.0, 2.0),
        #     scale=glm.vec3(0.4, 0.4, 0.4),
        #     rotation=(0.0, -90.0, 0.0)
        # )
        # self._add_object(self.register2)

    def _create_shelves(self):

        # shelves = InstancedModel3D(
        #     self.app,
        #     model_path="assets/models/supermarket_shelves/shelves2.glb",
        #     instances=SHELVES
        # )
        # self._add_object(shelves)
        # self.product_items.append(shelves)


        shelf_path = "assets/models/supermarket_shelves/shelves2.glb"
        for entry in SHELVES:
            pos = entry["pos"]
            rot = entry["rot"]
            shelf = Model3D(
                self.app,
                model_path=shelf_path,
                position=glm.vec3(*pos),
                scale=glm.vec3(0.8, 0.8, 0.8),
                rotation=rot
            )
            self.shelves.append(shelf)
            self._add_object(shelf)

    def _create_water_packs(self):
        water = InstancedModel3D(
            self.app,
            model_path="assets/models/water_bottle2.glb",
            instances=WATER_PACKS
        )
        self._add_object(water)
        self.product_items.append(water)

    def _create_chips(self):
        chips = InstancedModel3D(
            self.app,
            model_path="assets/models/chips.glb",
            instances=CHIPS
        )
        self._add_object(chips)
        self.product_items.append(chips)

    def _create_milk(self):
        milk = InstancedModel3D(
            self.app,
            model_path="assets/models/milk2.glb",
            instances=MILK
        )
        self._add_object(milk)
        self.product_items.append(milk)

    def _create_apples(self):
        apples = InstancedModel3D(
            self.app,
            model_path="assets/models/apple2.glb",
            instances=APPLE
        )
        self._add_object(apples)
        self.product_items.append(apples)

    def _create_orange(self):
        orange = InstancedModel3D(
            self.app,
            model_path="assets/models/orange.glb",
            instances=ORANGE
        )
        self._add_object(orange)
        self.product_items.append(orange)

    def _create_kinder(self):
        kinder = InstancedModel3D(
            self.app,
            model_path="assets/models/kinder.glb",
            instances=KINDER
        )
        self._add_object(kinder)
        self.product_items.append(kinder)
    
    def _create_tuna(self):
        tuna = InstancedModel3D(
            self.app,
            model_path="assets/models/tuna.glb",
            instances=TUNA
        )
        self._add_object(tuna)
        self.product_items.append(tuna)

    def _create_cereals(self):
        cereals = InstancedModel3D(
            self.app,
            model_path="assets/models/cereals1.glb",
            instances=CEREALS
        )
        self._add_object(cereals)
        self.product_items.append(cereals)

    def _create_wine(self):
        wine = InstancedModel3D(
            self.app,
            model_path="assets/models/wine_bottle.glb",
            instances=WINE
        )
        self._add_object(wine)
        self.product_items.append(wine)

    def _create_cocacola(self):
        cocacola = InstancedModel3D(
            self.app,
            model_path="assets/models/coke_can.glb",
            instances=COCACOLA
        )
        self._add_object(cocacola)
        self.product_items.append(cocacola)

    def _create_cava(self):
        cava = InstancedModel3D(
            self.app,
            model_path="assets/models/champagne_bottle.glb",
            instances=CAVA
        )
        self._add_object(cava)
        self.product_items.append(cava)

    def _create_whiskey(self):
        whiskey = InstancedModel3D(
            self.app,
            model_path="assets/models/whiskey.glb",
            instances=WHISKEY
        )
        self._add_object(whiskey)
        self.product_items.append(whiskey)

    def _create_paper(self):
        paper = InstancedModel3D(
            self.app,
            model_path="assets/models/toilet_paper.glb",
            instances=PAPER
        )
        self._add_object(paper)
        self.product_items.append(paper)

    def _create_shampoo(self):
        shampoo = InstancedModel3D(
            self.app,
            model_path="assets/models/shampoo.glb",
            instances=SHAMPOO
        )
        self._add_object(shampoo)
        self.product_items.append(shampoo)

    def _create_sponge(self):
        sponge = InstancedModel3D(
            self.app,
            model_path="assets/models/sponge.glb",
            instances=SPONGE
        )
        self._add_object(sponge)
        self.product_items.append(sponge)

    def _create_candle(self):
        candle = InstancedModel3D(
            self.app,
            model_path="assets/models/candle3.glb",
            instances=CANDLE
        )
        self._add_object(candle)
        self.product_items.append(candle)

    def _create_jarron(self):
        jarron = InstancedModel3D(
            self.app,
            model_path="assets/models/jarron.glb",
            instances=JARRON
        )
        self._add_object(jarron)
        self.product_items.append(jarron)

    def _create_mug(self):
        mug = InstancedModel3D(
            self.app,
            model_path="assets/models/mug4.glb",
            instances=MUG
        )
        self._add_object(mug)
        self.product_items.append(mug)

    def _create_avatar(self):
        """Crea un capsule collider invisible como avatar físico."""
        print("\n🧍 Creando avatar físico (CapsuleCollider)...")

        from src.objects.capsule_collider import CapsuleCollider

        cam_pos = self.app.camera.position

        # === Capsule Collider ===
        # Radio: 0.30m
        # Altura: 1.75m
        self.avatar = CapsuleCollider(
            radius=0.30,
            height=1.75,
            position=glm.vec3(cam_pos.x, 0.01, cam_pos.z)  # 0.01 para evitar colisión con suelo
        )

        # NO agregamos el avatar a self.objects todavía
        # Primero construimos colliders sin él
        self._add_object(self.avatar)

        # Regenerar colliders SIN incluir el avatar
        print("🔄 Reconstruyendo colliders sin avatar...")
        self.rebuild_static_colliders()
        
        print(f"✓ Avatar creado en: ({self.avatar.position.x:.2f}, {self.avatar.position.y:.2f}, {self.avatar.position.z:.2f})")
        print(f"✓ Total colliders estáticos: {len(self.static_colliders)}")


    def get_scene_bounds(self):
        min_x = +10
        max_x = -10
        min_z = +10
        max_z = -10

        for obj in self.objects:   # Ajusta según tu lista real de objetos
            if hasattr(obj, "position"):
                px, pz = obj.position.x, obj.position.z
                min_x = min(min_x, px)
                max_x = max(max_x, px)
                min_z = min(min_z, pz)
                max_z = max(max_z, pz)

        # Añadir un pequeño margen
        return min_x - 1, max_x + 1, min_z - 1, max_z + 1



    # ======================================================================
    #                          UTILIDADES
    # ======================================================================
    def _add_object(self, obj):
        self.objects.append(obj)
        self.scene_objects["main"].append(obj)

    # ======================================================================
    #                          ESCENAS
    # ======================================================================
    def set_scene(self, scene_name):
        print(f"🎬 Cambiando escena: '{self.current_scene}' → '{scene_name}'")
        self.current_scene = scene_name

    def get_current_scene(self):
        return self.current_scene

    # ======================================================================
    #                          RENDER
    # ======================================================================
    def render(self, view_mode="third"):
        """Renderiza todos los objetos de la escena.

        - En primera persona (view_mode == 'first'): no dibujamos el avatar.
        - En modo dios (view_mode == 'third'): tampoco dibujamos el avatar.
        Así no tapa la cámara aunque esté en la misma posición.
        """
        avatar_ref = getattr(self, "avatar", None)

        for obj in self.objects:
            # Ocultar avatar tanto en first como en third
            if view_mode in ("first", "third") and obj is avatar_ref:
                continue

            obj.update_matrices()
            obj.render()


    # ======================================================================
    #                          CLEANUP
    # ======================================================================
    def cleanup(self):
        for obj in self.objects:
            try:
                obj.destroy()
            except Exception:
                pass
