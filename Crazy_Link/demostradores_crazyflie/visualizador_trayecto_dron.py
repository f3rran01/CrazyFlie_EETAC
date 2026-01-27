"""
Visualizador de Trayecto del Dron en 3D
Sistema de visualización para seguir el recorrido del Crazyflie en tiempo real
"""

import tkinter as tk
from tkinter import Canvas
import math
from typing import List, Tuple


class VisualizadorTrayecto3D:
    """
    Visualizador del trayecto del dron en un canvas 2D con información de altura.
    Muestra el recorrido en el plano XY con una estela roja y la altura en un indicador lateral.
    """

    def __init__(self, parent_frame, ancho=700, alto=600):
        """
        Inicializa el visualizador de trayecto.

        Args:
            parent_frame: Frame padre donde se colocará el visualizador
            ancho: Ancho del canvas en píxeles
            alto: Alto del canvas en píxeles
        """
        self.parent_frame = parent_frame
        self.ancho_canvas = ancho
        self.alto_canvas = alto

        # Configuración del espacio de vuelo (4x4 metros)
        self.espacio_vuelo = 4.0  # metros
        self.escala = (min(self.ancho_canvas, self.alto_canvas) * 0.8) / self.espacio_vuelo

        # Centro del canvas (origen de coordenadas)
        self.centro_x = self.ancho_canvas // 2
        self.centro_y = self.alto_canvas // 2

        # Historial de posiciones
        self.trayecto = []
        self.posicion_actual = [0.0, 0.0, 0.0]

        # Modo de edición interactiva
        self.modo_edicion = False
        self.waypoints_temporales = []
        self.marcadores_temporales = []
        self.validation_callback = None

        # NUEVO: Referencia al GeocageCreator activo (si existe)
        # IMPORTANTE: DEBE ESTAR ANTES DE _crear_visualizador()
        self.geocage_creator_activo = None

        # Elementos gráficos
        self.canvas = None
        self.dron_obj = None
        self.lineas_trayecto = []
        self.label_altura = None
        self.label_posicion = None

        # Crear visualizador DESPUÉS de inicializar todas las variables
        self._crear_visualizador()

    def _crear_visualizador(self):
        """Crea todos los elementos visuales del sistema"""

        # Frame contenedor principal
        container = tk.Frame(self.parent_frame, bg="white")
        container.pack(fill=tk.BOTH, expand=True)

        # Título
        titulo = tk.Label(container, text="🛸 Visualizador de Trayecto 3D",
                         font=("Arial", 14, "bold"), bg="white")
        titulo.pack(pady=5)

        # Frame para canvas y panel lateral
        frame_principal = tk.Frame(container, bg="white")
        frame_principal.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Canvas para el trayecto (plano XY) - Ahora se expande
        canvas_frame = tk.Frame(frame_principal, bg="white")
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.canvas = Canvas(canvas_frame, bg="#f0f0f0",
                            highlightthickness=1, highlightbackground="#cccccc")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Vincular evento de redimensionamiento
        self.canvas.bind('<Configure>', self._on_canvas_resize)

        # Panel lateral derecho para información
        panel_info = tk.Frame(frame_principal, bg="white", width=200)
        panel_info.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        panel_info.pack_propagate(False)  # Mantener ancho fijo

        # Indicador de altura
        tk.Label(panel_info, text="ALTURA (Z)", font=("Arial", 12, "bold"),
                bg="white").pack(pady=(10, 5))

        self.label_altura = tk.Label(panel_info, text="0.00 m",
                                     font=("Arial", 28, "bold"),
                                     fg="#2196F3", bg="white")
        self.label_altura.pack(pady=5)

        # Barra visual de altura
        self.frame_barra_altura = tk.Frame(panel_info, bg="white", width=100, height=250)
        self.frame_barra_altura.pack(pady=15)
        self.frame_barra_altura.pack_propagate(False)

        self.canvas_barra = Canvas(self.frame_barra_altura, width=80, height=250,
                                  bg="#e0e0e0", highlightthickness=1,
                                  highlightbackground="#999999")
        self.canvas_barra.pack()

        # Referencias de altura en la barra
        self._dibujar_escala_altura()

        # Indicador de altura en barra (rectángulo azul)
        self.indicador_altura = self.canvas_barra.create_rectangle(
            5, 245, 75, 250, fill="#2196F3", outline=""
        )

        # Separador
        tk.Frame(panel_info, height=2, bg="#cccccc").pack(fill=tk.X, pady=15)

        # Posición XY
        tk.Label(panel_info, text="POSICIÓN", font=("Arial", 12, "bold"),
                bg="white").pack(pady=(5, 5))

        self.label_posicion = tk.Label(panel_info,
                                       text="X: 0.00 m\nY: 0.00 m",
                                       font=("Arial", 11),
                                       bg="white", justify=tk.LEFT)
        self.label_posicion.pack(pady=5)

        # Botón limpiar trayecto
        tk.Button(panel_info, text="🗑 Limpiar\nTrayecto",
                 command=self.limpiar_trayecto,
                 bg="#ff5722", fg="white",
                 font=("Arial", 10, "bold"),
                 height=3).pack(pady=20, fill=tk.X, padx=5)

        # Leyenda en la parte inferior
        frame_leyenda = tk.Frame(container, bg="white")
        frame_leyenda.pack(fill=tk.X, pady=5)

        tk.Label(frame_leyenda, text="🔴 Trayecto recorrido  |  🔵 Posición actual  |  📏 Espacio: 4m × 4m",
                font=("Arial", 9), bg="white").pack()

        # Dibujar grid inicial
        self._dibujar_grid()

        # Dibujar dron en posición inicial
        self._dibujar_dron()

        # Vincular eventos de click en el canvas
        self.canvas.bind('<Button-1>', self._on_canvas_click)

    def activar_modo_edicion(self, validation_callback=None):
        self.modo_edicion = True
        self.waypoints_temporales = []
        self.marcadores_temporales = []
        self.validation_callback = validation_callback
        self._log_edicion("Modo edición ACTIVADO - Click en el canvas para añadir waypoints")

    def desactivar_modo_edicion(self):
        """Desactiva el modo de edición interactiva"""
        self.modo_edicion = False
        self.validation_callback = None
        self._limpiar_waypoints_temporales()
        self._log_edicion("Modo edición DESACTIVADO")

    def _on_canvas_click(self, event):
        """Maneja los clicks en el canvas"""

        # NUEVO: Si hay un GeocageCreator activo, redirigir el click ahí
        if self.geocage_creator_activo is not None:
            print("[Visualizador] Redirigiendo click a GeocageCreator...")
            self.geocage_creator_activo.procesar_click(event)
            return  # No procesar más

        # Si no hay geocage activo, procesar normalmente según el modo
        if not self.modo_edicion:
            return

        # Convertir coordenadas de píxeles a metros
        x_metros = (event.x - self.centro_x) / self.escala
        y_metros = -(event.y - self.centro_y) / self.escala
        z_metros = 0.5  # Altura por defecto

        # Añadir waypoint temporal
        self.waypoints_temporales.append((x_metros, y_metros, z_metros))

        # Dibujar marcador
        self._dibujar_marcador_temporal(event.x, event.y, len(self.waypoints_temporales))

        # Dibujar línea conectando waypoints
        if len(self.waypoints_temporales) == 1:
            self._dibujar_linea_desde_origen(event.x, event.y)
        else:
            self._dibujar_linea_temporal()

        self._log_edicion(
            f"Waypoint {len(self.waypoints_temporales)}: X={x_metros:.2f}m, Y={y_metros:.2f}m, Z={z_metros:.2f}m")

    def _dibujar_marcador_temporal(self, x_pixel, y_pixel, numero):
        """Dibuja un marcador temporal en el canvas"""
        # Círculo verde para el waypoint
        radio = 10
        circulo = self.canvas.create_oval(
            x_pixel - radio, y_pixel - radio,
            x_pixel + radio, y_pixel + radio,
            fill="#4CAF50", outline="#2E7D32", width=2,
            tags="temp_marker"
        )

        # Número del waypoint
        texto = self.canvas.create_text(
            x_pixel, y_pixel,
            text=str(numero),
            fill="white",
            font=("Arial", 10, "bold"),
            tags="temp_marker"
        )

        self.marcadores_temporales.append((circulo, texto))

    def _dibujar_linea_temporal(self):
        """Dibuja línea entre los dos últimos waypoints temporales"""
        if len(self.waypoints_temporales) < 2:
            return

        # Obtener últimos dos waypoints
        x1, y1, z1 = self.waypoints_temporales[-2]
        x2, y2, z2 = self.waypoints_temporales[-1]

        # Convertir a píxeles
        x1_pixel = self.centro_x + (x1 * self.escala)
        y1_pixel = self.centro_y - (y1 * self.escala)

        x2_pixel = self.centro_x + (x2 * self.escala)
        y2_pixel = self.centro_y - (y2 * self.escala)

        # Dibujar línea punteada verde
        linea = self.canvas.create_line(
            x1_pixel, y1_pixel, x2_pixel, y2_pixel,
            fill="#4CAF50", width=2, dash=(5, 3),
            tags="temp_line"
        )

    def _limpiar_waypoints_temporales(self):
        """Limpia todos los waypoints temporales del canvas"""
        self.canvas.delete("temp_marker")
        self.canvas.delete("temp_line")
        self.waypoints_temporales = []
        self.marcadores_temporales = []

    def convertir_lineas_temporales_a_permanentes(self):
        """Convierte las líneas verdes temporales preparándolas para conversión a rojas"""
        self.canvas.delete("temp_marker")
        self.marcadores_temporales = []

    def dibujar_linea_permanente(self, x1, y1, x2, y2):
        """Dibuja una línea roja permanente entre dos puntos en metros"""
        x1_pixel = self.centro_x + (x1 * self.escala)
        y1_pixel = self.centro_y - (y1 * self.escala)
        x2_pixel = self.centro_x + (x2 * self.escala)
        y2_pixel = self.centro_y - (y2 * self.escala)

        linea = self.canvas.create_line(
            x1_pixel, y1_pixel, x2_pixel, y2_pixel,
            fill="#f44336", width=3, smooth=True
        )
        self.lineas_trayecto.append(linea)

    def obtener_waypoints_temporales(self):
        """Retorna la lista de waypoints temporales creados"""
        return self.waypoints_temporales.copy()

    def tiene_waypoints_temporales(self):
        """Verifica si hay waypoints temporales"""
        return len(self.waypoints_temporales) > 0

    def _log_edicion(self, mensaje):
        """Log específico para el modo edición (se puede sobreescribir)"""
        print(f"[Visualizador] {mensaje}")

    def _on_canvas_resize(self, event):
        """Maneja el redimensionamiento del canvas"""
        # Actualizar dimensiones
        self.ancho_canvas = event.width
        self.alto_canvas = event.height

        # Recalcular centro y escala
        self.centro_x = self.ancho_canvas // 2
        self.centro_y = self.alto_canvas // 2
        self.escala = (min(self.ancho_canvas, self.alto_canvas) * 0.8) / self.espacio_vuelo

        # Redibujar todo
        self._redibujar_todo()

    def _redibujar_todo(self):
        """Redibuja todo el contenido del canvas"""
        # Limpiar canvas
        self.canvas.delete("all")

        # Redibujar grid
        self._dibujar_grid()

        # Redibujar trayecto completo
        if len(self.trayecto) > 1:
            for i in range(1, len(self.trayecto)):
                x1, y1, z1 = self.trayecto[i-1]
                x2, y2, z2 = self.trayecto[i]

                x1_pixel = self.centro_x + (x1 * self.escala)
                y1_pixel = self.centro_y - (y1 * self.escala)

                x2_pixel = self.centro_x + (x2 * self.escala)
                y2_pixel = self.centro_y - (y2 * self.escala)

                linea = self.canvas.create_line(
                    x1_pixel, y1_pixel, x2_pixel, y2_pixel,
                    fill="#f44336", width=3, smooth=True
                )
                self.lineas_trayecto.append(linea)

        # Redibujar dron
        self._dibujar_dron()

    def _dibujar_grid(self):
        """Dibuja la cuadrícula de referencia en el canvas"""
        # Limpiar canvas
        self.canvas.delete("grid")

        # Dibujar líneas de la cuadrícula cada 0.5 metros
        for i in range(-4, 5):
            distancia = i * 0.5
            pixel_pos = distancia * self.escala

            # Líneas verticales
            x = self.centro_x + pixel_pos
            self.canvas.create_line(x, 20, x, self.alto_canvas - 20,
                                   fill="#d0d0d0", width=1, tags="grid")

            # Líneas horizontales
            y = self.centro_y + pixel_pos
            self.canvas.create_line(20, y, self.ancho_canvas - 20, y,
                                   fill="#d0d0d0", width=1, tags="grid")

        # Ejes principales (X e Y)
        # Eje X (rojo) - horizontal
        self.canvas.create_line(20, self.centro_y, self.ancho_canvas - 20, self.centro_y,
                               fill="#ff6b6b", width=2, tags="grid", arrow=tk.LAST)
        self.canvas.create_text(self.ancho_canvas - 30, self.centro_y - 15,
                               text="X", fill="#ff6b6b", font=("Arial", 12, "bold"),
                               tags="grid")

        # Eje Y (verde) - vertical
        self.canvas.create_line(self.centro_x, self.alto_canvas - 20, self.centro_x, 20,
                               fill="#4caf50", width=2, tags="grid", arrow=tk.LAST)
        self.canvas.create_text(self.centro_x + 15, 30,
                               text="Y", fill="#4caf50", font=("Arial", 12, "bold"),
                               tags="grid")

        # Etiquetas de distancias
        distancias = [-2, -1, 1, 2]
        for d in distancias:
            pixel_pos = d * self.escala

            # Etiquetas en eje X
            x = self.centro_x + pixel_pos
            self.canvas.create_text(x, self.centro_y + 15,
                                   text=f"{d}m", fill="#666",
                                   font=("Arial", 8), tags="grid")

            # Etiquetas en eje Y
            y = self.centro_y + pixel_pos
            self.canvas.create_text(self.centro_x - 15, y,
                                   text=f"{-d}m", fill="#666",
                                   font=("Arial", 8), tags="grid")

        # Origen
        self.canvas.create_text(self.centro_x + 15, self.centro_y + 15,
                               text="(0,0)", fill="#333",
                               font=("Arial", 8, "bold"), tags="grid")

    def _dibujar_escala_altura(self):
        """Dibuja la escala de referencia en la barra de altura"""
        # Escala de 0 a 2 metros
        alturas = [0, 0.5, 1.0, 1.5, 2.0]
        altura_max_visual = 2.0  # metros

        for alt in alturas:
            # Calcular posición Y en la barra (invertida)
            y_pos = 250 - (alt / altura_max_visual * 250)

            # Línea de referencia
            self.canvas_barra.create_line(0, y_pos, 80, y_pos,
                                         fill="#999", width=1)

            # Texto de altura
            self.canvas_barra.create_text(40, y_pos - 12,
                                         text=f"{alt}m",
                                         font=("Arial", 8),
                                         fill="#666")

    def _dibujar_dron(self):
        """Dibuja el dron en su posición actual"""
        # Eliminar dron anterior si existe
        if self.dron_obj:
            self.canvas.delete(self.dron_obj)

        # Convertir coordenadas del dron a píxeles
        x_pixel = self.centro_x + (self.posicion_actual[0] * self.escala)
        y_pixel = self.centro_y - (self.posicion_actual[1] * self.escala)  # Y invertida

        # Dibujar dron como círculo azul con borde
        radio = 8
        self.dron_obj = self.canvas.create_oval(
            x_pixel - radio, y_pixel - radio,
            x_pixel + radio, y_pixel + radio,
            fill="#2196F3", outline="#1976D2", width=2
        )

        # Añadir cruz en el centro para mejor visibilidad
        self.canvas.create_line(x_pixel - 4, y_pixel, x_pixel + 4, y_pixel,
                               fill="white", width=2)
        self.canvas.create_line(x_pixel, y_pixel - 4, x_pixel, y_pixel + 4,
                               fill="white", width=2)

    def _dibujar_linea_desde_origen(self, x2_pixel, y2_pixel):
        """Dibuja línea desde el origen (0,0) al primer waypoint"""
        # Origen en píxeles
        x1_pixel = self.centro_x
        y1_pixel = self.centro_y

        # Dibujar línea punteada verde desde origen
        linea = self.canvas.create_line(
            x1_pixel, y1_pixel, x2_pixel, y2_pixel,
            fill="#4CAF50", width=2, dash=(5, 3),
            tags="temp_line"
        )

    def actualizar_posicion(self, x: float, y: float, z: float, animar_movimiento: bool = False):
        """
        Actualiza la posición del dron y dibuja el trayecto.

        Args:
            x: Coordenada X en metros (adelante/atrás)
            y: Coordenada Y en metros (izquierda/derecha)
            z: Coordenada Z en metros (altura)
            animar_movimiento: Si True, anima el movimiento del dron siguiendo la línea
        """
        # Guardar posición anterior
        pos_anterior = self.posicion_actual.copy()

        if animar_movimiento and len(self.trayecto) > 0:
            # Animar el movimiento del dron desde la posición anterior a la nueva
            pasos_animacion = 15

            for i in range(pasos_animacion + 1):
                t = i / pasos_animacion

                # Interpolación lineal
                x_temp = pos_anterior[0] + (x - pos_anterior[0]) * t
                y_temp = pos_anterior[1] + (y - pos_anterior[1]) * t
                z_temp = pos_anterior[2] + (z - pos_anterior[2]) * t

                # Actualizar posición del dron (sin añadir al trayecto aún)
                self.posicion_actual = [x_temp, y_temp, z_temp]

                # Redibujar solo el dron
                self._dibujar_dron()

                # Actualizar indicadores
                self._actualizar_indicadores()

                # Actualizar canvas y pequeña pausa
                self.canvas.update()
                self.canvas.after(30)

        # Actualizar posición final
        self.posicion_actual = [x, y, z]

        # Añadir al trayecto
        self.trayecto.append((x, y, z))

        # Dibujar línea desde posición anterior a actual
        if len(self.trayecto) > 1:
            x1_pixel = self.centro_x + (pos_anterior[0] * self.escala)
            y1_pixel = self.centro_y - (pos_anterior[1] * self.escala)

            x2_pixel = self.centro_x + (x * self.escala)
            y2_pixel = self.centro_y - (y * self.escala)

            # Dibujar línea del trayecto
            linea = self.canvas.create_line(
                x1_pixel, y1_pixel, x2_pixel, y2_pixel,
                fill="#f44336", width=3, smooth=True
            )
            self.lineas_trayecto.append(linea)

        # Redibujar dron en nueva posición
        self._dibujar_dron()

        # Actualizar indicadores de información
        self._actualizar_indicadores()

    def _actualizar_indicadores(self):
        """Actualiza los indicadores de altura y posición"""
        x, y, z = self.posicion_actual

        # Actualizar label de altura
        self.label_altura.config(text=f"{z:.2f} m")

        # Actualizar label de posición XY
        self.label_posicion.config(text=f"X: {x:+.2f} m\nY: {y:+.2f} m")

        # Actualizar barra de altura
        altura_max_visual = 2.0
        z_limitado = min(max(z, 0), altura_max_visual)

        # Calcular posición del indicador (invertida)
        y_top = 250 - (z_limitado / altura_max_visual * 245)
        y_bottom = 250

        # Actualizar rectángulo indicador
        self.canvas_barra.coords(self.indicador_altura, 5, y_top, 75, y_bottom)

        # Cambiar color según altura
        if z < 0.3:
            color = "#f44336"  # Rojo - muy bajo
        elif z < 0.8:
            color = "#ff9800"  # Naranja - bajo
        else:
            color = "#2196F3"  # Azul - altura normal

        self.canvas_barra.itemconfig(self.indicador_altura, fill=color)

    def limpiar_trayecto(self):
        """Limpia todo el trayecto y reinicia la visualización"""
        # Eliminar todas las líneas del trayecto
        for linea in self.lineas_trayecto:
            self.canvas.delete(linea)

        self.lineas_trayecto.clear()
        self.trayecto.clear()

        # Resetear posición a origen
        self.posicion_actual = [0.0, 0.0, 0.0]

        # Redibujar dron en origen
        self._dibujar_dron()

        # Actualizar indicadores
        self._actualizar_indicadores()

    def simular_patron(self, patron: str = "cuadrado", tamano: float = 2.0):
        """
        Simula un patrón de vuelo para demostración.

        Args:
            patron: Tipo de patrón ('cuadrado', 'circulo', 'linea')
            tamano: Tamaño del patrón en metros
        """
        self.limpiar_trayecto()

        if patron == "cuadrado":
            # Subir a altura de vuelo
            for i in range(6):
                self.actualizar_posicion(0, 0, i * 0.1)
                self.canvas.update()
                self.canvas.after(100)

            # Cuadrado
            puntos = [
                (tamano, 0, 0.5),
                (tamano, tamano, 0.5),
                (0, tamano, 0.5),
                (0, 0, 0.5)
            ]

            for px, py, pz in puntos:
                pasos = 20
                x_actual, y_actual, z_actual = self.posicion_actual

                for i in range(pasos + 1):
                    t = i / pasos
                    x = x_actual + (px - x_actual) * t
                    y = y_actual + (py - y_actual) * t
                    z = z_actual + (pz - z_actual) * t

                    self.actualizar_posicion(x, y, z)
                    self.canvas.update()
                    self.canvas.after(50)

        elif patron == "circulo":
            # Subir
            for i in range(6):
                self.actualizar_posicion(0, 0, i * 0.1)
                self.canvas.update()
                self.canvas.after(100)

            # Círculo
            radio = tamano / 2
            num_puntos = 50

            for i in range(num_puntos + 1):
                angulo = (i / num_puntos) * 2 * math.pi
                x = radio * math.cos(angulo)
                y = radio * math.sin(angulo)

                self.actualizar_posicion(x, y, 0.5)
                self.canvas.update()
                self.canvas.after(50)


