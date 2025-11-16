import pygame as pg
import numpy as np
import moderngl as mgl
import sys
import glm
from .camera import Camera
from src.gui.ui_manager import UIManager
from src.scene.scene_manager import SceneManager


class GraphicsEngine:
    def __init__(self):
        pg.init()
        self.WIN_SIZE = (1200, 800)

        # Configuración OpenGL
        self._setup_opengl()
        
        # Componentes principales
        self.camera = Camera(self)
        self.scene_manager = SceneManager(self)
        self.ui_manager = UIManager(self.WIN_SIZE)
        

        # Referencia al avatar controlable (si la escena lo define)
        self.avatar = getattr(self.scene_manager, "avatar", None)

        # Si hay avatar, inicializar cámara enganchada a él
        if self.avatar is not None:
            try:
                self.update_camera_from_avatar()
            except Exception:
                pass


        # Configurar callbacks de UI
        self._setup_ui_callbacks()
        
        # Estados de control
        self.left_mouse_pressed = False
        self.clock = pg.time.Clock()
        
        # Configuración inicial
        pg.mouse.set_visible(True)
        pg.event.set_grab(False)
        pg.display.set_caption("3D Store - Press M for Menu")

    def _setup_opengl(self):
        """Configura el contexto OpenGL"""
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MAJOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MINOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_PROFILE_MASK, pg.GL_CONTEXT_PROFILE_CORE)
        pg.display.gl_set_attribute(pg.GL_DEPTH_SIZE, 24)

        self.screen = pg.display.set_mode(self.WIN_SIZE, flags=pg.OPENGL | pg.DOUBLEBUF)
        self.ctx = mgl.create_context()
        self.ctx.enable(mgl.DEPTH_TEST)
        
        # Setup GUI rendering
        self._setup_gui_rendering()

    def _setup_gui_rendering(self):
        """Configura el renderizado de GUI"""
        self.gui_surface = pg.Surface(self.WIN_SIZE, pg.SRCALPHA)
        self.gui_texture = self.ctx.texture(self.WIN_SIZE, 4)
        
        # Quad para renderizado
        self.quad = self.ctx.buffer(np.array([
            -1.0,  1.0, 0.0, 1.0,
            -1.0, -1.0, 0.0, 0.0,
             1.0,  1.0, 1.0, 1.0,
             1.0, -1.0, 1.0, 0.0,
        ], dtype='f4').tobytes())

        self.quad_program = self.ctx.program(
            vertex_shader='''
                #version 330
                in vec2 in_vert;
                in vec2 in_uv;
                out vec2 v_uv;
                void main() {
                    v_uv = in_uv;
                    gl_Position = vec4(in_vert, 0.0, 1.0);
                }
            ''',
            fragment_shader='''
                #version 330
                uniform sampler2D tex;
                in vec2 v_uv;
                out vec4 fragColor;
                void main() {
                    fragColor = texture(tex, v_uv);
                }
            '''
        )

        self.quad_vao = self.ctx.vertex_array(
            self.quad_program,
            [(self.quad, '2f 2f', 'in_vert', 'in_uv')]
        )

    def _setup_ui_callbacks(self):
        """Configura los callbacks de la UI"""
        # Callbacks principales
        self.ui_manager.on_productos_click = self._on_productos_click
        self.ui_manager.on_carrito_click = self._on_carrito_click
        self.ui_manager.on_config_click = self._on_config_click
        self.ui_manager.on_close_menu = self._on_close_menu
        self.ui_manager.on_reset_camera = self._on_reset_camera
        self.ui_manager.on_toggle_fullscreen = self._on_toggle_fullscreen
        self.ui_manager.on_exit = self._on_exit
        
        # Callbacks del carrito
        self.ui_manager.on_continue_shopping = self._on_continue_shopping
        self.ui_manager.on_checkout = self._on_checkout
        
        # Callbacks de configuración
        self.ui_manager.on_apply_config = self._on_apply_config
        
        print("✅ Todos los callbacks de UI configurados correctamente")

    def _on_productos_click(self):
        """Callback para botón Productos"""
        print("✓ Abrir menú de productos")
        self.ui_manager.show_menu("products")
        self.scene_manager.set_scene("products")

    def _on_carrito_click(self):
        """Callback para botón Carrito"""
        print("✓ Abrir carrito")
        self.ui_manager.show_menu("cart")
        self.scene_manager.set_scene("cart")

    def _on_config_click(self):
        """Callback para botón Configuración"""
        print("✓ Abrir configuración")
        self.ui_manager.show_menu("config")
        self.scene_manager.set_scene("config")

    def _on_close_menu(self):
        """Callback para cerrar menú"""
        print("✓ Cerrando menús")
        self.ui_manager.hide_all_menus()
        self.scene_manager.set_scene("main")

    def _on_reset_camera(self):
        """Callback para resetear cámara"""
        self.camera.reset_camera()
        print("✓ Cámara resetada")

    def _on_toggle_fullscreen(self):
        """Callback para alternar pantalla completa"""
        try:
            if pg.display.is_fullscreen():
                # Cambiar a modo ventana
                self.screen = pg.display.set_mode(self.WIN_SIZE, flags=pg.OPENGL | pg.DOUBLEBUF)
                print("✓ Modo ventana activado")
            else:
                # Cambiar a pantalla completa
                self.screen = pg.display.set_mode(self.WIN_SIZE, flags=pg.OPENGL | pg.DOUBLEBUF | pg.FULLSCREEN)
                print("✓ Pantalla completa activada")
            
            # Actualizar matriz de proyección al cambiar tamaño
            self.camera.update_projection_matrix()
            
            # Recrear la textura GUI con el nuevo tamaño si es necesario
            self._setup_gui_rendering()
            
        except Exception as e:
            print(f"❌ Error al cambiar modo pantalla: {e}")

    def _on_exit(self):
        """Callback para salir de la aplicación"""
        self.cleanup()
        pg.quit()
        sys.exit()

    def _on_continue_shopping(self):
        """Callback para seguir comprando"""
        print("✓ Continuar comprando")
        self.ui_manager.show_menu("products")
        self.scene_manager.set_scene("products")

    def _on_checkout(self):
        """Callback para proceder al checkout"""
        print("✓ Procediendo al checkout...")
        # Aquí iría la lógica de checkout
        print("✓ Pedido procesado correctamente")

    def _on_apply_config(self):
        """Callback para aplicar configuración"""
        print("✓ Configuración aplicada")
        # Aquí aplicarías los cambios de configuración

    def get_events(self):
        """Obtiene eventos de pygame"""
        return pg.event.get()

    def handle_events(self, events, time_delta):
        """Procesa eventos de pygame - VERSIÓN CORREGIDA"""
        for event in events:
            # ✅ SOLUCIÓN: Procesar eventos de UI primero
            self.ui_manager.handle_ui_events(event)
            
            if event.type == pg.QUIT:
                self.cleanup()
                pg.quit()
                sys.exit()

            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_m:
                    visible = self.ui_manager.toggle_main_menu()
                    print(f"Menú principal: {'VISIBLE' if visible else 'OCULTO'}")
                elif event.key == pg.K_ESCAPE:
                    self.cleanup()
                    pg.quit()
                    sys.exit()

            elif event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:  # Click izquierdo
                    if not self.ui_manager.is_hovering_ui():
                        self.left_mouse_pressed = True
                        self.camera.first_mouse = True
                        pg.mouse.set_visible(False)
                        pg.event.set_grab(True)
                        print("✓ Control de cámara activado")
                elif event.button == 3:  # Click derecho
                    if not self.ui_manager.is_hovering_ui():
                        self.ui_manager.menu_gui.create_context_menu(event.pos)
                        print(f"✓ Menú contextual en: {event.pos}")

            elif event.type == pg.MOUSEBUTTONUP:
                if event.button == 1:
                    self.left_mouse_pressed = False
                    pg.mouse.set_visible(True)
                    pg.event.set_grab(False)
                    print("✓ Control de cámara desactivado")

            elif event.type == pg.MOUSEMOTION:
                if self.left_mouse_pressed and not self.ui_manager.is_hovering_ui():
                    self.handle_mouse_movement(event)

    def handle_mouse_movement(self, event):
        """Procesa el movimiento del ratón para la cámara"""
        if self.camera.first_mouse:
            self.camera.last_mouse_x = event.pos[0]
            self.camera.last_mouse_y = event.pos[1]
            self.camera.first_mouse = False

        x_offset = event.pos[0] - self.camera.last_mouse_x
        y_offset = self.camera.last_mouse_y - event.pos[1]
        self.camera.last_mouse_x = event.pos[0]
        self.camera.last_mouse_y = event.pos[1]
        self.camera.process_mouse_movement(x_offset, y_offset)

    def handle_keyboard_input(self):
        """Procesa input de teclado continuo para mover el AVATAR, no la cámara."""
        keys = pg.key.get_pressed()

        # Si no hay avatar definido, fallback al comportamiento antiguo (mover cámara)
        if not getattr(self, "avatar", None):
            if keys[pg.K_UP] or keys[pg.K_w]:
                self.camera.move_forward()
            if keys[pg.K_DOWN] or keys[pg.K_s]:
                self.camera.move_backward()
            if keys[pg.K_LEFT] or keys[pg.K_a]:
                self.camera.move_left()
            if keys[pg.K_RIGHT] or keys[pg.K_d]:
                self.camera.move_right()
            if keys[pg.K_SPACE] or keys[pg.K_q]:
                self.camera.move_up()
            if keys[pg.K_LSHIFT] or keys[pg.K_e]:
                self.camera.move_down()
            return

        # --- MODO AGENTE: mover avatar según la dirección de la cámara ---
        move_vec = glm.vec3(0.0, 0.0, 0.0)
        speed = self.camera.move_speed  # reutilizamos la misma velocidad

        # Vectores forward/right "planos" (sin componente vertical)
        forward = glm.vec3(self.camera.forward.x, 0.0, self.camera.forward.z)
        right = glm.vec3(self.camera.right.x, 0.0, self.camera.right.z)

        if glm.length(forward) > 0:
            forward = glm.normalize(forward)
        if glm.length(right) > 0:
            right = glm.normalize(right)

        # Movimiento en XZ según WASD
        if keys[pg.K_UP] or keys[pg.K_w]:
            move_vec += forward * speed
        if keys[pg.K_DOWN] or keys[pg.K_s]:
            move_vec -= forward * speed
        if keys[pg.K_LEFT] or keys[pg.K_a]:
            move_vec -= right * speed
        if keys[pg.K_RIGHT] or keys[pg.K_d]:
            move_vec += right * speed

        # subir/bajar avatar con Q/E/Space/Shift 
        if keys[pg.K_SPACE] or keys[pg.K_q]:
            move_vec.y += speed
        if keys[pg.K_LSHIFT] or keys[pg.K_e]:
            move_vec.y -= speed

        # Aplicar movimiento al avatar usando SceneManager.try_move (con colisiones)
        if glm.length(move_vec) > 0:
            self.scene_manager.try_move(self.avatar, move_vec)

        # Mantener al avatar orientado con la cámara (solo yaw)
        self.avatar.set_rotation((0.0, self.camera.yaw, 0.0))

    
    def update_camera_from_avatar(self):
        """
        Cámara en tercera persona:
        - Siempre detrás del avatar según la dirección de la cámara.
        - Un poco por encima.
        """
        if not getattr(self, "avatar", None):
            return

        avatar_pos = self.avatar.get_position()

        # Altura de "cuerpo" donde queremos el centro de cámara encima del avatar
        eye_height = 1.2
        # Distancia de la cámara detrás del avatar
        distance = 3.0

        # Dirección de avance basada en la orientación actual de la cámara (yaw/pitch),
        # pero proyectada en el plano XZ (no queremos que la cámara se hunda o suba por pitch)
        forward = glm.vec3(self.camera.forward.x, 0.0, self.camera.forward.z)
        if glm.length(forward) == 0:
            forward = glm.vec3(0.0, 0.0, -1.0)
        forward = glm.normalize(forward)

        # Punto "target" sobre el avatar (a la altura del cuerpo/cabeza)
        target = glm.vec3(
            avatar_pos.x,
            avatar_pos.y + eye_height,
            avatar_pos.z
        )

        # Colocamos la cámara DISTANCIA metros detrás del avatar y un pelín más arriba
        cam_pos = target - forward * distance + glm.vec3(0.0, 0.5, 0.0)

        self.camera.position = cam_pos
        # Recalculamos la view matrix con la NUEVA posición
        self.camera.update_view_matrix()



    def render_gui(self):
        """Renderiza la GUI sobre OpenGL"""
        # Limpiar surface de GUI
        self.gui_surface.fill((0, 0, 0, 0))
        
        # ✅ CORRECCIÓN: Usar el UIManager de pygame_gui para dibujar
        self.ui_manager.ui_manager.draw_ui(self.gui_surface)
        
        # Convertir surface a textura OpenGL (True = invertir verticalmente)
        texture_data = pg.image.tostring(self.gui_surface, 'RGBA', True)
        self.gui_texture.write(texture_data)
        
        # Renderizar textura GUI sobre la escena 3D
        self.ctx.disable(mgl.DEPTH_TEST)
        self.ctx.enable(mgl.BLEND)
        self.gui_texture.use(0)
        self.quad_program['tex'] = 0
        self.quad_vao.render(mgl.TRIANGLE_STRIP)
        self.ctx.enable(mgl.DEPTH_TEST)

    def render(self):
        """Renderiza la escena completa"""
        # Limpiar buffers
        self.ctx.clear(color=(0.5, 0.7, 1.0), depth=1.0)
        
        # Actualizar y renderizar escena 3D
        if self.scene_manager:
            self.scene_manager.render()
        
        # Renderizar GUI encima
        self.render_gui()
        
        # Intercambiar buffers
        pg.display.flip()

    def cleanup(self):
        """Limpia recursos al cerrar"""
        print("✓ Limpiando recursos...")
        pg.mouse.set_visible(True)
        pg.event.set_grab(False)
        
        if hasattr(self, 'scene_manager'):
            self.scene_manager.cleanup()
        
        if hasattr(self, 'ui_manager'):
            self.ui_manager.cleanup()
        
        print("✓ Recursos liberados correctamente")

    def run(self):
        """Loop principal de la aplicación - VERSIÓN CORREGIDA"""
        self.clock = pg.time.Clock()
        print("🚀 Aplicación iniciada - Versión corregida")
        print("🎯 Los botones deberían funcionar ahora correctamente")

        while True:
            # 1. delta de tiempo
            time_delta = self.clock.tick(60) / 1000.0
            events = self.get_events()
            
            # 2. UI primero
            for event in events:
                self.ui_manager.ui_manager.process_events(event)
            self.ui_manager.ui_manager.update(time_delta)
            
            # 3. Eventos propios (cámara, menús, etc.)
            self.handle_events(events, time_delta)
            
            # 4. Input de teclado continuo (MUEVE AVATAR)
            self.handle_keyboard_input()

            # 4.5. Enganchar cámara al avatar (posición)
            self.update_camera_from_avatar()
            
            # 5. Renderizar escena + UI
            self.render()
