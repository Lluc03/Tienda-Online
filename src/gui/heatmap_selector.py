import pygame as pg
import pygame_gui
import os
import glob

class HeatmapUserSelector:
    def __init__(self, app, ui_manager):
        self.app = app
        self.ui_manager = ui_manager

        self.window = pygame_gui.elements.UIWindow(
            rect=pg.Rect(300, 200, 500, 260),
            manager=ui_manager,
            window_display_title="Generar Heatmap"
        )

        self.label = pygame_gui.elements.UILabel(
            relative_rect=pg.Rect(20, 20, 460, 25),
            text="Introduce el número de usuario o 0 para global:",
            manager=ui_manager,
            container=self.window
        )

        # Entrada de texto
        self.input_box = pygame_gui.elements.UITextEntryLine(
            relative_rect=pg.Rect(20, 60, 460, 35),
            manager=ui_manager,
            container=self.window
        )

        # Botón confirmar
        self.btn_ok = pygame_gui.elements.UIButton(
            relative_rect=pg.Rect(20, 120, 200, 40),
            text="Generar Heatmap",
            manager=ui_manager,
            container=self.window
        )

        # Botón cancelar
        self.btn_cancel = pygame_gui.elements.UIButton(
            relative_rect=pg.Rect(240, 120, 200, 40),
            text="Cancelar",
            manager=ui_manager,
            container=self.window
        )

    def process_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.btn_cancel:
                self.window.kill()

            elif event.ui_element == self.btn_ok:
                value = self.input_box.get_text()

                if not value.isdigit():
                    print("❌ Entrada no válida (solo números).")
                    return

                user_index = int(value)
                self.window.kill()

                # Pedir al Analytics Manager que genere el heatmap
                self.app.analytics.generate_heatmap_interactive_direct(user_index)
