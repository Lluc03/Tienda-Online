import pygame as pg
import pygame_gui

class ZoneTimeSelector:
    def __init__(self, app, ui):
        self.app = app
        self.ui = ui

        self.window = pygame_gui.elements.UIWindow(
            rect=pg.Rect(300, 200, 500, 250),
            manager=self.ui,
            window_display_title="Tiempo por zonas"
        )

        pygame_gui.elements.UILabel(
            pg.Rect(20, 20, 450, 30),
            "Introduce nº usuario o 0 para global:",
            manager=self.ui,
            container=self.window
        )

        self.input = pygame_gui.elements.UITextEntryLine(
            pg.Rect(20, 60, 450, 35),
            manager=self.ui,
            container=self.window
        )

        self.ok = pygame_gui.elements.UIButton(
            pg.Rect(20, 120, 200, 40),
            text="Generar",
            manager=self.ui,
            container=self.window
        )

        self.cancel = pygame_gui.elements.UIButton(
            pg.Rect(250, 120, 200, 40),
            text="Cancelar",
            manager=self.ui,
            container=self.window
        )

    def process_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.cancel:
                self.window.kill()

            elif event.ui_element == self.ok:
                v = self.input.get_text()
                if not v.isdigit():
                    print("❌ Entrada no válida.")
                    return

                idx = int(v)
                self.window.kill()
                self.app.analytics.generate_zone_time(idx)