# ==================== DEMO STANDALONE ====================
if __name__ == "__main__":
    def test_visualizador():
        """Función de prueba del visualizador"""
        root = tk.Tk()
        root.title("Test - Visualizador de Trayecto 3D")
        root.geometry("900x700")

        # Frame principal
        frame = tk.Frame(root, bg="white")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Crear visualizador sin dimensiones fijas
        viz = VisualizadorTrayecto3D(frame)

        # Frame de botones de prueba
        frame_botones = tk.Frame(root, bg="#f0f0f0")
        frame_botones.pack(fill=tk.X, pady=10)

        tk.Label(frame_botones, text="Pruebas:", font=("Arial", 10, "bold"),
                bg="#f0f0f0").pack(side=tk.LEFT, padx=10)

        tk.Button(frame_botones, text="Simular Cuadrado",
                 command=lambda: viz.simular_patron("cuadrado", 2.0),
                 bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)

        tk.Button(frame_botones, text="Simular Círculo",
                 command=lambda: viz.simular_patron("circulo", 2.0),
                 bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=5)

        tk.Button(frame_botones, text="Limpiar",
                 command=viz.limpiar_trayecto,
                 bg="#f44336", fg="white").pack(side=tk.LEFT, padx=5)

        root.mainloop()

    test_visualizador()