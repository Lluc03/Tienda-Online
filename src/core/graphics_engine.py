import pygame as pg
import moderngl as mgl
import sys
from .camera import Camera
from src.scene.scene_manager import SceneManager 

class GraphicsEngine:
    def __init__(self, win_size=(900, 900)):
        pg.init()
        self.WIN_SIZE = win_size
        
        # OpenGL configuration
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MAJOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MINOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_PROFILE_MASK, pg.GL_CONTEXT_PROFILE_CORE)
        
        pg.display.set_mode(self.WIN_SIZE, flags=pg.OPENGL | pg.DOUBLEBUF)
        self.ctx = mgl.create_context()
        
        # Initialize components
        self.camera = Camera(self)
        self.scene_manager = SceneManager(self) 
        
        pg.display.set_caption("3D Store - Demo")
        
    def check_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                self.cleanup()
                pg.quit()
                sys.exit()
        
        # Movement control
        keys = pg.key.get_pressed()
        if keys[pg.K_UP]:
            self.camera.move_forward()
        if keys[pg.K_DOWN]:
            self.camera.move_backward()

    def cleanup(self):
        """Resource cleanup"""
        if hasattr(self, 'scene_manager'): # If the attribute scene_manager exists, do cleanup
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