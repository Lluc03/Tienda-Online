#!/usr/bin/env python3
"""
Main entry point for the 3D store application
"""
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.graphics_engine import GraphicsEngine

def main():
    """Función principal de la aplicación"""
    try:
        # Crear y ejecutar el motor gráfico
        engine = GraphicsEngine()
        
        print("🚀 Aplicación 3D Store iniciada correctamente")
        print("=" * 50)
        print("Controles:")
        print("• M: Mostrar/ocultar menú principal")
        print("• Click derecho: Menú contextual") 
        print("• Click izquierdo + arrastrar: Controlar cámara")
        print("• WASD/Flechas: Movimiento de cámara")
        print("• ESC: Salir de la aplicación")
        print("=" * 50)
        
        # Ejecutar loop principal
        engine.run()
        
    except Exception as e:
        print(f"❌ Error al iniciar la aplicación: {e}")
        import traceback
        traceback.print_exc()
        input("Presiona Enter para salir...")
        sys.exit(1)

if __name__ == "__main__":
    main()