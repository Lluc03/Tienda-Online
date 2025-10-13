#!/usr/bin/env python3
"""
Main entry point for the 3D store application
"""
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.graphics_engine import GraphicsEngine
from src.gui.menu_gui import GUIManager

def main():
    # Crear motor gráfico
    engine = GraphicsEngine()
    
    # ✅ CREAR Y CONECTAR EL GUI MANAGER
    gui_manager = GUIManager(engine.WIN_SIZE)
    engine.set_gui_manager(gui_manager)
    
    print("🚀 Aplicación iniciada - Haz clic derecho para abrir el menú")
    
    # Ejecutar aplicación
    engine.run()

if __name__ == "__main__":
    main()