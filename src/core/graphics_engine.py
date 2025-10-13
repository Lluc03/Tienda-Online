import numpy as np
import pygame as pg
import moderngl as mgl
import sys
from .camera import Camera
from src.scene.scene_manager import SceneManager 

class GraphicsEngine:
    def __init__(self):
        pg.init()
        self.WIN_SIZE = (1200, 800)
        
        # OpenGL configuration
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MAJOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MINOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_PROFILE_MASK, pg.GL_CONTEXT_PROFILE_CORE)
        pg.display.gl_set_attribute(pg.GL_DEPTH_SIZE, 24)
        
        pg.display.set_mode(self.WIN_SIZE, flags=pg.OPENGL | pg.DOUBLEBUF)
        self.ctx = mgl.create_context()
        self.ctx.enable(mgl.DEPTH_TEST)

        # Quad para overlay
        self.quad = self.ctx.buffer(np.array([
            -1.0,  1.0, 0.0, 0.0,
            -1.0, -1.0, 0.0, 1.0,  
             1.0,  1.0, 1.0, 0.0,
             1.0, -1.0, 1.0, 1.0,
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
            [
                (self.quad, '2f 2f', 'in_vert', 'in_uv')
            ]
        )
        
        # Initialize components
        self.camera = Camera(self)
        self.scene_manager = SceneManager(self) 
        
        # ✅ INICIALIZAR GUI MANAGER COMO None
        self.gui_manager = None
        
        # Control states
        self.left_mouse_pressed = False
        self.camera.first_mouse = True
        
        pg.mouse.set_visible(True)
        pg.event.set_grab(False)
        pg.display.set_caption("3D Store - Right Click for Context Menu")

    def set_gui_manager(self, gui_manager):
        """✅ CONECTAR EL GUI MANAGER AL MOTOR GRÁFICO"""
        self.gui_manager = gui_manager
        print("✅ GUI Manager conectado al motor gráfico")

    def get_events(self):
        """Obtener todos los eventos de pygame"""
        return pg.event.get()

    def handle_basic_events(self, events):
        """Manejo básico de eventos (cuando no hay GUI)"""
        for event in events:
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                self.cleanup()
                pg.quit()
                sys.exit()
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                self.left_mouse_pressed = True
                self.camera.first_mouse = True
            elif event.type == pg.MOUSEBUTTONUP and event.button == 1:
                self.left_mouse_pressed = False
            elif event.type == pg.MOUSEMOTION and self.left_mouse_pressed:
                self.handle_mouse_movement(event)

    def handle_mouse_movement(self, event):
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
        keys = pg.key.get_pressed()
        
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

    def render_overlay(self, overlay_surface):
        """Renderizar overlay GUI en la escena 3D"""
        if overlay_surface is None:
            return
            
        raw_data = pg.image.tostring(overlay_surface, "RGBA", False)
        texture = self.ctx.texture(self.WIN_SIZE, 4, raw_data)
        texture.build_mipmaps()

        self.ctx.disable(mgl.DEPTH_TEST)
        self.ctx.enable(mgl.BLEND)
        self.ctx.blend_func = (mgl.SRC_ALPHA, mgl.ONE_MINUS_SRC_ALPHA)

        texture.use(0)
        self.quad_program['tex'] = 0
        self.quad_vao.render(mgl.TRIANGLE_STRIP)

        self.ctx.disable(mgl.BLEND)
        self.ctx.enable(mgl.DEPTH_TEST)
        texture.release()

    def cleanup(self):
        pg.mouse.set_visible(True)
        if hasattr(self, 'scene_manager'):
            self.scene_manager.cleanup()

    def render(self):
        self.ctx.clear(color=(0.5, 0.7, 1.0), depth=1.0)
        self.camera.update_view_matrix()
        
        if self.scene_manager:
            self.scene_manager.render()
        
        # ✅ RENDERIZAR GUI SI EXISTE
        if self.gui_manager:
            self.gui_manager.render(self)
        
        pg.display.flip()
        
    def run(self):
        clock = pg.time.Clock()
        while True:
            # Obtener eventos
            events = self.get_events()
            
            # ✅ DELEGAR EVENTOS AL GUI MANAGER SI ESTÁ CONECTADO
            if self.gui_manager:
                self.gui_manager.handle_events(events, self)
            else:
                self.handle_basic_events(events)
                self.handle_keyboard_input()
                
            self.render()
            clock.tick(60)