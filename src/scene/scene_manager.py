import glm
from src.objects.Model3D import Model3D
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


class SceneManager:
    """
    🏗️ Gestor de escenas con sistema de habitación tipo cubo perfecto.
    
    Arquitectura:
    - Paredes exteriores que forman un cubo cerrado
    - Cada pared con una sola cara visible desde el interior
    - Sistema modular para añadir decoración
    """
    
    def __init__(self, app):
        self.app = app
        self.objects = []
        self.current_scene = "main"
        
        # Configuración de la sala
        self.room_config = {
            "width": 20.0,      # Ancho interior (eje X)
            "height": 5.0,      # Alto interior (eje Y)
            "depth": 15.0,      # Profundidad interior (eje Z)
            "wall_thickness": 0.3,  # Grosor de paredes más visible
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

        self.setup_main_room()
        self.setup_cash_registers()  # Movido aquí para que se cuente correctamente
        self._create_shelves()
        self._create_water_packs()
        self._create_chips()
        self._create_milk()
        self._create_apples()
        self._create_cereals()
        self._create_wine()


        print(f"\n📋 RESUMEN DE ESCENA:")
        print(f"   Total objetos: {len(self.objects)}")
        print(f"   Objetos en 'main': {len(self.scene_objects['main'])}")
        for i, obj in enumerate(self.objects):
            obj_type = type(obj).__name__
            pos = getattr(obj, 'position', 'N/A')
            print(f"   [{i}] {obj_type} en {pos}")
    
    def setup_main_room(self):
        """
        🏢 Construye una sala tipo cubo cerrado con puerta.
        Sistema simplificado con paredes que se tocan perfectamente.
        """
        print("🏗️ Construyendo sala del supermercado...")
        
        cfg = self.room_config
        
        # Dimensiones interiores
        w = cfg["width"]
        h = cfg["height"]
        d = cfg["depth"]
        t = cfg["wall_thickness"]
        
        # Texturas
        floor_tex = "assets/textures/floor_prove1.jpg"
        wall_tex = "assets/textures/wall_white.jpg"
        
        # ===== 📐 SUELO =====
        self._create_floor(floor_tex, w, d)
        
        # ===== 🧱 SISTEMA DE PAREDES (de dentro hacia fuera) =====
        
        # 1. PARED TRASERA (Z negativo) - Completa
        self._create_wall(
            texture_path=wall_tex,
            position=glm.vec3(0, h/2, -d/2 - t/2),
            size=glm.vec3(w + 2*t, h, t),  # Ancho total incluyendo laterales
            uv_scale=(w/4, h/4),
            rotation=(0, 0, 0),
            face="front",
            name="Pared trasera"
        )
        
        # 2. PAREDES LATERALES (solo la parte interior, sin incluir esquinas)
        # Izquierda (X negativo) - necesita rotar 90° para que mire hacia +X (interior)
        self._create_wall(
            texture_path=wall_tex,
            position=glm.vec3(-w/2 - t/2 + 1.0, h/2, 0),
            size=glm.vec3(d, h, t),  # d en X local, luego se rota
            uv_scale=(d/4, h/4),
            rotation=(0, 90, 0),  # Rota 90° en Y
            face="back",  # La cara trasera apuntará a +X después de rotar
            name="Pared izquierda"
        )
        
        # Derecha (X positivo) - necesita rotar -90° para que mire hacia -X (interior)
        self._create_wall(
            texture_path=wall_tex,
            position=glm.vec3(w/2 + t/2, h/2, 0),
            size=glm.vec3(d, h, t),  # d en X local, luego se rota
            uv_scale=(d/4, h/4),
            rotation=(0, -90, 0),  # Rota -90° en Y
            face="front",  # La cara frontal apuntará a -X después de rotar
            name="Pared derecha"
        )
        
        # 3. PARED FRONTAL CON PUERTA (Z positivo)
        self._create_front_wall_with_door(wall_tex, w, h, d, t, cfg)
        
        # 4. TECHO
        self._create_wall(
            texture_path=wall_tex,
            position=glm.vec3(0, h + t/2, 0),
            size=glm.vec3(w + 2*t, t, d + 2*t),  # Cubre todo
            uv_scale=(w/4, d/4),
            rotation=(90, 0, 0),  # Rota para mirar hacia abajo
            face="back",
            name="Techo"
        )
        
        print(f"✅ Sala base creada")
        print(f"   📏 Interior: {w}m × {h}m × {d}m")
        print(f"   🧱 Grosor paredes: {t}m")
        print(f"   🚪 Puerta: {cfg['door_width']}m × {cfg['door_height']}m")

        # ============================
        # 🌍 SUELO INFINITO EXTERIOR
        # ============================

        # Crear un plano enorme como asfalto
        asphalt = Floor(
            self.app,
            texture_path="assets/textures/asphalt_grey.jpg",
            uv_scale=(100, 100)   # repetición de la textura
        )

        # Colocar un modelo mucho más grande que la tienda
        # El floor original es 10x10, así que lo escalamos MUCHO
        asphalt.get_model_matrix = lambda: glm.scale(
            glm.mat4(),
            glm.vec3(200, 1, 200)   # 200m x 200m de asfalto
        )

        self._add_object(asphalt)
        print("✓ Añadido suelo exterior infinito (asfalto)")
    
    def _create_floor(self, texture_path, width, depth):
        """Crea el suelo a nivel Y=0."""
        floor = Floor(
            self.app,
            texture_path=texture_path,
            uv_scale=(width / 2.0, depth / 2.0)
        )
        
        # Escalar el floor base (10×10) a dimensiones reales
        floor.get_model_matrix = lambda: glm.translate(
            glm.scale(
                glm.mat4(),
                glm.vec3(width / 10.0, 1.0, depth / 10.0)
            ),
            glm.vec3(0.0, 0.005, 0.0)  # elevamos el suelo interior
        )
        
        self._add_object(floor)
        print(f"   ✓ Suelo: {width}m × {depth}m")
    
    def _create_wall(self, texture_path, position, size, uv_scale, rotation, face, name):
        """
        Crea una pared genérica.
        
        Args:
            rotation: tupla (rx, ry, rz) en grados
            face: "front" o "back"
        """
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
        print(f"   ✓ {name}: pos={position}, size={size}")
    
    def _create_front_wall_with_door(self, texture_path, w, h, d, t, cfg):
        """
        Crea la pared frontal con la puerta movida al lado DERECHO.
        """
        door_w = cfg["door_width"]
        door_h = cfg["door_height"]

        # Margen entre la puerta y la pared derecha
        margin = 0.5   # Puedes ajustar a tu gusto

        # Cálculo de posiciones
        z_pos = d/2 + t/2

        # La puerta irá en la derecha:
        # derecha total = w/2
        # puerta pegada justo a la izquierda del margen
        door_center_x = w/2 - margin - door_w/2

        # Pared izquierda mucho más grande
        left_part_width = w - door_w - margin

        # Pared derecha solo relleno del margen
        right_part_width = margin

        # === pared izquierda ===
        self._create_wall(
            texture_path=texture_path,
            position=glm.vec3(-w/2 + left_part_width/2, h/2, z_pos),
            size=glm.vec3(left_part_width, h, t),
            uv_scale=(left_part_width/4, h/4),
            rotation=(0, 180, 0),
            face="front",
            name="Pared frontal izquierda"
        )

        # === puerta (vacío, no se crea geometría; tú puedes poner un modelo aquí después) ===
        # Si quieres más tarde un modelo, este es el sitio exacto

        # === dintel sobre la puerta ===
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

        # === pared derecha (pequeña) ===
        self._create_wall(
            texture_path=texture_path,
            position=glm.vec3(w/2 - right_part_width/2, h/2, z_pos),
            size=glm.vec3(right_part_width, h, t),
            uv_scale=(right_part_width/4, h/4),
            rotation=(0, 180, 0),
            face="front",
            name="Pared frontal derecha"
        )

    
    def setup_cash_registers(self):
        """Añade 2 máquinas registradoras a la escena"""
        print("\n💰 Cargando máquinas registradoras...")
        
        # Máquina registradora 1 - ahora usando GLTF
        print("   🔸 Caja registradora 1...")
        self.register1 = Model3D(
            self.app,
            model_path="assets/models/supermarket_checkout.glb",  # Cambiado a GLTF
            position=glm.vec3(4.0, 0.0, -4.0),
            scale=glm.vec3(0.4, 0.4, 0.4),
            rotation=(0.0, -90.0, 0.0)
        )
        self._add_object(self.register1)
        
        # Máquina registradora 2 - ahora usando GLTF
        print("   🔸 Caja registradora 2...")
        self.register2 = Model3D(
            self.app,
            model_path="assets/models/SupermarketCheckout.glb",  # Cambiado a GLTF
            position=glm.vec3(4.0, 0.0, 2.0),
            scale=glm.vec3(0.4, 0.4, 0.4),
            rotation=(0.0, -90.0, 0.0)
        )
        self._add_object(self.register2)
        
        print("✅ Máquinas registradoras añadidas")

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
            app=self.app,
            model_path="assets/models/bottle_water.glb",
            instances=WATER_PACKS
        )

        self._add_object(water)

    def _create_chips(self):

        chips = InstancedModel3D(
            app=self.app,
            model_path="assets/models/chips.glb",
            instances=CHIPS
        )

        self._add_object(chips)

    def _create_milk(self):

        milk = InstancedModel3D(
            app=self.app,
            model_path="assets/models/milk2.glb",
            instances=MILK
        )

        self._add_object(milk)

    def _create_apples(self):

        apples = InstancedModel3D(
            app=self.app,
            model_path="assets/models/apple2.glb",
            instances=APPLE
        )

        self._add_object(apples)

    def _create_cereals(self):

        cereals = InstancedModel3D(
            app=self.app,
            model_path="assets/models/cereals1.glb",
            instances=CEREALS
        )

        self._add_object(cereals)

    def _create_wine(self):

        wine = InstancedModel3D(
            app=self.app,
            model_path="assets/models/wine_bottle.glb",
            instances=WINE
        )

        self._add_object(wine)
        
    def _add_object(self, obj):
        """Añade un objeto a la escena principal."""
        self.objects.append(obj)
        self.scene_objects["main"].append(obj)
    
    # ===== CONTROL DE ESCENAS =====
    
    def set_scene(self, scene_name):
        """Cambia entre diferentes vistas."""
        print(f"🎬 Cambiando escena: '{self.current_scene}' → '{scene_name}'")
        self.current_scene = scene_name
        
        scene_methods = {
            "main": self._setup_main_view,
            "products": self._setup_products_view,
            "cart": self._setup_cart_view,
            "config": self._setup_config_view
        }
        
        if scene_name in scene_methods:
            scene_methods[scene_name]()
    
    def _setup_main_view(self):
        print("  ↳ Vista principal: Supermercado")
    
    def _setup_products_view(self):
        print("  ↳ Vista productos: Catálogo")
    
    def _setup_cart_view(self):
        print("  ↳ Vista carrito: Items")
    
    def _setup_config_view(self):
        print("  ↳ Vista configuración")
    
    def get_current_scene(self):
        return self.current_scene
    
    # ===== RENDERIZADO =====
    
    def render(self):
        """Renderiza todos los objetos de la escena actual."""
        for obj in self.scene_objects[self.current_scene]:
            try:
                obj.update_matrices()
                obj.render()
            except Exception as e:
                obj_type = type(obj).__name__
                print(f"❌ Error renderizando {obj_type}: {e}")
    
    def cleanup(self):
        """Libera recursos de GPU."""
        for obj in self.objects:
            try:
                obj.destroy()
            except Exception as e:
                print(f"⚠️ Error liberando objeto: {e}")
        
        self.objects.clear()
        for scene_list in self.scene_objects.values():
            scene_list.clear()