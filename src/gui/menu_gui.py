import pygame as pg
import pygame_gui
from pygame_gui.elements import UIButton, UILabel, UIWindow, UIPanel, UITextBox


class MenuGUI:
    """Clase principal que gestiona todos los menús de la aplicación"""

    def __init__(self, ui_manager, win_size):
        self.ui_manager = ui_manager
        self.win_size = win_size

        # Menús
        self.main_menu = None
        self.context_menu = None
        self.product_menu = None
        self.cart_menu = None
        self.config_menu = None

        # Botones
        self.product_buttons = []

        # Estado
        self.current_menu = None

        # Widgets dinámicos del carrito
        self.cart_textbox = None
        self.btn_add_apple = None
        self.btn_remove_apple = None

    # ======================================================================
    #  MAIN MENU
    # ======================================================================

    def create_main_menu(self):
        """Crea el menú principal de la aplicación"""
        if self.main_menu:
            self.main_menu.kill()

        self.main_menu = UIWindow(
            rect=pg.Rect(20, 20, 300, 500),
            manager=self.ui_manager,
            window_display_title='3D Store Menu',
            object_id='#main_menu'
        )

        y_pos = 10
        spacing = 45

        # ---------------------------
        # TÍTULO
        # ---------------------------
        UILabel(
            relative_rect=pg.Rect(10, y_pos, 280, 30),
            text='Bienvenido a la Tienda 3D',
            manager=self.ui_manager,
            container=self.main_menu,
            object_id='#title_label'
        )
        y_pos += spacing

        # ---------------------------
        # BOTONES PRINCIPALES
        # ---------------------------
        self.btn_productos = UIButton(
            relative_rect=pg.Rect(10, y_pos, 280, 35),
            text='📦 Productos',
            manager=self.ui_manager,
            container=self.main_menu,
            object_id='#btn_productos'
        )
        y_pos += spacing

        self.btn_carrito = UIButton(
            relative_rect=pg.Rect(10, y_pos, 280, 35),
            text='🛒 Carrito de Compras',
            manager=self.ui_manager,
            container=self.main_menu,
            object_id='#btn_carrito'
        )
        y_pos += spacing

        self.btn_config = UIButton(
            relative_rect=pg.Rect(10, y_pos, 280, 35),
            text='⚙️ Configuración',
            manager=self.ui_manager,
            container=self.main_menu,
            object_id='#btn_config'
        )
        y_pos += spacing + 10

        # ---------------------------
        # SECCIÓN CONTROLES
        # ---------------------------
        self._create_controls_section(y_pos)

        return self.main_menu

    def _create_controls_section(self, y_pos):
        """Crea la sección de controles del menú principal"""

        UILabel(
            relative_rect=pg.Rect(10, y_pos, 280, 25),
            text='Controles de Cámara:',
            manager=self.ui_manager,
            container=self.main_menu,
            object_id='#controls_title'
        )
        y_pos += 30

        controls_text = [
            '• WASD: Movimiento',
            '• Ratón: Mirar alrededor',
            '• Click derecho: Menú contextual',
            '• M: Mostrar/ocultar menú'
        ]

        for control in controls_text:
            UILabel(
                relative_rect=pg.Rect(10, y_pos, 280, 20),
                text=control,
                manager=self.ui_manager,
                container=self.main_menu,
                object_id='#control_item'
            )
            y_pos += 25

        y_pos += 10

        # Botón cerrar
        self.btn_close_menu = UIButton(
            relative_rect=pg.Rect(10, y_pos, 280, 35),
            text='❌ Cerrar Menú (M)',
            manager=self.ui_manager,
            container=self.main_menu,
            object_id='#btn_close'
        )

    # ======================================================================
    #  CONTEXT MENU
    # ======================================================================

    def create_context_menu(self, pos):
        """Crea el menú contextual en posición específica"""
        if self.context_menu:
            self.context_menu.kill()

        x, y = pos
        self.context_menu = UIWindow(
            rect=pg.Rect(x, y, 180, 150),
            manager=self.ui_manager,
            window_display_title='Menú Rápido',
            object_id='#context_menu'
        )

        self.btn_reset_cam = UIButton(
            relative_rect=pg.Rect(5, 5, 170, 30),
            text='🔄 Reset Camera',
            manager=self.ui_manager,
            container=self.context_menu,
            object_id='#btn_reset'
        )

        self.btn_fullscreen = UIButton(
            relative_rect=pg.Rect(5, 40, 170, 30),
            text='📺 Toggle Fullscreen',
            manager=self.ui_manager,
            container=self.context_menu,
            object_id='#btn_fullscreen'
        )

        self.btn_exit_app = UIButton(
            relative_rect=pg.Rect(5, 75, 170, 30),
            text='🚪 Exit',
            manager=self.ui_manager,
            container=self.context_menu,
            object_id='#btn_exit'
        )

        return self.context_menu

    # ======================================================================
    #  PRODUCTS MENU
    # ======================================================================

    def create_products_menu(self):
        """Crea el menú de productos"""
        if self.product_menu:
            self.product_menu.kill()

        self.product_menu = UIWindow(
            rect=pg.Rect(350, 50, 400, 500),
            manager=self.ui_manager,
            window_display_title='Catálogo de Productos',
            object_id='#products_menu'
        )

        UILabel(
            relative_rect=pg.Rect(10, 10, 380, 30),
            text='Nuestros Productos 3D',
            manager=self.ui_manager,
            container=self.product_menu,
            object_id='#products_title'
        )

        products = ["Manzanas", "Leche", "Galletas", "Hamburguesas", "Pollo"]

        y_pos = 50
        self.product_buttons = []
        for i, product in enumerate(products):
            btn = UIButton(
                relative_rect=pg.Rect(10, y_pos, 380, 35),
                text=product,
                manager=self.ui_manager,
                container=self.product_menu,
                object_id=f'#product_{i}'
            )
            self.product_buttons.append(btn)
            y_pos += 45

        self.btn_close_products = UIButton(
            relative_rect=pg.Rect(10, y_pos + 10, 380, 35),
            text='Cerrar',
            manager=self.ui_manager,
            container=self.product_menu,
            object_id='#btn_close_products'
        )

        return self.product_menu

    # ======================================================================
    #  CART MENU — MERGEADO CON LAS MEJORAS DE TU COMPAÑERO
    # ======================================================================

    def create_cart_menu(self):
        """Crea el menú del carrito de compras (versión mejorada mergeada)"""
        if self.cart_menu:
            self.cart_menu.kill()

        self.cart_menu = UIWindow(
            rect=pg.Rect(350, 50, 400, 400),
            manager=self.ui_manager,
            window_display_title='Carrito de Compras',
            object_id='#cart_menu'
        )

        # -----------------------------
        # TEXTBOX DINÁMICO DEL CARRITO
        # -----------------------------
        self.cart_textbox = UITextBox(
            relative_rect=pg.Rect(10, 10, 380, 220),
            html_text="<b>Tu carrito está vacío</b>",
            manager=self.ui_manager,
            container=self.cart_menu,
            object_id='#cart_content'
        )

        # -----------------------------
        # BOTONES + / - PARA AJUSTAR CANTIDADES
        # -----------------------------
        self.btn_remove_apple = UIButton(
            relative_rect=pg.Rect(250, 40, 30, 30),
            text='−',
            manager=self.ui_manager,
            container=self.cart_menu,
            object_id='#btn_remove_apple'
        )

        self.btn_add_apple = UIButton(
            relative_rect=pg.Rect(290, 40, 30, 30),
            text='+',
            manager=self.ui_manager,
            container=self.cart_menu,
            object_id='#btn_add_apple'
        )

        # Inicialmente ocultos
        self.btn_remove_apple.hide()
        self.btn_add_apple.hide()

        # -----------------------------
        # BOTONES DEL CARRITO
        # -----------------------------
        self.btn_continue_shopping = UIButton(
            relative_rect=pg.Rect(10, 285, 185, 35),
            text='Seguir Comprando',
            manager=self.ui_manager,
            container=self.cart_menu,
            object_id='#btn_continue_shopping'
        )

        self.btn_checkout = UIButton(
            relative_rect=pg.Rect(205, 285, 185, 35),
            text='Checkout',
            manager=self.ui_manager,
            container=self.cart_menu,
            object_id='#btn_checkout'
        )

        self.btn_close_cart = UIButton(
            relative_rect=pg.Rect(10, 330, 380, 35),
            text='Cerrar Carrito',
            manager=self.ui_manager,
            container=self.cart_menu,
            object_id='#btn_close_cart'
        )

        return self.cart_menu

    # ----------------------------------------------------------------------
    #  MÉTODO NUEVO (HEREDADO DE TU COMPAÑERO)
    # ----------------------------------------------------------------------

    def update_cart_display(self, cart_dict):
        """
        Actualiza el contenido textual del carrito a partir de un dict {product_type: qty}.
        Controla también la visibilidad de los botones +/-.
        """
        total_items = sum(cart_dict.values()) if cart_dict else 0

        if total_items == 0:
            html = "<b>Tu carrito está vacío</b>"

            if self.btn_add_apple:
                self.btn_add_apple.hide()
            if self.btn_remove_apple:
                self.btn_remove_apple.hide()

        else:
            html = "<b>Contenido del carrito:</b><br>"
            qty_apple = cart_dict.get("apple", 0)

            if qty_apple > 0:
                html += f"- Manzana: {qty_apple} ud.<br>"

            html += f"<br><i>Total de artículos: {total_items}</i>"

            self.btn_add_apple.show()
            self.btn_remove_apple.show()

        if self.cart_textbox:
            self.cart_textbox.set_text(html)

    # ======================================================================
    #  CONFIG MENU
    # ======================================================================

    def create_config_menu(self):
        """Crea el menú de configuración"""
        if self.config_menu:
            self.config_menu.kill()

        self.config_menu = UIWindow(
            rect=pg.Rect(350, 50, 400, 450),
            manager=self.ui_manager,
            window_display_title='Configuración',
            object_id='#config_menu'
        )

        y_pos = 10

        UILabel(
            relative_rect=pg.Rect(10, y_pos, 380, 25),
            text='Configuración de Gráficos:',
            manager=self.ui_manager,
            container=self.config_menu,
            object_id='#graphics_title'
        )
        y_pos += 30

        config_options = [
            ("Calidad de Texturas", ["Baja", "Media", "Alta"]),
            ("Resolución", ["1280x720", "1920x1080", "2560x1440"]),
            ("Sombras", ["Desactivadas", "Activadas"]),
            ("Anti-aliasing", ["Off", "2x", "4x", "8x"]),
        ]

        for option_name, options in config_options:
            UILabel(
                relative_rect=pg.Rect(10, y_pos, 180, 25),
                text=option_name,
                manager=self.ui_manager,
                container=self.config_menu,
                object_id=f'#label_{option_name.lower()}'
            )
            y_pos += 30

        self.btn_apply_config = UIButton(
            relative_rect=pg.Rect(10, y_pos + 20, 185, 35),
            text='Aplicar Cambios',
            manager=self.ui_manager,
            container=self.config_menu,
            object_id='#btn_apply_config'
        )

        self.btn_close_config = UIButton(
            relative_rect=pg.Rect(205, y_pos + 20, 185, 35),
            text='Cerrar',
            manager=self.ui_manager,
            container=self.config_menu,
            object_id='#btn_close_config'
        )

        return self.config_menu

    # ======================================================================
    #  MENU HANDLING
    # ======================================================================

    def show_menu(self, menu_type):
        """Muestra un menú específico"""
        self.hide_all_menus()

        if menu_type == "main":
            self.current_menu = self.main_menu
            if self.main_menu:
                self.main_menu.show()

        elif menu_type == "products":
            self.current_menu = self.create_products_menu()

        elif menu_type == "cart":
            self.current_menu = self.create_cart_menu()

        elif menu_type == "config":
            self.current_menu = self.create_config_menu()

        return self.current_menu

    def hide_all_menus(self):
        """Oculta todos los menús"""
        for menu in [
            self.main_menu, self.context_menu, self.product_menu,
            self.cart_menu, self.config_menu
        ]:
            if menu:
                menu.hide()

    # ----------------------------------------------------------------------
    #  toggle_main_menu — FUNCIÓN MEJORADA (MERGE)
    # ----------------------------------------------------------------------

    def toggle_main_menu(self):
        """
        Alterna la visibilidad del menú principal.
        Incluye manejo especial si la ventana fue destruida con kill().
        """
        # Si la ventana ya no existe o está "muerta", recrearla
        if self.main_menu is None or not self.main_menu.alive():
            self.main_menu = self.create_main_menu()
            self.main_menu.show()
            return True

        # Alternar visibilidad
        if self.main_menu.visible:
            self.main_menu.hide()
            return False
        else:
            self.main_menu.show()
            return True

    # ======================================================================
    #  CLEANUP
    # ======================================================================

    def cleanup(self):
        """Limpia todos los recursos de UI"""
        for menu in [
            self.main_menu, self.context_menu, self.product_menu,
            self.cart_menu, self.config_menu
        ]:
            if menu:
                menu.kill()
