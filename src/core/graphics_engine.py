import pygame as pg
import moderngl as mgl
import sys
from .camera import Camera
from src.scene.scene_manager import SceneManager 

class GraphicsEngine:
    def __init__(self):
        pg.init()

        # Fullscreen detection
        display_info = pg.display.Info()
        self.WIN_SIZE = (display_info.current_w, display_info.current_h)
        
        # OpenGL configuration
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MAJOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MINOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_PROFILE_MASK, pg.GL_CONTEXT_PROFILE_CORE)
        
        pg.display.set_mode(self.WIN_SIZE, flags=pg.OPENGL | pg.DOUBLEBUF | pg.FULLSCREEN)
        self.ctx = mgl.create_context()
        
        # Mouse configuration - ALWAYS visible
        pg.mouse.set_visible(True)   # Mouse always visible
        pg.event.set_grab(False)     # Mouse NEVER captured

        # Initialize components
        self.camera = Camera(self)
        self.scene_manager = SceneManager(self) 
        
        # Mouse button state
        self.left_mouse_pressed = False
        self.camera.first_mouse = True
        
        pg.display.set_caption("3D Store - HOLD LEFT CLICK AND DRAG to look around - Arrows/WASD to move")
        
    def check_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                self.cleanup()
                pg.quit()
                sys.exit()
            
            # Left mouse button pressed
            elif event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button pressed
                    self.left_mouse_pressed = True
                    self.camera.first_mouse = True
                    pg.display.set_caption("3D Store - DRAGGING to look around - Release left click to stop")
            
            # Left mouse button released
            elif event.type == pg.MOUSEBUTTONUP:
                if event.button == 1:  # Left mouse button released
                    self.left_mouse_pressed = False
                    pg.display.set_caption("3D Store - HOLD LEFT CLICK AND DRAG to look around - Arrows/WASD to move")
            
            # Mouse movement only when left button is pressed
            elif event.type == pg.MOUSEMOTION:
                if self.left_mouse_pressed:
                    self.handle_mouse_movement(event)
        
        self.handle_keyboard_input()

    def handle_mouse_movement(self, event):
        if self.camera.first_mouse:
            self.camera.last_mouse_x = event.pos[0]
            self.camera.last_mouse_y = event.pos[1]
            self.camera.first_mouse = False
            return
        
        x_offset = event.pos[0] - self.camera.last_mouse_x
        y_offset = self.camera.last_mouse_y - event.pos[1]  # Inverted for natural movement
        
        self.camera.last_mouse_x = event.pos[0]
        self.camera.last_mouse_y = event.pos[1]
        
        # Only process if there's significant movement
        if abs(x_offset) > 0 or abs(y_offset) > 0:
            self.camera.process_mouse_movement(x_offset, y_offset)

    def handle_keyboard_input(self):
        keys = pg.key.get_pressed()
        
        # Forward/backward movement (always active)
        if keys[pg.K_UP] or keys[pg.K_w]:
            self.camera.move_forward()
        if keys[pg.K_DOWN] or keys[pg.K_s]:
            self.camera.move_backward()
        
        # Lateral movement (always active)
        if keys[pg.K_LEFT] or keys[pg.K_a]:
            self.camera.move_left()
        if keys[pg.K_RIGHT] or keys[pg.K_d]:
            self.camera.move_right()
        
        # Vertical movement (always active)
        if keys[pg.K_SPACE] or keys[pg.K_q]:
            self.camera.move_up()
        if keys[pg.K_LSHIFT] or keys[pg.K_e]:
            self.camera.move_down()

    def cleanup(self):
        """Resource cleanup"""
        # Mouse is already visible, no changes needed
        if hasattr(self, 'scene_manager'):
            self.scene_manager.cleanup()

    def render(self):
        self.ctx.clear(color=(0.5, 0.7, 1.0))
        self.camera.update_view_matrix()
        
        # Render scene
        if self.scene_manager:
            self.scene_manager.render()
        
        pg.display.flip()
        
    def run(self):
        clock = pg.time.Clock()
        while True:
            self.check_events()
            self.render()
            clock.tick(60)