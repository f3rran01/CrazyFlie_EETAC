"""
Creador de Geocage Avanzado con Obstáculos y Guardado de Mapas
Permite crear geocage, añadir obstáculos y guardar/cargar configuraciones
"""

import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Polygon as MPLPolygon
from typing import List, Tuple, Optional, Dict
import json
import os
from datetime import datetime


def line_intersects(p1, p2, p3, p4):
    """Verifica si dos líneas se intersectan"""
    def orientation(p, q, r):
        val = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
        if val == 0:
            return 0
        return 1 if val > 0 else 2

    def on_segment(p, q, r):
        return (q[0] <= max(p[0], r[0]) and q[0] >= min(p[0], r[0]) and
                q[1] <= max(p[1], r[1]) and q[1] >= min(p[1], r[1]))

    o1 = orientation(p1, p2, p3)
    o2 = orientation(p1, p2, p4)
    o3 = orientation(p3, p4, p1)
    o4 = orientation(p3, p4, p2)

    if o1 != o2 and o3 != o4:
        return True

    if (o1 == 0 and on_segment(p1, p3, p2)) or \
       (o2 == 0 and on_segment(p1, p4, p2)) or \
       (o3 == 0 and on_segment(p3, p1, p4)) or \
       (o4 == 0 and on_segment(p3, p2, p4)):
        return True

    return False


