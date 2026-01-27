"""
Visualizador de Telemetría en Tiempo Real para Crazyflie - VERSIÓN MEJORADA
Sistema de visualización con interfaz reestructurada y más compacta
"""

import tkinter as tk
from tkinter import Canvas
import math
from typing import List, Tuple, Optional
import threading
import time


class VisualizadorTelemetriaRealtime:
    """
    Visualizador mejorado del trayecto del dron con telemetría en tiempo real.
    Versión optimizada con interfaz más compacta y visible.
    """

    def __init__(self, parent_frame, ancho=700, alto=600, dron=None):
        """
        Inicializa el visualizador de telemetría en tiempo real.

        Args:
            parent_frame: Frame padre donde se colocará el visualizador
            ancho: Ancho del canvas en píxeles
            alto: Alto del canvas en píxeles
            dron: Instancia del dron para monitoreo en tiempo real (opcional)
        """
        self.parent_frame = parent_frame
        self.ancho_canvas = ancho
        self.alto_canvas = alto
        self.dron = dron

        # Configuración del espacio de vuelo DINÁMICO
        self.espacio_base = 4.0
        self.espacio_vuelo = self.espacio_base

        # Niveles de zoom basados en altura
        self.zoom_levels = {
            0.0: 0.4,
            0.3: 1.0,
            0.5: 2.0,
            1.0: 4.0,
            1.5: 6.0,
            2.0: 8.0
        }

        self.escala = (min(self.ancho_canvas, self.alto_canvas) * 0.8) / self.espacio_vuelo

        # Centro del canvas
        self.centro_x = self.ancho_canvas // 2
        self.centro_y = self.alto_canvas // 2

        # Historial de posiciones
        self.trayecto = []
        self.posicion_actual = [0.0, 0.0, 0.0]
        self.posicion_anterior = [0.0, 0.0, 0.0]

        # Modo de edición
        self.modo_edicion = False
        self.waypoints_temporales = []
        self.marcadores_temporales = []
        self.validation_callback = None
        self.geocage_creator_activo = None

        # Elementos gráficos
        self.canvas = None
        self.dron_obj = None
        self.lineas_trayecto = []
        self.label_altura = None
        self.label_posicion = None
        self.label_zoom = None
        self.label_velocidad = None

        # Monitoreo en tiempo real
        self.monitoreo_activo = False
        self.thread_monitoreo = None
        self.ultima_posicion_leida = None

        # Variables para calcular velocidad
        self.tiempo_ultima_actualizacion = time.time()
        self.velocidad_actual = 0.0

        # Log function (compatible con versión anterior)
        self._log_edicion = lambda msg: print(f"[Visualizador] {msg}")

        # Crear visualizador
        self._crear_visualizador()

    def _crear_visualizador(self):
        """Crea todos los elementos visuales del sistema - VERSIÓN OPTIMIZADA"""

        # Frame contenedor principal
        container = tk.Frame(self.parent_frame, bg="white")
        container.pack(fill=tk.BOTH, expand=True)

        # ========== TÍTULO CON ESTADO ==========
        frame_titulo = tk.Frame(container, bg="white")
        frame_titulo.pack(pady=5, fill=tk.X)

        titulo = tk.Label(frame_titulo, text="🛸 Telemetría en Tiempo Real",
                          font=("Arial", 13, "bold"), bg="white")
        titulo.pack(side=tk.LEFT, padx=10)

        self.label_telemetria_status = tk.Label(
            frame_titulo, text="⚫ Desconectado",
            font=("Arial", 9, "bold"), fg="gray", bg="white"
        )
        self.label_telemetria_status.pack(side=tk.LEFT, padx=10)

        # ========== FRAME PRINCIPAL DIVIDIDO ==========
        frame_principal = tk.Frame(container, bg="white")
        frame_principal.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # ===== CANVAS (IZQUIERDA) =====
        canvas_frame = tk.Frame(frame_principal, bg="white")
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.canvas = Canvas(canvas_frame, bg="#f0f0f0",
                             highlightthickness=2, highlightbackground="#2196F3")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind('<Configure>', self._on_canvas_resize)
        self.canvas.bind('<Button-1>', self._on_canvas_click)

        # ===== PANEL LATERAL (DERECHA) - OPTIMIZADO =====
        # Usar un Canvas con scrollbar para el panel lateral
        panel_container = tk.Frame(frame_principal, bg="white", width=200)
        panel_container.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        panel_container.pack_propagate(False)

        # Canvas scrollable
        canvas_scroll = Canvas(panel_container, bg="white", width=200,
                               highlightthickness=0)
        scrollbar = tk.Scrollbar(panel_container, orient="vertical",
                                 command=canvas_scroll.yview)

        # Frame interno que contendrá todos los widgets
        panel_info = tk.Frame(canvas_scroll, bg="white")

        # Configurar el canvas scrollable
        canvas_scroll.create_window((0, 0), window=panel_info, anchor="nw")
        canvas_scroll.configure(yscrollcommand=scrollbar.set)

        # Empaquetar el canvas y scrollbar
        canvas_scroll.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Actualizar scroll region cuando cambie el tamaño
        def _configure_scroll(event):
            canvas_scroll.configure(scrollregion=canvas_scroll.bbox("all"))

        panel_info.bind("<Configure>", _configure_scroll)

        # ============ ALTURA (COMPACTO) ============
        tk.Label(panel_info, text="ALTURA (Z)",
                 font=("Arial", 11, "bold"), bg="white").pack(pady=(5, 3))

        self.label_altura = tk.Label(panel_info, text="0.00 m",
                                     font=("Arial", 22, "bold"),
                                     fg="#2196F3", bg="white")
        self.label_altura.pack(pady=3)

        # Barra visual de altura (MÁS COMPACTA)
        self.frame_barra_altura = tk.Frame(panel_info, bg="white",
                                           width=90, height=150)
        self.frame_barra_altura.pack(pady=8)
        self.frame_barra_altura.pack_propagate(False)

        self.canvas_barra = Canvas(self.frame_barra_altura, width=75, height=150,
                                   bg="#e0e0e0", highlightthickness=1,
                                   highlightbackground="#999999")
        self.canvas_barra.pack()

        # Referencias de altura en la barra
        self._dibujar_escala_altura()

        # Indicador de altura en barra
        self.indicador_altura = self.canvas_barra.create_rectangle(
            5, 145, 70, 150, fill="#2196F3", outline=""
        )

        # ============ POSICIÓN (COMPACTO) ============
        tk.Frame(panel_info, height=1, bg="#cccccc").pack(fill=tk.X, pady=8)

        tk.Label(panel_info, text="POSICIÓN",
                 font=("Arial", 11, "bold"), bg="white").pack(pady=(3, 3))

        self.label_posicion = tk.Label(panel_info,
                                       text="X: 0.00 m\nY: 0.00 m",
                                       font=("Arial", 10),
                                       bg="white", justify=tk.LEFT)
        self.label_posicion.pack(pady=3)

        # ============ ZOOM (COMPACTO) ============
        tk.Frame(panel_info, height=1, bg="#cccccc").pack(fill=tk.X, pady=8)

        tk.Label(panel_info, text="ZOOM",
                 font=("Arial", 11, "bold"), bg="white").pack(pady=(3, 3))

        self.label_zoom = tk.Label(panel_info,
                                   text="🔍 4.0m × 4.0m",
                                   font=("Arial", 9),
                                   fg="#FF9800", bg="white")
        self.label_zoom.pack(pady=3)

        # ============ VELOCIDAD (COMPACTO) ============
        tk.Frame(panel_info, height=1, bg="#cccccc").pack(fill=tk.X, pady=8)

        tk.Label(panel_info, text="VELOCIDAD",
                 font=("Arial", 11, "bold"), bg="white").pack(pady=(3, 3))

        self.label_velocidad = tk.Label(panel_info,
                                        text="0.00 m/s",
                                        font=("Arial", 12, "bold"),
                                        fg="#4CAF50", bg="white")
        self.label_velocidad.pack(pady=3)

        # ============ BOTONES DE CONTROL (COMPACTOS) ============
        tk.Frame(panel_info, height=1, bg="#cccccc").pack(fill=tk.X, pady=10)

        self.btn_toggle_monitoreo = tk.Button(
            panel_info, text="▶ Iniciar Telemetría",
            command=self._toggle_monitoreo,
            bg="#4CAF50", fg="white",
            font=("Arial", 9, "bold"),
            height=2,
            relief=tk.RAISED,
            bd=2
        )
        self.btn_toggle_monitoreo.pack(pady=5, fill=tk.X, padx=10)

        tk.Button(panel_info, text="🗑 Limpiar Trayecto",
                  command=self.limpiar_trayecto,
                  bg="#ff5722", fg="white",
                  font=("Arial", 9, "bold"),
                  height=2,
                  relief=tk.RAISED,
                  bd=2).pack(pady=5, fill=tk.X, padx=10)

        # Espacio al final para que se pueda hacer scroll
        tk.Label(panel_info, text="", bg="white", height=2).pack()

        # ========== LEYENDA INFERIOR ==========
        frame_leyenda = tk.Frame(container, bg="white")
        frame_leyenda.pack(fill=tk.X, pady=5)

        leyenda_text = (
            "🔴 Trayecto  |  🔵 Dron  |  "
            "↑ ADELANTE  |  ↓ ATRÁS  |  "
            "← IZQUIERDA  |  → DERECHA"
        )
        tk.Label(frame_leyenda, text=leyenda_text,
                 font=("Arial", 8), bg="white").pack()

        # Dibujar grid y dron inicial
        self._dibujar_grid()
        self._dibujar_dron()

    def _dibujar_escala_altura(self):
        """Dibuja la escala de altura en la barra lateral - VERSIÓN COMPACTA"""
        alturas = [0, 0.5, 1.0, 1.5, 2.0]
        altura_max = 2.0

        for alt in alturas:
            y_pos = 150 - (alt / altura_max * 145)  # Ajustado para barra más pequeña

            # Línea de referencia
            self.canvas_barra.create_line(
                5, y_pos, 12, y_pos,
                fill="#666666", width=1
            )

            # Texto
            self.canvas_barra.create_text(
                43, y_pos,
                text=f"{alt:.1f}m",
                font=("Arial", 7),
                fill="#666666"
            )

    def _calcular_zoom_por_altura(self, altura: float) -> float:
        """Calcula el espacio de vuelo visible según la altura"""
        niveles = sorted(self.zoom_levels.keys())

        if altura <= niveles[0]:
            return self.zoom_levels[niveles[0]]
        elif altura >= niveles[-1]:
            return self.zoom_levels[niveles[-1]]

        # Interpolación entre niveles
        for i in range(len(niveles) - 1):
            if niveles[i] <= altura <= niveles[i + 1]:
                h1, h2 = niveles[i], niveles[i + 1]
                z1, z2 = self.zoom_levels[h1], self.zoom_levels[h2]

                t = (altura - h1) / (h2 - h1)
                return z1 + (z2 - z1) * t

        return self.espacio_base

    def _actualizar_zoom(self, altura: float):
        """Actualiza el zoom del canvas según la altura"""
        nuevo_espacio = self._calcular_zoom_por_altura(altura)

        if abs(nuevo_espacio - self.espacio_vuelo) > 0.1:
            self.espacio_vuelo = nuevo_espacio
            self.escala = (min(self.ancho_canvas, self.alto_canvas) * 0.8) / self.espacio_vuelo
            self._redibujar_todo()
            self.label_zoom.config(text=f"🔍 {self.espacio_vuelo:.1f}m × {self.espacio_vuelo:.1f}m")

    def _redibujar_todo(self):
        """Redibuja todo el canvas con la nueva escala"""
        self.canvas.delete("all")
        self._dibujar_grid()

        if len(self.trayecto) > 1:
            for i in range(1, len(self.trayecto)):
                x1, y1, z1 = self.trayecto[i - 1]
                x2, y2, z2 = self.trayecto[i]

                x1_pixel = self.centro_x + (x1 * self.escala)
                y1_pixel = self.centro_y - (y1 * self.escala)
                x2_pixel = self.centro_x + (x2 * self.escala)
                y2_pixel = self.centro_y - (y2 * self.escala)

                self.canvas.create_line(
                    x1_pixel, y1_pixel, x2_pixel, y2_pixel,
                    fill="#f44336", width=3, smooth=True
                )

        self._dibujar_dron()

    def _dibujar_grid(self):
        """Dibuja la cuadrícula y las etiquetas de dirección"""
        color_grid = "#cccccc"
        color_eje = "#999999"

        if self.espacio_vuelo <= 1.0:
            paso = 0.1
        elif self.espacio_vuelo <= 2.0:
            paso = 0.25
        elif self.espacio_vuelo <= 4.0:
            paso = 0.5
        else:
            paso = 1.0

        num_lineas = int(self.espacio_vuelo / paso)

        for i in range(-num_lineas, num_lineas + 1):
            pos_metros = i * paso

            # Líneas verticales
            x_pixel = self.centro_x + (pos_metros * self.escala)
            if 0 <= x_pixel <= self.ancho_canvas:
                color = color_eje if i == 0 else color_grid
                width = 2 if i == 0 else 1
                self.canvas.create_line(
                    x_pixel, 0, x_pixel, self.alto_canvas,
                    fill=color, width=width, dash=(4, 4) if i != 0 else ()
                )

            # Líneas horizontales
            y_pixel = self.centro_y + (pos_metros * self.escala)
            if 0 <= y_pixel <= self.alto_canvas:
                color = color_eje if i == 0 else color_grid
                width = 2 if i == 0 else 1
                self.canvas.create_line(
                    0, y_pixel, self.ancho_canvas, y_pixel,
                    fill=color, width=width, dash=(4, 4) if i != 0 else ()
                )

        # ETIQUETAS DE DIRECCIÓN
        padding = 25
        font_size = 11

        self.canvas.create_text(
            self.centro_x, padding,
            text="↑ ADELANTE",
            font=("Arial", font_size, "bold"),
            fill="#4CAF50"
        )

        self.canvas.create_text(
            self.centro_x, self.alto_canvas - padding,
            text="↓ ATRÁS",
            font=("Arial", font_size, "bold"),
            fill="#f44336"
        )

        self.canvas.create_text(
            padding + 10, self.centro_y,
            text="← IZQ",
            font=("Arial", font_size, "bold"),
            fill="#2196F3",
            angle=90
        )

        self.canvas.create_text(
            self.ancho_canvas - padding - 10, self.centro_y,
            text="DER →",
            font=("Arial", font_size, "bold"),
            fill="#FF9800",
            angle=90
        )

        # Origen
        self.canvas.create_oval(
            self.centro_x - 4, self.centro_y - 4,
            self.centro_x + 4, self.centro_y + 4,
            fill="black", outline="white", width=2
        )
        self.canvas.create_text(
            self.centro_x + 18, self.centro_y - 12,
            text="(0,0)",
            font=("Arial", 8, "bold"),
            fill="black"
        )

    def _dibujar_dron(self):
        """Dibuja el dron en su posición actual - SIN círculos extras"""
        x, y, z = self.posicion_actual

        x_pixel = self.centro_x + (x * self.escala)
        y_pixel = self.centro_y - (y * self.escala)

        # Eliminar dron anterior
        if self.dron_obj:
            self.canvas.delete(self.dron_obj)

        # Tamaño según zoom
        if self.espacio_vuelo <= 1.0:
            radio = 15
        elif self.espacio_vuelo <= 2.0:
            radio = 12
        else:
            radio = 10

        # ✅ SOLO el círculo principal del dron (sin extras)
        self.dron_obj = self.canvas.create_oval(
            x_pixel - radio, y_pixel - radio,
            x_pixel + radio, y_pixel + radio,
            fill="#2196F3", outline="white", width=3
        )

    def _on_canvas_resize(self, event):
        """Maneja el redimensionamiento del canvas"""
        self.ancho_canvas = event.width
        self.alto_canvas = event.height
        self.centro_x = self.ancho_canvas // 2
        self.centro_y = self.alto_canvas // 2
        self.escala = (min(self.ancho_canvas, self.alto_canvas) * 0.8) / self.espacio_vuelo
        self._redibujar_todo()

    def _on_canvas_click(self, event):
        """Maneja los clicks en el canvas"""
        if self.geocage_creator_activo is not None:
            self.geocage_creator_activo.procesar_click(event)
            return

        if not self.modo_edicion:
            return

        x_metros = (event.x - self.centro_x) / self.escala
        y_metros = -(event.y - self.centro_y) / self.escala
        z_metros = 0.5

        self.waypoints_temporales.append((x_metros, y_metros, z_metros))
        self._dibujar_marcador_temporal(event.x, event.y, len(self.waypoints_temporales))

    def _dibujar_marcador_temporal(self, x_pixel, y_pixel, numero):
        """Dibuja un marcador temporal en el canvas"""
        radio = 10
        circulo = self.canvas.create_oval(
            x_pixel - radio, y_pixel - radio,
            x_pixel + radio, y_pixel + radio,
            fill="#4CAF50", outline="#2E7D32", width=2,
            tags="temp_marker"
        )

        texto = self.canvas.create_text(
            x_pixel, y_pixel,
            text=str(numero),
            font=("Arial", 9, "bold"),
            fill="white",
            tags="temp_marker"
        )

        self.marcadores_temporales.extend([circulo, texto])

    def actualizar_posicion(self, x: float, y: float, z: float, animar_movimiento: bool = False):
        """Actualiza la posición del dron y dibuja el trayecto"""
        self.posicion_anterior = self.posicion_actual.copy()

        tiempo_actual = time.time()
        tiempo_transcurrido = tiempo_actual - self.tiempo_ultima_actualizacion

        if tiempo_transcurrido > 0:
            dx = x - self.posicion_anterior[0]
            dy = y - self.posicion_anterior[1]
            dz = z - self.posicion_anterior[2]
            distancia = math.sqrt(dx ** 2 + dy ** 2 + dz ** 2)
            self.velocidad_actual = distancia / tiempo_transcurrido

        self.tiempo_ultima_actualizacion = tiempo_actual

        self._actualizar_zoom(z)

        if animar_movimiento and len(self.trayecto) > 0:
            pasos_animacion = 15

            for i in range(pasos_animacion + 1):
                t = i / pasos_animacion

                x_temp = self.posicion_anterior[0] + (x - self.posicion_anterior[0]) * t
                y_temp = self.posicion_anterior[1] + (y - self.posicion_anterior[1]) * t
                z_temp = self.posicion_anterior[2] + (z - self.posicion_anterior[2]) * t

                self.posicion_actual = [x_temp, y_temp, z_temp]
                self._dibujar_dron()
                self._actualizar_indicadores()

                self.canvas.update()
                self.canvas.after(30)

        self.posicion_actual = [x, y, z]
        self.trayecto.append((x, y, z))

        if len(self.trayecto) > 1:
            x1_pixel = self.centro_x + (self.posicion_anterior[0] * self.escala)
            y1_pixel = self.centro_y - (self.posicion_anterior[1] * self.escala)

            x2_pixel = self.centro_x + (x * self.escala)
            y2_pixel = self.centro_y - (y * self.escala)

            linea = self.canvas.create_line(
                x1_pixel, y1_pixel, x2_pixel, y2_pixel,
                fill="#f44336", width=3, smooth=True
            )
            self.lineas_trayecto.append(linea)

        self._dibujar_dron()
        self._actualizar_indicadores()

    def _actualizar_indicadores(self):
        """Actualiza los indicadores de altura, posición y velocidad"""
        x, y, z = self.posicion_actual

        self.label_altura.config(text=f"{z:.2f} m")
        self.label_posicion.config(text=f"X: {x:+.2f} m\nY: {y:+.2f} m")
        self.label_velocidad.config(text=f"{self.velocidad_actual:.2f} m/s")

        altura_max_visual = 2.0
        z_limitado = min(max(z, 0), altura_max_visual)

        y_top = 150 - (z_limitado / altura_max_visual * 145)  # Ajustado para barra más pequeña
        y_bottom = 150

        self.canvas_barra.coords(self.indicador_altura, 5, y_top, 70, y_bottom)

        if z < 0.3:
            color = "#f44336"
        elif z < 0.8:
            color = "#ff9800"
        else:
            color = "#2196F3"

        self.canvas_barra.itemconfig(self.indicador_altura, fill=color)

    def limpiar_trayecto(self):
        """Limpia todo el trayecto y reinicia la visualización"""
        for linea in self.lineas_trayecto:
            self.canvas.delete(linea)

        self.lineas_trayecto.clear()
        self.trayecto.clear()
        self.posicion_actual = [0.0, 0.0, 0.0]
        self.posicion_anterior = [0.0, 0.0, 0.0]
        self.velocidad_actual = 0.0

        self._dibujar_dron()
        self._actualizar_indicadores()

    # ========== MONITOREO EN TIEMPO REAL ==========

    def configurar_dron(self, dron):
        """Configura el dron para monitoreo en tiempo real"""
        self.dron = dron
        print(f"[Visualizador] Dron configurado")

    def _toggle_monitoreo(self):
        """Activa/desactiva el monitoreo en tiempo real"""
        if not self.dron:
            print("[Visualizador] No hay dron configurado")
            return

        if self.monitoreo_activo:
            self._detener_monitoreo()
        else:
            self._iniciar_monitoreo()

    def _iniciar_monitoreo(self):
        """Inicia el monitoreo de telemetría en tiempo real"""
        if not self.dron:
            print("[Visualizador] No hay dron configurado")
            return

        self.monitoreo_activo = True
        self.btn_toggle_monitoreo.config(
            text="⏸ Pausar Telemetría",
            bg="#FF9800"
        )
        self.label_telemetria_status.config(
            text="🟢 Monitoreando",
            fg="#4CAF50"
        )

        self.thread_monitoreo = threading.Thread(target=self._loop_monitoreo, daemon=True)
        self.thread_monitoreo.start()

        print("[Visualizador] Monitoreo de telemetría iniciado")

    def _detener_monitoreo(self):
        """Detiene el monitoreo de telemetría"""
        self.monitoreo_activo = False
        self.btn_toggle_monitoreo.config(
            text="▶ Iniciar Telemetría",
            bg="#4CAF50"
        )
        self.label_telemetria_status.config(
            text="⚫ Pausado",
            fg="gray"
        )
        print("[Visualizador] Monitoreo de telemetría detenido")

    def _loop_monitoreo(self):
        """Loop principal de monitoreo (ejecutado en thread separado)"""
        print("[Visualizador] Loop de monitoreo iniciado")

        while self.monitoreo_activo:
            try:
                if self.dron and self.dron.state != "disconnected":
                    # Leer posición desde self.position
                    # IMPORTANTE: NO invertir Y aquí - ya viene corregido de dron_local_telemetry.py
                    if hasattr(self.dron, 'position') and len(self.dron.position) >= 3:
                        x = self.dron.position[0]      # X sin cambios
                        y = self.dron.position[1]      # Y SIN invertir (ya viene corregido)
                        z = self.dron.position[2]      # Z sin cambios
                    else:
                        x = getattr(self.dron, 'x', 0.0)
                        y = getattr(self.dron, 'y', 0.0)
                        z = getattr(self.dron, 'z', 0.0)

                    # Verificar si la posición cambió
                    if self.ultima_posicion_leida != (x, y, z):
                        self.ultima_posicion_leida = (x, y, z)

                        # Actualizar visualización
                        try:
                            x_val, y_val, z_val = x, y, z
                            self.canvas.after(0, lambda x=x_val, y=y_val, z=z_val:
                            self.actualizar_posicion(x, y, z))
                        except Exception as e:
                            print(f"[Visualizador] Error actualizar: {e}")

                time.sleep(0.1)

            except Exception as e:
                print(f"[Visualizador] Error en loop: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(0.5)

        print("[Visualizador] Loop de monitoreo finalizado")

    # ========== MÉTODOS DE COMPATIBILIDAD ==========

    def activar_modo_edicion(self, validation_callback=None):
        """Activa el modo de edición interactiva"""
        self.modo_edicion = True
        self.waypoints_temporales = []
        self.marcadores_temporales = []
        self.validation_callback = validation_callback
        self._log_edicion("Modo edición ACTIVADO")

    def desactivar_modo_edicion(self):
        """Desactiva el modo de edición"""
        self.modo_edicion = False
        self.validation_callback = None
        self._limpiar_waypoints_temporales()
        self._log_edicion("Modo edición DESACTIVADO")

    def _limpiar_waypoints_temporales(self):
        """Limpia los waypoints temporales del canvas"""
        self.canvas.delete("temp_marker")
        self.canvas.delete("temp_line")
        self.waypoints_temporales.clear()
        self.marcadores_temporales.clear()

    def obtener_waypoints_temporales(self):
        """Retorna la lista de waypoints temporales"""
        return self.waypoints_temporales.copy()