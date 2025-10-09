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
    """Main function"""
    try:
        app = GraphicsEngine()
        app.run()
    except Exception as e:
        print(f"Error running application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()