class MapaVuelo:
    """Clase para almacenar configuración completa de un mapa de vuelo"""
    
    def __init__(self, nombre: str = "Sin nombre"):
        self.nombre = nombre
        self.fecha_creacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.geocage = []  # Lista de puntos (x, y)
        self.obstaculos = []  # Lista de obstáculos (cada uno es lista de puntos)
        self.descripcion = ""
        
    def to_dict(self) -> Dict:
        """Convierte el mapa a diccionario para guardar"""
        return {
            'nombre': self.nombre,
            'fecha_creacion': self.fecha_creacion,
            'geocage': self.geocage,
            'obstaculos': self.obstaculos,
            'descripcion': self.descripcion
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Crea un MapaVuelo desde un diccionario"""
        mapa = cls(data.get('nombre', 'Sin nombre'))
        mapa.fecha_creacion = data.get('fecha_creacion', '')
        mapa.geocage = data.get('geocage', [])
        mapa.obstaculos = data.get('obstaculos', [])
        mapa.descripcion = data.get('descripcion', '')
        return mapa
    
    def guardar(self, ruta: str):
        """Guarda el mapa en un archivo JSON"""
        try:
            with open(ruta, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error guardando mapa: {e}")
            return False
    
    @classmethod
    def cargar(cls, ruta: str):
        """Carga un mapa desde un archivo JSON"""
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except Exception as e:
            print(f"Error cargando mapa: {e}")
            return None


class GeocageCreatorAvanzado:
    """Editor de Geocage con soporte para obstáculos y guardado de mapas"""

    def __init__(self, parent_window, visualizador, on_save_callback=None):
        self.parent_window = parent_window
        self.visualizador = visualizador
        self.on_save_callback = on_save_callback

        # Datos del geocage
        self.geocage_points = []
        self.geocage_x = []
        self.geocage_y = []
        
        # Obstáculos
        self.obstaculos = []  # Lista de obstáculos (cada uno es un dict con x, y coords)
        self.obstaculo_actual_x = []
        self.obstaculo_actual_y = []
        self.modo_edicion = "geocage"  # "geocage" o "obstaculo"
        
        # Mapa actual
        self.mapa_actual = MapaVuelo()
        
        # Directorio de mapas
        self.directorio_mapas = os.path.join(os.path.dirname(__file__), "mapas_vuelo")
        os.makedirs(self.directorio_mapas, exist_ok=True)

        # Crear ventana
        self._crear_ventana()

    def _crear_ventana(self):
        """Crea la ventana del editor"""
        # ✅ FIX: Usar parent_window directamente (ya es un Toplevel)
        # NO crear otra ventana Toplevel para evitar duplicación
        self.window = self.parent_window
        self.window.title("🗺️ Creador de Geocage con Obstáculos")
        self.window.geometry("1200x800")
        self.window.configure(bg="#f0f0f0")
        self.window.resizable(False, False)
        self.window.grab_set()

        # Frame izquierdo - controles
        left_frame = tk.Frame(self.window, bg="lightblue", width=350)
        left_frame.pack(side="left", fill="both", expand=False)
        left_frame.pack_propagate(False)

        # Frame derecho - canvas
        right_frame = tk.Frame(self.window, bg="white", width=850)
        right_frame.pack(side="right", fill="both", expand=True)

        # === PANEL DE CONTROL ===
        self._crear_panel_control(left_frame)
        
        # === CANVAS DE MATPLOTLIB ===
        self.fig, self.ax = plt.subplots(figsize=(8.5, 6.5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Conectar evento de click
        self.canvas.mpl_connect("button_press_event", self._on_click)

        # Dibujar grid inicial
        self._update_plot()

        # Protocolo de cierre
        self.window.protocol("WM_DELETE_WINDOW", self._cerrar_ventana)

        print("[Geocage] Editor avanzado abierto")

    def _crear_panel_control(self, parent):
        """Crea el panel de control izquierdo"""
        
        # Título
        tk.Label(parent, text="🗺️ Editor de Mapas de Vuelo",
                font=("Arial", 14, "bold"), bg="lightblue").pack(pady=10)
        
        # === SELECTOR DE MODO ===
        modo_frame = tk.LabelFrame(parent, text="🎯 Modo de Edición",
                                   font=("Arial", 11, "bold"), bg="white")
        modo_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.label_modo = tk.Label(modo_frame, text="GEOCAGE (Zona Verde)",
                                   font=("Arial", 11, "bold"), bg="white", fg="green")
        self.label_modo.pack(pady=5)
        
        btn_frame = tk.Frame(modo_frame, bg="white")
        btn_frame.pack(pady=5)
        
        tk.Button(btn_frame, text="🟢 Geocage",
                 command=lambda: self._cambiar_modo("geocage"),
                 bg="#4CAF50", fg="white", font=("Arial", 9, "bold"),
                 width=12).pack(side=tk.LEFT, padx=2)
        
        tk.Button(btn_frame, text="🔴 Obstáculo",
                 command=lambda: self._cambiar_modo("obstaculo"),
                 bg="#f44336", fg="white", font=("Arial", 9, "bold"),
                 width=12).pack(side=tk.LEFT, padx=2)
        
        # === ESTADO ===
        state_frame = tk.LabelFrame(parent, text="📊 Estado",
                                    font=("Arial", 10, "bold"), bg="white")
        state_frame.pack(fill=tk.X, padx=10, pady=5)

        self.label_geocage_puntos = tk.Label(state_frame, text="Geocage: 0 puntos",
                                             font=("Arial", 9), bg="white")
        self.label_geocage_puntos.pack(pady=2)

        self.label_obstaculos = tk.Label(state_frame, text="Obstáculos: 0",
                                         font=("Arial", 9), bg="white")
        self.label_obstaculos.pack(pady=2)

        self.label_puntos_actuales = tk.Label(state_frame, text="Puntos actuales: 0",
                                              font=("Arial", 9), bg="white", fg="blue")
        self.label_puntos_actuales.pack(pady=2)

        # === BOTONES DE EDICIÓN ===
        tk.Button(parent, text="⬅️ Eliminar Último Punto",
                  command=self._eliminar_ultimo,
                  bg="#ff9800", fg="white", font=("Arial", 10, "bold"),
                  height=2).pack(fill=tk.X, padx=10, pady=5)

        tk.Button(parent, text="💾 Guardar Obstáculo Actual",
                  command=self._guardar_obstaculo_actual,
                  bg="#2196F3", fg="white", font=("Arial", 10, "bold"),
                  height=2).pack(fill=tk.X, padx=10, pady=5)

        tk.Button(parent, text="🗑️ Borrar Último Obstáculo",
                  command=self._borrar_ultimo_obstaculo,
                  bg="#FF5722", fg="white", font=("Arial", 10, "bold"),
                  height=2).pack(fill=tk.X, padx=10, pady=5)

        # === BOTONES DE MAPA ===
        mapa_frame = tk.LabelFrame(parent, text="💾 Gestión de Mapas",
                                   font=("Arial", 10, "bold"), bg="lightblue")
        mapa_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Button(mapa_frame, text="💾 Guardar Mapa",
                  command=self._guardar_mapa,
                  bg="#9C27B0", fg="white", font=("Arial", 10, "bold"),
                  height=2, width=25).pack(fill=tk.X, padx=5, pady=5)  # Añadido width y más padding

        tk.Button(mapa_frame, text="📂 Cargar Mapa",
                  command=self._cargar_mapa,
                  bg="#3F51B5", fg="white", font=("Arial", 10, "bold"),
                  height=2, width=25).pack(fill=tk.X, padx=5, pady=5)  # Añadido width y más padding

        # === BOTÓN FINAL ===
        tk.Button(parent, text="✅ APLICAR Y VISUALIZAR",
                  command=self._aplicar_configuracion,
                  bg="#4CAF50", fg="white", font=("Arial", 11, "bold"),
                  height=3).pack(fill=tk.X, padx=10, pady=15)

    def _cambiar_modo(self, nuevo_modo):
        """Cambia entre modo geocage y obstáculo"""
        self.modo_edicion = nuevo_modo

        if nuevo_modo == "geocage":
            self.label_modo.config(text="GEOCAGE (Zona Verde)", fg="green")
        else:
            self.label_modo.config(text="OBSTÁCULO (Zona Roja)", fg="red")

        print(f"[Editor] Modo cambiado a: {nuevo_modo.upper()}")
        self._update_info()

    def _on_click(self, event):
        """Maneja clicks en el canvas"""
        if event.xdata is None or event.ydata is None:
            return

        x = round(event.xdata, 1)
        y = round(event.ydata, 1)

        if self.modo_edicion == "geocage":
            self._anadir_punto_geocage(x, y)
        else:
            self._anadir_punto_obstaculo(x, y)

    def _anadir_punto_geocage(self, x, y):
        """Añade un punto al geocage"""
        # Verificar duplicado
        if (x, y) in zip(self.geocage_x, self.geocage_y):
            print("[Geocage] Punto duplicado, ignorado")
            return

        # Verificar intersecciones
        if self._would_create_intersection(x, y, self.geocage_x, self.geocage_y):
            messagebox.showwarning("Polígono inválido",
                                  "Este punto crearía líneas que se cruzan.")
            return

        # Añadir punto
        self.geocage_x.append(x)
        self.geocage_y.append(y)

        print(f"[Geocage] Punto añadido: ({x}, {y}) - Total: {len(self.geocage_x)}")

        self._update_plot()
        self._update_info()

    def _anadir_punto_obstaculo(self, x, y):
        """Añade un punto al obstáculo actual"""
        # Verificar que hay geocage
        if len(self.geocage_x) < 3:
            messagebox.showwarning("Sin Geocage",
                                  "Primero debes crear el geocage antes de añadir obstáculos.")
            return

        # Verificar que el punto está dentro del geocage
        if not self._punto_dentro_poligono(x, y, self.geocage_x, self.geocage_y):
            messagebox.showwarning("Fuera del Geocage",
                                  "El obstáculo debe estar completamente dentro del geocage.")
            return

        # Verificar duplicado
        if (x, y) in zip(self.obstaculo_actual_x, self.obstaculo_actual_y):
            print("[Obstáculo] Punto duplicado, ignorado")
            return

        # Verificar intersecciones
        if self._would_create_intersection(x, y, self.obstaculo_actual_x, self.obstaculo_actual_y):
            messagebox.showwarning("Polígono inválido",
                                  "Este punto crearía líneas que se cruzan.")
            return

        # Añadir punto
        self.obstaculo_actual_x.append(x)
        self.obstaculo_actual_y.append(y)

        print(f"[Obstáculo] Punto añadido: ({x}, {y}) - Total: {len(self.obstaculo_actual_x)}")

        self._update_plot()
        self._update_info()

    def _would_create_intersection(self, new_x, new_y, x_coords, y_coords):
        """Verifica si añadir un punto crearía intersecciones"""
        if len(x_coords) < 2:
            return False

        new_line_start = (x_coords[-1], y_coords[-1])
        new_line_end = (new_x, new_y)

        for i in range(len(x_coords) - 1):
            if i == len(x_coords) - 2:
                continue

            existing_start = (x_coords[i], y_coords[i])
            existing_end = (x_coords[i + 1], y_coords[i + 1])

            if line_intersects(new_line_start, new_line_end,
                             existing_start, existing_end):
                return True

        # Verificar línea de cierre
        if len(x_coords) >= 3:
            closing_line_start = (new_x, new_y)
            closing_line_end = (x_coords[0], y_coords[0])

            for i in range(1, len(x_coords) - 1):
                existing_start = (x_coords[i], y_coords[i])
                existing_end = (x_coords[i + 1], y_coords[i + 1])

                if line_intersects(closing_line_start, closing_line_end,
                                 existing_start, existing_end):
                    return True

        return False

    def _update_plot(self):
        """Actualiza el gráfico"""
        self.ax.clear()

        # ✅ FIX: Configurar límites para coincidir con el visualizador principal (10m × 10m)
        # El visualizador principal usa espacio_vuelo = 10.0, es decir, rango de -5.0 a +5.0
        self.ax.set_xlim(-5.0, 5.0)
        self.ax.set_ylim(-5.0, 5.0)

        # Grid
        self.ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.7)
        self.ax.set_xlabel("X (m)", fontsize=11)
        self.ax.set_ylabel("Y (m)", fontsize=11)

        titulo = "🗺️ Mapa de Vuelo: Geocage y Obstáculos"
        self.ax.set_title(titulo, fontsize=12, fontweight="bold")

        # Punto origen
        self.ax.scatter(0, 0, color="blue", s=150, marker="o",
                       edgecolors="black", linewidths=2, label="Origen", zorder=10)

        # === DIBUJAR GEOCAGE ===
        if len(self.geocage_x) > 0:
            self.ax.scatter(self.geocage_x, self.geocage_y,
                          color="green", s=100, edgecolors="darkgreen",
                          linewidths=2, zorder=5, label="Geocage")

            # Números
            for i, (x, y) in enumerate(zip(self.geocage_x, self.geocage_y)):
                self.ax.text(x, y, str(i+1), color="white",
                           fontsize=8, fontweight="bold",
                           ha="center", va="center", zorder=6)

            # Líneas
            if len(self.geocage_x) > 1:
                self.ax.plot(self.geocage_x, self.geocage_y,
                           'g--', linewidth=2, alpha=0.7)

            # Cerrar polígono
            if len(self.geocage_x) >= 3:
                x_closed = self.geocage_x + [self.geocage_x[0]]
                y_closed = self.geocage_y + [self.geocage_y[0]]
                self.ax.plot(x_closed, y_closed, 'g-', linewidth=3, alpha=0.8)
                self.ax.fill(x_closed, y_closed, color="green", alpha=0.15)

        # === DIBUJAR OBSTÁCULOS GUARDADOS ===
        for idx, obs in enumerate(self.obstaculos):
            obs_x = obs['x']
            obs_y = obs['y']

            # Puntos
            self.ax.scatter(obs_x, obs_y,
                          color="red", s=80, edgecolors="darkred",
                          linewidths=2, zorder=4,
                          label=f"Obstáculo {idx+1}" if idx == 0 else "")

            # Cerrar polígono
            if len(obs_x) >= 3:
                x_closed = obs_x + [obs_x[0]]
                y_closed = obs_y + [obs_y[0]]
                self.ax.plot(x_closed, y_closed, 'r-', linewidth=2, alpha=0.8)
                self.ax.fill(x_closed, y_closed, color="red", alpha=0.3)

        # === DIBUJAR OBSTÁCULO ACTUAL (en edición) ===
        if len(self.obstaculo_actual_x) > 0:
            self.ax.scatter(self.obstaculo_actual_x, self.obstaculo_actual_y,
                          color="orange", s=100, edgecolors="darkorange",
                          linewidths=2, zorder=5, label="Editando obstáculo")

            # Números
            for i, (x, y) in enumerate(zip(self.obstaculo_actual_x, self.obstaculo_actual_y)):
                self.ax.text(x, y, str(i+1), color="white",
                           fontsize=8, fontweight="bold",
                           ha="center", va="center", zorder=6)

            # Líneas
            if len(self.obstaculo_actual_x) > 1:
                self.ax.plot(self.obstaculo_actual_x, self.obstaculo_actual_y,
                           'orange', linestyle='--', linewidth=2, alpha=0.7)

            # Cerrar polígono si hay 3+ puntos
            if len(self.obstaculo_actual_x) >= 3:
                x_closed = self.obstaculo_actual_x + [self.obstaculo_actual_x[0]]
                y_closed = self.obstaculo_actual_y + [self.obstaculo_actual_y[0]]
                self.ax.plot(x_closed, y_closed, 'orange', linestyle='--', linewidth=2)
                self.ax.fill(x_closed, y_closed, color="orange", alpha=0.2)

        self.ax.legend(loc="upper right", fontsize=8)
        self.canvas.draw()

    def _update_info(self):
        """Actualiza la información del estado"""
        self.label_geocage_puntos.config(text=f"Geocage: {len(self.geocage_x)} puntos")
        self.label_obstaculos.config(text=f"Obstáculos: {len(self.obstaculos)}")

        if self.modo_edicion == "geocage":
            puntos = len(self.geocage_x)
            self.label_puntos_actuales.config(
                text=f"Puntos Geocage: {puntos}",
                fg="green"
            )
        else:
            puntos = len(self.obstaculo_actual_x)
            self.label_puntos_actuales.config(
                text=f"Puntos Obstáculo: {puntos}",
                fg="red"
            )

    def _eliminar_ultimo(self):
        """Elimina el último punto según el modo"""
        if self.modo_edicion == "geocage":
            if not self.geocage_x:
                messagebox.showinfo("Info", "No hay puntos en el geocage")
                return
            self.geocage_x.pop()
            self.geocage_y.pop()
        else:
            if not self.obstaculo_actual_x:
                messagebox.showinfo("Info", "No hay puntos en el obstáculo actual")
                return
            self.obstaculo_actual_x.pop()
            self.obstaculo_actual_y.pop()

        self._update_plot()
        self._update_info()

    def _guardar_obstaculo_actual(self):
        """Guarda el obstáculo actual en la lista de obstáculos"""
        if len(self.obstaculo_actual_x) < 3:
            messagebox.showwarning("Incompleto",
                                  "El obstáculo necesita al menos 3 puntos.")
            return

        # Verificar que todos los puntos están dentro del geocage
        for x, y in zip(self.obstaculo_actual_x, self.obstaculo_actual_y):
            if not self._punto_dentro_poligono(x, y, self.geocage_x, self.geocage_y):
                messagebox.showwarning("Fuera del Geocage",
                                      "Todos los puntos del obstáculo deben estar dentro del geocage.")
                return

        # Guardar obstáculo
        obstaculo = {
            'x': self.obstaculo_actual_x.copy(),
            'y': self.obstaculo_actual_y.copy()
        }
        self.obstaculos.append(obstaculo)

        # Limpiar obstáculo actual
        self.obstaculo_actual_x.clear()
        self.obstaculo_actual_y.clear()

        messagebox.showinfo("Obstáculo Guardado",
                           f"✅ Obstáculo {len(self.obstaculos)} añadido correctamente.\n\n"
                           f"Puedes crear más obstáculos o aplicar la configuración.")

        self._update_plot()
        self._update_info()
        print(f"[Obstáculos] Total: {len(self.obstaculos)}")

    def _borrar_ultimo_obstaculo(self):
        """Borra el último obstáculo guardado"""
        if not self.obstaculos:
            messagebox.showinfo("Info", "No hay obstáculos guardados")
            return

        if messagebox.askyesno("Confirmar", f"¿Borrar obstáculo {len(self.obstaculos)}?"):
            self.obstaculos.pop()
            self._update_plot()
            self._update_info()
            print(f"[Obstáculos] Obstáculo eliminado - Total: {len(self.obstaculos)}")

    def _punto_dentro_poligono(self, x, y, poligono_x, poligono_y):
        """Verifica si un punto está dentro de un polígono usando ray casting"""
        n = len(poligono_x)
        inside = False

        p1x, p1y = poligono_x[0], poligono_y[0]
        for i in range(1, n + 1):
            p2x, p2y = poligono_x[i % n], poligono_y[i % n]

            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside

            p1x, p1y = p2x, p2y

        return inside

    def _guardar_mapa(self):
        """Guarda el mapa completo (geocage + obstáculos) en un archivo"""
        if len(self.geocage_x) < 3:
            messagebox.showwarning("Sin Geocage",
                                  "Primero debes crear un geocage para guardar el mapa.")
            return

        # Pedir nombre del mapa
        dialog = tk.Toplevel(self.window)
        dialog.title("💾 Guardar Mapa")
        dialog.geometry("400x200")
        dialog.transient(self.window)
        dialog.grab_set()

        tk.Label(dialog, text="Nombre del mapa:", font=("Arial", 11)).pack(pady=10)

        nombre_var = tk.StringVar(value=f"mapa_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        entry = tk.Entry(dialog, textvariable=nombre_var, font=("Arial", 11), width=30)
        entry.pack(pady=5)
        entry.focus()

        tk.Label(dialog, text="Descripción (opcional):", font=("Arial", 11)).pack(pady=10)
        desc_var = tk.StringVar()
        tk.Entry(dialog, textvariable=desc_var, font=("Arial", 11), width=30).pack(pady=5)

        def guardar():
            nombre = nombre_var.get().strip()
            if not nombre:
                messagebox.showwarning("Error", "El nombre no puede estar vacío")
                return

            # Crear mapa
            mapa = MapaVuelo(nombre)
            mapa.geocage = list(zip(self.geocage_x, self.geocage_y))
            mapa.obstaculos = [
                {'points': list(zip(obs['x'], obs['y']))}
                for obs in self.obstaculos
            ]
            mapa.descripcion = desc_var.get().strip()

            # Guardar archivo
            nombre_archivo = f"{nombre}.json"
            ruta = os.path.join(self.directorio_mapas, nombre_archivo)

            if mapa.guardar(ruta):
                messagebox.showinfo("Guardado",
                                   f"✅ Mapa guardado correctamente:\n\n"
                                   f"📁 {nombre_archivo}\n"
                                   f"📍 Geocage: {len(mapa.geocage)} puntos\n"
                                   f"🚧 Obstáculos: {len(mapa.obstaculos)}")
                dialog.destroy()
            else:
                messagebox.showerror("Error", "No se pudo guardar el mapa")

        tk.Button(dialog, text="💾 Guardar", command=guardar,
                 bg="#4CAF50", fg="white", font=("Arial", 11, "bold"),
                 width=15).pack(pady=15)

    def _cargar_mapa(self):
        """Carga un mapa desde un archivo"""
        # Listar mapas disponibles
        try:
            archivos = [f for f in os.listdir(self.directorio_mapas) if f.endswith('.json')]
        except:
            archivos = []

        if not archivos:
            messagebox.showinfo("Sin Mapas",
                               "No hay mapas guardados.\n\n"
                               "Crea un mapa y guárdalo primero.")
            return

        # Dialog de selección
        dialog = tk.Toplevel(self.window)
        dialog.title("📂 Cargar Mapa")
        dialog.geometry("500x400")
        dialog.transient(self.window)
        dialog.grab_set()

        tk.Label(dialog, text="Selecciona un mapa:", font=("Arial", 12, "bold")).pack(pady=10)

        # Listbox con scrollbar
        frame = tk.Frame(dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set,
                            font=("Arial", 10), height=15)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)

        # Llenar listbox
        for archivo in sorted(archivos, reverse=True):
            listbox.insert(tk.END, archivo)

        def cargar():
            if not listbox.curselection():
                messagebox.showwarning("Error", "Selecciona un mapa")
                return

            archivo = listbox.get(listbox.curselection()[0])
            ruta = os.path.join(self.directorio_mapas, archivo)

            mapa = MapaVuelo.cargar(ruta)
            if mapa:
                # Limpiar todo
                self.geocage_x.clear()
                self.geocage_y.clear()
                self.obstaculos.clear()
                self.obstaculo_actual_x.clear()
                self.obstaculo_actual_y.clear()

                # Cargar geocage
                if mapa.geocage:
                    for x, y in mapa.geocage:
                        self.geocage_x.append(x)
                        self.geocage_y.append(y)
                        self.geocage_points = list(zip(self.geocage_x, self.geocage_y))

                # Cargar obstáculos
                if mapa.obstaculos:
                    for obs_data in mapa.obstaculos:
                        points = obs_data.get('points', [])
                        if points:
                            obs_x = [p[0] for p in points]
                            obs_y = [p[1] for p in points]
                            self.obstaculos.append({'x': obs_x, 'y': obs_y})

                self._update_plot()
                self._update_info()

                # ✅ LLAMAR AL CALLBACK para pasar datos al GUI principal
                # El callback se encargará de dibujar en el visualizador principal
                if self.on_save_callback:
                    config = {
                        'geocage': self.geocage_points,
                        'obstaculos': [
                            {'points': list(zip(obs['x'], obs['y']))}
                            for obs in self.obstaculos
                        ]
                    }
                    self.on_save_callback(config)

                messagebox.showinfo("Cargado",
                                    f"✅ Mapa cargado:\n\n"
                                    f"📋 {mapa.nombre}\n"
                                    f"📍 Geocage: {len(mapa.geocage)} puntos\n"
                                    f"🚧 Obstáculos: {len(mapa.obstaculos)}\n"
                                    f"📅 {mapa.fecha_creacion}\n\n"
                                    f"✅ Visualizado en el mapa principal")
                dialog.destroy()
            else:
                messagebox.showerror("Error", "No se pudo cargar el mapa")

        def eliminar():
            if not listbox.curselection():
                messagebox.showwarning("Error", "Selecciona un mapa para eliminar")
                return

            archivo = listbox.get(listbox.curselection()[0])

            # Confirmar eliminación
            respuesta = messagebox.askyesno(
                "Confirmar Eliminación",
                f"¿Estás seguro de que quieres eliminar el mapa?\n\n"
                f"📋 {archivo}\n\n"
                f"⚠️ Esta acción no se puede deshacer."
            )

            if respuesta:
                try:
                    ruta = os.path.join(self.directorio_mapas, archivo)
                    os.remove(ruta)

                    # Actualizar listbox
                    listbox.delete(listbox.curselection()[0])

                    messagebox.showinfo("Eliminado", f"✅ Mapa eliminado correctamente:\n\n📋 {archivo}")

                    # Si no quedan mapas, cerrar el diálogo
                    if listbox.size() == 0:
                        messagebox.showinfo("Sin Mapas", "No quedan mapas guardados.")
                        dialog.destroy()

                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo eliminar el mapa:\n{e}")

        # Frame para botones
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="📂 Cargar", command=cargar,
                 bg="#2196F3", fg="white", font=("Arial", 11, "bold"),
                 width=15).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="🗑️ Eliminar", command=eliminar,
                 bg="#f44336", fg="white", font=("Arial", 11, "bold"),
                 width=15).pack(side=tk.LEFT, padx=5)

        def cargar_y_cerrar():
            cargar()
            # Llamar al callback si existe
            if self.on_save_callback:
                config = {
                    'geocage': list(zip(self.geocage_x, self.geocage_y)) if self.geocage_x else [],
                    'obstaculos': [
                        {'points': list(zip(obs['x'], obs['y']))}
                        for obs in self.obstaculos
                    ]
                }
                self.on_save_callback(config)



    def _aplicar_configuracion(self):
        """Aplica la configuración al visualizador y cierra"""
        if len(self.geocage_x) < 3:
            messagebox.showwarning("Incompleto",
                                   "Necesitas al menos 3 puntos para el geocage.")
            return

        # Verificar origen dentro del geocage
        if not self._punto_dentro_poligono(0, 0, self.geocage_x, self.geocage_y):
            messagebox.showerror(
                "Origen Fuera del Geocage",
                "❌ El punto de origen (0,0) está FUERA del geocage.\n\n"
                "El dron despega desde el origen, por lo que debe estar\n"
                "DENTRO del área de vuelo permitida."
            )
            return

        # Confirmar
        msg = f"¿Aplicar configuración al visualizador?\n\n" \
              f"📍 Geocage: {len(self.geocage_x)} puntos\n" \
              f"🚧 Obstáculos: {len(self.obstaculos)}"

        if not messagebox.askyesno("Aplicar", msg):
            return

        # Crear lista de puntos del geocage
        self.geocage_points = list(zip(self.geocage_x, self.geocage_y))

        # Callback - se encarga de dibujar en el visualizador principal
        if self.on_save_callback:
            config = {
                'geocage': self.geocage_points,
                'obstaculos': [
                    {'points': list(zip(obs['x'], obs['y']))}
                    for obs in self.obstaculos
                ]
            }
            self.on_save_callback(config)

        print(f"[Mapa] ✅ Aplicado - Geocage: {len(self.geocage_points)}, Obstáculos: {len(self.obstaculos)}")

        # Cerrar
        self.window.destroy()

        messagebox.showinfo("Aplicado",
                            f"✅ Configuración aplicada al visualizador:\n\n"
                            f"📍 Zona de vuelo: {len(self.geocage_points)} vértices\n"
                            f"🚧 Obstáculos: {len(self.obstaculos)}\n\n"
                            f"El dron respetará estas restricciones.\n"
                            f"El mapa está visible en el visualizador 3D.")

    def _dibujar_en_visualizador(self):
        """Dibuja el geocage y obstáculos en el visualizador"""
        if not self.visualizador:
            return

        # Limpiar anterior
        self.visualizador.canvas.delete("geocage_permanente")
        self.visualizador.canvas.delete("obstaculo_permanente")

        # === DIBUJAR GEOCAGE ===
        if self.geocage_points:
            # Líneas del geocage
            for i in range(len(self.geocage_points)):
                x1, y1 = self.geocage_points[i]
                x2, y2 = self.geocage_points[(i + 1) % len(self.geocage_points)]

                # Usar center_x/center_y (atributos correctos del visualizador)
                x1_px = self.visualizador.center_x + (x1 * self.visualizador.escala)
                y1_px = self.visualizador.center_y - (y1 * self.visualizador.escala)
                x2_px = self.visualizador.center_x + (x2 * self.visualizador.escala)
                y2_px = self.visualizador.center_y - (y2 * self.visualizador.escala)

                self.visualizador.canvas.create_line(
                    x1_px, y1_px, x2_px, y2_px,
                    fill="#4CAF50", width=3, tags="geocage_permanente"
                )

            # Relleno del geocage
            puntos_px = []
            for x, y in self.geocage_points:
                x_px = self.visualizador.center_x + (x * self.visualizador.escala)
                y_px = self.visualizador.center_y - (y * self.visualizador.escala)
                puntos_px.extend([x_px, y_px])

            self.visualizador.canvas.create_polygon(
                puntos_px, fill="#C8E6C9", outline="",
                stipple="gray25", tags="geocage_permanente"
            )
            self.visualizador.canvas.tag_lower("geocage_permanente")

        # === DIBUJAR OBSTÁCULOS ===
        for obs in self.obstaculos:
            puntos = list(zip(obs['x'], obs['y']))

            # Líneas del obstáculo
            for i in range(len(puntos)):
                x1, y1 = puntos[i]
                x2, y2 = puntos[(i + 1) % len(puntos)]

                x1_px = self.visualizador.center_x + (x1 * self.visualizador.escala)
                y1_px = self.visualizador.center_y - (y1 * self.visualizador.escala)
                x2_px = self.visualizador.center_x + (x2 * self.visualizador.escala)
                y2_px = self.visualizador.center_y - (y2 * self.visualizador.escala)

                self.visualizador.canvas.create_line(
                    x1_px, y1_px, x2_px, y2_px,
                    fill="#f44336", width=3, tags="obstaculo_permanente"
                )

            # Relleno del obstáculo
            puntos_px = []
            for x, y in puntos:
                x_px = self.visualizador.center_x + (x * self.visualizador.escala)
                y_px = self.visualizador.center_y - (y * self.visualizador.escala)
                puntos_px.extend([x_px, y_px])

            self.visualizador.canvas.create_polygon(
                puntos_px, fill="#FFCDD2", outline="",
                tags="obstaculo_permanente"
            )

        print("[Visualizador] Geocage y obstáculos dibujados")

    def _cerrar_ventana(self):
        """Cierra la ventana"""
        self.window.destroy()
        print("[Editor] Cerrado")


# Función de compatibilidad para reemplazar la clase antigua
def GeocageCreator(parent_window, visualizador, on_save_callback=None):
    """Wrapper para mantener compatibilidad con código existente"""
    return GeocageCreatorAvanzado(parent_window, visualizador, on_save_callback)