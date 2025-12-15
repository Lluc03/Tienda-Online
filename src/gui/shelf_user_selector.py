import pygame as pg
import pygame_gui
import glob
import os

class ShelfUserSelector:
    def __init__(self, app, ui_manager):
        self.app = app
        self.ui_manager = ui_manager

        self.window = pygame_gui.elements.UIWindow(
            rect=pg.Rect(350, 200, 500, 360),
            manager=ui_manager,
            window_display_title="Seleccionar usuario"
        )

        pygame_gui.elements.UILabel(
            relative_rect=pg.Rect(20, 20, 460, 30),
            text="Selecciona un usuario o GLOBAL:",
            manager=ui_manager,
            container=self.window
        )

        # ===== LISTA DE CSV =====
        csv_files = sorted(glob.glob(os.path.join(app.analytics.save_dir, "*.csv")))
        self.files = csv_files

        options = ["GLOBAL (todos)"]
        for i, f in enumerate(csv_files, 1):
            options.append(f"Usuario {i}: {os.path.basename(f)}")

        self.dropdown = pygame_gui.elements.UIDropDownMenu(
            options_list=options,
            starting_option=options[0],
            relative_rect=pg.Rect(20, 70, 460, 40),
            manager=ui_manager,
            container=self.window
        )

        # ===== BOTONES =====
        self.ok = pygame_gui.elements.UIButton(
            relative_rect=pg.Rect(20, 150, 200, 40),
            text="Siguiente",
            manager=ui_manager,
            container=self.window
        )

        self.cancel = pygame_gui.elements.UIButton(
            relative_rect=pg.Rect(240, 150, 200, 40),
            text="Cancelar",
            manager=ui_manager,
            container=self.window
        )


    def process_event(self, event):
        """Gestiona los eventos del selector de usuario para análisis de estanterías."""

        if event.type == pygame_gui.UI_BUTTON_PRESSED:

            # --------------------------
            # BOTÓN CANCELAR
            # --------------------------
            if event.ui_element == self.cancel:
                self.window.kill()
                return

            # --------------------------
            # BOTÓN SIGUIENTE
            # --------------------------
            if event.ui_element == self.ok:

                raw = self.dropdown.selected_option
                option = raw[0] if isinstance(raw, tuple) else raw

                # ===========================
                # CASO GLOBAL
                # ===========================
                if option.startswith("GLOBAL"):
                    self.selected_user_index = 0
                    filepath = None

                else:
                    # Ejemplo: "Usuario 2: usuario_20250201_142030.csv"
                    try:
                        num = option.split("Usuario ")[1].split(":")[0]
                        self.selected_user_index = int(num)
                        filepath = self.files[self.selected_user_index - 1]
                    except Exception as e:
                        print("❌ Error interpretando la selección:", e)
                        return

                # ===========================
                # ABRIR SELECTOR DE PRODUCTOS
                # ===========================
                from src.gui.shelf_product_selector import ShelfProductSelector

                self.app.shelf_product_selector = ShelfProductSelector(
                    self.app,
                    self.ui_manager,
                    filepath,                 # csv del usuario o None
                    self.selected_user_index  # ✔ NECESARIO
                )

                self.window.kill()
                return
