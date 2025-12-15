"""
Sistema de analíticas completo para el panel de administrador
Combina tracking en CSV + analíticas en tiempo real
Guarda en: src/system/analytics.py
"""

import csv
import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import pygame
from datetime import datetime
from collections import defaultdict

# ============================================================
# LÍMITES DE LA TIENDA (Configurable)
# ============================================================
STORE_BOUNDS = {
    "x_min": -30.0,
    "x_max": 30.0,
    "z_min": -30.0,
    "z_max": 30.0
}

# ============================================================
# DEFINICIÓN DE ZONAS (4 zonas)
# Todo el supermercado dividido por áreas simples.
# ============================================================

ZONES = {
    "entrada":  {"xmin": 2, "xmax": 10, "zmin": -9, "zmax": 10},
    "comida":   {"xmin": -8, "xmax": 2, "zmin": -9, "zmax": 10},
    "bebida":   {"xmin": -25, "xmax": -8, "zmin": -25, "zmax": -9},
    "otros":    {"xmin": -25, "xmax": -8, "zmin": -9, "zmax": 10},
}

class AnalyticsManager:
    def __init__(self, save_dir="analytics_data", app=None):
        self.save_dir = save_dir
        self.app = app
        os.makedirs(save_dir, exist_ok=True)
        
        # Tracking de sesión actual (CSV)
        self.active_tracking = None
        self.current_username = None
        
        # Analytics en tiempo real (RAM)
        self.user_positions = []
        self.product_visits = defaultdict(int)
        self.zone_times = defaultdict(float)
        self.current_zone = None
        self.zone_enter_time = None
        self.session_start_time = None
        
        # ⭐ NUEVO: Control de hover único
        self.last_hovered_product = None
        self.last_hovered_shelf = None
        self.hover_recorded = False  # Flag para evitar múltiples registros
        
        print(f"✅ Analytics inicializado en: {self.save_dir}")

    # ============================================================
    # GESTIÓN DE SESIONES
    # ============================================================

    def start_user_session(self, username):
        """Inicia una nueva sesión de tracking para un usuario"""
        # Cerrar sesión anterior si existe
        if self.active_tracking:
            self.end_user_session()
        
        self.current_username = username
        self.session_start_time = datetime.now()
        
        # Crear archivo CSV para esta sesión
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{username}_{timestamp}.csv"
        self.active_tracking = os.path.join(self.save_dir, filename)
        
        with open(self.active_tracking, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["time", "x", "y", "z", "product", "zone", "shelf"])
        
        # Reset analytics en RAM
        self.user_positions = []
        self.product_visits = defaultdict(int)
        self.zone_times = defaultdict(float)
        self.current_zone = None
        self.zone_enter_time = datetime.now()
        
        print(f"📊 Sesión iniciada para: {username}")
        print(f"   Archivo: {filename}")

    def end_user_session(self):
        """Finaliza la sesión actual y guarda estadísticas"""
        if not self.active_tracking:
            return
        
        # Cerrar zona actual
        if self.current_zone and self.zone_enter_time:
            elapsed = (datetime.now() - self.zone_enter_time).total_seconds()
            self.zone_times[self.current_zone] += elapsed
        
        # Mostrar resumen de sesión
        session_duration = (datetime.now() - self.session_start_time).total_seconds()
        print("\n" + "="*60)
        print(f"📊 FIN DE SESIÓN - {self.current_username}")
        print("="*60)
        print(f"⏱️  Duración: {int(session_duration // 60)}m {int(session_duration % 60)}s")
        print(f"📍 Posiciones registradas: {len(self.user_positions)}")
        print(f"🛒 Productos visitados: {sum(self.product_visits.values())}")
        print("="*60 + "\n")
        
        self.active_tracking = None
        self.current_username = None

    # ============================================================
    # TRACKING EN TIEMPO REAL
    # ============================================================

    # ============================================================
    # REEMPLAZAR método record COMPLETO
    # ============================================================

    def record(self, cam_pos, product=None):
        if not self.active_tracking:
            return

        # ⛔️ (IMPORTANTE) DESACTIVAMOS el filtro de límites
        # if not self._is_within_bounds(cam_pos):
        #     return

        current_time = pygame.time.get_ticks() / 1000.0

        # --------------------------
        # ZONA
        # --------------------------
        zone = self._get_zone_from_position(cam_pos)

        # --------------------------
        # PRODUCTO / ESTANTERÍA
        # --------------------------
        shelf = None

        if self.app.hover_instance_data:
            y = self.app.hover_instance_data["pos"][1]
            shelf = self.get_shelf_from_y(y)

        # --------------------------
        # ⭐ ESCRIBIR SIEMPRE (CLAVE)
        # --------------------------
        with open(self.active_tracking, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                current_time,
                cam_pos.x,
                cam_pos.y,
                cam_pos.z,
                product,
                zone,
                shelf
            ])

        # --------------------------
        # RAM (opcional, pero útil)
        # --------------------------
        self.user_positions.append({
            "time": current_time,
            "x": cam_pos.x,
            "y": cam_pos.y,
            "z": cam_pos.z,
            "zone": zone,
            "product": product,
            "shelf": shelf
        })

        # --------------------------
        # CONTADOR DE PRODUCTOS
        # --------------------------
        if product:
            self.product_visits[product] += 1




    # ============================================================
    # MÉTODO AUXILIAR: Reset hover al cambiar de zona
    # ============================================================

    def reset_hover_tracking(self):
        """Resetea el tracking de hover cuando el usuario se mueve significativamente."""
        self.last_hovered_product = None
        self.hover_recorded = False



    def _is_within_bounds(self, pos):
        """Verifica si la posición está dentro de los límites de la tienda."""
        return (STORE_BOUNDS["x_min"] <= pos.x <= STORE_BOUNDS["x_max"] and
                STORE_BOUNDS["z_min"] <= pos.z <= STORE_BOUNDS["z_max"])

    def _get_zone_from_position(self, pos):
        """Determina zona según áreas definidas en ZONES."""
        x, z = pos.x, pos.z
        for zone_name, bounds in ZONES.items():
            if (
                bounds["xmin"] <= x <= bounds["xmax"] and
                bounds["zmin"] <= z <= bounds["zmax"]
            ):
                return zone_name
        return "sin_clasificar"
    
    def get_shelf_from_instance(self, instance_id):
        """Devuelve estante 1–4 según el instance_id."""
        if instance_id is None or instance_id < 0:
            return None

        # 20 instancias por estante
        shelf_size = 20
        return (instance_id // shelf_size) + 1
    
    def generate_shelf_histogram_for_product(self, product_name, filepath=None):
        """
        Genera histograma de visitas por estantería
        - Si filepath es None → GLOBAL
        - Si es un CSV concreto → análisis por usuario
        """
        import pandas as pd
        import matplotlib.pyplot as plt
        import glob
        import os

        visits = {1: 0, 2: 0, 3: 0, 4: 0}
        files = []

        # GLOBAL
        if filepath is None:
            files = sorted(glob.glob(os.path.join(self.save_dir, "*.csv")))
            title = f"Visitas por estantería — GLOBAL — {product_name}"
        else:
            files = [filepath]
            title = f"Visitas por estantería — {os.path.basename(filepath)} — {product_name}"

        # === PROCESSAR CSVs ===
        for f in files:
            try:
                df = pd.read_csv(f)
            except:
                continue

            if "product" not in df.columns or "shelf" not in df.columns:
                continue

            df = df[df["product"] == product_name]
            df = df.dropna(subset=["shelf"])

            for shelf in df["shelf"]:
                try:
                    shelf = int(shelf)
                    if shelf in visits:
                        visits[shelf] += 1
                except:
                    pass

        # === PREPARAR GRÀFIC ===
        shelves = [1, 2, 3, 4]  # Ordre natural: 1 abaix → 4 adalt
        counts = [visits[s] for s in shelves]

        plt.figure(figsize=(9, 5))
        plt.barh(shelves, counts, color="#ff9933")

        plt.xlabel("Número de visitas")
        plt.ylabel("Estantería (1 = abajo, 4 = arriba)")
        plt.title(title)

        # Escriure valors al costat de cada barra
        for s, c in zip(shelves, counts):
            plt.text(c + 0.2, s, str(c), va="center")

        # ✔ NO invertir eix Y → 1 abaix, 4 adalt
        plt.yticks([1, 2, 3, 4], ["1", "2", "3", "4"])

        plt.tight_layout()
        plt.show()



    def generate_shelf_histogram(self, user_index):
        """Muestra un histograma de qué estanterías reciben más visitas."""

        files = sorted(glob.glob(os.path.join(self.save_dir, "*.csv")))
        if not files:
            print("⚠ No hay CSVs")
            return

        # --------------------
        # GLOBAL
        # --------------------
        if user_index == 0:
            dfs = []
            for f in files:
                df = pd.read_csv(f)
                if "shelf" in df.columns:
                    dfs.append(df)
            if not dfs:
                print("⚠ No hay datos de estanterías")
                return
            df = pd.concat(dfs, ignore_index=True)
            title = "Visitas por Estantería — GLOBAL"

        # --------------------
        # INDIVIDUAL
        # --------------------
        elif 1 <= user_index <= len(files):
            df = pd.read_csv(files[user_index - 1])
            title = f"Visitas por Estantería — Usuario {user_index}"
        else:
            print("❌ Número fuera de rango")
            return

        if "shelf" not in df.columns:
            print("⚠ El CSV no contiene información de estantería")
            return

        df = df.dropna(subset=["shelf"])

        counts = df["shelf"].value_counts().sort_index()

        # --------------------
        # Mostrar gráfico
        # --------------------
        plt.figure(figsize=(8,5))
        plt.bar(counts.index.astype(int), counts.values, color="orange")
        plt.xlabel("Estantería (1 = abajo, 4 = arriba)")
        plt.ylabel("Visitas registradas")
        plt.title(title)
        plt.xticks([1,2,3,4])
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()


    # ============================================================
    # ESTADÍSTICAS GLOBALES (TODOS LOS USUARIOS)
    # ============================================================

    @staticmethod
    def make_transparent_cmap(base_cmap="YlOrRd"):
        """Colormap transparente donde los valores bajos son invisibles y los altos rojo intenso."""
        import matplotlib.colors as mcolors
        cmap = plt.get_cmap(base_cmap)
        cmap_colors = cmap(np.arange(cmap.N))

        # Hacer totalmente transparente el valor más bajo (fondo)
        cmap_colors[0, -1] = 0.0  

        return mcolors.LinearSegmentedColormap.from_list(
            "transparent_" + base_cmap,
            cmap_colors
        )

    
    def get_shelf_from_y(self, y):
        """
        Clasifica estantería según altura Y.
        Ajustado según valores reales: Y=1.850 y Y=2.650 son estanterías diferentes.
        """
        if y is None:
            return None
        
        # Rangos ampliados para 4 estanterías
        if y < 0.8:      # Estantería 1 (muy baja)
            return 1
        elif y < 1.6:    # Estantería 2 (baja-media)
            return 2
        elif y < 2.4:    # Estantería 3 (media-alta) ← Y=1.850 cae aquí
            return 3
        else:            # Estantería 4 (muy alta) ← Y=2.650 cae aquí
            return 4


    def generate_heatmap_interactive(self):
        """
        Pregunta al usuario qué heatmap desea generar:
        - Global
        - O uno específico por número de archivo CSV
        """
        files = sorted(glob.glob(os.path.join(self.save_dir, "*.csv")))

        if not files:
            print("⚠ No hay datos disponibles para generar heatmaps.")
            return

        print("\n📁 Archivos de sesión encontrados:")
        for i, f in enumerate(files, start=1):
            print(f"  {i}. {os.path.basename(f)}")

        print("\n👉 Selecciona el número de usuario para generar su heatmap individual.")
        print("👉 O introduce '0' para generar el heatmap GLOBAL.")
        
        try:
            choice = int(input("\nNúmero de usuario (0 = global): "))
        except:
            print("❌ Entrada no válida.")
            return

        if choice == 0:
            print("\n🌍 Generando heatmap GLOBAL...")
            self.generate_heatmap_all_users()
            return

        if 1 <= choice <= len(files):
            selected_file = files[choice - 1]
            print(f"\n👤 Generando heatmap del usuario: {os.path.basename(selected_file)}")
            self.generate_heatmap_single_user(selected_file)
        else:
            print("❌ Selección fuera de rango.")

    def generate_heatmap_interactive_direct(self, index):
        """Genera heatmap según un índice recibido desde UI (0 = global)."""
        files = sorted(glob.glob(os.path.join(self.save_dir, "*.csv")))

        if not files:
            print("⚠ No hay archivos CSV.")
            return

        if index == 0:
            self.generate_heatmap_all_users()
            return

        if 1 <= index <= len(files):
            filepath = files[index - 1]
            print(f"👤 Generando heatmap del usuario {index}: {filepath}")
            self.generate_heatmap_single_user(filepath)
            return

        print("❌ Número fuera de rango.")


    def generate_heatmap_single_user(self, filepath):
        """Genera un heatmap solo para un usuario (archivo CSV específico)."""
        import pandas as pd
        import matplotlib.pyplot as plt
        import numpy as np
        import os

        # ============================================================
        # 0) Verificar y generar mapa cenital si no existe
        # ============================================================
        map_path = "src/analytics/top_view.png"
        
        if not os.path.exists(map_path):
            print("⚠️ No existe el mapa cenital. Generándolo automáticamente...")
            self._generate_topdown_map_from_analytics(map_path)

        try:
            df = pd.read_csv(filepath)
        except Exception as e:
            print(f"❌ No se pudo leer {filepath}: {e}")
            return

        if df.empty:
            print("⚠ El archivo está vacío, no se puede generar heatmap.")
            return

        df = df.dropna(subset=['x', 'z'])
        
        # ===== FILTRAR DATOS FUERA DE LÍMITES =====
        df = df[
            (df['x'] >= STORE_BOUNDS['x_min']) & (df['x'] <= STORE_BOUNDS['x_max']) &
            (df['z'] >= STORE_BOUNDS['z_min']) & (df['z'] <= STORE_BOUNDS['z_max'])
        ]
        
        if df.empty:
            print("⚠ No hay datos dentro de los límites de la tienda.")
            return
        
        x, z = df['x'].values, df['z'].values

        # Renderizar el heatmap sobre el mapa cenital
        fig, ax = plt.subplots(figsize=(12, 8))

        # Cargar mapa cenital generado
        if os.path.exists(map_path):
            try:
                bg = plt.imread(map_path)
                ax.imshow(bg,
                        extent=[STORE_BOUNDS['x_min'], STORE_BOUNDS['x_max'], 
                               STORE_BOUNDS['z_min'], STORE_BOUNDS['z_max']],
                        origin="lower",
                        aspect='auto',
                        alpha=1.0,
                        zorder=1)
                print(f"🗺️ Mapa cenital cargado: {map_path}")
            except Exception as e:
                print(f"⚠ Error cargando mapa: {e}")
                ax.set_facecolor('#2a2a2a')
        else:
            print(f"⚠ No se pudo generar el mapa cenital")
            ax.set_facecolor('#2a2a2a')

        from scipy.ndimage import gaussian_filter

        H, xe, ze = np.histogram2d(
            x, z, bins=120,
            range=[[STORE_BOUNDS['x_min'], STORE_BOUNDS['x_max']],
                [STORE_BOUNDS['z_min'], STORE_BOUNDS['z_max']]]
        )

        H = gaussian_filter(H, sigma=2.5)


        transparent_hot = AnalyticsManager.make_transparent_cmap("YlOrRd")
        
        im = ax.imshow(H.T,
                extent=[STORE_BOUNDS['x_min'], STORE_BOUNDS['x_max'], 
                       STORE_BOUNDS['z_min'], STORE_BOUNDS['z_max']],
                origin="lower",
                cmap=transparent_hot,
                aspect='auto',
                alpha=0.7,
                zorder=2)

        ax.set_title(f"Heatmap Usuario — {os.path.basename(filepath)}", fontsize=14, pad=20)
        ax.set_xlabel("X", fontsize=12)
        ax.set_ylabel("Z", fontsize=12)
        plt.colorbar(im, ax=ax, label="Intensidad")
        ax.set_xlim(STORE_BOUNDS['x_min'], STORE_BOUNDS['x_max'])
        ax.set_ylim(STORE_BOUNDS['z_min'], STORE_BOUNDS['z_max'])
        plt.tight_layout()
        plt.show()


    def generate_heatmap_all_users(self):
        """Genera un heatmap global combinando todas las sesiones."""

        import pandas as pd
        import numpy as np
        import matplotlib.pyplot as plt
        import os

        # ============================================================
        # 0) Verificar y generar mapa cenital si no existe
        # ============================================================
        map_path = "src/analytics/top_view.png"
        
        if not os.path.exists(map_path):
            print("⚠️ No existe el mapa cenital. Generándolo automáticamente...")
            self._generate_topdown_map_from_analytics(map_path)
        
        # ============================================================
        # 1) Cargar CSVs
        # ============================================================
        files = glob.glob(os.path.join(self.save_dir, "*.csv"))

        if not files:
            print("⚠️ No hay archivos CSV para generar heatmap.")
            return

        dfs = []
        for f in files:
            try:
                df = pd.read_csv(f)
                if not df.empty:
                    dfs.append(df)
            except Exception as e:
                print(f"⚠ Error leyendo {f}: {e}")

        if not dfs:
            print("⚠ No se pudieron cargar CSV válidos.")
            return

        df = pd.concat(dfs, ignore_index=True)

        # Necesitamos columnas x/z
        if "x" not in df.columns or "z" not in df.columns:
            print("⚠ Los CSV no contienen coordenadas x/z.")
            return

        df = df.dropna(subset=["x", "z"])
        
        # ===== FILTRAR DATOS FUERA DE LÍMITES =====
        df = df[
            (df['x'] >= STORE_BOUNDS['x_min']) & (df['x'] <= STORE_BOUNDS['x_max']) &
            (df['z'] >= STORE_BOUNDS['z_min']) & (df['z'] <= STORE_BOUNDS['z_max'])
        ]
        
        if df.empty:
            print("⚠ No hay posiciones válidas dentro de los límites.")
            return

        x = df["x"].values
        z = df["z"].values

        # ============================================================
        # 2) Generar figura
        # ============================================================
        fig, ax = plt.subplots(figsize=(12, 8))

        # ---------------------------------------------
        # Fondo: mapa cenital generado automáticamente
        # ---------------------------------------------
        if os.path.exists(map_path):
            try:
                bg = plt.imread(map_path)
                ax.imshow(
                    bg,
                    extent=[STORE_BOUNDS['x_min'], STORE_BOUNDS['x_max'], 
                           STORE_BOUNDS['z_min'], STORE_BOUNDS['z_max']],
                    origin="lower",
                    aspect='auto',
                    alpha=1.0,
                    zorder=1
                )
                print(f"🗺️ Mapa cenital cargado: {map_path}")
            except Exception as e:
                print(f"⚠ Error cargando mapa: {e}")
                ax.set_facecolor('#2a2a2a')
        else:
            print(f"⚠ No se pudo generar el mapa cenital")
            ax.set_facecolor('#2a2a2a')

        # ============================================================
        # 3) Heatmap 2D
        # ============================================================
        from scipy.ndimage import gaussian_filter

        H, xe, ze = np.histogram2d(
            x, z, bins=200,
            range=[[STORE_BOUNDS['x_min'], STORE_BOUNDS['x_max']],
                [STORE_BOUNDS['z_min'], STORE_BOUNDS['z_max']]]
        )

        # ⭐ Gaussian blur para suavizar el heatmap
        H = gaussian_filter(H, sigma=2.5)

        transparent_hot = AnalyticsManager.make_transparent_cmap("YlOrRd")

        im = ax.imshow(
            H.T,
            extent=[STORE_BOUNDS['x_min'], STORE_BOUNDS['x_max'], 
                   STORE_BOUNDS['z_min'], STORE_BOUNDS['z_max']],
            origin="lower",
            cmap=transparent_hot,
            interpolation="bilinear",
            aspect='auto',
            alpha=0.7,
            zorder=2
        )

        # ============================================================
        # 4) Decoración
        # ============================================================
        plt.colorbar(im, ax=ax, label="Intensidad de movimiento")
        ax.set_title("Heatmap GLOBAL del movimiento (vista cenital)", fontsize=14, pad=20)
        ax.set_xlabel("X", fontsize=12)
        ax.set_ylabel("Z", fontsize=12)
        ax.set_xlim(STORE_BOUNDS['x_min'], STORE_BOUNDS['x_max'])
        ax.set_ylim(STORE_BOUNDS['z_min'], STORE_BOUNDS['z_max'])
        
        plt.tight_layout()
        plt.show()


   
    def shelf_from_height(self, y):
        """Alias de get_shelf_from_y para compatibilidad."""
        return self.get_shelf_from_y(y)


    def _draw_zone_labels(self, ax):
        """Dibuja etiquetas de zonas en el heatmap"""
        zones = [
            ("Entrada", -10, 0),
            ("Frutas", -5, 0),
            ("Central", 0, 0),
            ("Varios", 5, 0),
            ("Caja", 10, 0)
        ]
        
        for label, x, z in zones:
            ax.text(x, z, label, fontsize=10, color='white',
                   bbox=dict(boxstyle='round', facecolor='black', alpha=0.5),
                   ha='center', va='center')

    def show_product_stats(self):
        """Muestra estadísticas de productos más visitados (global)"""
        files = glob.glob(os.path.join(self.save_dir, "*.csv"))
        
        if not files:
            print("⚠️ No hay datos de productos")
            return
        
        try:
            # Leer todos los CSVs
            dfs = [pd.read_csv(f) for f in files if os.path.getsize(f) > 0]
            if not dfs:
                print("⚠️ No hay archivos con datos")
                return
            
            df = pd.concat(dfs, ignore_index=True)
            
            # Filtrar productos válidos
            df = df[df["product"].notna() & (df["product"] != "")]
            
            if df.empty:
                print("⚠️ No se han registrado visitas a productos")
                return
            
            print("="*60)
            print("📦 ESTADÍSTICAS DE PRODUCTOS (GLOBAL)")
            print("="*60)
            
            counts = df["product"].value_counts()
            total_visits = counts.sum()
            
            print(f"\n📊 Total de interacciones: {total_visits}")
            print(f"🎯 Productos únicos: {len(counts)}\n")
            
            print("🔝 TOP 10 Productos más visitados:")
            for i, (product, count) in enumerate(counts.head(10).items(), 1):
                percentage = (count / total_visits) * 100
                bar = "█" * int(percentage / 2)
                print(f"  {i:2d}. {product:20s} {count:4d} visitas {bar} {percentage:.1f}%")
            
            print("="*60)
            
            # Gráfico
            plt.figure(figsize=(12, 6))
            counts.head(10).plot(kind='barh', color='skyblue')
            plt.xlabel('Número de visitas')
            plt.title('Top 10 Productos Más Visitados')
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            print(f"❌ Error mostrando estadísticas: {e}")

    def generate_zone_time(self, user_index):
        """Genera estadísticas de tiempo por zonas para un usuario o global."""

        files = sorted(glob.glob(os.path.join(self.save_dir, "*.csv")))

        if not files:
            print("⚠ No hay sesiones registradas.")
            return

        # =============================
        # GLOBAL
        # =============================
        if user_index == 0:
            print("\n🌍 TIEMPO GLOBAL POR ZONAS")
            all_times = defaultdict(float)

            for f in files:
                zt = self._compute_zone_times_from_file(f)
                for z, t in zt.items():
                    all_times[z] += t

            zone_times = dict(all_times)
            title = "Tiempo Global por Zonas"

        # =============================
        # INDIVIDUAL
        # =============================
        elif 1 <= user_index <= len(files):
            f = files[user_index - 1]
            print(f"\n👤 Usuario {user_index} → {os.path.basename(f)}")

            zone_times = self._compute_zone_times_from_file(f)
            title = f"Tiempo por Zonas — Usuario {user_index}"

        else:
            print("❌ Número fuera de rango.")
            return

        # ===================================
        # Consola
        # ===================================
        print("\n" + "="*60)
        total = sum(zone_times.values())

        for zone, t in sorted(zone_times.items(), key=lambda x: -x[1]):
            pct = (t / total * 100) if total > 0 else 0
            print(f"{zone:15s} {self._format_time(t):10s} → {pct:5.1f}%")

        print("="*60)

        # ===================================
        # Gráfica Matplotlib
        # ===================================
        import matplotlib.pyplot as plt

        zones = list(zone_times.keys())
        times = list(zone_times.values())
        times_human = [self._format_time(t) for t in times]

        plt.figure(figsize=(10, 6))
        bars = plt.barh(zones, times)

        # etiquetas
        for bar, label in zip(bars, times_human):
            plt.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                    label, va='center')

        plt.title(title)
        plt.xlabel("Tiempo (segundos realmente, pero etiquetado arriba)")
        plt.tight_layout()
        plt.show()


    def _format_time(self, seconds):
        """Convierte segundos → formato legible (h, m, s)."""
        seconds = int(seconds)

        if seconds < 60:
            return f"{seconds} s"

        minutes = seconds // 60
        seconds %= 60

        if minutes < 60:
            return f"{minutes} min {seconds:02d} s"

        hours = minutes // 60
        minutes %= 60

        return f"{hours} h {minutes:02d} min"

    def _compute_zone_times_from_file(self, filepath):
        """Lee un CSV y devuelve tiempos por zona correctamente."""
        df = pd.read_csv(filepath)

        if df.empty or "zone" not in df.columns or "time" not in df.columns:
            return {}

        df = df.sort_values("time")

        zone_times = defaultdict(float)

        prev_zone = None
        prev_time = None

        for _, row in df.iterrows():
            t = row["time"]
            zone = row["zone"]

            if prev_zone is not None:
                zone_times[prev_zone] += (t - prev_time)

            prev_zone = zone
            prev_time = t

        return zone_times


    def save_stock(self, stock_dict):
        """Guarda el estocaje final de la sesión."""
        filename = os.path.join(self.save_dir, "stock_log.csv")

        # Si es primera vez, crear encabezado
        write_header = not os.path.exists(filename)

        with open(filename, "a", newline="") as f:
            writer = csv.writer(f)

            if write_header:
                writer.writerow(["timestamp"] + list(stock_dict.keys()))

            writer.writerow([datetime.now()] + list(stock_dict.values()))

        print("📦 Estocaje final guardado correctamente.")

    def _generate_topdown_map_from_analytics(self, save_path):
        """
        Solicita al GraphicsEngine que genere el mapa cenital.
        Este método es llamado automáticamente si no existe el mapa.
        """
        try:
            # Intentar obtener referencia al app desde el analytics manager
            # Esto requiere que el analytics tenga acceso al app
            print("⚠️ El mapa cenital debe generarse desde el modo admin (tecla 'T')")
            print("   o asegúrate de que analytics.app esté configurado correctamente.")
            
            # Si tenemos referencia al app, generar el mapa
            if hasattr(self, 'app') and self.app:
                self.app.generate_topdown_map(save_path)
                print(f"✅ Mapa cenital generado: {save_path}")
            else:
                print("❌ No se puede generar automáticamente. Usa la tecla 'T' en modo admin.")
                
        except Exception as e:
            print(f"❌ Error generando mapa cenital: {e}")
            print("   → Genera manualmente con la tecla 'T' en modo admin")


    # ============================================================
    # UTILIDADES
    # ============================================================

    def get_session_summary(self):
        """Devuelve resumen de la sesión actual"""
        if not self.current_username:
            return None
        
        duration = (datetime.now() - self.session_start_time).total_seconds()
        
        return {
            'username': self.current_username,
            'duration_seconds': duration,
            'positions_tracked': len(self.user_positions),
            'products_visited': sum(self.product_visits.values()),
            'unique_products': len(self.product_visits),
            'zones_visited': len(self.zone_times)
        }

    def export_summary_report(self, output_file="analytics_report.txt"):
        """Genera un reporte de texto con todas las estadísticas"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("="*60 + "\n")
                f.write("REPORTE DE ANALÍTICAS - 3D STORE\n")
                f.write(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("="*60 + "\n\n")
                
                # Sesión actual
                summary = self.get_session_summary()
                if summary:
                    f.write("SESIÓN ACTUAL:\n")
                    f.write(f"  Usuario: {summary['username']}\n")
                    f.write(f"  Duración: {int(summary['duration_seconds']//60)}m\n")
                    f.write(f"  Productos visitados: {summary['products_visited']}\n")
                    f.write("\n")
                
                # Estadísticas globales
                files = glob.glob(os.path.join(self.save_dir, "*.csv"))
                f.write(f"DATOS GLOBALES:\n")
                f.write(f"  Total de sesiones: {len(files)}\n")
                
            print(f"✅ Reporte exportado a: {output_file}")
            
        except Exception as e:
            print(f"❌ Error exportando reporte: {e}")