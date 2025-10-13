import pygame as pg
import sys

class GUIManager:
    def __init__(self, win_size):
        self.WIN_SIZE = win_size
        self.show_context_menu = False
        self.context_buttons = []
        
        # Fuentes
        try:
            self.font = pg.font.SysFont('Arial', 32)
            self.small_font = pg.font.SysFont('Arial', 24)
            self.title_font = pg.font.SysFont('Arial', 38)
        except:
            self.font = pg.font.Font(None, 32)
            self.small_font = pg.font.Font(None, 24)
            self.title_font = pg.font.Font(None, 38)
        
        print("✅ GUIManager inicializado correctamente")

    def handle_events(self, events, engine):
        """Manejar eventos de la aplicación"""
        for event in events:
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                self.exit_app(engine)
            
            # ✅ CLIC DERECHO - ABRIR MENÚ
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 3:
                self.show_context_menu = True
                print("📋 Context menu opened")
            
            # CLIC IZQUIERDO
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos
                
                if self.show_context_menu:
                    button_clicked = False
                    for button in self.context_buttons:
                        if button["rect"].collidepoint(mouse_pos):
                            print(f"✅ Button clicked: {button['text']}")
                            button["action"](engine)
                            button_clicked = True
                            break
                    
                    if not button_clicked:
                        self.show_context_menu = False
                        print("❌ Context menu closed")
                
                else:
                    engine.left_mouse_pressed = True
                    engine.camera.first_mouse = True
            
            elif event.type == pg.MOUSEBUTTONUP and event.button == 1:
                engine.left_mouse_pressed = False
            
            elif event.type == pg.MOUSEMOTION and engine.left_mouse_pressed and not self.show_context_menu:
                engine.handle_mouse_movement(event)
        
        engine.handle_keyboard_input()

    def render(self, engine):
        """Renderizar la GUI"""
        if not self.show_context_menu:
            return
            
        overlay = pg.Surface(self.WIN_SIZE, pg.SRCALPHA)
        overlay.fill((0, 0, 0, 0))
        self.draw_context_menu(overlay)
        engine.render_overlay(overlay)

    def draw_context_menu(self, overlay):
        """Dibujar el menú contextual"""
        menu_width, menu_height = 400, 300
        menu_x = (self.WIN_SIZE[0] - menu_width) // 2
        menu_y = (self.WIN_SIZE[1] - menu_height) // 2

        # Fondo con sombra
        shadow_rect = pg.Rect(menu_x + 5, menu_y + 5, menu_width, menu_height)
        pg.draw.rect(overlay, (0, 0, 0, 100), shadow_rect, border_radius=12)
        
        # Fondo principal
        menu_rect = pg.Rect(menu_x, menu_y, menu_width, menu_height)
        pg.draw.rect(overlay, (35, 35, 45, 250), menu_rect, border_radius=12)
        pg.draw.rect(overlay, (80, 80, 120, 255), menu_rect, 3, border_radius=12)
        
        # Título
        title_text = self.title_font.render("3D STORE", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(menu_x + menu_width//2, menu_y + 40))
        overlay.blit(title_text, title_rect)
        
        # Línea separadora
        pg.draw.line(overlay, (100, 100, 140, 255), 
                    (menu_x + 30, menu_y + 70), 
                    (menu_x + menu_width - 30, menu_y + 70), 2)
        
        # Texto informativo
        info_lines = [
            "EXI | Vbb",
            "## @yobbju@ Cstf", 
            "EXI | APP",
            "3D Store System"
        ]
        
        text_y = menu_y + 100
        for i, line in enumerate(info_lines):
            color = (255, 255, 255) if i == 0 else (200, 200, 220)
            font = self.font if i == 0 else self.small_font
            
            text_surface = font.render(line, True, color)
            text_rect = text_surface.get_rect(center=(menu_x + menu_width//2, text_y))
            overlay.blit(text_surface, text_rect)
            text_y += 35 if i == 0 else 30
        
        # Botones
        buttons = [
            {
                "text": "🛒 SHOPPING CART", 
                "rect": pg.Rect(menu_x + 50, menu_y + 220, menu_width - 100, 45), 
                "action": self.show_cart
            },
            {
                "text": "❌ EXIT APP", 
                "rect": pg.Rect(menu_x + 50, menu_y + 275, menu_width - 100, 45), 
                "action": self.exit_app
            },
        ]
        
        self.context_buttons = buttons

        for button in buttons:
            pg.draw.rect(overlay, (60, 110, 170, 255), button["rect"], border_radius=10)
            pg.draw.rect(overlay, (160, 160, 190, 255), button["rect"], 2, border_radius=10)
            
            button_text = self.small_font.render(button["text"], True, (255, 255, 255))
            button_text_rect = button_text.get_rect(center=button["rect"].center)
            overlay.blit(button_text, button_text_rect)

    def show_cart(self, engine):
        print("🛒 Shopping cart opened!")
        self.show_context_menu = False

    def exit_app(self, engine):
        engine.cleanup()
        pg.quit()
        sys.exit()