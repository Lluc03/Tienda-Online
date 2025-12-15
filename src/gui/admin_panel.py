import pygame as pg

class AdminPanel:
    def __init__(self, app):
        self.app = app
        self.font = pg.font.SysFont("Arial", 28)
        self.visible = True

    def render(self, screen):
        screen.fill((15, 15, 15))

        title = self.font.render("Panel Administrador", True, (255, 255, 0))
        screen.blit(title, (100, 50))

        screen.blit(self.font.render("[H] Heatmap de usuarios", True, (255,255,255)), (100, 150))
        screen.blit(self.font.render("[S] Productos más visitados", True, (255,255,255)), (100, 200))
        screen.blit(self.font.render("[T] Tiempo por zonas", True, (255,255,255)), (100, 250))
        screen.blit(self.font.render("[K] Ver stock", True, (255,255,255)), (100, 300))
        screen.blit(self.font.render("[E] Visitas por estantería", True, (255,255,255)), (100, 350))
        screen.blit(self.font.render("[L] Modo Login", True, (255,255,255)), (100, 400))



    def handle_event(self, event):
        if event.type == pg.KEYDOWN:

            if event.key == pg.K_h:
                print("📊 Abrir selector de heatmap")
                from src.gui.heatmap_selector import HeatmapUserSelector
                self.app.heatmap_selector = HeatmapUserSelector(self.app, self.app.ui_manager.ui_manager)


            if event.key == pg.K_s:
                self.app.analytics.show_product_stats()

            if event.key == pg.K_t:
                from src.gui.zone_selector import ZoneTimeSelector
                self.app.zone_selector = ZoneTimeSelector(self.app, self.app.ui_manager.ui_manager)

            if event.key == pg.K_e:
                print("📊 Selector de usuario para análisis por estantería")
                from src.gui.shelf_user_selector import ShelfUserSelector
                self.app.shelf_user_selector = ShelfUserSelector(self.app, self.app.ui_manager.ui_manager)


            if event.key == pg.K_k:
                print("📦 Abriendo panel de stock")
                from src.gui.stock_window import StockWindow
                self.app.stock_window = StockWindow(self.app, self.app.ui_manager.ui_manager)

