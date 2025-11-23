import glm
import math
from src.objects.Model3D import Model3D
from src.objects.model_obj import ModelOBJ
from src.objects.floor import Floor
from src.objects.wall import Wall
from src.objects.InstancedModel3D import InstancedModel3D
from src.objects.coordenates.shelves_positions import SHELVES
from src.objects.coordenates.water_positions import WATER_PACKS
from src.objects.coordenates.chips_positions import CHIPS
from src.objects.coordenates.milk_positions import MILK
from src.objects.coordenates.apple_positions import APPLE
from src.objects.coordenates.cereals_positions import CEREALS
from src.objects.coordenates.wine_positions import WINE

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
        self.setup_main_room()
        self.setup_cash_registers()
        self._create_shelves()
        self._create_water_packs()
        self._create_chips()
        self._create_milk()
        self._create_apples()
        self._create_cereals()
        self._create_wine()
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
        """Construye colliders AABB de todos los objetos excepto el avatar y suelos caminables."""
        self.static_colliders = []

        avatar = getattr(self, "avatar", None)

        for obj in self.objects:
            # No incluir avatar
            if obj is avatar:
                continue

            # Excluir objetos marcados como caminables
            if getattr(obj, "is_walkable", False):
                continue

            # No podemos obtener matriz → no se usa como colisionador
            if not hasattr(obj, "get_model_matrix"):
                continue

            # AABB local correcto
            if hasattr(obj, "aabb_local") and callable(obj.aabb_local):
                local = obj.aabb_local()
            else:
                local = (glm.vec3(-0.5, 0, -0.5), glm.vec3(0.5, 1.0, 0.5))

            if not local:
                continue

            local_min, local_max = local

            wmin, wmax = aabb_world_from_local(
                local_min, local_max,
                obj.get_model_matrix()
            )

            self.static_colliders.append(
                (glm.vec3(*wmin), glm.vec3(*wmax))
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

        for b_min, b_max in self.static_colliders:
            if aabb_overlap_3d((a_min.x, a_min.y, a_min.z),
                               (a_max.x, a_max.y, a_max.z),
                               (b_min.x, b_min.y, b_min.z),
                               (b_max.x, b_max.y, b_max.z)):
                # revertimos
                entity.position = old_pos
                return False

        return True

    def raycast_pick_product(self, ray_origin, ray_dir):
        """Raycast contra productos GLTF con detección por instancia."""
        best = None
        best_instance_id = -1
        best_t = None

        for item in self.product_items:
            # Para InstancedModel3D, verificar cada instancia
            from src.objects.InstancedModel3D import InstancedModel3D
            
            if isinstance(item, InstancedModel3D):
                # Obtener AABB local base
                local_aabb = item.aabb_local()
                if local_aabb is None:
                    continue
                
                local_min, local_max = local_aabb
                
                # Verificar cada instancia
                for inst_id, inst_data in enumerate(item.instances):
                    # Construir matriz de transformación para esta instancia
                    pos = inst_data.get("pos", (0, 0, 0))
                    rot = inst_data.get("rot", (0, 0, 0))
                    scale = inst_data.get("scale", (1, 1, 1))
                    
                    # Normalizar a tuplas
                    if isinstance(pos, (int, float)):
                        pos = (pos, pos, pos)
                    if isinstance(rot, (int, float)):
                        rot = (rot, rot, rot)
                    if isinstance(scale, (int, float)):
                        scale = (scale, scale, scale)
                    
                    # Crear matriz de transformación para esta instancia
                    m = glm.mat4(1.0)
                    m = glm.translate(m, glm.vec3(*pos))
                    m = glm.rotate(m, glm.radians(rot[0]), glm.vec3(1, 0, 0))
                    m = glm.rotate(m, glm.radians(rot[1]), glm.vec3(0, 1, 0))
                    m = glm.rotate(m, glm.radians(rot[2]), glm.vec3(0, 0, 1))
                    m = glm.scale(m, glm.vec3(*scale))
                    
                    # Transformar AABB al espacio mundial
                    from src.utils.geometry import aabb_world_from_local, ray_aabb_intersection
                    wmin, wmax = aabb_world_from_local(local_min, local_max, m)
                    
                    # Raycast contra este AABB
                    t = ray_aabb_intersection(ray_origin, ray_dir, 
                                            glm.vec3(*wmin), glm.vec3(*wmax))
                    
                    if t is None or t < 0:
                        continue
                    
                    # Guardar si es el más cercano
                    if best_t is None or t < best_t:
                        best_t = t
                        best = item
                        best_instance_id = inst_id
            
            else:
                # Objeto normal (no instanciado)
                aabb = self.get_entity_aabb_world(item)
                if aabb is None:
                    continue

                a_min, a_max = aabb
                from src.utils.geometry import ray_aabb_intersection
                t = ray_aabb_intersection(ray_origin, ray_dir, a_min, a_max)
                if t is None or t < 0:
                    continue

                if best_t is None or t < best_t:
                    best_t = t
                    best = item
                    best_instance_id = -1

        return best, best_instance_id, best_t

    # ======================================================================
    #                       ⬇️ CÓDIGO ORIGINAL COMPLETO
    # ======================================================================
    def setup_main_room(self):
        print("🏗️ Construyendo sala del supermercado...")

        cfg = self.room_config
        w = cfg["width"]
        h = cfg["height"]
        d = cfg["depth"]
        t = cfg["wall_thickness"]

        floor_tex = "assets/textures/floor_prove1.jpg"
        wall_tex = "assets/textures/wall_white.jpg"

        self._create_floor(floor_tex, w, d)

        # ===== PAREDES =====
        self._create_wall(
            texture_path=wall_tex,
            position=glm.vec3(0, h/2, -d/2 - t/2),
            size=glm.vec3(w + 2*t, h, t),
            uv_scale=(w/4, h/4),
            rotation=(0, 0, 0),
            face="front",
            name="Pared trasera"
        )

        self._create_wall(
            texture_path=wall_tex,
            position=glm.vec3(-w/2 - t/2 + 1.0, h/2, 0),
            size=glm.vec3(d, h, t),
            uv_scale=(d/4, h/4),
            rotation=(0, 90, 0),
            face="back",
            name="Pared izquierda"
        )

        self._create_wall(
            texture_path=wall_tex,
            position=glm.vec3(w/2 + t/2, h/2, 0),
            size=glm.vec3(d, h, t),
            uv_scale=(d/4, h/4),
            rotation=(0, -90, 0),
            face="front",
            name="Pared derecha"
        )

        self._create_front_wall_with_door(wall_tex, w, h, d, t, cfg)

        self._create_wall(
            texture_path=wall_tex,
            position=glm.vec3(0, h + t/2, 0),
            size=glm.vec3(w + 2*t, t, d + 2*t),
            uv_scale=(w/4, d/4),
            rotation=(90, 0, 0),
            face="back",
            name="Techo"
        )

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
        self.register1 = Model3D(
            self.app,
            model_path="assets/models/supermarket_checkout.glb",
            position=glm.vec3(4.0, 0.0, -4.0),
            scale=glm.vec3(0.4, 0.4, 0.4),
            rotation=(0.0, -90.0, 0.0)
        )
        self._add_object(self.register1)

        self.register2 = Model3D(
            self.app,
            model_path="assets/models/SupermarketCheckout.glb",
            position=glm.vec3(4.0, 0.0, 2.0),
            scale=glm.vec3(0.4, 0.4, 0.4),
            rotation=(0.0, -90.0, 0.0)
        )
        self._add_object(self.register2)

    def _create_shelves(self):
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
            model_path="assets/models/bottle_water.glb",
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
