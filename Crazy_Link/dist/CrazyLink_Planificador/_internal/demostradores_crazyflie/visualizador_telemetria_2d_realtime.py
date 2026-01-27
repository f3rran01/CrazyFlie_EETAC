"""
Visualizador de Telemetría 2D en Tiempo Real para Crazyflie
Sistema de visualización clara con mapa tipo DashboardPlot
Muestra trayecto en tiempo real con zoom dinámico basado en altura

MEJORAS:
- Línea ROJA: Indica hacia dónde mira la cabeza del dron (heading) - SIEMPRE VISIBLE
- Línea NARANJA: Indica la dirección de desplazamiento (vector velocidad)
"""

import tkinter as tk
from tkinter import Canvas
import math
import threading
import time


class VisualizadorTelemetria2D:
    """
    Visualizador 2D del trayecto del dron con telemetría en tiempo real.
    Vista desde arriba (top-down) con indicadores claros de dirección.
    """

    def __init__(self, parent_frame, ancho=700, alto=600, dron=None):
        """
        Inicializa el visualizador de telemetría 2D.

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

        # Configuración del espacio de vuelo FIJO de 10x10 metros
        self.altura_actual = 0.5  # Altura por defecto
        self.espacio_vuelo = 10.0  # ✅ MAPA FIJO: 10m × 10m (sin zoom dinámico)

        # Calcular escala inicial (píxeles por metro)
        self.escala = (min(self.ancho_canvas, self.alto_canvas) * 0.85) / self.espacio_vuelo

        # Centro del canvas (origen de coordenadas)
        self.center_x = self.ancho_canvas // 2
        self.center_y = self.alto_canvas // 2

        # Historial de posiciones para el trayecto
        self.trayecto = []  # Lista de tuplas (x, y, z)
        self.posicion_actual = [0.0, 0.0, 0.0]  # [x, y, z]
        self.posicion_anterior = [0.0, 0.0, 0.0]

        # Variables para calcular velocidad
        self.tiempo_ultima_actualizacion = time.time()
        self.velocidad_actual = 0.0
        
        # ✅ NUEVO: Variables para dirección de movimiento
        self.direccion_movimiento = 0.0  # Ángulo de la dirección de desplazamiento en grados
        self.tiene_movimiento = False  # Flag para saber si el dron se está moviendo
        
        # ✅ Heading real del dron (yaw de telemetría) con filtrado
        self.heading_real = 0.0  # Orientación real del dron según telemetría
        self.heading_anterior = 0.0  # Heading anterior para detectar cambios
        self.heading_buffer = []  # Buffer para suavizado (media móvil)
        self.heading_buffer_size = 15  # Tamaño del buffer de suavizado
        self.heading_umbral_minimo = 10  # Umbral mínimo de cambio (grados)
        self.heading_umbral_maximo = 180.0  # Umbral máximo para detectar saltos (grados)
        
        # ✅ OBSOLETO: Heading planificado (NO SE USA MÁS para la flecha roja)
        self.heading_planificado = 0.0  # Inicia apuntando hacia ADELANTE (+X)

        # Elementos gráficos
        self.canvas = None
        self.dron_marker = None
        self.lineas_trayecto = []

        # Labels de información
        self.label_altura = None
        self.label_posicion = None
        self.label_zoom = None
        self.label_velocidad = None
        self.label_telemetria_status = None

        # Monitoreo en tiempo real
        self.monitoreo_activo = False
        self.thread_monitoreo = None
        self.ultima_posicion_leida = None

        # Modo edición (para waypoints)
        self.modo_edicion = False
        self.waypoints_temporales = []
        self.validation_callback = None

        # ✅ NUEVO: Guardar waypoints planificados para redibujar al cambiar zoom
        self.waypoints_planificados = []
        self.fotos_planificadas = []  # Lista de posiciones donde hay fotos

        # ✅ NUEVO: Guardar datos del geocage y obstáculos para redibujar al cambiar zoom
        self.geocage_points = None
        self.obstaculos = []

        # Log function
        self._log_edicion = lambda msg: print(f"[Visualizador] {msg}")

        # Crear visualizador
        self._crear_visualizador()

    def _crear_visualizador(self):
        """Crea todos los elementos visuales del sistema"""

        # Frame contenedor principal
        container = tk.Frame(self.parent_frame, bg="white")
        container.pack(fill=tk.BOTH, expand=True)

        # ========== TÍTULO CON ESTADO ==========
        frame_titulo = tk.Frame(container, bg="white")
        frame_titulo.pack(pady=5, fill=tk.X)

        titulo = tk.Label(frame_titulo, text="🗺️ Mapa de Vuelo (Vista Superior)",
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

        # ===== CANVAS PRINCIPAL (MAPA 2D) =====
        canvas_frame = tk.Frame(frame_principal, bg="white")
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.canvas = Canvas(canvas_frame, bg="#f5f5f5",
                             highlightthickness=2, highlightbackground="#2196F3")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind('<Configure>', self._on_canvas_resize)
        self.canvas.bind('<Button-1>', self._on_canvas_click)

        # ===== PANEL LATERAL DERECHO (INFO) =====
        panel_info = tk.Frame(frame_principal, bg="white", width=200)
        panel_info.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        panel_info.pack_propagate(False)

        # ===== ALTURA =====
        tk.Label(panel_info, text="ALTURA (Z)",
                 font=("Arial", 11, "bold"), bg="white").pack(pady=(5, 3))

        self.label_altura = tk.Label(panel_info, text="0.00 m",
                                     font=("Arial", 22, "bold"),
                                     fg="#2196F3", bg="white")
        self.label_altura.pack(pady=3)

        # Barra visual de altura
        self.frame_barra_altura = tk.Frame(panel_info, bg="white",
                                           width=90, height=120)
        self.frame_barra_altura.pack(pady=8)
        self.frame_barra_altura.pack_propagate(False)

        self.canvas_barra = Canvas(self.frame_barra_altura, width=75, height=120,
                                   bg="#e0e0e0", highlightthickness=1,
                                   highlightbackground="#999999")
        self.canvas_barra.pack()

        # Referencias de altura en la barra
        self._dibujar_escala_altura()

        # Indicador de altura en barra
        self.indicador_altura = self.canvas_barra.create_rectangle(
            5, 115, 70, 120, fill="#2196F3", outline=""
        )

        # Separador
        tk.Frame(panel_info, height=1, bg="#cccccc").pack(fill=tk.X, pady=8)

        # ===== POSICIÓN XY =====
        tk.Label(panel_info, text="POSICIÓN",
                 font=("Arial", 11, "bold"), bg="white").pack(pady=(3, 3))

        self.label_posicion = tk.Label(panel_info,
                                       text="X: 0.00 m\nY: 0.00 m",
                                       font=("Arial", 10),
                                       bg="white", justify=tk.LEFT)
        self.label_posicion.pack(pady=3)

        # Separador
        tk.Frame(panel_info, height=1, bg="#cccccc").pack(fill=tk.X, pady=8)

        # ===== ZOOM =====
        tk.Label(panel_info, text="ZOOM",
                 font=("Arial", 11, "bold"), bg="white").pack(pady=(3, 3))

        self.label_zoom = tk.Label(panel_info,
                                   text="🔍 10.0m × 10.0m",
                                   font=("Arial", 9),
                                   fg="#FF9800", bg="white")
        self.label_zoom.pack(pady=3)

        # Separador
        tk.Frame(panel_info, height=1, bg="#cccccc").pack(fill=tk.X, pady=8)

        # ===== VELOCIDAD =====
        tk.Label(panel_info, text="VELOCIDAD",
                 font=("Arial", 11, "bold"), bg="white").pack(pady=(3, 3))

        self.label_velocidad = tk.Label(panel_info,
                                        text="0.01 m/s",
                                        font=("Arial", 10),
                                        bg="white")
        self.label_velocidad.pack(pady=3)

        # Separador
        tk.Frame(panel_info, height=1, bg="#cccccc").pack(fill=tk.X, pady=8)

        # ===== BOTONES DE CONTROL =====
        frame_botones = tk.Frame(panel_info, bg="white")
        frame_botones.pack(pady=10, fill=tk.X)

        self.btn_telemetria = tk.Button(
            frame_botones,
            text="[📊] Pausar Telemetría",
            command=self._toggle_telemetria,
            bg="#FF9800", fg="white",
            font=("Arial", 9, "bold"),
            state=tk.DISABLED
        )
        self.btn_telemetria.pack(fill=tk.X, pady=3)

        self.btn_limpiar = tk.Button(
            frame_botones,
            text="🧹 Limpiar Trayecto",
            command=self.limpiar_trayecto,
            bg="#f44336", fg="white",
            font=("Arial", 9, "bold")
        )
        self.btn_limpiar.pack(fill=tk.X, pady=3)

        # Dibujar mapa base
        self._dibujar_mapa_base()

    def _dibujar_escala_altura(self):
        """Dibuja marcas de referencia en la barra de altura"""
        alturas = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5]
        altura_maxima = 2.5

        for alt in alturas:
            y_pos = 115 - int((alt / altura_maxima) * 110)

            self.canvas_barra.create_line(
                5, y_pos, 10, y_pos,
                fill="#666666", width=1
            )

            self.canvas_barra.create_text(
                52, y_pos,
                text=f"{alt}m",
                font=("Arial", 7),
                fill="#666666",
                anchor=tk.W
            )

    def _dibujar_mapa_base(self):
        """Dibuja el fondo del mapa con ejes y cuadrícula"""
        self.canvas.delete("grid")
        self.canvas.delete("axis")
        self.canvas.delete("label")

        # Cuadrícula cada 1 metro
        grid_spacing = 1.0
        num_lines = int(self.espacio_vuelo / grid_spacing)

        for i in range(-num_lines // 2, num_lines // 2 + 1):
            pos = i * grid_spacing * self.escala

            # Líneas verticales (paralelas al eje Y)
            self.canvas.create_line(
                self.center_x + pos, 0,
                self.center_x + pos, self.alto_canvas,
                fill="#d0d0d0", width=1, tags="grid"
            )

            # Líneas horizontales (paralelas al eje X)
            self.canvas.create_line(
                0, self.center_y + pos,
                self.ancho_canvas, self.center_y + pos,
                fill="#d0d0d0", width=1, tags="grid"
            )

        # Ejes principales (después de corregir X/Y)
        # Eje vertical (X del dron - adelante/atrás) - azul
        self.canvas.create_line(
            self.center_x, 0,
            self.center_x, self.alto_canvas,
            fill="#4ECDC4", width=2, tags="axis", arrow=tk.FIRST
        )
        self.canvas.create_text(
            self.center_x + 50, 15,
            text="ADELANTE (+X)", fill="#4ECDC4",
            font=("Arial", 9, "bold"), tags="label"
        )
        self.canvas.create_text(
            self.center_x + 40, self.alto_canvas - 15,
            text="ATRÁS (-X)", fill="#4ECDC4",
            font=("Arial", 9, "bold"), tags="label"
        )

        # Eje horizontal (Y del dron - izquierda/derecha) - rojo
        self.canvas.create_line(
            0, self.center_y,
            self.ancho_canvas, self.center_y,
            fill="#FF6B6B", width=2, tags="axis", arrow=tk.FIRST
        )
        self.canvas.create_text(
            15, self.center_y - 15,
            text="IZQ (+Y)", fill="#FF6B6B",
            font=("Arial", 9, "bold"), tags="label"
        )
        self.canvas.create_text(
            self.ancho_canvas - 40, self.center_y + 15,
            text="DER (-Y)", fill="#FF6B6B",
            font=("Arial", 9, "bold"), tags="label"
        )

        # Origen
        origen_size = 8
        self.canvas.create_oval(
            self.center_x - origen_size, self.center_y - origen_size,
            self.center_x + origen_size, self.center_y + origen_size,
            fill="#4CAF50", outline="white", width=2, tags="axis"
        )
        self.canvas.create_text(
            self.center_x + 30, self.center_y,
            text="ORIGEN (0,0)", fill="#4CAF50",
            font=("Arial", 9, "bold"), tags="label"
        )

    def actualizar_posicion(self, x, y, z):
        """
        Actualiza la posición actual del dron en el mapa.

        Args:
            x, y, z: Coordenadas del dron en metros
        """
        # Guardar posición anterior
        self.posicion_anterior = self.posicion_actual.copy()

        # Actualizar posición actual
        self.posicion_actual = [x, y, z]
        self.altura_actual = z

        # Calcular velocidad
        tiempo_actual = time.time()
        dt = tiempo_actual - self.tiempo_ultima_actualizacion

        if dt > 0:
            dx = x - self.posicion_anterior[0]
            dy = y - self.posicion_anterior[1]
            dz = z - self.posicion_anterior[2]

            distancia = math.sqrt(dx ** 2 + dy ** 2 + dz ** 2)
            self.velocidad_actual = distancia / dt

            # Calcular dirección de movimiento (para flecha naranja)
            if distancia > 0.01:  # Umbral mínimo de movimiento
                self.tiene_movimiento = True
                # Ángulo en grados (0° = +X, 90° = +Y)
                self.direccion_movimiento = math.degrees(math.atan2(dy, dx))
            else:
                self.tiene_movimiento = False

        self.tiempo_ultima_actualizacion = tiempo_actual

        # Añadir al historial
        self.trayecto.append((x, y, z))

        # Redibujar
        self._redibujar_trayecto()
        self._actualizar_indicadores()

    def _filtrar_heading(self, heading_crudo):
        """
        Filtra el heading del dron para reducir ruido y saltos.
        
        Args:
            heading_crudo: Valor crudo del heading del dron (grados)
            
        Returns:
            Heading filtrado
        """
        # Añadir al buffer
        self.heading_buffer.append(heading_crudo)
        if len(self.heading_buffer) > self.heading_buffer_size:
            self.heading_buffer.pop(0)
        
        # Si no hay suficientes datos, devolver el valor crudo
        if len(self.heading_buffer) < 3:
            return heading_crudo
        
        # Calcular media móvil
        heading_filtrado = sum(self.heading_buffer) / len(self.heading_buffer)
        
        # Detectar saltos grandes (posibles errores)
        diferencia = abs(heading_filtrado - self.heading_anterior)
        
        # Si el salto es muy grande, probablemente es un error
        if diferencia > self.heading_umbral_maximo:
            # Mantener el valor anterior
            heading_filtrado = self.heading_anterior
        
        # Si el cambio es muy pequeño, mantener el valor anterior (reducir jitter)
        elif diferencia < self.heading_umbral_minimo:
            heading_filtrado = self.heading_anterior
        
        # Actualizar heading anterior
        self.heading_anterior = heading_filtrado
        
        return heading_filtrado

    def _redibujar_trayecto(self):
        """Redibuja todo el trayecto y el marcador del dron"""
        # Limpiar elementos antiguos
        self.canvas.delete("trayecto")
        self.canvas.delete("dron")

        # Redibujar waypoints planificados si existen
        if self.waypoints_planificados:
            self._redibujar_waypoints_planificados()

        # Redibujar fotos planificadas
        if self.fotos_planificadas:
            self._redibujar_fotos_planificadas()

        # Dibujar líneas del trayecto
        if len(self.trayecto) > 1:
            for i in range(len(self.trayecto) - 1):
                x1, y1, z1 = self.trayecto[i]
                x2, y2, z2 = self.trayecto[i + 1]

                # CORRECCIÓN: Intercambiar X e Y para vista superior correcta
                # X del dron (adelante/atrás) → Y del canvas (vertical)
                # Y del dron (izq/der) → X del canvas (horizontal)
                x1_pixel = self.center_x - (y1 * self.escala)
                y1_pixel = self.center_y - (x1 * self.escala)
                x2_pixel = self.center_x - (y2 * self.escala)
                y2_pixel = self.center_y - (x2 * self.escala)

                self.canvas.create_line(
                    x1_pixel, y1_pixel, x2_pixel, y2_pixel,
                    fill="#2196F3", width=3, tags="trayecto"
                )

        # Dibujar dron en posición actual
        if len(self.posicion_actual) == 3:
            x, y, z = self.posicion_actual

            # CORRECCIÓN: Intercambiar X e Y para vista superior correcta
            x_pixel = self.center_x - (y * self.escala)
            y_pixel = self.center_y - (x * self.escala)

            # Círculo del dron
            radio = 15
            self.canvas.create_oval(
                x_pixel - radio, y_pixel - radio,
                x_pixel + radio, y_pixel + radio,
                fill="#4CAF50", outline="white", width=3, tags="dron"
            )

            # ✅ FLECHA ROJA: Heading real del dron (con filtrado) - DOBLE DE LARGA Y MÁS FINA
            longitud_flecha = radio * 5.0  # Doble de largo (de 2.5 a 5.0)
            
            # Convertir heading_real a radianes
            angulo_rad = math.radians(self.heading_real)
            
            # Calcular punto final de la flecha
            dx_heading = longitud_flecha * math.cos(angulo_rad)
            dy_heading = longitud_flecha * math.sin(angulo_rad)
            
            self.canvas.create_line(
                x_pixel, y_pixel,
                x_pixel + dy_heading, y_pixel + dx_heading,
                fill="#FF0000", width=3, arrow=tk.LAST,  # Grosor reducido de 8 a 3
                arrowshape=(8, 10, 4), tags="dron"  # Punta más pequeña
            )

            # ✅ FLECHA NARANJA: Dirección de movimiento (solo si hay movimiento) - DOBLE DE LARGA Y MÁS FINA
            if self.tiene_movimiento:
                longitud_naranja = radio * 4.0  # Doble de largo (de 2 a 4)
                
                # Convertir dirección de movimiento a radianes
                angulo_mov_rad = math.radians(self.direccion_movimiento)
                
                # Calcular punto final
                dx_mov = longitud_naranja * math.cos(angulo_mov_rad)
                dy_mov = longitud_naranja * math.sin(angulo_mov_rad)
                
                self.canvas.create_line(
                    x_pixel, y_pixel,
                    x_pixel + dy_mov, y_pixel + dx_mov,
                    fill="#FF9800", width=3, arrow=tk.LAST,  # Grosor reducido de 8 a 3
                    arrowshape=(8, 10, 4), tags="dron"  # Punta más pequeña
                )

    def _redibujar_waypoints_planificados(self):
        """Redibuja los waypoints planificados"""
        for i, wp in enumerate(self.waypoints_planificados):
            x = wp['x']
            y = wp['y']

            # CORRECCIÓN: Intercambiar X e Y para vista superior correcta
            x_pixel = self.center_x - (y * self.escala)
            y_pixel = self.center_y - (x * self.escala)

            # Dibujar marcador
            radio = 10
            self.canvas.create_oval(
                x_pixel - radio, y_pixel - radio,
                x_pixel + radio, y_pixel + radio,
                fill="#FF0000", outline="black", width=3,
                tags="waypoint_marker"
            )

            # Número de waypoint
            self.canvas.create_text(
                x_pixel, y_pixel,
                text=str(i + 1),
                font=("Arial", 10, "bold"),
                fill="white",
                tags="waypoint_marker"
            )

            # Conectar con línea al waypoint anterior
            if i > 0:
                x_prev = self.waypoints_planificados[i - 1]['x']
                y_prev = self.waypoints_planificados[i - 1]['y']

                # CORRECCIÓN: Intercambiar X e Y para vista superior correcta
                x_prev_pixel = self.center_x - (y_prev * self.escala)
                y_prev_pixel = self.center_y - (x_prev * self.escala)

                self.canvas.create_line(
                    x_prev_pixel, y_prev_pixel, x_pixel, y_pixel,
                    fill="#FF0000", width=3, dash=(10, 5),
                    tags="waypoint_line"
                )

    def _redibujar_fotos_planificadas(self):
        """Redibuja los marcadores de fotos planificadas"""
        for x, y, z in self.fotos_planificadas:
            # CORRECCIÓN: Intercambiar X e Y para vista superior correcta
            x_pixel = self.center_x - (y * self.escala)
            y_pixel = self.center_y - (x * self.escala)

            # Círculo azul de fondo
            self.canvas.create_oval(
                x_pixel - 15, y_pixel - 15,
                x_pixel + 15, y_pixel + 15,
                fill="#2196F3", outline="white", width=2,
                tags="photo_marker"
            )

            # Icono de cámara
            self.canvas.create_text(
                x_pixel, y_pixel,
                text="📷", font=("Arial", 20, "bold"),
                fill="white", tags="photo_marker"
            )

    def _actualizar_indicadores(self):
        """Actualiza todos los indicadores numéricos"""
        # Altura
        self.label_altura.config(text=f"{self.altura_actual:.2f} m")

        # Barra de altura
        altura_maxima = 2.5
        if self.altura_actual > altura_maxima:
            fill_color = "#f44336"  # Rojo si excede
        elif self.altura_actual > altura_maxima * 0.7:
            fill_color = "#FF9800"  # Naranja si está alto
        else:
            fill_color = "#2196F3"  # Azul normal

        altura_normalizada = min(self.altura_actual / altura_maxima, 1.0)
        altura_pixel = int(altura_normalizada * 110)

        self.canvas_barra.coords(
            self.indicador_altura,
            5, 115 - altura_pixel, 70, 115
        )
        self.canvas_barra.itemconfig(self.indicador_altura, fill=fill_color)

        # Posición XY
        x, y, z = self.posicion_actual
        self.label_posicion.config(
            text=f"X: {x:+.2f} m\nY: {y:+.2f} m"
        )

        # Zoom
        self.label_zoom.config(
            text=f"🔍 {self.espacio_vuelo:.1f}m × {self.espacio_vuelo:.1f}m"
        )

        # Velocidad
        self.label_velocidad.config(text=f"{self.velocidad_actual:.2f} m/s")

    def limpiar_trayecto(self):
        """Limpia el trayecto pero mantiene la posición actual"""
        self.trayecto = []
        if len(self.posicion_actual) == 3:
            self.trayecto.append(tuple(self.posicion_actual))
        self._redibujar_trayecto()
        print("[Visualizador] Trayecto limpiado")

    def reiniciar(self):
        """Reinicia completamente el visualizador"""
        self.trayecto = []
        self.posicion_actual = [0.0, 0.0, 0.0]
        self.posicion_anterior = [0.0, 0.0, 0.0]
        self.velocidad_actual = 0.0
        self.altura_actual = 0.5
        self.heading_real = 0.0
        self.heading_planificado = 0.0
        self.tiene_movimiento = False
        
        self.waypoints_planificados = []
        self.fotos_planificadas = []
        
        self._redibujar_trayecto()
        self._actualizar_indicadores()
        print("[Visualizador] Sistema reiniciado")

    # ========== SISTEMA DE TELEMETRÍA EN TIEMPO REAL ==========

    def iniciar_monitoreo(self):
        """Inicia el monitoreo de telemetría en tiempo real"""
        if not self.dron:
            print("[Visualizador] No hay dron conectado")
            return

        if self.monitoreo_activo:
            print("[Visualizador] Monitoreo ya está activo")
            return

        self.monitoreo_activo = True
        self.thread_monitoreo = threading.Thread(target=self._loop_monitoreo, daemon=True)
        self.thread_monitoreo.start()

        if hasattr(self, 'btn_telemetria'):
            self.btn_telemetria.config(
                text="[⏸] Pausar Telemetría",
                state=tk.NORMAL,
                bg="#FF9800"
            )
        self.label_telemetria_status.config(
            text="🟢 Monitoreando",
            fg="#4CAF50"
        )
        print("[Visualizador] Monitoreo de telemetría iniciado")

    def _toggle_telemetria(self):
        """Alterna entre pausar y reanudar la telemetría"""
        if self.monitoreo_activo:
            self.pausar_monitoreo()
        else:
            self.iniciar_monitoreo()

    def pausar_monitoreo(self):
        """Pausa el monitoreo de telemetría"""
        self.monitoreo_activo = False

        try:
            if hasattr(self, 'btn_telemetria'):
                self.btn_telemetria.config(
                    text="[▶] Reanudar Telemetría",
                    bg="#4CAF50"
                )
            if hasattr(self, 'label_telemetria_status'):
                self.label_telemetria_status.config(
                    text="⚫ Pausado",
                    fg="gray"
                )
        except Exception as e:
            # Ignorar errores si los widgets ya fueron destruidos
            pass
        print("[Visualizador] Monitoreo de telemetría detenido")

    def _loop_monitoreo(self):
        """Loop principal de monitoreo (ejecutado en thread separado)"""
        print("[Visualizador] Loop de monitoreo iniciado")

        while self.monitoreo_activo:
            try:
                if self.dron and self.dron.state != "disconnected":
                    # Leer posición del dron
                    if hasattr(self.dron, 'position') and len(self.dron.position) >= 3:
                        x = self.dron.position[0]
                        y = self.dron.position[1]
                        z = self.dron.position[2]
                    else:
                        x = getattr(self.dron, 'x', 0.0)
                        y = getattr(self.dron, 'y', 0.0)
                        z = getattr(self.dron, 'z', 0.0)
                    
                    # ✅ Leer y filtrar heading real del dron (yaw)
                    if hasattr(self.dron, 'heading'):
                        heading_crudo = self.dron.heading
                        # Aplicar filtros de estabilización
                        self.heading_real = self._filtrar_heading(heading_crudo)
                    else:
                        # Si no hay heading, mantener el valor actual
                        pass

                    # Verificar si la posición cambió
                    if self.ultima_posicion_leida != (x, y, z):
                        self.ultima_posicion_leida = (x, y, z)

                        # Actualizar visualización en el thread principal
                        self.canvas.after(0, lambda: self.actualizar_posicion(x, y, z))

                time.sleep(0.1)  # 10 Hz de actualización

            except Exception as e:
                print(f"[Visualizador] Error en loop: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(0.5)

        print("[Visualizador] Loop de monitoreo finalizado")

    # ========== MÉTODOS DE COMPATIBILIDAD ==========

    def _on_canvas_resize(self, event):
        """Maneja el redimensionamiento del canvas"""
        self.ancho_canvas = event.width
        self.alto_canvas = event.height
        self.center_x = self.ancho_canvas // 2
        self.center_y = self.alto_canvas // 2

        # Recalcular escala
        self.escala = (min(self.ancho_canvas, self.alto_canvas) * 0.85) / self.espacio_vuelo

        # Redibujar todo
        self._dibujar_mapa_base()
        self._redibujar_geocage_y_obstaculos()  # ✅ NUEVO: Redibujar geocage y obstáculos
        self._redibujar_trayecto()

    def _on_canvas_click(self, event):
        """Maneja clicks en el canvas (para modo edición)"""
        if not self.modo_edicion:
            return

        # Convertir píxeles a coordenadas del mundo
        # CORRECCIÓN: Intercambiar X e Y para vista superior correcta
        # X del canvas → Y del dron, Y del canvas → X del dron
        y = -(event.x - self.center_x) / self.escala
        x = -(event.y - self.center_y) / self.escala
        z = 0.5  # Altura por defecto

        # Validar si está permitido
        if self.validation_callback:
            if not self.validation_callback(x, y, z):
                return

        # Añadir waypoint temporal
        self.waypoints_temporales.append([x, y, z])

        # Dibujar marcador
        # CORRECCIÓN: Intercambiar X e Y para vista superior correcta
        x_pixel = self.center_x - (y * self.escala)
        y_pixel = self.center_y - (x * self.escala)

        self.canvas.create_oval(
            x_pixel - 5, y_pixel - 5,
            x_pixel + 5, y_pixel + 5,
            fill="#4CAF50", outline="#2E7D32", width=2,
            tags="temp_marker"
        )

        self._log_edicion(f"Waypoint añadido: X={x:.2f}, Y={y:.2f}, Z={z:.2f}")

    def activar_modo_edicion(self, validation_callback=None):
        """Activa el modo de edición interactiva"""
        self.modo_edicion = True
        self.waypoints_temporales = []
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

    def obtener_waypoints_temporales(self):
        """Retorna la lista de waypoints temporales"""
        return self.waypoints_temporales.copy()

    def dibujar_waypoints(self, waypoints, color="#FF0000"):
        """
        Dibuja una lista de waypoints en el mapa.

        Args:
            waypoints: Lista de diccionarios con 'x', 'y', 'z'
            color: Color para los marcadores (por defecto ROJO)
        """
        print(f"[VISUALIZADOR] dibujar_waypoints llamado con {len(waypoints)} waypoints")
        
        # ✅ GUARDAR waypoints para redibujar al cambiar zoom
        self.waypoints_planificados = waypoints.copy()
        
        # Limpiar waypoints anteriores
        self.canvas.delete("waypoint_marker")
        self.canvas.delete("waypoint_line")

        for i, wp in enumerate(waypoints):
            x = wp['x']
            y = wp['y']

            print(f"[VISUALIZADOR] WP {i+1}: x={x}, y={y}")

            # Calcular posición en píxeles
            # CORRECCIÓN: Intercambiar X e Y para vista superior correcta
            x_pixel = self.center_x - (y * self.escala)
            y_pixel = self.center_y - (x * self.escala)
            
            print(f"[VISUALIZADOR] WP {i+1} pixels: x={x_pixel}, y={y_pixel}")

            # Dibujar marcador GRANDE y VISIBLE (radio 10px, rojo brillante)
            radio = 10
            self.canvas.create_oval(
                x_pixel - radio, y_pixel - radio,
                x_pixel + radio, y_pixel + radio,
                fill=color, outline="black", width=3,
                tags="waypoint_marker"
            )

            # Número de waypoint en BLANCO para mejor contraste
            self.canvas.create_text(
                x_pixel, y_pixel,
                text=str(i + 1),
                font=("Arial", 10, "bold"),
                fill="white",
                tags="waypoint_marker"
            )

            # Conectar con línea al waypoint anterior
            if i > 0:
                x_prev = waypoints[i - 1]['x']
                y_prev = waypoints[i - 1]['y']

                # CORRECCIÓN: Intercambiar X e Y para vista superior correcta
                x_prev_pixel = self.center_x - (y_prev * self.escala)
                y_prev_pixel = self.center_y - (x_prev * self.escala)

                self.canvas.create_line(
                    x_prev_pixel, y_prev_pixel, x_pixel, y_pixel,
                    fill=color, width=3, dash=(10, 5),
                    tags="waypoint_line"
                )
        
        print(f"[VISUALIZADOR] Waypoints dibujados correctamente")
        self.canvas.update()  # Forzar actualización del canvas
    
    def anadir_foto_planificada(self, x, y, z):
        """
        Registra una foto planificada para redibujar al cambiar zoom.
        
        Args:
            x, y, z: Coordenadas de la foto en metros
        """
        posicion = (x, y, z)
        if posicion not in self.fotos_planificadas:
            self.fotos_planificadas.append(posicion)
            print(f"[VISUALIZADOR] Foto planificada registrada en ({x}, {y}, {z})")
    
    def limpiar_planificacion(self):
        """Limpia waypoints y fotos planificadas"""
        self.waypoints_planificados.clear()
        self.fotos_planificadas.clear()
        self.canvas.delete("waypoint_marker")
        self.canvas.delete("waypoint_line")
        self.canvas.delete("photo_marker")
        print("[VISUALIZADOR] Planificación limpiada")

    def registrar_geocage_y_obstaculos(self, geocage_points, obstaculos):
        """
        Registra los datos del geocage y obstáculos para redibujar al cambiar zoom.

        Args:
            geocage_points: Lista de tuplas (x, y) con los puntos del geocage
            obstaculos: Lista de diccionarios con 'points' conteniendo las coordenadas
        """
        self.geocage_points = geocage_points
        self.obstaculos = obstaculos
        print(f"[VISUALIZADOR] Geocage y obstáculos registrados: {len(geocage_points)} puntos, {len(obstaculos)} obstáculos")
        self._redibujar_geocage_y_obstaculos()

    def _redibujar_geocage_y_obstaculos(self):
        """Redibuja el geocage y los obstáculos en el canvas"""
        # Limpiar elementos anteriores
        self.canvas.delete("geocage_permanente")
        self.canvas.delete("obstaculo_permanente")

        # Dibujar geocage si existe
        if self.geocage_points and len(self.geocage_points) >= 3:
            # Líneas del geocage
            for i in range(len(self.geocage_points)):
                x1, y1 = self.geocage_points[i]
                x2, y2 = self.geocage_points[(i + 1) % len(self.geocage_points)]

                # Convertir a píxeles
                x1_px = self.center_x + (x1 * self.escala)
                y1_px = self.center_y - (y1 * self.escala)
                x2_px = self.center_x + (x2 * self.escala)
                y2_px = self.center_y - (y2 * self.escala)

                self.canvas.create_line(
                    x1_px, y1_px, x2_px, y2_px,
                    fill="#4CAF50", width=3, tags="geocage_permanente"
                )

            # Relleno del geocage
            puntos_px = []
            for x, y in self.geocage_points:
                x_px = self.center_x + (x * self.escala)
                y_px = self.center_y - (y * self.escala)
                puntos_px.extend([x_px, y_px])

            self.canvas.create_polygon(
                puntos_px, fill="#C8E6C9", outline="",
                stipple="gray25", tags="geocage_permanente"
            )
            self.canvas.tag_lower("geocage_permanente")

        # Dibujar obstáculos
        for obs in self.obstaculos:
            points = obs.get('points', [])
            if len(points) >= 3:
                # Líneas del obstáculo
                for i in range(len(points)):
                    x1, y1 = points[i]
                    x2, y2 = points[(i + 1) % len(points)]

                    # Convertir a píxeles
                    x1_px = self.center_x + (x1 * self.escala)
                    y1_px = self.center_y - (y1 * self.escala)
                    x2_px = self.center_x + (x2 * self.escala)
                    y2_px = self.center_y - (y2 * self.escala)

                    self.canvas.create_line(
                        x1_px, y1_px, x2_px, y2_px,
                        fill="#f44336", width=3, tags="obstaculo_permanente"
                    )

                # Relleno del obstáculo
                puntos_px = []
                for x, y in points:
                    x_px = self.center_x + (x * self.escala)
                    y_px = self.center_y - (y * self.escala)
                    puntos_px.extend([x_px, y_px])

                self.canvas.create_polygon(
                    puntos_px, fill="#FFCDD2", outline="",
                    tags="obstaculo_permanente"
                )

        print(f"[VISUALIZADOR] Geocage y obstáculos redibujados")
