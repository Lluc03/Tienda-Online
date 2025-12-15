import pygame as pg
import pygame_gui

STOCK_INICIAL = 100  # stock inicial por producto


class StockWindow:
    def __init__(self, app, ui_manager):
        self.app = app
        self.ui_manager = ui_manager
        self.inputs = {}

        # Crear ventana
        self.window = pygame_gui.elements.UIWindow(
            rect=pg.Rect(250, 80, 600, 500),
            manager=ui_manager,
            window_display_title="📦 Panel de Stock Avanzado"
        )

        # Títulos de columnas
        header = [
            ("Producto", 20),
            ("Inicial", 150),
            ("Actual", 230),
            ("Vendido", 310),
            ("Nivel", 390),
            ("Modificar", 500),
        ]

        for text, xpos in header:
            pygame_gui.elements.UILabel(
                relative_rect=pg.Rect(xpos, 20, 100, 25),
                text=text,
                manager=ui_manager,
                container=self.window
            )

        # --- Listado dinámico ---
        self._populate_stock_rows()

        # --- Botones ---
        self.btn_save = pygame_gui.elements.UIButton(
            relative_rect=pg.Rect(20, 430, 200, 40),
            text="💾 Guardar cambios",
            manager=ui_manager,
            container=self.window
        )

        self.btn_reset = pygame_gui.elements.UIButton(
            relative_rect=pg.Rect(240, 430, 200, 40),
            text="🔄 Restablecer stock",
            manager=ui_manager,
            container=self.window
        )

        self.btn_close = pygame_gui.elements.UIButton(
            relative_rect=pg.Rect(460, 430, 120, 40),
            text="Cerrar",
            manager=ui_manager,
            container=self.window
        )


    def _populate_stock_rows(self):
        """Genera dinámicamente filas por producto."""
        y = 60
        self.rows = {}

        for product, actual in self.app.stock.items():

            vendido = STOCK_INICIAL - actual
            porcentaje = max(0, min(100, (actual / STOCK_INICIAL) * 100))

            # Color según nivel (semáforo)
            if porcentaje > 60:
                color = "green"
            elif porcentaje > 30:
                color = "yellow"
            else:
                color = "red"

            # PRODUCTO
            pygame_gui.elements.UILabel(
                relative_rect=pg.Rect(20, y, 120, 30),
                text=product.capitalize(),
                manager=self.ui_manager,
                container=self.window
            )

            # STOCK INICIAL
            pygame_gui.elements.UILabel(
                relative_rect=pg.Rect(150, y, 60, 30),
                text=str(STOCK_INICIAL),
                manager=self.ui_manager,
                container=self.window
            )

            # STOCK ACTUAL
            pygame_gui.elements.UILabel(
                relative_rect=pg.Rect(230, y, 60, 30),
                text=str(actual),
                manager=self.ui_manager,
                container=self.window
            )

            # VENDIDO
            pygame_gui.elements.UILabel(
                relative_rect=pg.Rect(310, y, 60, 30),
                text=str(vendido),
                manager=self.ui_manager,
                container=self.window
            )

            # BARRA DE NIVEL
            bar = pygame_gui.elements.UIProgressBar(
                relative_rect=pg.Rect(390, y, 90, 30),
                manager=self.ui_manager,
                container=self.window
            )
            bar.set_current_progress(porcentaje)
            bar.colour = pg.Color(color)

            # MODIFICAR STOCK
            input_box = pygame_gui.elements.UITextEntryLine(
                relative_rect=pg.Rect(500, y, 70, 30),
                manager=self.ui_manager,
                container=self.window
            )
            input_box.set_text(str(actual))

            self.inputs[product] = input_box

            y += 40


    def process_event(self, event):
        """Procesa clics de botones desde pygame_gui."""
        if event.type == pygame_gui.UI_BUTTON_PRESSED:

            # Cerrar ventana
            if event.ui_element == self.btn_close:
                self.window.kill()
                return

            # Guardar cambios
            if event.ui_element == self.btn_save:
                print("💾 Guardando cambios de stock...")
                for product, input_box in self.inputs.items():

                    text = input_box.get_text()
                    if text.isdigit():
                        nuevo_stock = int(text)
                        self.app.stock[product] = nuevo_stock
                        print(f"  ✓ {product}: {nuevo_stock}")
                    else:
                        print(f"⚠ Valor inválido en {product}: {text}")

                # Recargar ventana con nuevos valores
                self.window.kill()
                self.app.stock_window = StockWindow(self.app, self.ui_manager)

            # Restablecer valores
            if event.ui_element == self.btn_reset:
                print("🔄 Restableciendo stock a 100...")
                for product in self.app.stock:
                    self.app.stock[product] = STOCK_INICIAL

                self.window.kill()
                self.app.stock_window = StockWindow(self.app, self.ui_manager)
