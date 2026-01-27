import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import logging
import sys
import os
from config_mision import ConfigMision
from integracion_planificador import integrar_planificador_interactivo
try:
    from voz_crazyflie import VoiceRecognitionSystem, procesar_comando_completo, procesar_comando_basico

    VOZ_DISPONIBLE = True
    print("✓ Módulo de voz cargado")

except (ImportError, OSError) as e:
    VOZ_DISPONIBLE = False
    print(f"Módulo de voz no disponible: {e}")

# Agregar rutas necesarias al path
sys.path.append('..')

# Agregar la carpeta modules_crazyflie al path - CORRECCIÓN PARA ESTRUCTURA REAL
ruta_actual = os.path.dirname(os.path.abspath(__file__))  # .../demostradores_crazyflie
ruta_crazy_link = os.path.dirname(ruta_actual)  # .../Crazy_Link
ruta_crazyflie = os.path.join(ruta_crazy_link, 'crazyLink')  # .../Crazy_Link/crazyLink
ruta_modules = os.path.join(ruta_crazyflie, 'modules_crazyflie')  # .../Crazy_Link/crazyLink/modules_crazyflie

# Agregar ambas rutas al path
if os.path.exists(ruta_crazyflie):
    sys.path.insert(0, ruta_crazyflie)
    print(f"✓ Ruta crazyLink añadida: {ruta_crazyflie}")

if os.path.exists(ruta_modules):
    sys.path.insert(0, ruta_modules)
    print(f"✓ Ruta modules_crazyflie añadida: {ruta_modules}")
else:
    print(f"⚠ WARNING: No se encontró la carpeta modules_crazyflie en: {ruta_modules}")

from crazyLink.Dron_crazyflie import Dron
from dron_plan_vuelo_extended import (
    FlightMission,
    crear_mision_desde_comandos,
    crear_mision_patron,
    ejecutar_mision,
    previsualizar_mision,
    calcular_distancia_total,
    estimar_tiempo_vuelo
)

# Import corregido para dron_camera desde modules_crazyflie
try:
    from dron_camera import DroneCamera

    print("✓ DroneCamera importado desde modules_crazyflie")
except ImportError:
    try:
        from modules_crazyflie.dron_camera import DroneCamera

        print("✓ DroneCamera importado con path completo")
    except ImportError as e:
        print(f"⚠ ERROR: No se pudo importar DroneCamera: {e}")
        # Fallback: intentar import directo
        import sys

        sys.exit("No se puede continuar sin el módulo dron_camera")
from photo_gallery import MediaGallery
from visualizador_telemetria_2d_realtime import VisualizadorTelemetria2D
from geocage_creator_con_obstaculos import GeocageCreatorAvanzado as GeocageCreator
from pathfinding_obstaculos import PathFinder, crear_pathfinder_desde_mapa
from vuelo_libre_joystick import VueloLibreJoystick


