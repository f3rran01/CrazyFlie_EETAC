"""
Módulo de Configuración de Waypoints Interactivos
Permite configurar acciones en cada punto del plan de vuelo mediante un popup
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Callable
import logging


class WaypointConfigDialog:
    """
    Diálogo de configuración para un waypoint individual.
    Aparece cuando el usuario hace click en el mapa para añadir un punto.
    """

    def __init__(self, parent, x: float, y: float, z: float = 0.5,
                 waypoint_number: int = 1,
                 on_save: Optional[Callable] = None,
                 on_cancel: Optional[Callable] = None):
        """
        Inicializa el diálogo de configuración.

        Args:
            parent: Ventana padre
            x, y, z: Coordenadas del waypoint en metros
            waypoint_number: Número del waypoint en la secuencia
            on_save: Callback cuando se guarda (recibe dict con config)
            on_cancel: Callback cuando se cancela
        """
        self.parent = parent
        self.x = x
        self.y = y
        self.z = z
        self.waypoint_number = waypoint_number
        self.on_save = on_save
        self.on_cancel = on_cancel
        self.result = None

        # Crear ventana
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"📍 Waypoint {waypoint_number}")
        self.dialog.geometry("320x450")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Centrar en pantalla
        self.dialog.update_idletasks()
        x_pos = parent.winfo_rootx() + (parent.winfo_width() - 320) // 2
        y_pos = parent.winfo_rooty() + (parent.winfo_height() - 450) // 2
        self.dialog.geometry(f"+{x_pos}+{y_pos}")

        # Configurar cierre
        self.dialog.protocol("WM_DELETE_WINDOW", self._cancelar)

        # Variables
        self.var_altura = tk.DoubleVar(value=z)
        self.var_rotacion = tk.DoubleVar(value=0.0)
        self.var_foto = tk.BooleanVar(value=False)
        self.var_video_corto = tk.BooleanVar(value=False)
        self.var_video_ruta = tk.BooleanVar(value=False)

        # Crear interfaz
        self._crear_interfaz()

    def _crear_interfaz(self):
        """Crea todos los elementos de la interfaz"""
        main_frame = tk.Frame(self.dialog, padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # === TÍTULO ===
        tk.Label(main_frame, text=f"📍 Configurar Waypoint {self.waypoint_number}",
                 font=("Arial", 12, "bold")).pack(pady=(0, 10))

        # === COORDENADAS (Solo lectura) ===
        frame_coords = tk.LabelFrame(main_frame, text="Posición", padx=10, pady=5)
        frame_coords.pack(fill=tk.X, pady=5)

        tk.Label(frame_coords, text=f"X: {self.x:.2f} m",
                 font=("Arial", 10)).pack(side=tk.LEFT, padx=10)
        tk.Label(frame_coords, text=f"Y: {self.y:.2f} m",
                 font=("Arial", 10)).pack(side=tk.LEFT, padx=10)

        # === ALTURA ===
        frame_altura = tk.LabelFrame(main_frame, text="🔺 Altura", padx=10, pady=8)
        frame_altura.pack(fill=tk.X, pady=5)

        tk.Label(frame_altura, text="Altura (m):",
                 font=("Arial", 10)).pack(side=tk.LEFT, padx=5)

        self.spin_altura = tk.Spinbox(frame_altura, from_=0.2, to=2.5,
                                       increment=0.1, width=8,
                                       textvariable=self.var_altura,
                                       font=("Arial", 10))
        self.spin_altura.pack(side=tk.LEFT, padx=5)

        # Slider para altura
        self.scale_altura = tk.Scale(frame_altura, from_=0.2, to=2.5,
                                      resolution=0.1, orient=tk.HORIZONTAL,
                                      variable=self.var_altura, length=100,
                                      showvalue=False)
        self.scale_altura.pack(side=tk.LEFT, padx=5)

        # === ROTACIÓN ===
        frame_rotacion = tk.LabelFrame(main_frame, text="🔄 Rotación", padx=10, pady=8)
        frame_rotacion.pack(fill=tk.X, pady=5)

        tk.Label(frame_rotacion, text="Grados:",
                 font=("Arial", 10)).pack(side=tk.LEFT, padx=5)

        self.spin_rotacion = tk.Spinbox(frame_rotacion, from_=-180, to=180,
                                         increment=15, width=8,
                                         textvariable=self.var_rotacion,
                                         font=("Arial", 10))
        self.spin_rotacion.pack(side=tk.LEFT, padx=5)

        # Botones rápidos de rotación
        frame_rot_rapido = tk.Frame(frame_rotacion)
        frame_rot_rapido.pack(side=tk.LEFT, padx=5)

        tk.Button(frame_rot_rapido, text="-90°",
                  command=lambda: self.var_rotacion.set(-90),
                  width=4, font=("Arial", 8)).pack(side=tk.LEFT, padx=2)
        tk.Button(frame_rot_rapido, text="0°",
                  command=lambda: self.var_rotacion.set(0),
                  width=3, font=("Arial", 8)).pack(side=tk.LEFT, padx=2)
        tk.Button(frame_rot_rapido, text="+90°",
                  command=lambda: self.var_rotacion.set(90),
                  width=4, font=("Arial", 8)).pack(side=tk.LEFT, padx=2)

        # === ACCIONES DE CÁMARA ===
        frame_camara = tk.LabelFrame(main_frame, text="📷 Acciones de Cámara", padx=10, pady=8)
        frame_camara.pack(fill=tk.X, pady=5)

        # Foto
        self.check_foto = tk.Checkbutton(frame_camara,
                                          text="📷 Hacer foto",
                                          variable=self.var_foto,
                                          font=("Arial", 10))
        self.check_foto.pack(anchor=tk.W, pady=2)

        # Video corto
        frame_video_corto = tk.Frame(frame_camara)
        frame_video_corto.pack(anchor=tk.W, pady=2)

        self.check_video_corto = tk.Checkbutton(frame_video_corto,
                                                 text="🎬 Grabar video corto (10s)",
                                                 variable=self.var_video_corto,
                                                 font=("Arial", 10),
                                                 command=self._on_video_corto_toggle)
        self.check_video_corto.pack(side=tk.LEFT)

        # Video de ruta
        frame_video_ruta = tk.Frame(frame_camara)
        frame_video_ruta.pack(anchor=tk.W, pady=2)

        self.check_video_ruta = tk.Checkbutton(frame_video_ruta,
                                                text="🎥 Empezar video de ruta",
                                                variable=self.var_video_ruta,
                                                font=("Arial", 10),
                                                command=self._on_video_ruta_toggle)
        self.check_video_ruta.pack(side=tk.LEFT)

        # Info sobre video de ruta
        self.label_video_info = tk.Label(frame_camara,
                                          text="(Graba hasta el final de la ruta)",
                                          font=("Arial", 8), fg="gray")
        self.label_video_info.pack(anchor=tk.W, padx=20)

        # === BOTONES ===
        frame_botones = tk.Frame(main_frame)
        frame_botones.pack(fill=tk.X, pady=(15, 0))

        tk.Button(frame_botones, text="❌ Cancelar",
                  command=self._cancelar,
                  width=12, font=("Arial", 10),
                  bg="#f44336", fg="white").pack(side=tk.LEFT, padx=5)

        tk.Button(frame_botones, text="✅ Guardar",
                  command=self._guardar,
                  width=12, font=("Arial", 10, "bold"),
                  bg="#4CAF50", fg="white").pack(side=tk.RIGHT, padx=5)

    def _on_video_corto_toggle(self):
        """Maneja el toggle del video corto"""
        if self.var_video_corto.get():
            # Desactivar video de ruta si se activa video corto
            self.var_video_ruta.set(False)

    def _on_video_ruta_toggle(self):
        """Maneja el toggle del video de ruta"""
        if self.var_video_ruta.get():
            # Desactivar video corto si se activa video de ruta
            self.var_video_corto.set(False)

    def _guardar(self):
        """Guarda la configuración y cierra el diálogo"""
        self.result = {
            'x': self.x,
            'y': self.y,
            'z': self.var_altura.get(),
            'rotacion': self.var_rotacion.get(),
            'foto': self.var_foto.get(),
            'video_corto': self.var_video_corto.get(),
            'video_ruta': self.var_video_ruta.get(),
            'waypoint_number': self.waypoint_number
        }

        logging.info(f"[WaypointConfig] Waypoint {self.waypoint_number} configurado: {self.result}")

        if self.on_save:
            self.on_save(self.result)

        self.dialog.destroy()

    def _cancelar(self):
        """Cancela y cierra el diálogo"""
        self.result = None

        if self.on_cancel:
            self.on_cancel()

        self.dialog.destroy()

    def get_result(self) -> Optional[Dict]:
        """Retorna el resultado de la configuración"""
        return self.result


class InteractiveFlightPlanner:
    """
    Sistema de planificación de vuelo interactivo.
    Gestiona la creación de waypoints mediante clicks en el canvas.
    """

    def __init__(self, canvas, visualizador, on_waypoint_added: Optional[Callable] = None):
        """
        Inicializa el planificador interactivo.

        Args:
            canvas: Canvas de Tkinter donde se dibuja el mapa
            visualizador: Instancia del VisualizadorTelemetria2D
            on_waypoint_added: Callback cuando se añade un waypoint
        """
        self.canvas = canvas
        self.visualizador = visualizador
        self.on_waypoint_added = on_waypoint_added

        # Estado
        self.modo_activo = False
        self.waypoints_configurados = []  # Lista de waypoints con su configuración completa
        self.waypoint_counter = 0
        self.video_ruta_activo = False  # Si hay un video de ruta en progreso
        self.video_ruta_inicio_wp = None  # Waypoint donde inició el video de ruta

        # Callback original del canvas (para restaurar)
        self._original_click_callback = None

        # Colores para waypoints
        self.COLOR_NORMAL = "#4CAF50"  # Verde
        self.COLOR_FOTO = "#2196F3"    # Azul
        self.COLOR_VIDEO = "#FF9800"   # Naranja
        self.COLOR_VIDEO_RUTA = "#9C27B0"  # Púrpura

        logging.info("[InteractivePlanner] Sistema de planificación interactivo inicializado")

    def activar(self, validation_callback: Optional[Callable] = None):
        """
        Activa el modo de planificación interactiva.

        Args:
            validation_callback: Función para validar si un punto está permitido
        """
        self.modo_activo = True
        self.validation_callback = validation_callback
        self.waypoints_configurados = []
        self.waypoint_counter = 0
        self.video_ruta_activo = False
        self.video_ruta_inicio_wp = None

        # Limpiar marcadores anteriores
        self.canvas.delete("interactive_waypoint")
        self.canvas.delete("interactive_line")

        # Bind del click
        self.canvas.bind('<Button-1>', self._on_click)

        logging.info("[InteractivePlanner] Modo de planificación ACTIVADO")

    def desactivar(self):
        """Desactiva el modo de planificación interactiva"""
        self.modo_activo = False

        # Deshacer bind
        self.canvas.unbind('<Button-1>')

        logging.info("[InteractivePlanner] Modo de planificación DESACTIVADO")

    def _on_click(self, event):
        """Maneja el click en el canvas"""
        if not self.modo_activo:
            return

        # CORRECCIÓN: Intercambiar X e Y para vista superior correcta
        # X del canvas → Y del dron, Y del canvas → X del dron
        y_metros = -(event.x - self.visualizador.center_x) / self.visualizador.escala
        x_metros = -(event.y - self.visualizador.center_y) / self.visualizador.escala

        # ✅ FIX: Permitir crear waypoints en cualquier lugar
        # La validación del geocage se hará durante la EJECUCIÓN, no durante la planificación
        # Si el dron intenta salir del área permitida durante el vuelo, hará RTL automático
        # (Código de validación comentado - validación ahora solo en ejecución)

        # if self.validation_callback:
        #     if not self.validation_callback(x_metros, y_metros, 0.5):
        #         logging.warning(f"[InteractivePlanner] Punto ({x_metros:.2f}, {y_metros:.2f}) fuera del área permitida")
        #         return

        # Incrementar contador
        self.waypoint_counter += 1

        # Mostrar diálogo de configuración
        self._mostrar_dialogo_config(x_metros, y_metros, event.x, event.y)

    def _mostrar_dialogo_config(self, x_metros: float, y_metros: float,
                                  pixel_x: int, pixel_y: int):
        """
        Muestra el diálogo de configuración para el waypoint.

        Args:
            x_metros, y_metros: Coordenadas en metros
            pixel_x, pixel_y: Coordenadas en píxeles (para dibujar)
        """
        def on_save(config):
            """Callback cuando se guarda la configuración"""
            self._procesar_waypoint_guardado(config, pixel_x, pixel_y)

        def on_cancel():
            """Callback cuando se cancela"""
            self.waypoint_counter -= 1  # Revertir contador
            logging.info("[InteractivePlanner] Waypoint cancelado por el usuario")

        # Crear diálogo
        WaypointConfigDialog(
            parent=self.canvas.winfo_toplevel(),
            x=x_metros,
            y=y_metros,
            z=0.5,  # Altura por defecto
            waypoint_number=self.waypoint_counter,
            on_save=on_save,
            on_cancel=on_cancel
        )

    def _procesar_waypoint_guardado(self, config: Dict, pixel_x: int, pixel_y: int):
        """
        Procesa un waypoint guardado.

        Args:
            config: Diccionario con la configuración del waypoint
            pixel_x, pixel_y: Coordenadas en píxeles
        """
        # Determinar color según acciones
        if config['video_ruta']:
            color = self.COLOR_VIDEO_RUTA
            self.video_ruta_activo = True
            self.video_ruta_inicio_wp = config['waypoint_number']
        elif config['video_corto']:
            color = self.COLOR_VIDEO
        elif config['foto']:
            color = self.COLOR_FOTO
        else:
            color = self.COLOR_NORMAL

        # Guardar configuración
        config['pixel_x'] = pixel_x
        config['pixel_y'] = pixel_y
        config['color'] = color
        self.waypoints_configurados.append(config)

        # Dibujar waypoint
        self._dibujar_waypoint(config, pixel_x, pixel_y, color)

        # Dibujar línea al waypoint anterior
        if len(self.waypoints_configurados) > 1:
            self._dibujar_linea_conexion(
                self.waypoints_configurados[-2],
                config
            )
        else:
            # Primera línea desde el origen
            self._dibujar_linea_origen(config)

        # Callback externo
        if self.on_waypoint_added:
            self.on_waypoint_added(config)

        logging.info(f"[InteractivePlanner] Waypoint {config['waypoint_number']} añadido: "
                    f"({config['x']:.2f}, {config['y']:.2f}, {config['z']:.2f})")

    def _dibujar_waypoint(self, config: Dict, pixel_x: int, pixel_y: int, color: str):
        """Dibuja un waypoint en el canvas"""
        radio = 12

        # Círculo principal
        self.canvas.create_oval(
            pixel_x - radio, pixel_y - radio,
            pixel_x + radio, pixel_y + radio,
            fill=color, outline="white", width=2,
            tags="interactive_waypoint"
        )

        # Número del waypoint
        self.canvas.create_text(
            pixel_x, pixel_y,
            text=str(config['waypoint_number']),
            font=("Arial", 9, "bold"),
            fill="white",
            tags="interactive_waypoint"
        )

        # Iconos de acciones
        icon_offset_x = radio + 8
        icon_offset_y = -radio

        if config['foto']:
            self.canvas.create_text(
                pixel_x + icon_offset_x, pixel_y + icon_offset_y,
                text="📷", font=("Arial", 10),
                tags="interactive_waypoint"
            )
            icon_offset_y += 15

        if config['video_corto']:
            self.canvas.create_text(
                pixel_x + icon_offset_x, pixel_y + icon_offset_y,
                text="🎬", font=("Arial", 10),
                tags="interactive_waypoint"
            )
            icon_offset_y += 15

        if config['video_ruta']:
            self.canvas.create_text(
                pixel_x + icon_offset_x, pixel_y + icon_offset_y,
                text="🎥", font=("Arial", 10),
                tags="interactive_waypoint"
            )

        if config['rotacion'] != 0:
            # Indicador de rotación
            rot_text = f"{config['rotacion']:+.0f}°"
            self.canvas.create_text(
                pixel_x, pixel_y + radio + 12,
                text=rot_text, font=("Arial", 8),
                fill=color,
                tags="interactive_waypoint"
            )

    def _dibujar_linea_origen(self, config: Dict):
        """Dibuja línea desde el origen al primer waypoint"""
        origen_x = self.visualizador.center_x
        origen_y = self.visualizador.center_y

        self.canvas.create_line(
            origen_x, origen_y,
            config['pixel_x'], config['pixel_y'],
            fill="#FFA726", width=2, dash=(8, 4),
            tags="interactive_line"
        )

    def _dibujar_linea_conexion(self, wp1: Dict, wp2: Dict):
        """Dibuja línea de conexión entre dos waypoints"""
        # Determinar color de la línea
        if self.video_ruta_activo:
            color = self.COLOR_VIDEO_RUTA
            dash = (4, 2)
        else:
            color = "#FF5252"
            dash = (6, 3)

        self.canvas.create_line(
            wp1['pixel_x'], wp1['pixel_y'],
            wp2['pixel_x'], wp2['pixel_y'],
            fill=color, width=2, dash=dash,
            tags="interactive_line"
        )

    def limpiar(self):
        """Limpia todos los waypoints del canvas"""
        self.canvas.delete("interactive_waypoint")
        self.canvas.delete("interactive_line")
        self.waypoints_configurados = []
        self.waypoint_counter = 0
        self.video_ruta_activo = False
        self.video_ruta_inicio_wp = None

        logging.info("[InteractivePlanner] Planificación limpiada")

    def eliminar_ultimo(self) -> bool:
        """
        Elimina el último waypoint añadido.

        Returns:
            True si se eliminó un waypoint, False si no había waypoints
        """
        if not self.waypoints_configurados:
            return False

        # Eliminar último
        wp_eliminado = self.waypoints_configurados.pop()
        self.waypoint_counter -= 1

        # Si era el inicio del video de ruta, desactivarlo
        if wp_eliminado.get('video_ruta'):
            self.video_ruta_activo = False
            self.video_ruta_inicio_wp = None

        # Redibujar todo
        self._redibujar_todos()

        logging.info(f"[InteractivePlanner] Waypoint {wp_eliminado['waypoint_number']} eliminado")
        return True

    def _redibujar_todos(self):
        """Redibuja todos los waypoints"""
        # Limpiar canvas
        self.canvas.delete("interactive_waypoint")
        self.canvas.delete("interactive_line")

        # Redibujar cada waypoint
        for i, config in enumerate(self.waypoints_configurados):
            # CORRECCIÓN: Intercambiar X e Y para vista superior correcta
            # X del dron → Y del canvas (vertical), Y del dron → X del canvas (horizontal)
            pixel_x = self.visualizador.center_x - (config['y'] * self.visualizador.escala)
            pixel_y = self.visualizador.center_y - (config['x'] * self.visualizador.escala)

            config['pixel_x'] = pixel_x
            config['pixel_y'] = pixel_y

            # Dibujar waypoint
            self._dibujar_waypoint(config, pixel_x, pixel_y, config['color'])

            # Dibujar líneas
            if i == 0:
                self._dibujar_linea_origen(config)
            else:
                self._dibujar_linea_conexion(
                    self.waypoints_configurados[i - 1],
                    config
                )

    def obtener_mision(self) -> list:
        """
        Obtiene la lista de waypoints configurados como misión.

        Returns:
            Lista de diccionarios con la configuración de cada waypoint
        """
        return self.waypoints_configurados.copy()

    def tiene_waypoints(self) -> bool:
        """Verifica si hay waypoints configurados"""
        return len(self.waypoints_configurados) > 0

    def get_num_waypoints(self) -> int:
        """Retorna el número de waypoints configurados"""
        return len(self.waypoints_configurados)
