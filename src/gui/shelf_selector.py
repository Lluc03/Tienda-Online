import pygame as pg
import pygame_gui
import glob
import os

class ShelfSelector:
    def __init__(self, app, ui_manager):
        self.app = app
        self.ui_manager = ui_manager

        self.window = pygame_gui.elements.UIWindow(
            rect=pg.Rect(350, 200, 500, 260),
            manager=ui_manager,
            window_display_title="Estadísticas por estantería"
        )

        pygame_gui.elements.UILabel(
            relative_rect=pg.Rect(20, 20, 460, 30),
            text="Número de usuario (0 = global):",
            manager=ui_manager,
            container=self.window
        )

        self.input_box = pygame_gui.elements.UITextEntryLine(
            relative_rect=pg.Rect(20, 60, 460, 35),
            manager=ui_manager,
            container=self.window
        )

        self.ok = pygame_gui.elements.UIButton(
            relative_rect=pg.Rect(20, 120, 200, 40),
            text="Generar",
            manager=ui_manager,
            container=self.window
        )

        self.cancel = pygame_gui.elements.UIButton(
            relative_rect=pg.Rect(240, 120, 200, 40),
            text="Cancelar",
            manager=ui_manager,
            container=self.window
        )

    def process_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:

            if event.ui_element == self.cancel:
                self.window.kill()
                return

            if event.ui_element == self.ok:
                text = self.input_box.get_text()
                if not text.isdigit():
                    print("❌ Solo números")
                    return

                idx = int(text)
                self.window.kill()

                # Llamar al AnalyticsManager
                self.app.analytics.generate_shelf_histogram(idx)
