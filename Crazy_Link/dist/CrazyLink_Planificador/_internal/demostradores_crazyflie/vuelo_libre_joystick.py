"""
Vuelo Libre con Joystick
Sistema de control del dron Crazyflie mediante joystick con visualización en tiempo real
TODO EL CONTROL SE REALIZA DESDE EL MANDO
"""

import tkinter as tk
from tkinter import messagebox
import threading
import time
import logging
import pygame

from crazyLink.Dron_crazyflie import Dron
from crazyLink.modules_crazyflie.Joystick import Joystick
from crazyLink.modules_crazyflie.dron_camera import DroneCamera
from visualizador_telemetria_2d_realtime import VisualizadorTelemetria2D


class VueloLibreJoystick:
    """
    Controlador de vuelo libre con joystick que integra:
    - Conexión y control del dron DESDE EL MANDO
    - Visualización en tiempo real del trayecto
    - Interfaz gráfica de usuario (solo para visualización)
    """

    def __init__(self, parent=None):
        """Inicializa el sistema de vuelo libre

        Args:
            parent: Ventana padre (opcional). Si se proporciona, se crea como Toplevel
        """
        logging.basicConfig(level=logging.INFO)

        # Estado del sistema
        self.dron = None
        self.joystick = None
        self.joystick_conectado = False
        self.dron_conectado = False
        self.vuelo_libre_activo = False
        self.visualizador = None
        self.camera = None

        # Última posición conocida
        self.ultima_posicion = [0.0, 0.0, 0.0]

        # Thread para actualizar posición
        self.actualizando_posicion = False

        # Thread para monitorear estado del dron
        self.monitoreando_estado = False

        # Crear ventana principal o secundaria
        self._crear_ventana(parent)

    def _crear_ventana(self, parent=None):
        """Crea la interfaz gráfica principal o secundaria

        Args:
            parent: Ventana padre (opcional). Si se proporciona, se crea como Toplevel
        """
        if parent:
            self.ventana = tk.Toplevel(parent)
        else:
            self.ventana = tk.Tk()

        self.ventana.title("🎮 Vuelo Libre con Joystick - Control Total por Mando")
        self.ventana.geometry("1200x800")
        self.ventana.configure(bg="white")

        # Configurar el protocolo de cierre
        self.ventana.protocol("WM_DELETE_WINDOW", self._cerrar_ventana)

        # Configurar grid principal
        self.ventana.rowconfigure(0, weight=1)
        self.ventana.columnconfigure(0, weight=1)
        self.ventana.columnconfigure(1, weight=2)

        # === PANEL IZQUIERDO: ESTADO Y CONTROLES ===
        panel_control = tk.Frame(self.ventana, bg="#f5f5f5", width=350)
        panel_control.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        panel_control.grid_propagate(False)

        # Título del panel
        tk.Label(panel_control, text="🎮 CONTROL POR MANDO",
                font=("Arial", 16, "bold"), bg="#f5f5f5", fg="#333"
        ).pack(pady=15)

        # --- Botón Principal: Conectar Mando ---
        frame_principal = tk.LabelFrame(panel_control, text="🎮 Conexión",
                                       font=("Arial", 12, "bold"),
                                       bg="#f5f5f5", padx=10, pady=10)
        frame_principal.pack(fill=tk.X, padx=10, pady=5)

        self.btn_conectar_mando = tk.Button(
            frame_principal, text="🎮 CONECTAR MANDO Y DRON",
            bg="#2196F3", fg="white", font=("Arial", 12, "bold"),
            height=3, command=self.conectar_sistema
        )
        self.btn_conectar_mando.pack(fill=tk.X, pady=5)

        # --- Indicadores de Estado ---
        frame_estado = tk.LabelFrame(panel_control, text="📊 Estado del Sistema",
                                     font=("Arial", 12, "bold"),
                                     bg="#f5f5f5", padx=10, pady=10)
        frame_estado.pack(fill=tk.X, padx=10, pady=5)

        # Estado del mando
        self.lbl_mando_estado = tk.Label(
            frame_estado, text="❌ Mando: Desconectado",
            font=("Arial", 11), bg="#f5f5f5", fg="#f44336", anchor="w"
        )
        self.lbl_mando_estado.pack(fill=tk.X, pady=3)

        # Estado del dron
        self.lbl_dron_estado = tk.Label(
            frame_estado, text="❌ Dron: Desconectado",
            font=("Arial", 11), bg="#f5f5f5", fg="#f44336", anchor="w"
        )
        self.lbl_dron_estado.pack(fill=tk.X, pady=3)

        # Estado de armado
        self.lbl_armado_estado = tk.Label(
            frame_estado, text="⚪ Armado: No armado",
            font=("Arial", 11), bg="#f5f5f5", fg="#999", anchor="w"
        )
        self.lbl_armado_estado.pack(fill=tk.X, pady=3)

        # Estado de vuelo
        self.lbl_vuelo_estado = tk.Label(
            frame_estado, text="⚪ Vuelo: En tierra",
            font=("Arial", 11), bg="#f5f5f5", fg="#999", anchor="w"
        )
        self.lbl_vuelo_estado.pack(fill=tk.X, pady=3)

        # Estado de vuelo libre
        self.lbl_vuelo_libre_estado = tk.Label(
            frame_estado, text="⚪ Vuelo Libre: Inactivo",
            font=("Arial", 11, "bold"), bg="#f5f5f5", fg="#999", anchor="w"
        )
        self.lbl_vuelo_libre_estado.pack(fill=tk.X, pady=3)

        # Separador
        tk.Frame(frame_estado, height=2, bg="#cccccc").pack(fill=tk.X, pady=10)

        # Modo actual
        self.lbl_modo = tk.Label(
            frame_estado, text="Modo: --",
            font=("Arial", 10), bg="#f5f5f5", fg="#666", anchor="w"
        )
        self.lbl_modo.pack(fill=tk.X, pady=3)

        # --- Controles del Mando ---
        frame_controles = tk.LabelFrame(panel_control, text="🎮 Controles del Mando",
                                       font=("Arial", 12, "bold"),
                                       bg="#f5f5f5", padx=10, pady=10)
        frame_controles.pack(fill=tk.X, padx=10, pady=5)

        controles_text = """
🔘 SELECT:
   → ARMAR el dron

🔘 START:
   → DESPEGAR (sube a 1m)

🔘 Botón 0:
   → GRABAR VIDEO (10s) 🎬

🔘 Botón 1:
   → RTL (Return to Launch)

🔘 Botón 3:
   → ROTAR (mantener presionado)

🔘 Botón 4:
   → HACER FOTO 📷

🔘 Gatillo IZQ. 1:
   → ATERRIZAR

───────────────────────

🕹️ Joystick IZQUIERDO:
   Controla la ALTURA
   (Arriba/Abajo)

🕹️ Joystick DERECHO:
   Controla MOVIMIENTO
   (Adelante/Atrás/Izq/Der)
   Y rotación (Yaw)
        """

        tk.Label(
            frame_controles, text=controles_text,
            font=("Arial", 9), bg="#f5f5f5",
            justify=tk.LEFT, anchor="w"
        ).pack(fill=tk.BOTH, expand=True)

        # --- Información de Telemetría ---
        frame_telemetria = tk.LabelFrame(panel_control, text="📊 Telemetría",
                                         font=("Arial", 12, "bold"),
                                         bg="#f5f5f5", padx=10, pady=10)
        frame_telemetria.pack(fill=tk.X, padx=10, pady=5)

        self.lbl_posicion = tk.Label(
            frame_telemetria, text="X: 0.00m  Y: 0.00m  Z: 0.00m",
            font=("Arial", 10), bg="#f5f5f5"
        )
        self.lbl_posicion.pack(pady=5)

        self.lbl_bateria = tk.Label(
            frame_telemetria, text="Batería: ---%",
            font=("Arial", 10), bg="#f5f5f5"
        )
        self.lbl_bateria.pack(pady=5)

        # --- Botón de Emergencia ---
        frame_emergencia = tk.Frame(panel_control, bg="#f5f5f5")
        frame_emergencia.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(
            frame_emergencia, text="🚨 DESCONECTAR TODO",
            bg="#f44336", fg="white", font=("Arial", 11, "bold"),
            height=2, command=self.desconectar_todo
        ).pack(fill=tk.X)

        # === PANEL DERECHO: VISUALIZADOR ===
        panel_visualizador = tk.Frame(self.ventana, bg="white")
        panel_visualizador.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        # Crear visualizador de telemetría en tiempo real
        # Nota: pasamos None inicialmente, el dron se asignará después de conectar
        self.visualizador = VisualizadorTelemetria2D(panel_visualizador, dron=None)

    def conectar_sistema(self):
        """Conecta el mando y el dron"""
        try:
            # Verificar si hay joysticks disponibles
            pygame.init()
            pygame.joystick.init()

            num_joysticks = pygame.joystick.get_count()

            if num_joysticks == 0:
                messagebox.showwarning(
                    "Mando no encontrado",
                    "No se encontró ningún mando conectado.\n\n"
                    "Por favor:\n"
                    "1. Conecta el mando por USB\n"
                    "2. Vuelve a intentarlo"
                )
                return

            # Mostrar joysticks disponibles
            joystick_info = f"Se encontraron {num_joysticks} mando(s):\n"
            for i in range(num_joysticks):
                joy = pygame.joystick.Joystick(i)
                joy.init()
                joystick_info += f"\n{i}: {joy.get_name()}"
                joy.quit()

            logging.info(joystick_info)

            # Usar el primer joystick (ID 0)
            joystick_id = 0

            # Actualizar interfaz
            self.btn_conectar_mando.config(text="Conectando...", state=tk.DISABLED)
            self.ventana.update()

            # 1. CONECTAR EL DRON
            self.lbl_dron_estado.config(text="🔄 Dron: Conectando...", fg="#FF9800")
            self.ventana.update()

            self.dron = Dron()
            self.dron.connect()
            self.dron_conectado = True

            self.lbl_dron_estado.config(text="✅ Dron: Conectado", fg="#4CAF50")
            logging.info("✅ Dron conectado correctamente")

            # Asignar el dron al visualizador
            self.visualizador.dron = self.dron

            # 2. CONECTAR EL MANDO
            self.lbl_mando_estado.config(text="🔄 Mando: Conectando...", fg="#FF9800")
            self.ventana.update()

            # 3. INICIALIZAR CÁMARA (ANTES del joystick para que esté disponible)
            self.camera = DroneCamera(carpeta_fotos="fotos_vuelo_libre", carpeta_videos="videos_vuelo_libre")
            self.camera.abrir_camara()
            logging.info("✅ Cámara inicializada")

            def identificar_joystick(id_joy):
                logging.info(f"Joystick {id_joy} identificado")

            # Crear el joystick con callback personalizado y cámara
            self.joystick = JoystickExtendido(
                joystick_id,
                self.dron,
                identificar_joystick,
                callback_estado=self._actualizar_estados_desde_joystick,
                camera=self.camera
            )
            self.joystick_conectado = True

            self.lbl_mando_estado.config(text="✅ Mando: Conectado", fg="#4CAF50")
            logging.info(f"✅ Mando conectado: {joystick_info}")

            # 4. INICIAR TELEMETRÍA
            self._iniciar_telemetria()

            # 5. INICIAR MONITOREO DE ESTADO
            self._iniciar_monitoreo_estado()

            # 6. INICIAR MONITOREO DEL VISUALIZADOR
            self.visualizador.iniciar_monitoreo()

            # Actualizar interfaz
            self.btn_conectar_mando.config(
                text="✅ SISTEMA CONECTADO",
                bg="green"
            )

        except Exception as e:
            logging.error(f"Error al conectar el sistema: {e}")
            messagebox.showerror("Error", f"No se pudo conectar:\n{e}")
            self.lbl_dron_estado.config(text="❌ Dron: Error de conexión", fg="#f44336")
            self.lbl_mando_estado.config(text="❌ Mando: Error de conexión", fg="#f44336")
            self.btn_conectar_mando.config(
                text="🎮 CONECTAR MANDO Y DRON",
                state=tk.NORMAL,
                bg="#2196F3"
            )

    def _actualizar_estados_desde_joystick(self, evento, datos=None):
        """Callback para recibir eventos del joystick"""
        try:
            if evento == "armado":
                self.lbl_armado_estado.config(text="✅ Armado: SÍ", fg="#4CAF50")

            elif evento == "despegue_iniciado":
                self.lbl_vuelo_estado.config(text="🔄 Vuelo: Despegando...", fg="#FF9800")

            elif evento == "volando":
                self.lbl_vuelo_estado.config(text="✅ Vuelo: EN EL AIRE", fg="#4CAF50")
                # Activar vuelo libre automáticamente
                if not self.vuelo_libre_activo:
                    self._activar_vuelo_libre()

            elif evento == "aterrizado":
                self.lbl_vuelo_estado.config(text="⚪ Vuelo: En tierra", fg="#999")
                if self.vuelo_libre_activo:
                    self._desactivar_vuelo_libre()

            elif evento == "modo_cambiado":
                modo = datos.get("modo", "--")
                self.lbl_modo.config(text=f"Modo: {modo}")

        except Exception as e:
            logging.warning(f"Error actualizando estados: {e}")

    def _activar_vuelo_libre(self):
        """Activa el modo de vuelo libre"""
        try:
            logging.info("🚀 Activando vuelo libre...")

            # Activar control del joystick
            if self.joystick:
                self.joystick.activar_control()

            self.vuelo_libre_activo = True
            self.lbl_vuelo_libre_estado.config(
                text="✅ Vuelo Libre: ACTIVO",
                fg="#4CAF50",
                font=("Arial", 11, "bold")
            )
            self.lbl_modo.config(text="Modo: Control Manual Activo")

            # El visualizador ya está monitoreando automáticamente

            logging.info("✅ Vuelo libre ACTIVADO")

        except Exception as e:
            logging.error(f"Error activando vuelo libre: {e}")

    def _desactivar_vuelo_libre(self):
        """Desactiva el modo de vuelo libre"""
        try:
            logging.info("⏸ Desactivando vuelo libre...")

            # Desactivar control del joystick
            if self.joystick:
                self.joystick.desactivar_control()

            self.vuelo_libre_activo = False
            self.lbl_vuelo_libre_estado.config(
                text="⚪ Vuelo Libre: Inactivo",
                fg="#999"
            )
            self.lbl_modo.config(text="Modo: Control Desactivado")

            # El visualizador sigue monitoreando automáticamente

            logging.info("⏸ Vuelo libre DESACTIVADO")

        except Exception as e:
            logging.error(f"Error desactivando vuelo libre: {e}")

    def _iniciar_monitoreo_estado(self):
        """Inicia el monitoreo constante del estado del dron"""
        self.monitoreando_estado = True

        def monitorear_loop():
            estado_anterior = None
            while self.monitoreando_estado and self.dron:
                try:
                    estado_actual = self.dron.state

                    # Solo actualizar si cambió el estado
                    if estado_actual != estado_anterior:
                        logging.info(f"Estado del dron cambió: {estado_actual}")

                        if estado_actual == "armed":
                            self.lbl_armado_estado.config(text="✅ Armado: SÍ", fg="#4CAF50")

                        elif estado_actual == "takingOff":
                            self.lbl_vuelo_estado.config(text="🔄 Vuelo: Despegando...", fg="#FF9800")

                        elif estado_actual == "flying":
                            self.lbl_vuelo_estado.config(text="✅ Vuelo: EN EL AIRE", fg="#4CAF50")
                            # Activar vuelo libre automáticamente
                            if not self.vuelo_libre_activo:
                                self._activar_vuelo_libre()

                        elif estado_actual == "landing":
                            self.lbl_vuelo_estado.config(text="🔄 Vuelo: Aterrizando...", fg="#FF9800")

                        elif estado_actual == "connected":
                            self.lbl_vuelo_estado.config(text="⚪ Vuelo: En tierra", fg="#999")
                            self.lbl_armado_estado.config(text="⚪ Armado: No armado", fg="#999")
                            if self.vuelo_libre_activo:
                                self._desactivar_vuelo_libre()

                        estado_anterior = estado_actual

                    time.sleep(0.2)

                except Exception as e:
                    logging.warning(f"Error en monitoreo de estado: {e}")
                    time.sleep(0.5)

        threading.Thread(target=monitorear_loop, daemon=True).start()

    def _iniciar_telemetria(self):
        """Inicia el thread de telemetría"""
        def actualizar_telemetria():
            self.dron.send_local_telemetry_info(self._callback_telemetria)

        threading.Thread(target=actualizar_telemetria, daemon=True).start()

    def _callback_telemetria(self, data):
        """Callback para recibir datos de telemetría"""
        try:
            x = data.get('posX', 0.0)
            y = data.get('posY', 0.0)
            z = data.get('posZ', 0.0)
            bat = data.get('batt', 0.0)

            # Actualizar labels
            self.lbl_posicion.config(text=f"X: {x:.2f}m  Y: {y:.2f}m  Z: {z:.2f}m")
            self.lbl_bateria.config(text=f"Batería: {bat:.1f}%")

            # Guardar última posición
            self.ultima_posicion = [x, y, z]

        except Exception as e:
            logging.warning(f"Error en callback de telemetría: {e}")

    # Nota: _iniciar_actualizacion_posicion ya no es necesario
    # El VisualizadorTelemetria2D tiene su propio sistema de monitoreo automático

    def _cerrar_ventana(self):
        """Maneja el cierre de la ventana"""
        respuesta = messagebox.askyesno(
            "Cerrar Vuelo Libre",
            "¿Deseas cerrar la interfaz de vuelo libre?\n\n"
            "Se desconectará el joystick y la telemetría."
        )

        if respuesta:
            self.desconectar_todo()
            self.ventana.destroy()

    def desconectar_todo(self):
        """Desconecta todo el sistema"""
        try:
            # Detener vuelo libre
            if self.vuelo_libre_activo:
                self._desactivar_vuelo_libre()

            # Detener monitoreo
            self.monitoreando_estado = False

            # Detener visualizador
            if self.visualizador:
                self.visualizador.pausar_monitoreo()

            # Detener joystick
            if self.joystick:
                self.joystick.stop()

            # Detener telemetría
            if self.dron:
                self.dron.stop_sending_local_telemetry_info()

            # Cerrar cámara
            if self.camera:
                self.camera.cerrar_camara()

            # Resetear estados
            self.lbl_mando_estado.config(text="❌ Mando: Desconectado", fg="#f44336")
            self.lbl_dron_estado.config(text="❌ Dron: Desconectado", fg="#f44336")
            self.lbl_armado_estado.config(text="⚪ Armado: No armado", fg="#999")
            self.lbl_vuelo_estado.config(text="⚪ Vuelo: En tierra", fg="#999")
            self.lbl_vuelo_libre_estado.config(text="⚪ Vuelo Libre: Inactivo", fg="#999")
            self.lbl_modo.config(text="Modo: --")

            self.btn_conectar_mando.config(
                text="🎮 CONECTAR MANDO Y DRON",
                state=tk.NORMAL,
                bg="#2196F3"
            )

            logging.info("Sistema desconectado")

        except Exception as e:
            logging.error(f"Error al desconectar: {e}")

    def abrir_ventana(self):
        """Abre la ventana sin mainloop (para uso como ventana secundaria)"""
        # La ventana ya fue creada en __init__
        # Solo se asegura de que esté visible
        self.ventana.deiconify()

    def run(self):
        """Ejecuta la aplicación (solo para uso standalone)"""
        self.ventana.mainloop()

        # Limpieza al cerrar
        self._limpiar_recursos()

    def _limpiar_recursos(self):
        """Limpia todos los recursos al cerrar"""
        self.monitoreando_estado = False
        if self.visualizador:
            self.visualizador.pausar_monitoreo()
        if self.joystick:
            self.joystick.stop()
        if self.dron:
            self.dron.stop_sending_local_telemetry_info()
        if self.camera:
            self.camera.cerrar_camara()


