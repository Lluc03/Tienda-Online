import pygame as pg
import numpy as np
import moderngl as mgl
import sys
import glm
import os

from .camera import Camera
from src.gui.ui_manager import UIManager
from src.scene.scene_manager import SceneManager
from src.system.session_manager import SessionManager
from src.gui.login_menu import LoginMenu
from src.gui.admin_panel import AdminPanel
from src.analytics.analytics_manager import AnalyticsManager 


class GraphicsEngine:
    def __init__(self):
        pg.init()
        self.WIN_SIZE = (1200, 800)

        # ==============================
        # OpenGL
        # ==============================
        self._setup_opengl()

        # ==============================
        # Componentes principales
        # ==============================
        self.camera = Camera(self)
        self.scene_manager = SceneManager(self)
        self.ui_manager = UIManager(self.WIN_SIZE)
        self.session = SessionManager()
        self.analytics = AnalyticsManager(app=self)
        self.login_menu = LoginMenu(self)
        self.admin_panel = AdminPanel(self) 

        # Modo de vista:
        #   "third" = modo dios (cámara libre)
        #   "first" = primera persona pegada al avatar
        self.view_mode = "third"

        # Carrito lógico (por ahora solo manzanas)
        self.cart = {}

        # Estocaje inicial
        self.stock = {
            "water": 200,
            "chips": 200,
            "milk": 200,
            "apple": 200,
            "orange": 200,
            "kinder": 200,
            "cereals": 200,
            "wine": 200,
            "cocacola": 200,
            "cava": 200,
            "whiskey": 200,
            "paper": 200,
            "shampoo": 200,
            "sponge": 200,
            "candle": 200,
            "jarron": 200,
            "mug": 200,
            "tuna": 200,
        }


        # Referencia al avatar controlable (definido en SceneManager)
        self.avatar = getattr(self.scene_manager, "avatar", None)

        # Si hay avatar, inicializar cámara enganchada a él en primera persona
        if self.avatar is not None:
            try:
                self.update_camera_from_avatar()
            except Exception:
                pass

        # Callbacks de UI
        self._setup_ui_callbacks()

        # Estados de control
        self.left_mouse_pressed = False
        self.clock = pg.time.Clock()

        # Config ventana / ratón
        pg.mouse.set_visible(True)
        pg.event.set_grab(False)
        pg.display.set_caption("3D Store - Press M for Menu")

        # ===== NUEVO: Sistema de hover =====
        self.hovered_product = None
        self.hover_check_cooldown = 0
        self.hover_check_interval = 3
        self.hover_instance_data = None


    # ======================================================================
    # OPENGL / GUI
    # ======================================================================

    def _setup_opengl(self):
        """Configura el contexto OpenGL"""
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MAJOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MINOR_VERSION, 3)
        pg.display.gl_set_attribute(
            pg.GL_CONTEXT_PROFILE_MASK, pg.GL_CONTEXT_PROFILE_CORE
        )
        pg.display.gl_set_attribute(pg.GL_DEPTH_SIZE, 24)

        self.screen = pg.display.set_mode(
            self.WIN_SIZE, flags=pg.OPENGL | pg.DOUBLEBUF
        )
        self.ctx = mgl.create_context()
        self.ctx.enable(mgl.DEPTH_TEST)

        # Setup GUI rendering
        self._setup_gui_rendering()

    def _setup_gui_rendering(self):
        """Configura el renderizado de GUI en un quad 2D encima del 3D"""
        self.gui_surface = pg.Surface(self.WIN_SIZE, pg.SRCALPHA)
        self.gui_texture = self.ctx.texture(self.WIN_SIZE, 4)

        # Quad pantalla completa
        self.quad = self.ctx.buffer(
            np.array(
                [
                    -1.0,
                    1.0,
                    0.0,
                    1.0,
                    -1.0,
                    -1.0,
                    0.0,
                    0.0,
                    1.0,
                    1.0,
                    1.0,
                    1.0,
                    1.0,
                    -1.0,
                    1.0,
                    0.0,
                ],
                dtype="f4",
            ).tobytes()
        )

        self.quad_program = self.ctx.program(
            vertex_shader="""
                #version 330
                in vec2 in_vert;
                in vec2 in_uv;
                out vec2 v_uv;
                void main() {
                    v_uv = in_uv;
                    gl_Position = vec4(in_vert, 0.0, 1.0);
                }
            """,
            fragment_shader="""
                #version 330
                uniform sampler2D tex;
                in vec2 v_uv;
                out vec4 fragColor;
                void main() {
                    fragColor = texture(tex, v_uv);
                }
            """,
        )

        self.quad_vao = self.ctx.vertex_array(
            self.quad_program, [(self.quad, "2f 2f", "in_vert", "in_uv")]
        )

    # ======================================================================
    # UI CALLBACKS
    # ======================================================================

    def _setup_ui_callbacks(self):
        """Configura los callbacks de la UI"""
        # Menús
        self.ui_manager.on_productos_click = self._on_productos_click
        self.ui_manager.on_carrito_click = self._on_carrito_click
        self.ui_manager.on_config_click = self._on_config_click
        self.ui_manager.on_close_menu = self._on_close_menu
        self.ui_manager.on_return_to_login = self._on_return_to_login

        # Cámara / pantalla / salida
        self.ui_manager.on_reset_camera = self._on_reset_camera
        self.ui_manager.on_toggle_fullscreen = self._on_toggle_fullscreen
        self.ui_manager.on_exit = self._on_exit

        # Carrito
        self.ui_manager.on_continue_shopping = self._on_continue_shopping
        self.ui_manager.on_checkout = self._on_checkout
        self.ui_manager.on_cart_add_item = self._on_cart_add_item
        self.ui_manager.on_cart_remove_item = self._on_cart_remove_item


        # Configuración
        self.ui_manager.on_apply_config = self._on_apply_config

        print("✅ Todos los callbacks de UI configurados correctamente")

    # -------------------- Menús --------------------
    def _on_return_to_login(self):
        print("🔄 Volviendo al modo login...")
        self.login_menu.active = True
        self.session.mode = None
        self.ui_manager.hide_all_menus()


    def _on_productos_click(self):
        print("✓ Abrir menú de productos")
        self.ui_manager.show_menu("products")
        self.scene_manager.set_scene("products")

        # ⭐ Iniciar tracking si es primera vez
        if self.session.is_user() and not self.analytics.active_tracking:
            username = self.session.current_user or "usuario"
            self.analytics.start_user_session(username)

    def _on_carrito_click(self):
        print("✓ Abrir carrito")
        self.ui_manager.show_menu("cart")
        self.scene_manager.set_scene("cart")
        # Actualizar contenido del carrito en la UI
        self.ui_manager.menu_gui.update_cart_display(self.cart)

    def _on_config_click(self):
        print("✓ Abrir configuración")
        self.ui_manager.show_menu("config")
        self.scene_manager.set_scene("config")

    def _on_close_menu(self):
        print("✓ Cerrando menús")
        self.ui_manager.hide_all_menus()
        self.scene_manager.set_scene("main")

    # -------------------- Cámara / pantalla / salida --------------------

    def _on_reset_camera(self):
        self.camera.reset_camera()
        print("✓ Cámara resetada")

    def _on_toggle_fullscreen(self):
        try:
            if pg.display.is_fullscreen():
                self.screen = pg.display.set_mode(
                    self.WIN_SIZE, flags=pg.OPENGL | pg.DOUBLEBUF
                )
                print("✓ Modo ventana activado")
            else:
                self.screen = pg.display.set_mode(
                    self.WIN_SIZE,
                    flags=pg.OPENGL | pg.DOUBLEBUF | pg.FULLSCREEN,
                )
                print("✓ Pantalla completa activada")

            self.camera.update_projection_matrix()
            self._setup_gui_rendering()
        except Exception as e:
            print(f"❌ Error al cambiar modo pantalla: {e}")

    def _on_exit(self):
        # Guardar estocaje final
        self.analytics.save_stock(self.stock)

        self.cleanup()
        pg.quit()
        sys.exit()

    # -------------------- Carrito --------------------

    def _on_continue_shopping(self):
        print("✓ Continuar comprando")
        self.ui_manager.show_menu("products")
        self.scene_manager.set_scene("products")

    def _on_checkout(self):
        print("✓ Procediendo al checkout...")
        print("✓ Pedido procesado correctamente")

    def _on_apply_config(self):
        print("✓ Configuración aplicada")

    def _on_cart_add_item(self):
        product = self.ui_manager.menu_gui.selected_cart_product
        if product:
            self.add_product_to_cart(product)
            self.ui_manager.menu_gui.update_cart_display(self.cart)

    def _on_cart_remove_item(self):
        product = self.ui_manager.menu_gui.selected_cart_product
        if product and self.cart.get(product, 0) > 0:
            self.cart[product] -= 1
            if self.cart[product] == 0:
                del self.cart[product]
            self.ui_manager.menu_gui.update_cart_display(self.cart)


    def generate_topdown_map(self, save_path="src/analytics/top_view.png"):
        """
        Renderiza la escena desde arriba usando límites configurables
        y genera un mapa cenital perfecto que coincide con los heatmaps.
        """
        # Importar límites del analytics
        from src.analytics.analytics_manager import STORE_BOUNDS
        
        min_x = STORE_BOUNDS["x_min"]
        max_x = STORE_BOUNDS["x_max"]
        min_z = STORE_BOUNDS["z_min"]
        max_z = STORE_BOUNDS["z_max"]

        # ============================
        # 1) Configurar cámara cenital
        # ============================
        cam_height = 30.0  # altura suficiente

        top_cam_pos = glm.vec3(0, cam_height, 0)
        target = glm.vec3(0, 0, 0)
        up = glm.vec3(0, 0, -1)

        view = glm.lookAt(top_cam_pos, target, up)
        proj = glm.ortho(min_x, max_x, min_z, max_z, 0.1, 200)

        # Guardar matrices reales de la cámara
        old_proj = self.camera.m_proj
        old_view = self.camera.m_view

        # Aplicar matrices temporales
        self.camera.m_proj = proj
        self.camera.m_view = view

        # ============================
        # 2) Crear FBO y renderizar
        # ============================
        fbo = self.ctx.simple_framebuffer(self.WIN_SIZE)
        fbo.use()
        fbo.clear(0.3, 0.3, 0.3, 1.0)

        # Render real de la escena 3D
        self.scene_manager.render(view_mode="third")

        # ============================
        # 3) Convertir FBO → imagen PNG
        # ============================
        data = fbo.read(components=3)

        from PIL import Image
        img = Image.frombytes("RGB", self.WIN_SIZE, data)
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
        
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        img.save(save_path)

        print(f"🗺️ Mapa cenital generado: {save_path}")
        print(f"   Límites: X=[{min_x}, {max_x}], Z=[{min_z}, {max_z}]")

        # ============================
        # 4) Restaurar matrices reales
        # ============================
        self.camera.m_proj = old_proj
        self.camera.m_view = old_view
        
        # Restaurar el framebuffer original
        self.ctx.screen.use()


    # ===== NUEVO MÉTODO: Actualizar hover =====
    # En GraphicsEngine, método update_hover(), añadir después de detectar hover:

    def update_hover(self):
        """Detecta qué producto está bajo el cursor, y guarda su instancia."""
        self.hover_check_cooldown += 1
        if self.hover_check_cooldown < self.hover_check_interval:
            return
        self.hover_check_cooldown = 0

        # Reset si está sobre UI
        if self.ui_manager.is_hovering_ui():
            if self.hovered_product:
                self.hovered_product.set_hovered(False)
            self.hovered_product = None
            self.hover_instance_data = None
            return

        # Raycast
        mouse_x, mouse_y = pg.mouse.get_pos()
        ray_o, ray_d = self._screen_ray(mouse_x, mouse_y)

        item, instance_id, dist, inst_data = self.scene_manager.raycast_pick_product(ray_o, ray_d)
        
        if item is None:
            if self.hovered_product:
                self.hovered_product.set_hovered(False)
            self.hovered_product = None
            self.hover_instance_data = None
            return

        # Guardar la instancia si hay
        if inst_data:
            self.hover_instance_data = inst_data
            
            # ⭐ DEBUG: Mostrar altura Y real
            y_pos = inst_data["pos"][1]
            product_name = item.product_type if hasattr(item, 'product_type') else "unknown"
            shelf_computed = self.analytics.get_shelf_from_y(y_pos)
            print(f"🔍 Hover: {product_name} | Y={y_pos:.3f} | Estantería={shelf_computed}")
            
        else:
            self.hover_instance_data = None

        # Actualización de hover visual
        if item != self.hovered_product:
            if self.hovered_product:
                self.hovered_product.set_hovered(False)

            if item:
                item.set_hovered(True, instance_id)
                pg.mouse.set_cursor(pg.SYSTEM_CURSOR_HAND)
            else:
                pg.mouse.set_cursor(pg.SYSTEM_CURSOR_ARROW)

            self.hovered_product = item

        elif item and instance_id >= 0:
            item.set_hovered(True, instance_id)


    # ======================================================================
    # EVENTOS
    # ======================================================================

    def get_events(self):
        return pg.event.get()

    def handle_events(self, events, time_delta):
        """Procesa eventos con soporte para Login / Admin / Usuario."""

        # ======================================================================
        # 1) LOGIN — SOLO procesa botones del menú de login
        # ======================================================================
        if self.login_menu.active:

            for event in events:
                # LoginMenu es manual (no usa pygame_gui)
                self.login_menu.handle_event(event)

                if event.type == pg.QUIT:
                    print("⚠ QUIT ignorado en login")

                if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                    print("⚠ ESC ignorado en login")

            # Asegurar que UI no interfiere
            if hasattr(self, "heatmap_selector"):
                self.heatmap_selector = None

            self.ui_manager.hide_all_menus()
            return  # ⛔ NO continuar


        # ======================================================================
        # 2) MODO ADMINISTRADOR — UI pygame_gui + admin panel
        # ======================================================================
        if self.session.is_admin():

            for event in events:

                # UI
                self.ui_manager.handle_ui_events(event)

                # Panel admin
                self.admin_panel.handle_event(event)

                # Selectores opcionales
                if hasattr(self, "heatmap_selector") and self.heatmap_selector:
                    self.heatmap_selector.process_event(event)

                if hasattr(self, "zone_selector") and self.zone_selector:
                    self.zone_selector.process_event(event)

                if hasattr(self, "shelf_user_selector") and self.shelf_user_selector:
                    self.shelf_user_selector.process_event(event)

                if hasattr(self, "shelf_product_selector") and self.shelf_product_selector:
                    self.shelf_product_selector.process_event(event)

                # Cerrar app
                if event.type == pg.QUIT:
                    self.cleanup()
                    pg.quit()
                    sys.exit()

                # Volver al login
                if event.type == pg.KEYDOWN and event.key == pg.K_l:
                    print("🔄 Saliendo de Administrador → Login")
                    self.login_menu.active = True
                    self.session.mode = None

                    # Limpiar selectores
                    self.heatmap_selector = None
                    self.zone_selector = None
                    self.shelf_user_selector = None
                    self.shelf_product_selector = None

                    self.ui_manager.hide_all_menus()
                    return

            return  # ⛔ NO pasar a modo usuario


        # ======================================================================
        # 3) MODO USUARIO — JUEGO NORMAL
        # ======================================================================
        for event in events:

            # --- UI siempre primero ---
            self.ui_manager.handle_ui_events(event)

            if event.type == pg.QUIT:
                self.cleanup()
                pg.quit()
                sys.exit()

            # -----------------------
            # TECLADO
            # -----------------------
            if event.type == pg.KEYDOWN:

                if event.key == pg.K_m:
                    visible = self.ui_manager.toggle_main_menu()
                    print(f"Menú principal: {'VISIBLE' if visible else 'OCULTO'}")

                elif event.key == pg.K_ESCAPE:
                    self.cleanup()
                    pg.quit()
                    sys.exit()

                elif event.key == pg.K_v:
                    self.toggle_view_mode()

            # -----------------------
            # CLIC IZQUIERDO (CRÍTICO)
            # -----------------------
            if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:

                # 🚫 Si el ratón está sobre UI → NO 3D
                if self.ui_manager.is_hovering_ui():
                    continue

                # ✅ Producto clicado → AÑADIR UNA SOLA VEZ
                if self.hovered_product is not None:
                    self.click_product(self.hovered_product)
                    continue   # ⛔ consumir evento (evita +2)

                # Movimiento cámara
                self.left_mouse_pressed = True
                self.camera.first_mouse = True
                pg.mouse.set_visible(False)
                pg.event.set_grab(False)

                print("✓ Control cámara activado")

            # -----------------------
            # CLIC DERECHO → menú contextual
            # -----------------------
            if event.type == pg.MOUSEBUTTONDOWN and event.button == 3:
                if not self.ui_manager.is_hovering_ui():
                    self.ui_manager.menu_gui.create_context_menu(event.pos)

            # -----------------------
            # SOLTAR CLICK IZQUIERDO
            # -----------------------
            if event.type == pg.MOUSEBUTTONUP and event.button == 1:
                self.left_mouse_pressed = False
                pg.mouse.set_visible(True)
                pg.event.set_grab(False)

            # -----------------------
            # MOVIMIENTO RATÓN
            # -----------------------
            if event.type == pg.MOUSEMOTION:
                if self.left_mouse_pressed and not self.ui_manager.is_hovering_ui():
                    self.handle_mouse_movement(event)

    def handle_mouse_movement(self, event):
        """Procesa el movimiento del ratón para rotar la cámara (ambos modos)."""
        if self.camera.first_mouse:
            self.camera.last_mouse_x = event.pos[0]
            self.camera.last_mouse_y = event.pos[1]
            self.camera.first_mouse = False

        x_offset = event.pos[0] - self.camera.last_mouse_x
        y_offset = self.camera.last_mouse_y - event.pos[1]
        
        self.camera.last_mouse_x = event.pos[0]
        self.camera.last_mouse_y = event.pos[1]
        
        # Rotar cámara
        self.camera.process_mouse_movement(x_offset, y_offset)
        
        # En primera persona, la cámara rota pero la posición sigue al avatar
        if self.view_mode == "first":
            # Mantener la posición enganchada al avatar pero con la nueva rotación
            self.update_camera_from_avatar()

    # ======================================================================
    # INPUT CONTINUO (TECLADO)
    # ======================================================================

    def handle_keyboard_input(self):
        """Manejo unificado de teclado para ambos modos."""
        keys = pg.key.get_pressed()
        avatar = self.scene_manager.avatar

        # ============================
        # MOVIMIENTO UNIFICADO
        # ============================
        
        if self.view_mode == "third":
            # MODO DIOS: Movimiento libre de cámara
            if keys[pg.K_w]: self.camera.move_forward()
            if keys[pg.K_s]: self.camera.move_backward()
            if keys[pg.K_a]: self.camera.move_left()
            if keys[pg.K_d]: self.camera.move_right()
            if keys[pg.K_q]: self.camera.move_up()
            if keys[pg.K_e]: self.camera.move_down()
            
        else:
            # PRIMERA PERSONA: Movimiento con avatar
            if not avatar:
                return
            
            speed = 0.08
            
            # Calcular direcciones basadas en la cámara
            forward = glm.normalize(glm.vec3(self.camera.forward.x, 0, self.camera.forward.z))
            right = glm.normalize(glm.vec3(self.camera.right.x, 0, self.camera.right.z))
            
            # WASD horizontal
            if keys[pg.K_w]:
                move = forward * speed
                self.scene_manager.try_move(avatar, move)
            if keys[pg.K_s]:
                move = -forward * speed
                self.scene_manager.try_move(avatar, move)
            if keys[pg.K_a]:
                move = -right * speed
                self.scene_manager.try_move(avatar, move)
            if keys[pg.K_d]:
                move = right * speed
                self.scene_manager.try_move(avatar, move)
            
            # Q/E vertical (volar en primera persona)
            if keys[pg.K_q]:
                move = glm.vec3(0, -speed, 0)
                self.scene_manager.try_move(avatar, move, keep_on_ground=False)
            if keys[pg.K_e]:
                move = glm.vec3(0, speed, 0)
                self.scene_manager.try_move(avatar, move, keep_on_ground=False)
            
            # Actualizar cámara después del movimiento
            self.update_camera_from_avatar()

    # ======================================================================
    # CÁMARA ↔ AVATAR
    # ======================================================================

    def update_camera_from_avatar(self):
        """Posiciona la cámara en primera persona encima del CapsuleCollider."""
        if self.view_mode != "first":
            return

        avatar = self.scene_manager.avatar
        if not avatar:
            return

        pos = avatar.get_position()

        eye_height = 1.6          # altura real de los ojos
        cam_forward = glm.normalize(glm.vec3(self.camera.forward.x, 0, self.camera.forward.z))
        cam_offset = cam_forward * 0.20    # cámara adelantada 20cm

        self.camera.position = glm.vec3(
            pos.x + cam_offset.x,
            eye_height,
            pos.z + cam_offset.z
        )

        self.camera.update_view_matrix()



    def _set_avatar_yaw(self, yaw_deg: float):
        """
        Ajusta la rotación Y del avatar, sea ModelOBJ (set_rotation)
        o un Wall con rotation_deg.
        """
        avatar = getattr(self, "avatar", None)
        if avatar is None:
            return

        # Caso ModelOBJ (tiene set_rotation)
        if hasattr(avatar, "set_rotation"):
            avatar.set_rotation((0.0, yaw_deg, 0.0))
            return

        # Caso Wall u otro que solo tenga rotation_deg
        if hasattr(avatar, "rotation_deg"):
            try:
                avatar.rotation_deg = (0.0, yaw_deg, 0.0)
            except Exception:
                avatar.rotation_deg = glm.vec3(0.0, yaw_deg, 0.0)

    def toggle_view_mode(self):
        """Alterna entre primera persona y modo dios."""
        
        if self.view_mode == "third":
            # ===== CAMBIAR A PRIMERA PERSONA =====
            print("🔁 Cambiando a: Primera persona")
            
            # 1. Sincronizar avatar con la posición actual de la cámara
            if self.avatar:
                self.avatar.sync_with_camera(self.camera)
                print(f"   Avatar sincronizado en: {self.avatar.position}")
            
            # 2. Cambiar modo
            self.view_mode = "first"
            
            # 3. Actualizar cámara para primera persona
            self.update_camera_from_avatar()
            
            print("✓ Modo primera persona activado - Usa WASD para moverte")
            
        else:
            # ===== CAMBIAR A MODO DIOS =====
            print("🔁 Cambiando a: Modo dios")
            
            # La cámara ya está donde debe estar
            # Solo cambiamos el modo
            self.view_mode = "third"
            
            # Liberar control del ratón en modo dios
            self.left_mouse_pressed = False
            pg.mouse.set_visible(True)
            pg.event.set_grab(False)
            
            print("✓ Modo dios activado - Click izquierdo + arrastrar para rotar")



    # ======================================================================
    # PICKING / CARRITO
    # ======================================================================

    def _screen_ray(self, mouse_x, mouse_y):
        """Convierte un punto en pantalla a un rayo en espacio mundo."""
        w, h = self.WIN_SIZE
        x = (2.0 * mouse_x) / w - 1.0
        y = 1.0 - (2.0 * mouse_y) / h

        p_near = glm.vec4(x, y, -1.0, 1.0)
        p_far = glm.vec4(x, y, 1.0, 1.0)

        inv_vp = glm.inverse(self.camera.m_proj * self.camera.m_view)
        world_near = inv_vp * p_near
        world_far = inv_vp * p_far

        world_near /= world_near.w
        world_far /= world_far.w

        origin = glm.vec3(world_near.x, world_near.y, world_near.z)
        direction = glm.normalize(glm.vec3(world_far - world_near))
        return origin, direction

    def pick_product_at(self, mouse_pos):
        """Intenta seleccionar un producto bajo el cursor y añadirlo al carrito."""
        if not hasattr(self.scene_manager, "raycast_pick_product"):
            return

        mx, my = mouse_pos
        ray_o, ray_d = self._screen_ray(mx, my)

        item, dist = self.scene_manager.raycast_pick_product(ray_o, ray_d)
        if item is None:
            print("🙅‍♂️ No se ha clicado ningún producto")
            return

        product_type = getattr(item, "product_type", "apple")
        self.add_product_to_cart(product_type)
        print(f"✅ Producto seleccionado: {product_type} (dist={dist:.3f})")

        if self.ui_manager.menu_gui.cart_menu:
            self.ui_manager.menu_gui.update_cart_display(self.cart)

    def add_product_to_cart(self, product_type):
        # Crear stock si no existe
        if product_type not in self.stock:
            self.stock[product_type] = 200

        # Comprobar stock
        if self.stock[product_type] <= 0:
            print(f"❌ Sin stock de {product_type}")
            return

        # Descontar stock
        self.stock[product_type] -= 1

        # Añadir al carrito
        self.cart[product_type] = self.cart.get(product_type, 0) + 1

        print(f"🛒 Carrito: {product_type} -> {self.cart[product_type]} ud.")
        print(f"📦 Stock restante {product_type}: {self.stock[product_type]}")



    def remove_product_from_cart(self, product_type):
        if product_type not in self.cart:
            return
        if self.cart[product_type] <= 0:
            return
        self.cart[product_type] -= 1
        print(f"🛒 Carrito: {product_type} -> {self.cart[product_type]} ud.")

    # ===== NUEVO MÉTODO: Click en producto =====
    def click_product(self, product):
        """Método llamado cuando se clica un producto en la escena 3D"""
        # Tipo del producto
        product_type = getattr(product, "product_type", "unknown")

        # Registrar analítica
        # ⚠️ NO pasar shelf_id ni shelf_y
        self.analytics.record(
            cam_pos=self.camera.position,
            product=product_type
        )

        # ✅ SOLUCIÓN 2: Añadir al carrito SOLO desde aquí
        # Antes NO se llamaba directamente, causando problemas
        self.add_product_to_cart(product_type)

        print(f"🛒 Producto clicado: {product_type}")

        # Reset hover visual
        product.set_hovered(False)




    # ======================================================================
    # RENDER
    # ======================================================================

    def render_gui(self):
        """Renderiza la GUI sobre la escena 3D."""
        self.gui_surface.fill((0, 0, 0, 0))

        # Dibujar UI de pygame_gui
        self.ui_manager.ui_manager.draw_ui(self.gui_surface)

        texture_data = pg.image.tostring(self.gui_surface, "RGBA", True)
        self.gui_texture.write(texture_data)

        self.ctx.disable(mgl.DEPTH_TEST)
        self.ctx.enable(mgl.BLEND)
        self.gui_texture.use(0)
        self.quad_program["tex"] = 0
        self.quad_vao.render(mgl.TRIANGLE_STRIP)
        self.ctx.enable(mgl.DEPTH_TEST)

    def render(self):
        """Render general de GraphicsEngine con soporte para Login, Admin y Usuario."""

        # =========================================================================
        # 1) LOGIN (solo pygame sobre la surface, luego OpenGL)
        # =========================================================================
        if self.login_menu.active:

            # Limpiar GUI surface
            self.gui_surface.fill((25, 25, 25, 255))

            # Dibujar login (pygame puro)
            self.login_menu.render(self.gui_surface)

            # Subir surface a textura OpenGL
            texture_data = pg.image.tostring(self.gui_surface, "RGBA", True)
            self.gui_texture.write(texture_data)

            # Dibujar quad con la textura
            self.ctx.disable(mgl.DEPTH_TEST)
            self.ctx.enable(mgl.BLEND)

            self.gui_texture.use(0)
            self.quad_program["tex"] = 0
            self.quad_vao.render(mgl.TRIANGLE_STRIP)

            self.ctx.enable(mgl.DEPTH_TEST)
            pg.display.flip()
            return



        # =========================================================================
        # 2) ADMIN PANEL (pygame + pygame_gui → OpenGL)
        # =========================================================================
        if self.session.is_admin():

            # 1. Limpiar surface
            self.gui_surface.fill((15, 15, 15, 255))

            # 2. Dibujar panel de administrador
            self.admin_panel.render(self.gui_surface)

            # 3. Actualizar UI pygame_gui (para selector heatmap, etc.)
            time_delta = self.clock.get_time() / 1000
            self.ui_manager.update(time_delta)

            # 4. Dibujar UI pygame_gui encima
            self.ui_manager.draw_ui(self.gui_surface)

            # 5. Subir surface a textura
            texture_data = pg.image.tostring(self.gui_surface, "RGBA", True)
            self.gui_texture.write(texture_data)

            # 6. Dibujar en pantalla el quad 2D con la GUI
            self.ctx.disable(mgl.DEPTH_TEST)
            self.ctx.enable(mgl.BLEND)

            self.gui_texture.use(0)
            self.quad_program["tex"] = 0
            self.quad_vao.render(mgl.TRIANGLE_STRIP)

            self.ctx.enable(mgl.DEPTH_TEST)
            pg.display.flip()
            return



        # =========================================================================
        # 3) MODO USUARIO (Render 3D normal + GUI)
        # =========================================================================

        # Limpiar pantalla 3D (color + depth)
        self.ctx.clear(color=(0.5, 0.7, 1.0), depth=1.0)

        # Renderizar escena 3D
        if self.scene_manager:
            self.scene_manager.render(view_mode=self.view_mode)

        # Renderizar UI (menú principal, carrito, etc.)
        self.render_gui()

        pg.display.flip()



    # ======================================================================
    # CLEANUP / LOOP
    # ======================================================================

    def cleanup(self):
        print("✓ Limpiando recursos...")
        pg.mouse.set_visible(True)
        pg.event.set_grab(False)

        if hasattr(self, "scene_manager"):
            self.scene_manager.cleanup()
        if hasattr(self, "ui_manager"):
            self.ui_manager.cleanup()

        print("✓ Recursos liberados correctamente")

    def run(self):
        self.clock = pg.time.Clock()
        print("🚀 Aplicación iniciada")

        while True:
            time_delta = self.clock.tick(60) / 1000.0
            events = self.get_events()

            for event in events:
                self.ui_manager.ui_manager.process_events(event)
            self.ui_manager.ui_manager.update(time_delta)

            self.handle_events(events, time_delta)

            if self.session.is_user():
                self.handle_keyboard_input()
                self.update_hover()

                # ⭐ TRACKING DE POSICIÓN
                if self.analytics.active_tracking:

                    if self.view_mode == "first" and self.avatar:
                        pos = self.avatar.get_position()
                    else:
                        # MODO DIOS → usar posición real de la cámara
                        pos = self.camera.position

                    product = self.hovered_product.product_type if self.hovered_product else None
                    self.analytics.record(pos, product)


                if self.view_mode == "first":
                    self.update_camera_from_avatar()

            self.render()
