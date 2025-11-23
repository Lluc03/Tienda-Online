import pygame as pg
import pygame_gui
from .menu_gui import MenuGUI

class UIManager:
    def __init__(self, win_size):
        self.win_size = win_size
        self.ui_manager = pygame_gui.UIManager(win_size)
        self.menu_gui = MenuGUI(self.ui_manager, win_size)
        
        # =====================================================
        # Callbacks (TU LISTA + LOS NUEVOS DE TU COMPAÑERO)
        # =====================================================
        self.on_productos_click = None
        self.on_carrito_click = None
        self.on_config_click = None
        self.on_close_menu = None
        self.on_reset_camera = None
        self.on_toggle_fullscreen = None
        self.on_exit = None
        self.on_continue_shopping = None
        self.on_checkout = None
        self.on_apply_config = None

        # Añadidos por tu compañero
        self.on_cart_add_apple = None
        self.on_cart_remove_apple = None
        
        # Crear menú principal al inicio
        self.menu_gui.create_main_menu()

        self.setup_debug()

    def setup_debug(self):
        """Configuración para debug"""
        print("🎯 UIManager inicializado")
        print(f"🎯 Tamaño ventana: {self.win_size}")

    # ======================================================================
    # EVENTOS
    # ======================================================================

    def handle_ui_events(self, event):
        """Procesa eventos de UI con debug"""
        if event.type == pg.MOUSEBUTTONDOWN:
            print(f"🖱️ Mouse click en: {event.pos}")

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            ui_element = event.ui_element
            
            print(f"🔘 Botón presionado: {ui_element.text if hasattr(ui_element, 'text') else 'Sin texto'}")
            
            # -------------------------------
            # MENÚ PRINCIPAL
            # -------------------------------
            if hasattr(self.menu_gui, 'btn_productos') and ui_element == self.menu_gui.btn_productos:
                print("📦 Botón Productos presionado")
                if self.on_productos_click: self.on_productos_click()
                    
            elif hasattr(self.menu_gui, 'btn_carrito') and ui_element == self.menu_gui.btn_carrito:
                print("🛒 Botón Carrito presionado")
                if self.on_carrito_click: self.on_carrito_click()
                    
            elif hasattr(self.menu_gui, 'btn_config') and ui_element == self.menu_gui.btn_config:
                print("⚙️ Botón Configuración presionado")
                if self.on_config_click: self.on_config_click()

            elif hasattr(self.menu_gui, 'btn_close_menu') and ui_element == self.menu_gui.btn_close_menu:
                print("❌ Botón Cerrar Menú presionado")
                if self.on_close_menu: self.on_close_menu()

            # -------------------------------
            # MENÚ CONTEXTUAL
            # -------------------------------
            elif hasattr(self.menu_gui, 'btn_reset_cam') and ui_element == self.menu_gui.btn_reset_cam:
                print("🔄 Botón Reset Camera presionado")
                if self.on_reset_camera: self.on_reset_camera()
                self._close_context_menu()
                        
            elif hasattr(self.menu_gui, 'btn_fullscreen') and ui_element == self.menu_gui.btn_fullscreen:
                print("📺 Botón Toggle Fullscreen presionado")
                if self.on_toggle_fullscreen: self.on_toggle_fullscreen()
                self._close_context_menu()
                        
            elif hasattr(self.menu_gui, 'btn_exit_app') and ui_element == self.menu_gui.btn_exit_app:
                print("🚪 Botón Exit presionado")
                if self.on_exit: self.on_exit()

            # -------------------------------
            # MENÚ DE PRODUCTOS
            # -------------------------------
            elif hasattr(self.menu_gui, 'btn_close_products') and ui_element == self.menu_gui.btn_close_products:
                print("❌ Botón Cerrar Productos presionado")
                if self.on_close_menu: self.on_close_menu()

            # -------------------------------
            # MENÚ DEL CARRITO (TU + MEJORAS)
            # -------------------------------
            elif hasattr(self.menu_gui, 'btn_continue_shopping') and ui_element == self.menu_gui.btn_continue_shopping:
                print("🛍️ Botón Seguir Comprando presionado")
                if self.on_continue_shopping: self.on_continue_shopping()
                    
            elif hasattr(self.menu_gui, 'btn_checkout') and ui_element == self.menu_gui.btn_checkout:
                print("💳 Botón Checkout presionado")
                if self.on_checkout: self.on_checkout()
                    
            elif hasattr(self.menu_gui, 'btn_close_cart') and ui_element == self.menu_gui.btn_close_cart:
                print("❌ Botón Cerrar Carrito presionado")
                if self.on_close_menu: self.on_close_menu()

            # Botones específicos de carrito que añadió tu compañero
            elif hasattr(self.menu_gui, 'btn_add_apple') and ui_element == self.menu_gui.btn_add_apple:
                print("➕ Añadir manzana desde carrito")
                if self.on_cart_add_apple: self.on_cart_add_apple()

            elif hasattr(self.menu_gui, 'btn_remove_apple') and ui_element == self.menu_gui.btn_remove_apple:
                print("➖ Quitar manzana desde carrito")
                if self.on_cart_remove_apple: self.on_cart_remove_apple()

            # -------------------------------
            # MENÚ DE CONFIGURACIÓN
            # -------------------------------
            elif hasattr(self.menu_gui, 'btn_apply_config') and ui_element == self.menu_gui.btn_apply_config:
                print("✅ Botón Aplicar Configuración presionado")
                if self.on_apply_config: self.on_apply_config()
                    
            elif hasattr(self.menu_gui, 'btn_close_config') and ui_element == self.menu_gui.btn_close_config:
                print("❌ Botón Cerrar Configuración presionado")
                if self.on_close_menu: self.on_close_menu()

            # -------------------------------
            # BOTONES DE PRODUCTOS INDIVIDUALES
            # -------------------------------
            elif hasattr(self.menu_gui, 'product_buttons'):
                for i, btn in enumerate(self.menu_gui.product_buttons):
                    if ui_element == btn:
                        print(f"📦 Producto {i+1} añadido al carrito")
                        # Puedes añadir callback si quieres

    # ======================================================================
    # CONTEXT MENU
    # ======================================================================

    def _close_context_menu(self):
        """Cierra el menú contextual"""
        if self.menu_gui.context_menu:
            self.menu_gui.context_menu.kill()
            self.menu_gui.context_menu = None

    # ======================================================================
    # UPDATE & DRAW
    # ======================================================================

    def update(self, time_delta):
        self.ui_manager.update(time_delta)

    def draw_ui(self, surface):
        self.ui_manager.draw_ui(surface)

    # ======================================================================
    # MENU SHORTCUTS
    # ======================================================================

    def toggle_main_menu(self):
        return self.menu_gui.toggle_main_menu()

    def is_hovering_ui(self):
        return self.ui_manager.get_hovering_any_element()

    def show_menu(self, menu_type):
        return self.menu_gui.show_menu(menu_type)

    def hide_all_menus(self):
        self.menu_gui.hide_all_menus()

    # ======================================================================
    # CLEANUP
    # ======================================================================

    def cleanup(self):
        """Limpia recursos de UI"""
        self.menu_gui.cleanup()
        self.ui_manager.clear_and_reset()