class MissionPlannerGUI:
    """Interfaz gráfica para planificar y ejecutar misiones de vuelo"""

    def __init__(self, root):
        self.root = root
        self.root.title("Planificador de Misiones - Crazyflie")
        self.root.geometry("1600x900")  # Ventana más grande
        self.threads_activos = []
        self.ejecutando_mision = False
        self._cerrando_app = False
        self.root.protocol("WM_DELETE_WINDOW", self._cerrar_aplicacion)
        self.dron = None
        self.mission = None
        self.waypoint_list = []
        self.visualizador = None
        self.modo_edicion_activo = False



        self.geocage_points = None
        self.geocage_activo = False
        self.obstaculos = []
        self.pathfinder = None
        self.voice_system = None

        # Sistema de cámara para fotos
        self.camera = DroneCamera(carpeta_fotos="fotos_vuelo")
        self.photo_gallery = None
        self.vuelo_joystick = None
        logging.info("✓ Sistema de cámara inicializado")
        self.voice_recording = False

        # Variables para monitoreo de batería
        self.timer_bateria = None
        self.bateria_baja_mostrada = False

        if VOZ_DISPONIBLE:
            try:
                self.voice_system = VoiceRecognitionSystem()
                print("✓ Sistema de voz inicializado")
            except Exception as e:
                print(f"Error inicializando voz: {e}")
                self.voice_system = None

        # Sistema de cámara para fotos
        self.camera = DroneCamera(carpeta_fotos="fotos_vuelo")
        self.photo_gallery = None
        logging.info("✓ Sistema de cámara inicializado")

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        self._crear_interfaz()
        self.planificador_interactivo = integrar_planificador_interactivo(self)

    def _crear_interfaz(self):
        """Crea todos los elementos de la interfaz"""
        frame_conexion = tk.LabelFrame(self.root, text="Conexión y Control", padx=5, pady=5)
        frame_conexion.pack(fill=tk.X, padx=10, pady=3)

        frame_botones = tk.Frame(frame_conexion)
        frame_botones.grid(row=0, column=0, columnspan=5)

        tk.Button(frame_botones, text="Conectar Dron", command=self._conectar_dron,
                  bg="lightblue", width=10, font=("Arial", 8)).pack(side=tk.LEFT, padx=3, pady=3)
        tk.Button(frame_botones, text="Armar", command=self._armar_dron,
                  bg="yellow", width=8, font=("Arial", 8)).pack(side=tk.LEFT, padx=3, pady=3)
        tk.Button(frame_botones, text="Despegar", command=self._despegar_dron,
                  bg="lightgreen", width=8, font=("Arial", 8)).pack(side=tk.LEFT, padx=3, pady=3)
        tk.Button(frame_botones, text="Aterrizar", command=self._aterrizar_dron,
                  bg="orange", width=8, font=("Arial", 8)).pack(side=tk.LEFT, padx=3, pady=3)
        tk.Button(frame_botones, text="🔷 Geocage", command=self._abrir_geocage,
                  bg="#81C784", fg="white", font=("Arial", 8, "bold"),
                  width=9).pack(side=tk.LEFT, padx=3, pady=3)
        tk.Button(frame_botones, text="📷 Galería", command=self._abrir_galeria,
                  bg="#FF9800", fg="white", font=("Arial", 8, "bold"),
                  width=8).pack(side=tk.LEFT, padx=3, pady=3)
        tk.Button(frame_botones, text="🎮 Joystick", command=self._abrir_joystick,
                  bg="#9C27B0", fg="white", font=("Arial", 8, "bold"),
                  width=8).pack(side=tk.LEFT, padx=3, pady=3)

        tk.Button(frame_conexion, text="ℹ Help", command=self._mostrar_ayuda,
                  bg="#e3f2fd", font=("Arial", 8), width=8).grid(row=0, column=5, padx=5, sticky="ne")

        self.label_estado = tk.Label(frame_conexion, text="Estado: Desconectado",
                                     font=("Arial", 10, "bold"))
        self.label_estado.grid(row=1, column=0, columnspan=6, pady=5)

        main_container = tk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Panel izquierdo más pequeño (ancho fijo de 350px)
        frame_izq = tk.Frame(main_container, width=350)
        frame_izq.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        frame_izq.pack_propagate(False)  # Mantener ancho fijo

        # Panel derecho (mapa) ocupa todo el espacio restante
        frame_der = tk.LabelFrame(main_container, text="🗺 Visualización del Trayecto", padx=5, pady=5)
        frame_der.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self.visualizador = VisualizadorTelemetria2D(frame_der)
        self.visualizador._log_edicion = self._log

        if VOZ_DISPONIBLE and self.voice_system:
            frame_voz = tk.LabelFrame(frame_izq, text="🎤 Control por Voz Completo", padx=5, pady=5)
            frame_voz.pack(fill=tk.X, pady=3)

            self.btn_grabar = tk.Button(frame_voz, text="🎙 Grabar Comando (5 seg)",
                                        command=self._comando_voz,
                                        bg="lightpink",
                                        font=("Arial", 9, "bold"),
                                        height=1)
            self.btn_grabar.pack(pady=3, fill=tk.X)

            self.label_voz_status = tk.Label(frame_voz, text="Listo para comando de voz",
                                             font=("Arial", 8), fg="green")
            self.label_voz_status.pack()

        frame_waypoint = tk.LabelFrame(frame_izq, text="Añadir Waypoint Manual", padx=5, pady=5)
        frame_waypoint.pack(fill=tk.X, pady=3)

        tk.Label(frame_waypoint, text="X (m):").grid(row=0, column=0)
        self.entry_x = tk.Entry(frame_waypoint, width=7)
        self.entry_x.grid(row=0, column=1, padx=3)
        self.entry_x.insert(0, "0.0")

        tk.Label(frame_waypoint, text="Y (m):").grid(row=0, column=2)
        self.entry_y = tk.Entry(frame_waypoint, width=7)
        self.entry_y.grid(row=0, column=3, padx=3)
        self.entry_y.insert(0, "0.0")

        tk.Label(frame_waypoint, text="Z (m):").grid(row=0, column=4)
        self.entry_z = tk.Entry(frame_waypoint, width=7)
        self.entry_z.grid(row=0, column=5, padx=3)
        self.entry_z.insert(0, "0.5")

        tk.Button(frame_waypoint, text="Añadir Waypoint",
                  command=self._anadir_waypoint, bg="lightgreen", 
                  font=("Arial", 8)).grid(row=1, column=0, columnspan=6, pady=3)

        frame_comandos = tk.LabelFrame(frame_izq, text="Comandos de Movimiento", padx=5, pady=5)
        frame_comandos.pack(fill=tk.X, pady=3)

        tk.Label(frame_comandos, text="Dirección:", font=("Arial", 8)).grid(row=0, column=0)
        self.combo_direccion = ttk.Combobox(frame_comandos, width=12, values=[
            "recto", "atras", "izquierda", "derecha", "arriba", "abajo"
        ], font=("Arial", 8))
        self.combo_direccion.grid(row=0, column=1, padx=3)
        self.combo_direccion.set("recto")

        tk.Label(frame_comandos, text="Distancia (m):", font=("Arial", 8)).grid(row=0, column=2)
        self.entry_distancia = tk.Entry(frame_comandos, width=7)
        self.entry_distancia.grid(row=0, column=3, padx=3)
        self.entry_distancia.insert(0, "1.0")

        tk.Button(frame_comandos, text="Añadir Movimiento",
                  command=self._anadir_movimiento, bg="lightblue",
                  font=("Arial", 8)).grid(row=1, column=0, columnspan=4, pady=3)

        frame_patrones = tk.LabelFrame(frame_izq, text="Patrones Predefinidos", padx=5, pady=5)
        frame_patrones.pack(fill=tk.X, pady=3)

        tk.Label(frame_patrones, text="Patrón:", font=("Arial", 8)).grid(row=0, column=0)
        self.combo_patron = ttk.Combobox(frame_patrones, width=12, values=[
            "cuadrado", "circulo", "triangulo", "linea", "zigzag", "espiral"
        ], font=("Arial", 8))
        self.combo_patron.grid(row=0, column=1, padx=3)
        self.combo_patron.set("cuadrado")

        tk.Label(frame_patrones, text="Tamaño (m):", font=("Arial", 8)).grid(row=0, column=2)
        self.entry_tamano = tk.Entry(frame_patrones, width=7)
        self.entry_tamano.grid(row=0, column=3, padx=3)
        self.entry_tamano.insert(0, "1.0")

        tk.Button(frame_patrones, text="Crear Patrón",
                  command=self._crear_patron, bg="lightcoral",
                  font=("Arial", 8)).grid(row=1, column=0, columnspan=4, pady=3)

        frame_misiones = tk.LabelFrame(frame_izq, text="Gestión de Misión", padx=10, pady=10)
        frame_misiones.pack(fill=tk.X, pady=5)

        btn_frame = tk.Frame(frame_misiones)
        btn_frame.pack(pady=5)

        tk.Button(btn_frame, text="📋 Previsualizar",
                  command=self._previsualizar_mision, bg="#90CAF9",
                  width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🚁 EJECUTAR",
                  command=self._ejecutar_mision, bg="#4CAF50",
                  fg="white", font=("Arial", 10, "bold"),
                  width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🧹 Limpiar",
                  command=self._limpiar_mision, bg="#FF9800",
                  width=12).pack(side=tk.LEFT, padx=5)

        btn_frame2 = tk.Frame(frame_misiones)
        btn_frame2.pack(pady=5)

        tk.Button(btn_frame2, text="📷 Añadir Foto",
                  command=self._anadir_foto, bg="#FF6B9D",
                  font=("Arial", 10, "bold"),
                  width=15).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame2, text="⚡ PARADA EMERGENCIA",
                  command=self._parada_emergencia, bg="#f44336",
                  fg="white", font=("Arial", 10, "bold"),
                  width=20).pack(side=tk.LEFT, padx=5)

        frame_velocidad = tk.LabelFrame(frame_misiones, text="⚙️ Configuración de Velocidad", padx=10, pady=5)
        frame_velocidad.pack(fill=tk.X, pady=(10, 0))

        config_frame = tk.Frame(frame_velocidad)
        config_frame.pack()

        tk.Label(config_frame, text="Modo:").grid(row=0, column=0, padx=5)
        self.combo_velocidad = ttk.Combobox(config_frame, width=12, values=[
            "NORMAL", "RÁPIDO", "ESTABLE"
        ], state="readonly")
        self.combo_velocidad.grid(row=0, column=1, padx=5)
        self.combo_velocidad.set("NORMAL")
        self.combo_velocidad.bind("<<ComboboxSelected>>", self._cambiar_velocidad)

        tk.Label(config_frame, text="Velocidad:").grid(row=0, column=2, padx=5)
        self.label_vel_info = tk.Label(config_frame, text="0.3 m/s", font=("Arial", 9, "bold"), fg="#2196F3")
        self.label_vel_info.grid(row=0, column=3, padx=5)

        self.label_bateria = tk.Label(frame_conexion, text="🔋 Batería: -- V",
                                      font=("Arial", 10, "bold"), fg="gray")
        self.label_bateria.grid(row=2, column=0, columnspan=6, pady=5)

        frame_log = tk.LabelFrame(frame_izq, text="Registro de Actividad", padx=10, pady=10)
        frame_log.pack(fill=tk.BOTH, expand=True, pady=5)

        self.log_text = scrolledtext.ScrolledText(frame_log, height=12, state=tk.DISABLED, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def _log(self, mensaje):
        """Añade mensaje al log"""
        self.log_text.config(state=tk.NORMAL)
        timestamp = time.strftime('%H:%M:%S')
        self.log_text.insert(tk.END, f"[{timestamp}] {mensaje}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        logging.info(mensaje)

    def _conectar_dron(self):
        """Conecta con el dron"""
        if self.dron and self.dron.state != "disconnected":
            messagebox.showinfo("Info", "El dron ya está conectado")
            return

        self._log("Intentando conectar con el dron...")

        def conectar_thread():
            try:
                self.dron = Dron()
                self.dron.connect()

                # Verificar si realmente se conectó
                if self.dron.state == "connected":
                    # Configurar visualizador
                    if self.visualizador:
                        self.visualizador.dron = self.dron
                        self.visualizador.iniciar_monitoreo()
                        self.root.after(0, lambda: self._log("✓ Visualizador configurado y telemetría iniciada"))

                    self.root.after(0, lambda: self._log("✓ Dron conectado correctamente"))
                    self.root.after(0, lambda: self.label_estado.config(text="Estado: Conectado ✓", fg="green"))
                    self.root.after(0, self._iniciar_monitoreo_bateria)
                else:
                    # No se pudo conectar
                    raise Exception("El dron no respondió a la conexión")

            except Exception as e:
                self.root.after(0, lambda e=e: self._log(f"✗ Error de conexión: {e}"))
                self.root.after(0, lambda e=e: self.label_estado.config(text="Estado: Error de conexión", fg="red"))
                self.root.after(0, lambda e=e: messagebox.showerror("Error de Conexión",
                                                                    f"No se pudo conectar con el dron:\n\n{str(e)}\n\n"
                                                                    "Verifica que:\n"
                                                                    "• El dron esté encendido\n"
                                                                    "• El Crazyradio PA esté conectado\n"
                                                                    "• No haya otro programa usando el dron"))

        thread = threading.Thread(target=conectar_thread, daemon=True)
        thread.start()

    def _armar_dron(self):
        """Arma el dron"""
        if not self.dron:
            messagebox.showwarning("Advertencia", "Primero conecta el dron")
            return

        self._log("Armando dron...")

        def armar_thread():
            try:
                self.dron.arm()
                self.root.after(0, lambda: self._log("✓ Dron armado"))
                self.root.after(0, lambda: self.label_estado.config(text="Estado: Armado ✓", fg="orange"))
            except Exception as e:
                self.root.after(0, lambda: self._log(f"✗ Error al armar: {e}"))
                self.root.after(0, lambda: messagebox.showerror("Error", f"No se pudo armar: {e}"))

        thread = threading.Thread(target=armar_thread, daemon=True)
        thread.start()

    def _despegar_dron(self):
        """Despega el dron"""
        if not self.dron:
            messagebox.showwarning("Advertencia", "Primero conecta el dron")
            return

        self._log("Iniciando despegue...")

        def despegar_thread():
            try:
                if self.dron.state != "armed":
                    self.dron.arm()
                    time.sleep(1)

                self.dron.takeOff(0.5)
                self.root.after(0, lambda: self._log("✓ Dron en vuelo"))
                self.root.after(0, lambda: self.label_estado.config(text="Estado: Volando ✈", fg="blue"))
            except Exception as e:
                self.root.after(0, lambda: self._log(f"✗ Error al despegar: {e}"))
                self.root.after(0, lambda: messagebox.showerror("Error", f"No se pudo despegar: {e}"))

        thread = threading.Thread(target=despegar_thread, daemon=True)
        thread.start()

    def _aterrizar_dron(self):
        """Aterriza el dron"""
        if not self.dron:
            messagebox.showwarning("Advertencia", "El dron no está conectado")
            return

        self._log("Iniciando aterrizaje...")

        def aterrizar_thread():
            try:
                self.dron.Land()
                time.sleep(3)
                self.root.after(0, lambda: self._log("✓ Dron aterrizado"))
                self.root.after(0, lambda: self.label_estado.config(text="Estado: Aterrizado", fg="green"))
            except Exception as e:
                self.root.after(0, lambda: self._log(f"✗ Error al aterrizar: {e}"))
                self.root.after(0, lambda: messagebox.showerror("Error", f"No se pudo aterrizar: {e}"))

        thread = threading.Thread(target=aterrizar_thread, daemon=True)
        thread.start()

    def _anadir_waypoint(self):
        """Añade un waypoint a la misión"""
        try:
            x = float(self.entry_x.get())
            y = float(self.entry_y.get())
            z = float(self.entry_z.get())

            if self.mission is None:
                self.mission = FlightMission()
                self._log("Nueva misión creada")

            self.mission.add_waypoint(x, y, z)
            self._actualizar_visualizacion()
            self._log(f"Waypoint añadido: ({x:.2f}, {y:.2f}, {z:.2f})")

        except ValueError:
            messagebox.showerror("Error", "Por favor introduce valores numéricos válidos")

    def _anadir_movimiento(self):
        """Añade un comando de movimiento relativo"""
        try:
            direccion = self.combo_direccion.get()
            distancia = float(self.entry_distancia.get())

            if self.mission is None:
                self.mission = FlightMission()
                self._log("Nueva misión creada")

            mapa_direcciones = {
                "recto": (distancia, 0, 0),
                "atras": (-distancia, 0, 0),
                "izquierda": (0, distancia, 0),
                "derecha": (0, -distancia, 0),
                "arriba": (0, 0, distancia),
                "abajo": (0, 0, -distancia)
            }

            delta = mapa_direcciones.get(direccion, (0, 0, 0))
            self.mission.add_relative_move(*delta)
            self._actualizar_visualizacion()
            self._log(f"Movimiento añadido: {direccion} {distancia:.2f}m")

        except ValueError:
            messagebox.showerror("Error", "Por favor introduce una distancia válida")

    def _crear_patron(self):
        """Crea un patrón predefinido"""
        try:
            patron = self.combo_patron.get()
            tamano = float(self.entry_tamano.get())

            if self.mission is None:
                self.mission = FlightMission()
                self._log("Nueva misión creada")

            self.mission = crear_mision_patron(patron, tamano)
            self._actualizar_visualizacion()
            self._log(f"Patrón creado: {patron} (tamaño {tamano:.2f}m)")

        except ValueError:
            messagebox.showerror("Error", "Por favor introduce un tamaño válido")

    def _previsualizar_mision(self):
        """Previsualiza la misión actual"""
        if not self.mission or len(self.mission.waypoints) == 0:
            messagebox.showinfo("Info", "No hay waypoints para previsualizar")
            return

        distancia = calcular_distancia_total(self.mission)
        tiempo = estimar_tiempo_vuelo(self.mission, ConfigMision.ACTIVO['velocidad'])

        mensaje = f"""
📍 Waypoints: {len(self.mission.waypoints)}
📏 Distancia total: {distancia:.2f} m
⏱ Tiempo estimado: {tiempo:.1f} s
⚡ Velocidad: {ConfigMision.ACTIVO['velocidad']} m/s
"""
        messagebox.showinfo("Previsualización de Misión", mensaje)
        self._log("Misión previsualizada")

    def _ejecutar_mision(self):
        """Ejecuta la misión actual"""
        if not self.dron:
            messagebox.showwarning("Advertencia", "Primero conecta el dron")
            return

        if not self.mission or len(self.mission.waypoints) == 0:
            messagebox.showwarning("Advertencia", "No hay waypoints para ejecutar")
            return

        if self.ejecutando_mision:
            messagebox.showinfo("Info", "Ya hay una misión en ejecución")
            return

        # Verificar si hay geocage activo y si la misión está dentro
        if self.geocage_activo and self.geocage_points:
            waypoints_fuera = []
            for i, wp in enumerate(self.mission.waypoints):
                # ✅ FIX: Manejar waypoints como tupla o diccionario
                if isinstance(wp, dict):
                    x, y, z = wp['x'], wp['y'], wp['z']
                else:
                    x, y, z = wp

                if not self._punto_dentro_geocage(x, y):
                    waypoints_fuera.append((i + 1, x, y, z))

            if waypoints_fuera:
                mensaje = "⚠️ ADVERTENCIA: Algunos waypoints están FUERA del Geocage:\n\n"
                for idx, x, y, z in waypoints_fuera[:5]:
                    mensaje += f"  • WP {idx}: ({x:.2f}, {y:.2f}, {z:.2f})\n"

                if len(waypoints_fuera) > 5:
                    mensaje += f"  ... y {len(waypoints_fuera) - 5} más\n"

                mensaje += "\n¿Deseas continuar de todos modos?\n(El dron se detendrá al alcanzar el límite)"

                respuesta = messagebox.askyesno("Waypoints fuera del Geocage", mensaje)
                if not respuesta:
                    self._log("Ejecución cancelada por usuario (waypoints fuera)")
                    return
                else:
                    self._log("Usuario decidió continuar con waypoints fuera del geocage")

        self.ejecutando_mision = True
        distancia = calcular_distancia_total(self.mission)
        tiempo = estimar_tiempo_vuelo(self.mission, ConfigMision.ACTIVO['velocidad'])
        self._log(f"Iniciando misión - {len(self.mission.waypoints)} waypoints, {distancia:.2f}m, ~{tiempo:.1f}s")

        def ejecutar_thread():
            try:
                if self.dron.state == "disconnected":
                    raise Exception("Dron desconectado")

                if self.dron.state != "armed":
                    self.root.after(0, lambda: self._log("Armando dron automáticamente..."))
                    self.dron.arm()
                    time.sleep(1)

                self.root.after(0, lambda: self._log("Despegando..."))
                self.dron.takeOff(0.5)

                # ✅ FIX: Esperar a que el dron termine de despegar antes de ejecutar misión
                self.root.after(0, lambda: self._log("Esperando a que el dron termine de despegar..."))
                time.sleep(3)  # Esperar a que el dron alcance la altura y estado "flying"

                self.root.after(0, lambda: self.label_estado.config(text="Estado: Ejecutando Misión 🚁", fg="blue"))

                # Ejecutar misión con el objeto dron y cámara
                ejecutar_mision(
                    self.dron,
                    self.mission,
                    velocidad=ConfigMision.ACTIVO['velocidad'],
                    callback_posicion=self._actualizar_posicion_real,
                    camera=self.camera,
                    geocage_validator=self._validar_geocage if self.geocage_activo else None,
                    pathfinder=self.pathfinder  # ✅ NUEVO: Pasar pathfinder para evasión de obstáculos
                )

                self.root.after(0, lambda: self._log("✓ Misión completada"))
                self.root.after(0, lambda: self._log("Aterrizando..."))

                self.dron.Land()
                time.sleep(3)

                self.root.after(0, lambda: self.label_estado.config(text="Estado: Misión Completada ✓", fg="green"))
                self.root.after(0, lambda: messagebox.showinfo("Éxito", "¡Misión completada correctamente!"))

                # Limpiar el trayecto después de completar la misión
                self.root.after(0, self._limpiar_trayecto_completo)

            except Exception as e:
                self.root.after(0, lambda: self._log(f"✗ Error en misión: {e}"))
                self.root.after(0, lambda: messagebox.showerror("Error", f"Error durante la misión: {e}"))

                try:
                    if self.dron and self.dron.state != "disconnected":
                        self.root.after(0, lambda: self._log("Intentando aterrizaje de emergencia..."))
                        self.dron.Land()
                        time.sleep(2)
                except:
                    pass
            finally:
                self.ejecutando_mision = False

        thread = threading.Thread(target=ejecutar_thread, daemon=True)
        self.threads_activos.append(thread)
        thread.start()

    def _limpiar_mision(self):
        """Limpia la misión actual"""
        self.mission = None
        self.waypoint_list = []
        if self.visualizador:
            if hasattr(self.visualizador, 'limpiar_planificacion'):
                self.visualizador.limpiar_planificacion()
            
            # Limpiar elementos del canvas (por si acaso)
            if hasattr(self.visualizador, 'canvas'):
                self.visualizador.canvas.delete("mission_line")
                self.visualizador.canvas.delete("waypoint_marker")
                self.visualizador.canvas.delete("waypoint_line")
                self.visualizador.canvas.delete("photo_marker")
            
            self.visualizador.limpiar()
        self._log("Misión limpiada")

    def _limpiar_trayecto_completo(self):
        """Limpia completamente el trayecto (trail y waypoints) del visualizador"""
        if self.visualizador:
            # Limpiar líneas de misión del canvas
            if hasattr(self.visualizador, 'canvas'):
                self.visualizador.canvas.delete("mission_line")
            # CORRECCIÓN: Usar limpiar_trayecto en lugar de limpiar_trail
            if hasattr(self.visualizador, 'limpiar_trayecto'):
                self.visualizador.limpiar_trayecto()
            if hasattr(self.visualizador, 'limpiar'):
                self.visualizador.limpiar()
            self._log("✓ Trayecto limpiado completamente")

    def _actualizar_visualizacion(self):
        """Actualiza la información de la misión y dibuja waypoints en el canvas"""
        if not self.mission:
            return

        # Actualizar info de la misión en el log
        distancia = calcular_distancia_total(self.mission)
        tiempo = estimar_tiempo_vuelo(self.mission, ConfigMision.ACTIVO['velocidad'])
        self._log(f"Misión actualizada: {len(self.mission.waypoints)} WPs, {distancia:.2f}m, ~{tiempo:.1f}s")
        
        # ✅ NUEVO: Dibujar waypoints en el visualizador
        if self.visualizador and hasattr(self.visualizador, 'dibujar_waypoints'):
            print(f"[DEBUG] Dibujando {len(self.mission.waypoints)} waypoints")
            print(f"[DEBUG] Waypoints: {self.mission.waypoints}")
            self.visualizador.dibujar_waypoints(self.mission.waypoints, color="#FF0000")  # ROJO

    def _actualizar_posicion_real(self, x, y, z):
        """Callback para actualizar posición del dron en tiempo real"""
        if self.visualizador:
            self.root.after(0, lambda: self.visualizador.actualizar_posicion(x, y, z))

    def _parada_emergencia(self):
        """Detiene inmediatamente el dron"""
        if not self.dron:
            messagebox.showwarning("Advertencia", "El dron no está conectado")
            return

        respuesta = messagebox.askyesno(
            "Parada de Emergencia",
            "⚠️ ¿Activar parada de emergencia?\n\nEl dron se detendrá inmediatamente."
        )

        if respuesta:
            self._log("PARADA DE EMERGENCIA ACTIVADA")

            def emergencia_thread():
                try:
                    if self.dron.state != "disconnected":
                        self.dron.Land()
                        time.sleep(2)
                        self.root.after(0, lambda: self._log("✓ Dron detenido"))
                        self.root.after(0, lambda: self.label_estado.config(
                            text="Estado: Parada de Emergencia", fg="red"))
                except Exception as e:
                    self.root.after(0, lambda: self._log(f"✗ Error en parada de emergencia: {e}"))

            thread = threading.Thread(target=emergencia_thread, daemon=True)
            thread.start()

    def _cerrar_aplicacion(self):
        """Cierra la aplicación de forma segura"""
        if self._cerrando_app:
            return

        self._cerrando_app = True

        if self.ejecutando_mision:
            respuesta = messagebox.askyesno(
                "Misión en Curso",
                "Hay una misión en ejecución.\n¿Deseas cerrar de todos modos?"
            )
            if not respuesta:
                self._cerrando_app = False
                return

        self._log("Cerrando aplicación...")

        # Detener el visualizador si existe
        if self.visualizador:
            try:
                self.visualizador.detener_monitoreo()
            except:
                pass

        # Detener sistema de voz si existe
        if hasattr(self, 'voice_system') and self.voice_system:
            try:
                self.voice_system.stop()
            except:
                pass

        # Cerrar cámara si existe
        if hasattr(self, 'camera') and self.camera:
            try:
                self.camera.cerrar_camara()
            except:
                pass

        if self.dron and self.dron.state != "disconnected":
            try:
                if self.dron.state != "landed":
                    self.dron.Land()
                    time.sleep(1)
                self.dron.disconnect()
            except:
                pass

        # Cancelar timer de batería si existe
        if self.timer_bateria:
            self.root.after_cancel(self.timer_bateria)

        # Forzar terminación de threads pendientes
        import os
        self.root.quit()
        self.root.destroy()
        os._exit(0)  # Forzar cierre de todos los threads

    def _abrir_geocage(self):
        """Abre la ventana de creación de geocage"""
        try:
            ventana_geo = tk.Toplevel(self.root)
            ventana_geo.title("🔷 Creador de Geocage con Obstáculos")
            ventana_geo.geometry("900x700")

            # Callback cuando se guarda el geocage
            def on_guardar(config):
                # El config es un dict con 'geocage' y 'obstaculos'
                self.geocage_points = config.get('geocage', [])
                self.obstaculos = config.get('obstaculos', [])
                self.geocage_activo = True

                # ✅ DEBUG: Mostrar coordenadas guardadas
                print(f"[DEBUG] Geocage Y range: {min(y for x,y in self.geocage_points):.2f} to {max(y for x,y in self.geocage_points):.2f}")
                print(f"[DEBUG] Geocage X range: {min(x for x,y in self.geocage_points):.2f} to {max(x for x,y in self.geocage_points):.2f}")
                if self.obstaculos:
                    for idx, obs in enumerate(self.obstaculos):
                        points = obs.get('points', [])
                        if points:
                            print(f"[DEBUG] Obstáculo {idx+1} Y range: {min(y for x,y in points):.2f} to {max(y for x,y in points):.2f}")
                            print(f"[DEBUG] Obstáculo {idx+1} X range: {min(x for x,y in points):.2f} to {max(x for x,y in points):.2f}")
                            print(f"[DEBUG] Obstáculo {idx+1} coords: {points}")

                # ✅ FIX: Crear pathfinder siempre que haya geocage
                # El pathfinder es necesario para validar límites del geocage Y evitar obstáculos
                # Usar config ORIGINAL (sin invertir) ya que las coordenadas vienen correctas
                if self.geocage_points:
                    self.pathfinder = crear_pathfinder_desde_mapa(config)
                    if self.obstaculos:
                        self._log(f"✓ Pathfinder creado: Geocage con {len(self.obstaculos)} obstáculos")
                    else:
                        self._log(f"✓ Pathfinder creado: Geocage sin obstáculos")
                else:
                    self.pathfinder = None

                # ✅ REGISTRAR en el visualizador para redibujar automáticamente al hacer resize
                if self.visualizador:
                    # ✅ NUEVO: Registrar geocage y obstáculos en el visualizador
                    # Esto permite que se redibuje automáticamente al cambiar el tamaño del canvas
                    self.visualizador.registrar_geocage_y_obstaculos(
                        self.geocage_points,
                        self.obstaculos
                    )

                self._log(f"✓ Geocage aplicado: {len(self.geocage_points)} puntos, {len(self.obstaculos)} obstáculos")
                self._log("✓ Mapa visualizado en el canvas 2D")

            # Crear el geocage creator con el callback
            geo_creator = GeocageCreator(
                parent_window=ventana_geo,
                visualizador=self.visualizador,
                on_save_callback=on_guardar
            )

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el geocage: {e}")
            self._log(f"Error abriendo geocage: {e}")

    def _punto_dentro_geocage(self, x, y):
        """Verifica si un punto está dentro del geocage usando ray casting"""
        if not self.geocage_points or len(self.geocage_points) < 3:
            return True  # Si no hay geocage, todo está "dentro"

        # Ray casting algorithm
        n = len(self.geocage_points)
        dentro = False

        p1x, p1y = self.geocage_points[0]
        for i in range(1, n + 1):
            p2x, p2y = self.geocage_points[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            dentro = not dentro
            p1x, p1y = p2x, p2y

        return dentro

    def _validar_geocage(self, x, y, z):
        """Valida si una posición está dentro del geocage"""
        if not self.geocage_activo:
            return True

        if not self._punto_dentro_geocage(x, y):
            self._log(f"Posición ({x:.2f}, {y:.2f}) fuera del geocage")
            return False

        return True

    def _comando_voz(self):
        """Procesa un comando de voz completo (5 segundos)"""
        if not self.voice_system:
            messagebox.showwarning("Advertencia", "Sistema de voz no disponible")
            return

        if self.voice_recording:
            return

        self.voice_recording = True
        self.label_voz_status.config(text="🎙️ Grabando... (5 seg)", fg="red")
        self.btn_grabar.config(state=tk.DISABLED)

        def grabar_y_procesar():
            try:
                # Grabar comando (5 segundos)
                texto = self.voice_system.grabar_y_reconocer(duracion=5)

                if texto:
                    self.root.after(0, lambda: self._log(f"Comando detectado: '{texto}'"))
                    self.root.after(0, lambda: self.label_voz_status.config(
                        text=f"Procesando: '{texto}'", fg="blue"))

                    # Procesar comando completo
                    resultado = procesar_comando_completo(texto)
                    
                    if resultado is None:
                        self.root.after(0, lambda: self._log(f"Comando no reconocido: '{texto}'"))
                        self.root.after(0, lambda: self.label_voz_status.config(
                            text="Comando no reconocido", fg="red"))

                    elif resultado.get('tipo') == 'error':
                        self.root.after(0, lambda: self._log(f"{resultado['mensaje']}"))
                        self.root.after(0, lambda: messagebox.showwarning("Error", resultado['mensaje']))
                    
                    # ✅ COMANDOS DE CONTROL DEL DRON
                    elif resultado['tipo'] == 'control':
                        accion = resultado['accion']
                        
                        if accion == 'conectar':
                            self.root.after(0, self._conectar_dron)
                            self.root.after(0, lambda: self._log("✓ Comando: CONECTAR"))
                        
                        elif accion == 'armar':
                            self.root.after(0, self._armar_dron)
                            self.root.after(0, lambda: self._log("✓ Comando: ARMAR"))
                        
                        elif accion == 'despegar':
                            altura = resultado.get('altura', 0.5)
                            self.root.after(0, lambda: self._despegar_dron())
                            self.root.after(0, lambda: self._log(f"✓ Comando: DESPEGAR a {altura}m"))
                        
                        elif accion == 'aterrizar':
                            self.root.after(0, self._aterrizar_dron)
                            self.root.after(0, lambda: self._log("✓ Comando: ATERRIZAR"))
                        
                        self.root.after(0, lambda: self.label_voz_status.config(
                            text="✅ Comando ejecutado", fg="green"))
                    
                    # ✅ COMANDOS DE MISIÓN
                    elif resultado['tipo'] == 'mision':
                        if resultado['accion'] == 'ejecutar':
                            self.root.after(0, self._ejecutar_mision)
                            self.root.after(0, lambda: self._log("✓ Comando: EJECUTAR MISIÓN"))
                        
                        elif resultado['accion'] == 'limpiar':
                            self.root.after(0, self._limpiar_mision)
                            self.root.after(0, lambda: self._log("✓ Comando: LIMPIAR MISIÓN"))
                        
                        self.root.after(0, lambda: self.label_voz_status.config(
                            text="✅ Comando ejecutado", fg="green"))
                    
                    # ✅ COMANDOS QUE MODIFICAN LA MISIÓN (patrones, movimientos, waypoints)
                    elif resultado['tipo'] in ['patron', 'movimiento', 'waypoint']:
                        # Crear o actualizar misión
                        if self.mission is None:
                            self.mission = FlightMission()

                        # Procesar según tipo de comando
                        if resultado['tipo'] == 'patron':
                            self.mission = crear_mision_patron(
                                resultado['patron'],
                                resultado.get('tamano', 1.0)
                            )
                            self.root.after(0, lambda: self._log(
                                f"✓ Patrón '{resultado['patron']}' creado por voz"))

                        elif resultado['tipo'] == 'movimiento':
                            if resultado['accion'] == 'move':
                                # Convertir direction/distance a delta (dx, dy, dz)
                                direction = resultado['direction']
                                distance = resultado['distance']
                                
                                # Mapeo de direcciones a deltas
                                delta_map = {
                                    'forward': (distance, 0, 0),   # Adelante = +X
                                    'back': (-distance, 0, 0),     # Atrás = -X
                                    'left': (0, distance, 0),      # Izquierda = +Y
                                    'right': (0, -distance, 0),    # Derecha = -Y
                                    'up': (0, 0, distance),        # Arriba = +Z
                                    'down': (0, 0, -distance)      # Abajo = -Z
                                }
                                
                                dx, dy, dz = delta_map.get(direction, (0, 0, 0))
                                self.mission.add_relative_move(dx, dy, dz)
                                self.root.after(0, lambda d=direction, dist=distance, x=dx, y=dy, z=dz: self._log(
                                    f"✓ Movimiento añadido: {d.upper()} ({dist:.2f}m) → ({x:.2f}, {y:.2f}, {z:.2f})"))
                            
                            elif resultado['accion'] == 'rotate':
                                # Comando de rotación
                                grados = resultado['degrees']
                                self.mission.add_rotation(grados)
                                # ✅ ACTUALIZAR LA FLECHA ROJA DEL VISUALIZADOR
                                if self.visualizador:
                                    self.visualizador.agregar_rotacion(grados)
                                self.root.after(0, lambda g=grados: self._log(f"✓ Rotación añadida: {g}°"))

                        elif resultado['tipo'] == 'waypoint':
                            x, y, z = resultado['posicion']
                            self.mission.add_waypoint(x, y, z)
                            self.root.after(0, lambda px=x, py=y, pz=z: self._log(
                                f"✓ Waypoint añadido: ({px:.2f}, {py:.2f}, {pz:.2f})"))

                        # Actualizar visualización
                        self.root.after(0, self._actualizar_visualizacion)
                        self.root.after(0, lambda: self.label_voz_status.config(
                            text="✅ Comando ejecutado", fg="green"))

                else:
                    self.root.after(0, lambda: self._log("No se detectó voz"))
                    self.root.after(0, lambda: self.label_voz_status.config(
                        text="No se detectó comando", fg="red"))

            except Exception as e:
                self.root.after(0, lambda: self._log(f"Error en comando de voz: {e}"))
                self.root.after(0, lambda: messagebox.showerror("Error", f"Error procesando voz: {e}"))
            finally:
                self.voice_recording = False
                self.root.after(0, lambda: self.btn_grabar.config(state=tk.NORMAL))
                self.root.after(2000, lambda: self.label_voz_status.config(
                    text="Listo para comando de voz", fg="green"))

        thread = threading.Thread(target=grabar_y_procesar, daemon=True)
        thread.start()

    def _mostrar_ayuda(self):
        """Muestra la ventana de ayuda con comandos y guía"""
        ventana_ayuda = tk.Toplevel(self.root)
        ventana_ayuda.title("ℹ Ayuda - Planificador de Misiones")
        ventana_ayuda.geometry("900x700")

        notebook = ttk.Notebook(ventana_ayuda)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Pestaña 1: Guía de Uso General
        frame_guia = tk.Frame(notebook)
        notebook.add(frame_guia, text="📖 Guía de Uso")

        text_guia = scrolledtext.ScrolledText(frame_guia, wrap=tk.WORD,
                                              font=("Arial", 10), padx=15, pady=15)
        text_guia.pack(fill=tk.BOTH, expand=True)

        guia_uso = """GUÍA DE USO - PLANIFICADOR DE MISIONES

══════════════════════════════════════════════════════════════════

1. CONEXIÓN INICIAL:
   • Enciende el dron Crazyflie
   • Conecta el Crazyradio PA por USB
   • Pulsa "Conectar Dron"
   • Espera a ver "Estado: Conectado ✓"

2. ARMAR Y DESPEGAR:
   • Pulsa "Armar" (el dron se armará)
   • Pulsa "Despegar" (subirá a 0.5m)
   • O usa comandos de voz: "Armar", "Despegar"

3. CREAR MISIÓN:
   Tienes varias opciones:

   A) Waypoints Manuales:
      • Introduce coordenadas X, Y, Z
      • Pulsa "Añadir Waypoint"

   B) Comandos de Movimiento:
      • Selecciona dirección (recto, atrás, izq, der, arriba, abajo)
      • Introduce distancia
      • Pulsa "Añadir Movimiento"

   C) Patrones Predefinidos:
      • Selecciona patrón (cuadrado, círculo, triángulo, etc.)
      • Introduce tamaño
      • Pulsa "Crear Patrón"

   D) Modo Click (Plan Interactivo):
      • Usa el "Plan Interactivo" en la parte inferior
      • Activa "Modo Click"
      • Click en el mapa para añadir waypoints

   E) Comandos de Voz:
      • Pulsa "🎙 Grabar Comando"
      • Di el comando claramente (5 segundos)
      • Ejemplos: "Crear cuadrado de 2 metros"

4. EJECUTAR MISIÓN:
   • Revisa los waypoints en el mapa
   • Pulsa "🚁 EJECUTAR"
   • El sistema arma y despega automáticamente
   • Sigue la ruta planificada
   • Aterriza automáticamente al finalizar

5. ATERRIZAR MANUALMENTE:
   • Pulsa "Aterrizar" en cualquier momento
   • El dron descenderá y se posará suavemente

══════════════════════════════════════════════════════════════════

CONSEJOS:
• Empieza con misiones simples y cortas
• Usa el Geocage para seguridad (define límites de vuelo)
• Verifica la batería antes de cada vuelo
• Prueba primero sin dron (visualización)"""

        text_guia.insert(tk.END, guia_uso)
        text_guia.config(state=tk.DISABLED)

        # Pestaña 2: Plan Interactivo / Modo Click
        frame_click = tk.Frame(notebook)
        notebook.add(frame_click, text="🖱️ Plan Interactivo")

        text_click = scrolledtext.ScrolledText(frame_click, wrap=tk.WORD,
                                               font=("Arial", 10), padx=15, pady=15)
        text_click.pack(fill=tk.BOTH, expand=True)

        click_info = """PLAN INTERACTIVO - MODO CLICK

══════════════════════════════════════════════════════════════════

El Plan Interactivo te permite crear misiones de forma visual haciendo
click directamente en el mapa. Es la forma más rápida e intuitiva.

CÓMO USAR:

1. ACTIVAR MODO CLICK:
   • Busca el panel "Plan Interactivo" en la parte inferior
   • Pulsa el botón naranja "Modo Click"
   • El botón cambiará a verde cuando esté activo

2. AÑADIR WAYPOINTS:
   • Haz click en cualquier punto del mapa
   • Se creará un waypoint en esa posición (altura 0.5m)
   • Los waypoints aparecen numerados en orden
   • Líneas punteadas conectan los waypoints

3. COLORES DE LAS LÍNEAS:
   • 🟠 Naranja: Ruta desde origen al primer waypoint
   • 🔴 Rojo: Conexiones entre waypoints
   • 🟢 Verde: Retorno al origen (última conexión)

4. EJECUTAR RUTA:
   • Conecta y arma el dron primero
   • Haz que despegue
   • Pulsa "EJECUTAR RUTA" en el Plan Interactivo
   • El dron seguirá la ruta automáticamente

5. LIMPIAR:
   • Pulsa el botón rojo para limpiar todos los waypoints
   • Empieza de nuevo

VENTAJAS:
✓ Muy rápido y visual
✓ Ves inmediatamente la ruta en el mapa
✓ Fácil de modificar
✓ Ideal para rutas complejas

LIMITACIÓN:
• Altura fija de 0.5m (para altura variable usa waypoints manuales)"""

        text_click.insert(tk.END, click_info)
        text_click.config(state=tk.DISABLED)

        # Pestaña 3: Modo Joystick
        frame_joy = tk.Frame(notebook)
        notebook.add(frame_joy, text="🎮 Modo Joystick")

        text_joy = scrolledtext.ScrolledText(frame_joy, wrap=tk.WORD,
                                             font=("Arial", 10), padx=15, pady=15)
        text_joy.pack(fill=tk.BOTH, expand=True)

        joy_info = """MODO JOYSTICK - CONTROL TOTAL POR MANDO

══════════════════════════════════════════════════════════════════

El Modo Joystick te da control total del dron usando un mando USB.
TODO se controla desde el mando, incluyendo armar y despegar.

CONFIGURACIÓN INICIAL:

1. CONECTAR MANDO:
   • Conecta el mando por USB
   • Pulsa el botón "🎮 Joystick" en la barra superior
   • Se abrirá la ventana de control por mando

2. CONECTAR SISTEMA:
   • Pulsa "🎮 CONECTAR MANDO Y DRON"
   • El sistema detectará automáticamente el mando
   • Conectará con el dron
   • El botón se pondrá verde cuando esté listo

CONTROLES DEL MANDO:

🔘 SELECT → ARMAR el dron
🔘 START → DESPEGAR (sube a 1m)

🔘 Botón 0 → GRABAR VIDEO (10 segundos) 🎬
🔘 Botón 1 → RTL (Return to Launch - volver al origen)
🔘 Botón 2 → ROTAR (mantener presionado para girar)
🔘 Botón 3 → HACER FOTO 📷
🔘 Botón 4 → ATERRIZAR

🕹️ JOYSTICK IZQUIERDO:
   • Arriba/Abajo → Controla ALTURA (throttle)

🕹️ JOYSTICK DERECHO:
   • Arriba/Abajo → ADELANTE/ATRÁS (pitch)
   • Izquierda/Derecha → IZQUIERDA/DERECHA (roll)
   • Rotación → YAW (girar sobre sí mismo)

VUELO LIBRE:
• El modo "Vuelo Libre" se activa automáticamente al despegar
• Puedes volar libremente por el espacio
• El visualizador muestra el trayecto en tiempo real

FOTOS Y VIDEOS:
• Las fotos/videos se guardan automáticamente
• Revísalos en la "📷 Galería"

CONSEJOS:
✓ Practica los controles en tierra primero
✓ Movimientos suaves y progresivos
✓ Mantén el dron siempre a la vista
✓ RTL (Botón 1) te devuelve al origen automáticamente"""

        text_joy.insert(tk.END, joy_info)
        text_joy.config(state=tk.DISABLED)

        # Pestaña 4: Geocage y Obstáculos
        frame_geo = tk.Frame(notebook)
        notebook.add(frame_geo, text="🔷 Geocage")

        text_geo = scrolledtext.ScrolledText(frame_geo, wrap=tk.WORD,
                                             font=("Arial", 10), padx=15, pady=15)
        text_geo.pack(fill=tk.BOTH, expand=True)

        geo_info = """GEOCAGE Y OBSTÁCULOS - LÍMITES DE SEGURIDAD

══════════════════════════════════════════════════════════════════

El Geocage es un perímetro virtual de seguridad que limita el área
donde puede volar el dron. También puedes añadir obstáculos virtuales.

CREAR GEOCAGE:

1. ABRIR CREADOR:
   • Pulsa el botón "🔷 Geocage" en la barra superior
   • Se abre una ventana con mapa interactivo

2. DEFINIR PERÍMETRO:
   • Haz click en el mapa para añadir puntos (mínimo 3)
   • Los puntos se conectan formando un polígono
   • 🟢 Verde = Área permitida
   • El primer punto se marca en naranja

3. AÑADIR OBSTÁCULOS (Opcional):
   • Pulsa "Añadir Obstáculo"
   • Haz click para definir un nuevo polígono
   • 🔴 Rojo = Área prohibida (obstáculo)
   • Puedes añadir múltiples obstáculos

4. GUARDAR:
   • Pulsa "💾 Guardar Geocage"
   • El mapa aparecerá en el visualizador principal
   • Ya está activo para las misiones

FUNCIONALIDAD:

• GEOCAGE (Verde):
  - Define el área máxima de vuelo
  - El dron NO puede salir de esta área
  - Si una misión sale del geocage, recibirás advertencia

• OBSTÁCULOS (Rojo):
  - Definen áreas donde NO puede volar el dron
  - El planificador los evita automáticamente
  - Útil para simular edificios, árboles, etc.

PLANIFICACIÓN AUTOMÁTICA:
• Si hay obstáculos, el sistema calcula rutas que los evitan
• Usa algoritmo A* para encontrar el camino óptimo
• Visualiza la ruta antes de ejecutarla

LIMPIAR GEOCAGE:
• Pulsa "🧹 Limpiar Todo" en el creador
• O cierra y vuelve a abrir para empezar de nuevo

CONSEJOS:
✓ Define siempre un geocage para seguridad
✓ Deja margen en los bordes (0.5-1m)
✓ Los obstáculos ayudan a planificar rutas realistas
✓ Prueba la ruta en el visualizador antes de volar"""

        text_geo.insert(tk.END, geo_info)
        text_geo.config(state=tk.DISABLED)

        # Pestaña 5: Comandos de Voz
        frame_voz = tk.Frame(notebook)
        notebook.add(frame_voz, text="🎤 Comandos de Voz")

        text_voz = scrolledtext.ScrolledText(frame_voz, wrap=tk.WORD,
                                             font=("Arial", 10), padx=15, pady=15)
        text_voz.pack(fill=tk.BOTH, expand=True)

        comandos_voz = """COMANDOS DE VOZ DISPONIBLES

══════════════════════════════════════════════════════════════════

Controla el dron y crea misiones usando tu voz. Habla claro y espera
5 segundos mientras graba el comando.

CONTROL DEL DRON:
• "Conectar"
• "Armar"
• "Despegar" / "Despegar a X metros"
• "Aterrizar"

PATRONES:
• "Crear cuadrado de X metros"
• "Crear círculo de X metros"
• "Crear triángulo de X metros"
• "Crear línea de X metros"
• "Crear zigzag de X metros"
• "Crear espiral de X metros"

MOVIMIENTO:
• "Adelante X metros"
• "Atrás X metros"
• "Izquierda X metros"
• "Derecha X metros"
• "Arriba X metros"
• "Abajo X metros"

ROTACIÓN:
• "Rotar X grados"
• "Girar X grados"
• "Girar X grados a la derecha"
• "Girar X grados a la izquierda"

GESTIÓN DE MISIÓN:
• "Ejecutar misión"
• "Limpiar misión"

IMPORTANTE:
✓ Habla claro y con pronunciación correcta
✓ Espera los 5 segundos completos
✓ Usa números claros (ej: "dos metros", no "2")
✓ Si no funciona, inténtalo de nuevo con más claridad

EJEMPLOS DE USO:
1. "Crear cuadrado de tres metros"
2. "Adelante dos metros"
3. "Rotar noventa grados"
4. "Ejecutar misión"
"""

        text_voz.insert(tk.END, comandos_voz)
        text_voz.config(state=tk.DISABLED)

        # Pestaña 6: Galería
        frame_galeria = tk.Frame(notebook)
        notebook.add(frame_galeria, text="📷 Galería")

        text_galeria = scrolledtext.ScrolledText(frame_galeria, wrap=tk.WORD,
                                                 font=("Arial", 10), padx=15, pady=15)
        text_galeria.pack(fill=tk.BOTH, expand=True)

        galeria_info = """GALERÍA DE MEDIOS - FOTOS Y VIDEOS

══════════════════════════════════════════════════════════════════

La Galería almacena todas las fotos y videos capturados durante
los vuelos, tanto en misiones planificadas como en modo joystick.

ABRIR GALERÍA:
• Pulsa el botón "📷 Galería" en la barra superior
• Se abrirá una ventana con todas tus capturas

CAPTURAR FOTOS:

1. EN MISIONES PLANIFICADAS:
   • Añade waypoints a tu misión
   • Pulsa "📷 Añadir Foto"
   • Se capturará una foto en el último waypoint añadido
   • En el mapa verás un icono 📷 azul

2. EN MODO JOYSTICK:
   • Durante el vuelo, pulsa Botón 3 del mando
   • Se captura instantáneamente
   • Se guarda con coordenadas GPS y metadatos

GRABAR VIDEOS:

EN MODO JOYSTICK:
• Pulsa Botón 0 del mando
• Grabará automáticamente 10 segundos
• Se guarda con timestamp y posición
• NO interrumpas el vuelo mientras graba

ORGANIZACIÓN:
• Fotos: carpeta "fotos_vuelo/"
• Videos: carpeta "videos_vuelo/"
• Cada archivo tiene:
  - Fecha y hora
  - Coordenadas de captura
  - Metadatos del vuelo

VISUALIZAR:
• Navega por las miniaturas en la galería
• Click para ver en tamaño completo
• Videos se pueden reproducir directamente

CONSEJOS:
✓ Revisa las fotos después de cada misión
✓ Borra las que no necesites para ahorrar espacio
✓ Los videos de 10s son ideales para clips cortos
✓ Las coordenadas te ayudan a recordar dónde volaste"""

        text_galeria.insert(tk.END, galeria_info)
        text_galeria.config(state=tk.DISABLED)

        btn_cerrar = tk.Button(ventana_ayuda, text="Cerrar",
                               command=ventana_ayuda.destroy,
                               bg="#4CAF50", fg="white",
                               font=("Arial", 10, "bold"),
                               width=15)
        btn_cerrar.pack(pady=10)

    def _cambiar_velocidad(self, event=None):
        """Cambia la velocidad según selección"""
        modo = self.combo_velocidad.get()

        if modo == "RÁPIDO":
            ConfigMision.ACTIVO = ConfigMision.RAPIDO
            vel = 0.4
        elif modo == "ESTABLE":
            ConfigMision.ACTIVO = ConfigMision.ESTABLE
            vel = 0.2
        else:  # NORMAL
            ConfigMision.ACTIVO = ConfigMision.NORMAL
            vel = 0.3

        self.label_vel_info.config(text=f"{vel} m/s")
        self._log(f"Velocidad cambiada: {modo} ({vel} m/s)")

        # Actualizar tiempo si hay misión
        if self.mission:
            self._actualizar_visualizacion()

    def _iniciar_monitoreo_bateria(self):
        """Inicia el monitoreo continuo de la batería"""
        self._actualizar_bateria()

    def _actualizar_bateria(self):
        """Actualiza el indicador de batería cada segundo"""
        if not self.dron or self.dron.state == "disconnected":
            # Detener monitoreo si se desconecta
            if self.timer_bateria:
                self.root.after_cancel(self.timer_bateria)
                self.timer_bateria = None
            self.label_bateria.config(text=" Batería: -- V", fg="gray")
            self.bateria_baja_mostrada = False
            return

        try:
            # Obtener voltaje de batería
            voltaje = self.dron.battery_level

            # Actualizar label con color según nivel
            if voltaje >= 3.8:
                color = "#4CAF50"
                estado = "BUENA"
                self.bateria_baja_mostrada = False
            elif voltaje >= 3.6:
                color = "#FF9800"
                estado = "MEDIA"
                self.bateria_baja_mostrada = False
            else:
                color = "#f44336"
                estado = "BAJA"

                # Actualizar el label
            self.label_bateria.config(
                text=f" Batería: {voltaje:.2f}V ({estado})",
                fg=color
            )
        except Exception as e:
            self._log(f"Error leyendo batería: {e}")
            self.label_bateria.config(text="🔋 Batería: Error", fg="red")
            # Intentar de nuevo en 2 segundos
            self.timer_bateria = self.root.after(2000, self._actualizar_bateria)

    def _anadir_foto(self):
        """Añade un comando de foto a la misión en la posición del último waypoint"""
        if self.mission is None:
            self.mission = FlightMission()
            self._log("Nueva misión creada")

        # CORRECCIÓN: Verificar que hay al menos un waypoint
        if len(self.mission.waypoints) == 0:
            messagebox.showwarning(
                "Sin Waypoints",
                "Debes añadir al menos un waypoint antes de añadir una foto.\n\n"
                "La foto se capturará en la posición del último waypoint añadido."
            )
            return

        # Añadir comando de foto con metadata
        metadata = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'waypoint': len(self.mission.waypoints)
        }

        self.mission.add_photo_command(metadata)
        self._actualizar_visualizacion()

        #  CORRECCIÓN: Usar la posición del último waypoint (current_position ya está actualizada)
        posicion = self.mission.current_position
        
        print(f"[DEBUG FOTO] Añadiendo foto en posición: {posicion}")

        # Mostrar icono de cámara en el canvas
        # CORRECCIÓN: Intercambiar X e Y para vista superior correcta
        # X del dron → Y del canvas (vertical), Y del dron → X del canvas (horizontal)
        if hasattr(self.visualizador, 'canvas'):
            x_canvas = self.visualizador.center_x - (posicion[1] * self.visualizador.escala)
            y_canvas = self.visualizador.center_y - (posicion[0] * self.visualizador.escala)
            
            print(f"[DEBUG FOTO] Posición en canvas: x={x_canvas}, y={y_canvas}")
            print(f"[DEBUG FOTO] Escala: {self.visualizador.escala}, Center: ({self.visualizador.center_x}, {self.visualizador.center_y})")


            if hasattr(self.visualizador, 'anadir_foto_planificada'):
                self.visualizador.anadir_foto_planificada(posicion[0], posicion[1], posicion[2])

            # Dibujar círculo azul como fondo para la cámara
            self.visualizador.canvas.create_oval(
                x_canvas - 15, y_canvas - 15,
                x_canvas + 15, y_canvas + 15,
                fill="#2196F3", outline="white", width=2,
                tags="photo_marker"
            )
            
            # Dibujar icono de cámara MÁS GRANDE
            self.visualizador.canvas.create_text(
                x_canvas, y_canvas,
                text="📷", font=("Arial", 20, "bold"),
                fill="white", tags="photo_marker"
            )
            
            self.visualizador.canvas.update()  # Forzar actualización
            print(f"[DEBUG FOTO] Icono de cámara dibujado")

        messagebox.showinfo("Foto Añadida",
                            f"📷 Comando de foto añadido en el último waypoint:\n\n"
                            f"X={posicion[0]:.2f}m, "
                            f"Y={posicion[1]:.2f}m, "
                            f"Z={posicion[2]:.2f}m\n\n"
                            f"El dron capturará una foto cuando llegue a este punto.")
        self._log(f"Comando de FOTO añadido en ({posicion[0]:.2f}, {posicion[1]:.2f}, {posicion[2]:.2f})")

    def _abrir_galeria(self):
        """Abre la galería de medios (fotos y videos)"""
        try:
            if self.photo_gallery is None or self.photo_gallery.ventana is None:
                self.photo_gallery = MediaGallery(
                    carpeta_fotos="fotos_vuelo",
                    carpeta_videos="videos_vuelo"
                )
                self.photo_gallery.abrir_galeria()
                self._log("Galería de medios abierta")
            else:
                self.photo_gallery.ventana.lift()
                self._log("Galería ya está abierta")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir la galería: {e} ")
            logging.error(f"Error abriendo galería: {e}")

    def _abrir_joystick(self):
        """Abre la interfaz de vuelo libre con joystick"""
        try:
            if self.vuelo_joystick is None or not hasattr(self.vuelo_joystick, 'ventana') or not self.vuelo_joystick.ventana.winfo_exists():
                self.vuelo_joystick = VueloLibreJoystick(parent=self.root)
                self.vuelo_joystick.abrir_ventana()
                self._log("Interfaz de vuelo libre con joystick abierta")
            else:
                self.vuelo_joystick.ventana.lift()
                self._log("Interfaz de joystick ya está abierta")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir la interfaz de joystick:\n{e}")
            logging.error(f"Error abriendo interfaz de joystick: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = MissionPlannerGUI(root)
    root.mainloop()