class JoystickExtendido(Joystick):
    """
    Versión extendida de Joystick con callbacks para actualizar la interfaz
    """
    def __init__(self, num, dron, idCallback, callback_estado=None, camera=None):
        self.callback_estado = callback_estado
        self.camera = camera
        super().__init__(num, dron, idCallback)

    def control_loop(self):
        # Inicializar pygame y el módulo de joystick
        pygame.init()
        pygame.joystick.init()
        # Obtener el primer joystick
        self.joystick = pygame.joystick.Joystick(self.id)
        self.joystick.init()
        print("Name: ", self.joystick.get_name())
        self.pitch = 2
        if self.joystick.get_name() == 'USB Gamepad':
            self.pitch = 2
        elif self.joystick.get_name() == 'Generic USB Joystick':
            self.pitch = 4

        print("Joystick preparado: ", self.id)
        self.working = True

        # Variables para detectar cambios de estado
        armado_anterior = False
        volando_anterior = False
        grabando_anterior = False

        while self.working:
            pygame.event.pump()
            # Leer estado de botones y ejes
            roll = self.map_axis(self.joystick.get_axis(3))  # RC1: Roll
            pitch = self.map_axis(self.joystick.get_axis(self.pitch))  # RC2: Pitch
            throttle = self.map_axis(-self.joystick.get_axis(1))  # RC3: Throttle
            yaw = self.map_axis(self.joystick.get_axis(0))  # RC4: Yaw
            print(roll, pitch, throttle, yaw)

            # Solo enviar comandos si el control está activo
            if self.control_activo:
                self.dron.send_rc(roll, pitch, throttle, yaw)

            # BOTÓN 0: GRABAR VIDEO CORTO (10 segundos)
            if self.joystick.get_button(0) == 1:
                if not grabando_anterior:
                    if self.camera:
                        try:
                            # Verificar que no hay una grabación en curso
                            if not self.camera.esta_grabando():
                                # Obtener posición actual del dron
                                posicion = tuple(self.dron.position)
                                # Iniciar grabación de video de 10 segundos
                                ruta_video = self.camera.iniciar_video_corto(
                                    duracion=10,
                                    posicion=posicion,
                                    metadata={"estado": self.dron.state}
                                )
                                if ruta_video:
                                    print(f"🎬 Botón 0 → GRABANDO VIDEO (10s): {ruta_video}")
                                else:
                                    print("🎬 Botón 0 → Error al iniciar grabación de video")
                            else:
                                print("🎬 Botón 0 → Ya hay una grabación en curso")
                        except Exception as e:
                            print(f"🎬 Error al grabar video: {e}")
                    else:
                        print("🎬 Botón 0 → Cámara no disponible")
                    grabando_anterior = True
                    time.sleep(0.5)  # Evitar múltiples pulsaciones
            else:
                grabando_anterior = False

            # BOTÓN SELECT (8): ARMAR
            if self.joystick.get_button(8) == 1:
                if not armado_anterior:
                    print("SELECT presionado → ARMANDO DRON")
                    self.dron.arm()
                    if self.callback_estado:
                        self.callback_estado("armado")
                    armado_anterior = True
                    time.sleep(0.5)  # Evitar múltiples pulsaciones
            else:
                armado_anterior = False

            # BOTÓN START (9): DESPEGAR
            if self.joystick.get_button(9) == 1:
                if not volando_anterior:
                    print("START presionado → DESPEGANDO")
                    if self.callback_estado:
                        self.callback_estado("despegue_iniciado")
                    self.dron.takeOff(1, blocking=False)
                    volando_anterior = True
                    time.sleep(0.5)  # Evitar múltiples pulsaciones
            else:
                volando_anterior = False

            # BOTÓN 1: RTL
            if self.joystick.get_button(1) == 1:
                self.dron.RTL(blocking=False)
                print("Botón 1 → RTL activado")
                time.sleep(0.5)

            # BOTÓN 2: ROTAR CONTINUAMENTE (mientras se mantiene presionado)
            if self.joystick.get_button(2) == 1:
                # Enviar comando de yaw para rotar continuamente
                # Rotación a la derecha con velocidad máxima del protocolo RC
                if self.control_activo:
                    self.dron.send_rc(1500, 1500, 1500, 2000)  # Yaw máximo a la derecha
                    print("Botón 2 → ROTANDO...")

            # BOTÓN 3: HACER FOTO
            if self.joystick.get_button(3) == 1:
                if self.camera:
                    try:
                        # Obtener posición actual del dron
                        posicion = tuple(self.dron.position)
                        # Capturar foto
                        ruta_foto = self.camera.capturar_foto(posicion=posicion, metadata={"estado": self.dron.state})
                        if ruta_foto:
                            print(f"📷 Botón 4 → FOTO CAPTURADA: {ruta_foto}")
                        else:
                            print("📷 Botón 4 → Error al capturar foto")
                    except Exception as e:
                        print(f"📷 Error al capturar foto: {e}")
                else:
                    print("📷 Botón 4 → Cámara no disponible")
                time.sleep(0.5)  # Evitar múltiples capturas

            # BOTÓN 4: ATERRIZAR
            if self.joystick.get_button(4) == 1:
                self.dron.Land(blocking=False)
                if self.callback_estado:
                    self.callback_estado("aterrizado")
                print("Gatillo IZQ. 1 → ATERRIZANDO")
                time.sleep(0.5)

            time.sleep(0.1)


if __name__ == "__main__":
    print("=" * 70)
    print("🎮 SISTEMA DE VUELO LIBRE CON CONTROL TOTAL POR MANDO")
    print("=" * 70)
    print()
    print("INSTRUCCIONES:")
    print("1. Conecta el mando por USB")
    print("2. Click en 'CONECTAR MANDO Y DRON'")
    print("3. Usa el mando para:")
    print("   - SELECT → Armar")
    print("   - START → Despegar")
    print("   - Botón 0 → Grabar video (10s) 🎬")
    print("   - Botón 1 → RTL")
    print("   - Botón 2 → Rotar (mantener presionado)")
    print("   - Botón 3 → Hacer foto 📷")
    print("   - Botón 4 → Aterrizar")
    print()
    print("El vuelo libre se activará automáticamente al despegar")
    print("=" * 70)
    print()

    app = VueloLibreJoystick()
    app.run()
