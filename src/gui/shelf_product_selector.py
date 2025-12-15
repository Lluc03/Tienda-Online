import pygame as pg
import pygame_gui

class ShelfProductSelector:
    def __init__(self, app, ui_manager, csv_file, user_index):
        self.app = app
        self.ui_manager = ui_manager
        self.csv_file = csv_file      # None = GLOBAL
        self.selected_user_index = user_index

        self.window = pygame_gui.elements.UIWindow(
            rect=pg.Rect(350, 200, 500, 360),
            manager=ui_manager,
            window_display_title="Seleccionar producto"
        )

        pygame_gui.elements.UILabel(
            relative_rect=pg.Rect(20, 20, 460, 30),
            text="Selecciona un producto:",
            manager=ui_manager,
            container=self.window
        )

        # OPCIONS = productes del stock
        product_list = list(app.stock.keys())

        self.dropdown = pygame_gui.elements.UIDropDownMenu(
            options_list=product_list,
            starting_option=product_list[0],
            relative_rect=pg.Rect(20, 70, 460, 40),
            manager=ui_manager,
            container=self.window
        )

        self.ok = pygame_gui.elements.UIButton(
            relative_rect=pg.Rect(20, 150, 200, 40),
            text="Generar histograma",
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
        if event.type == pygame_gui.UI_BUTTON_PRESSED:

            # CERRAR
            if event.ui_element == self.cancel:
                self.window.kill()
                return

            # GENERAR HISTOGRAMA
            if event.ui_element == self.ok:

                raw = self.dropdown.selected_option
                product = raw[0] if isinstance(raw, tuple) else raw

                print(f"📊 Generando histograma para producto '{product}'")
                self.window.kill()

                # GLOBAL
                if self.selected_user_index == 0:
                    self.app.analytics.generate_shelf_histogram_for_product(
                        product, 
                        filepath=None
                    )

                # USUARIO INDIVIDUAL
                else:
                    self.app.analytics.generate_shelf_histogram_for_product(
                        product, 
                        filepath=self.csv_file
                    )
