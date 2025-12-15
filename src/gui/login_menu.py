import pygame as pg

class LoginMenu:
    def __init__(self, engine):
        self.engine = engine
        self.active = True

        self.font_title = pg.font.SysFont("Arial", 48)
        self.font_button = pg.font.SysFont("Arial", 32)

        # Botones
        self.btn_user_rect = pg.Rect(400, 300, 400, 70)
        self.btn_admin_rect = pg.Rect(400, 400, 400, 70)

    def handle_event(self, event):

        if event.type == pg.MOUSEBUTTONDOWN:
            x, y = event.pos

            # Usuario
            if self.btn_user_rect.collidepoint(x, y):
                print("👤 Entrar como USUARIO")
                username = "usuario_1"
                self.engine.session.set_user_mode(username)

                # iniciar tracking automático
                self.engine.analytics.start_user_session(username)

                self.active = False
                return

            # Administrador
            if self.btn_admin_rect.collidepoint(x, y):
                print("🛠 Entrar como ADMINISTRADOR")
                self.engine.session.set_admin_mode("admin")
                self.active = False
                return

    def render(self, surface):
        surface.fill((25, 25, 25, 255))  # ← SUPERFICIE pygame NORMAL

        # Título
        title = self.font_title.render("Selecciona el modo", True, (255, 255, 255))
        surface.blit(title, (400, 150))

        # Botón usuario
        pg.draw.rect(surface, (70, 130, 180), self.btn_user_rect)
        txt1 = self.font_button.render("Entrar como Usuario", True, (255, 255, 255))
        surface.blit(txt1, (self.btn_user_rect.x + 30, self.btn_user_rect.y + 18))

        # Botón admin
        pg.draw.rect(surface, (120, 60, 60), self.btn_admin_rect)
        txt2 = self.font_button.render("Entrar como Administrador", True, (255, 255, 255))
        surface.blit(txt2, (self.btn_admin_rect.x + 20, self.btn_admin_rect.y + 18))

