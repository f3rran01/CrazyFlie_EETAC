"""
Módulo de Integración del Planificador Interactivo
Este módulo añade funcionalidad de planificación por clicks al Demo_plan_de_vuelo.py

CÓMO USAR:
1. Importar este módulo en Demo_plan_de_vuelo.py
2. Llamar a integrar_planificador_interactivo(gui_instance) después de crear la GUI

FUNCIONALIDADES AÑADIDAS:
- Modo "Click para añadir waypoints" en el mapa
- Popup de configuración para cada waypoint
- Soporte para fotos, videos cortos y videos de ruta
- Visualización diferenciada por tipo de acción
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
import time
import threading

# Importar módulos del planificador interactivo
from waypoint_config_dialog import InteractiveFlightPlanner, WaypointConfigDialog
from mision_interactiva import InteractiveMission, ejecutar_mision_interactiva, previsualizar_mision_interactiva

# Nota: La cámara se obtiene de la GUI principal (self.gui.camera)


class PlanificadorInteractivoUI:
    """
    Clase que añade la interfaz de planificación interactiva a la GUI principal.
    """

    def __init__(self, gui_principal):
        """
        Inicializa el planificador interactivo.

        Args:
            gui_principal: Instancia de MissionPlannerGUI
        """
        self.gui = gui_principal
        self.planner = None
        self.mission_interactiva = None
        self.modo_activo = False

        # Reemplazar la cámara por la versión extendida (con soporte de video)
        self.camera_extended = None

        # Referencias a elementos UI
        self.btn_modo_interactivo = None
        self.btn_limpiar_interactivo = None
        self.btn_eliminar_ultimo = None
        self.btn_ejecutar_interactivo = None
        self.label_waypoints_count = None
        self.frame_interactivo = None

        # Inicializar
        self._crear_ui()
        self._inicializar_planner()

        logging.info("[PlanificadorUI] Planificador interactivo integrado")

    def _crear_ui(self):
        """Crea los elementos de interfaz para el planificador interactivo"""
        # Buscar el frame izquierdo donde están los otros controles
        # Asumimos que está en el mismo contenedor que los otros LabelFrames
        parent_frame = None

        # Buscar el frame_izq en la estructura de la GUI
        for child in self.gui.root.winfo_children():
            for subchild in child.winfo_children():
                if isinstance(subchild, tk.Frame) and subchild.winfo_width() < 400:
                    # Probablemente es el panel izquierdo
                    parent_frame = subchild
                    break

        if parent_frame is None:
            # Fallback: usar el root
            parent_frame = self.gui.root

        # Crear frame para planificación interactiva (COMPACTO)
        self.frame_interactivo = tk.LabelFrame(
            parent_frame,
            text="🗺️ Plan Interactivo",
            padx=5, pady=3,
            font=("Arial", 9, "bold")
        )

        # Insertar después del frame de patrones
        self.frame_interactivo.pack(fill=tk.X, pady=3, after=None)

        # Fila 1: Botón modo + contador
        frame_fila1 = tk.Frame(self.frame_interactivo)
        frame_fila1.pack(fill=tk.X, pady=2)

        self.btn_modo_interactivo = tk.Button(
            frame_fila1,
            text="🖱️ Modo Click",
            command=self._toggle_modo_interactivo,
            bg="#9C27B0", fg="white",
            font=("Arial", 8, "bold"),
            width=12
        )
        self.btn_modo_interactivo.pack(side=tk.LEFT, padx=2)

        # Botones pequeños: Deshacer y Limpiar
        self.btn_eliminar_ultimo = tk.Button(
            frame_fila1,
            text="↩",
            command=self._eliminar_ultimo_waypoint,
            bg="#FF9800", fg="white",
            font=("Arial", 9),
            width=3,
            state=tk.DISABLED
        )
        self.btn_eliminar_ultimo.pack(side=tk.LEFT, padx=1)

        self.btn_limpiar_interactivo = tk.Button(
            frame_fila1,
            text="🗑",
            command=self._limpiar_planificacion,
            bg="#f44336", fg="white",
            font=("Arial", 9),
            width=3,
            state=tk.DISABLED
        )
        self.btn_limpiar_interactivo.pack(side=tk.LEFT, padx=1)

        self.btn_previsualizar = tk.Button(
            frame_fila1,
            text="📋",
            command=self._previsualizar_interactivo,
            bg="#2196F3", fg="white",
            font=("Arial", 9),
            width=3,
            state=tk.DISABLED
        )
        self.btn_previsualizar.pack(side=tk.LEFT, padx=1)

        # Contador de waypoints
        self.label_waypoints_count = tk.Label(
            frame_fila1,
            text="WPs: 0",
            font=("Arial", 9, "bold"),
            fg="#2196F3"
        )
        self.label_waypoints_count.pack(side=tk.RIGHT, padx=5)

        # Fila 2: Botón EJECUTAR grande y visible
        self.btn_ejecutar_interactivo = tk.Button(
            self.frame_interactivo,
            text="▶ EJECUTAR RUTA",
            command=self._ejecutar_mision_interactiva,
            bg="#4CAF50", fg="white",
            font=("Arial", 9, "bold"),
            state=tk.DISABLED,
            height=1
        )
        self.btn_ejecutar_interactivo.pack(fill=tk.X, padx=2, pady=3)

    def _inicializar_planner(self):
        """Inicializa el planificador interactivo"""
        if hasattr(self.gui, 'visualizador') and self.gui.visualizador:
            self.planner = InteractiveFlightPlanner(
                canvas=self.gui.visualizador.canvas,
                visualizador=self.gui.visualizador,
                on_waypoint_added=self._on_waypoint_added
            )
            logging.info("[PlanificadorUI] Planner vinculado al visualizador")
        else:
            logging.warning("[PlanificadorUI] Visualizador no disponible aún")

    def _toggle_modo_interactivo(self):
        """Activa/desactiva el modo de planificación interactiva"""
        if self.planner is None:
            self._inicializar_planner()
            if self.planner is None:
                messagebox.showerror("Error", "No se pudo inicializar el planificador")
                return

        if self.modo_activo:
            # Desactivar
            self.planner.desactivar()
            self.modo_activo = False
            self.btn_modo_interactivo.config(
                text="🖱️ Modo Click",
                bg="#9C27B0"
            )
            self._log("Modo interactivo DESACTIVADO")
            
            # Resetear flag de ejecución si quedó bloqueado
            if hasattr(self.gui, 'ejecutando_mision') and self.gui.ejecutando_mision:
                self.gui.ejecutando_mision = False
                self._log("Estado de ejecución reseteado")
        else:
            # Activar
            # Crear callback de validación para geocage
            validation_callback = None
            if hasattr(self.gui, 'geocage_activo') and self.gui.geocage_activo:
                if hasattr(self.gui, '_punto_dentro_geocage'):
                    validation_callback = lambda x, y, z: self.gui._punto_dentro_geocage(x, y)

            self.planner.activar(validation_callback)
            self.modo_activo = True
            self.btn_modo_interactivo.config(
                text="⏹️ Desactivar",
                bg="#E91E63"
            )
            self._log("Modo interactivo ACTIVADO - Click en el mapa para añadir waypoints")

    def _on_waypoint_added(self, config):
        """Callback cuando se añade un waypoint"""
        # Actualizar contador
        num_wps = self.planner.get_num_waypoints()
        self.label_waypoints_count.config(text=f"WPs: {num_wps}")

        # Habilitar botones
        self.btn_eliminar_ultimo.config(state=tk.NORMAL)
        self.btn_limpiar_interactivo.config(state=tk.NORMAL)
        self.btn_previsualizar.config(state=tk.NORMAL)

        # CORRECCIÓN: Resetear flag si está bloqueado
        if hasattr(self.gui, 'ejecutando_mision') and self.gui.ejecutando_mision:
            try:
                if self.gui.dron and self.gui.dron.state not in ["flying", "armed"]:
                    logging.info("[PlanificadorUI] Reseteando flag ejecutando_mision")
                    self.gui.ejecutando_mision = False
            except:
                pass

        # Habilitar ejecutar si hay dron conectado Y no está ejecutando
        dron_listo = False
        if hasattr(self.gui, 'dron') and self.gui.dron is not None:
            try:
                dron_listo = self.gui.dron.state != "disconnected"
            except:
                dron_listo = False

        no_ejecutando = not (hasattr(self.gui, 'ejecutando_mision') and self.gui.ejecutando_mision)
        
        if dron_listo and no_ejecutando:
            self.btn_ejecutar_interactivo.config(state=tk.NORMAL)
        else:
            self.btn_ejecutar_interactivo.config(state=tk.DISABLED)

        # Log
        acciones = []
        if config['foto']:
            acciones.append("📷")
        if config['video_corto']:
            acciones.append("🎬")
        if config['video_ruta']:
            acciones.append("🎥")
        if config['rotacion'] != 0:
            acciones.append(f"↻{config['rotacion']}°")

        acciones_str = " ".join(acciones) if acciones else "sin acciones"
        self._log(f"WP{config['waypoint_number']}: ({config['x']:.2f}, {config['y']:.2f}, {config['z']:.2f}m) - {acciones_str}")

    def _eliminar_ultimo_waypoint(self):
        """Elimina el último waypoint añadido"""
        if self.planner and self.planner.eliminar_ultimo():
            num_wps = self.planner.get_num_waypoints()
            self.label_waypoints_count.config(text=f"WPs: {num_wps}")

            if num_wps == 0:
                self.btn_eliminar_ultimo.config(state=tk.DISABLED)
                self.btn_limpiar_interactivo.config(state=tk.DISABLED)
                self.btn_previsualizar.config(state=tk.DISABLED)
                self.btn_ejecutar_interactivo.config(state=tk.DISABLED)

            self._log("Último waypoint eliminado")

    def _limpiar_planificacion(self):
        """Limpia todos los waypoints"""
        if not self.planner or not self.planner.tiene_waypoints():
            return

        respuesta = messagebox.askyesno(
            "Confirmar",
            "¿Eliminar todos los waypoints de la planificación interactiva?"
        )

        if respuesta:
            self.planner.limpiar()
            self.label_waypoints_count.config(text="WPs: 0")
            self.btn_eliminar_ultimo.config(state=tk.DISABLED)
            self.btn_limpiar_interactivo.config(state=tk.DISABLED)
            self.btn_previsualizar.config(state=tk.DISABLED)
            self.btn_ejecutar_interactivo.config(state=tk.DISABLED)
            self._log("Planificación interactiva limpiada")

    def _previsualizar_interactivo(self):
        """Muestra previsualización de la misión interactiva"""
        if not self.planner or not self.planner.tiene_waypoints():
            messagebox.showinfo("Info", "No hay waypoints para previsualizar")
            return

        # Crear misión temporal para previsualización
        mission = InteractiveMission()
        mission.add_waypoints_from_planner(self.planner.obtener_mision())

        # Mostrar en consola
        previsualizar_mision_interactiva(mission)

        # Mostrar resumen en diálogo
        summary = mission.get_mission_summary()

        mensaje = f"""📊 RESUMEN DE LA RUTA INTERACTIVA

📍 Waypoints: {summary['num_waypoints']}
📷 Fotos programadas: {summary['num_fotos']}
🎬 Videos cortos: {summary['num_videos_cortos']}
🎥 Video de ruta: {'Sí' if summary['tiene_video_ruta'] else 'No'}
↻ Rotaciones: {summary['num_rotaciones']}

📏 Distancia total: {summary['distancia_total']:.2f} m
⏱ Tiempo estimado: {summary['tiempo_estimado']:.1f} s"""

        messagebox.showinfo("Previsualización de Ruta", mensaje)

    def _ejecutar_mision_interactiva(self):
        """Ejecuta la misión creada interactivamente"""
        # === VERIFICACIONES PREVIAS (antes de cualquier cambio de estado) ===
        
        if not self.planner or not self.planner.tiene_waypoints():
            messagebox.showwarning("Advertencia", "No hay waypoints para ejecutar")
            return

        # Verificar que el dron existe
        if not hasattr(self.gui, 'dron') or self.gui.dron is None:
            messagebox.showwarning("Advertencia", "Dron no conectado.\n\nPulsa 'Conectar Dron' primero.")
            return
        
        # Verificar estado del dron
        try:
            dron_state = self.gui.dron.state
        except:
            dron_state = "disconnected"
            
        if dron_state == "disconnected":
            messagebox.showwarning("Advertencia", "Dron desconectado.\n\nPulsa 'Conectar Dron' primero.")
            return

        # Verificar si ya hay misión en ejecución
        if hasattr(self.gui, 'ejecutando_mision') and self.gui.ejecutando_mision:
            messagebox.showinfo("Info", "Ya hay una misión en ejecución.\n\nEspera a que termine.")
            return

        # === PREPARAR MISIÓN ===
        mission = InteractiveMission()
        mission.add_waypoints_from_planner(self.planner.obtener_mision())
        summary = mission.get_mission_summary()

        # Confirmar ejecución
        mensaje = f"""¿Ejecutar ruta interactiva?

📍 {summary['num_waypoints']} waypoints
📏 {summary['distancia_total']:.2f} m
⏱ ~{summary['tiempo_estimado']:.1f} s"""

        if summary['num_fotos'] > 0:
            mensaje += f"\n📷 {summary['num_fotos']} fotos"
        if summary['num_videos_cortos'] > 0:
            mensaje += f"\n🎬 {summary['num_videos_cortos']} videos cortos"
        if summary['tiene_video_ruta']:
            mensaje += f"\n🎥 Video de ruta"

        respuesta = messagebox.askyesno("Confirmar Ejecución", mensaje)
        if not respuesta:
            return

        # === VERIFICAR DE NUEVO EL DRON (pudo desconectarse mientras el diálogo estaba abierto) ===
        try:
            if self.gui.dron is None or self.gui.dron.state == "disconnected":
                messagebox.showwarning("Advertencia", "El dron se desconectó.\n\nReconecta e intenta de nuevo.")
                return
        except:
            messagebox.showwarning("Advertencia", "Error al verificar el dron.\n\nReconecta e intenta de nuevo.")
            return

        # Usar la cámara de la GUI principal (ya inicializada)
        if self.camera_extended is None:
            if hasattr(self.gui, 'camera') and self.gui.camera is not None:
                self.camera_extended = self.gui.camera
                logging.info("[PlanificadorUI] Usando cámara de la GUI principal")
            else:
                logging.warning("[PlanificadorUI] No hay cámara disponible, continuando sin cámara")
                self.camera_extended = None

        # === AHORA SÍ MARCAMOS COMO EJECUTANDO ===
        self.gui.ejecutando_mision = True
        self._log(f"🚁 Iniciando ruta interactiva - {summary['num_waypoints']} waypoints")

        # Deshabilitar botones
        self.btn_ejecutar_interactivo.config(state=tk.DISABLED)
        self.btn_modo_interactivo.config(state=tk.DISABLED)

        def ejecutar_thread():
            try:
                dron = self.gui.dron

                # Armar si es necesario
                if dron.state != "armed" and dron.state != "flying":
                    self.gui.root.after(0, lambda: self._log("Armando dron..."))
                    dron.arm()
                    time.sleep(1)

                # Despegar si no está volando
                if dron.state != "flying":
                    self.gui.root.after(0, lambda: self._log("Despegando..."))
                    dron.takeOff(0.5)
                    time.sleep(2)

                self.gui.root.after(0, lambda: self.gui.label_estado.config(
                    text="Estado: Ejecutando Ruta 🚁", fg="blue"
                ))

                # Ejecutar misión
                from config_mision import ConfigMision
                velocidad = ConfigMision.get_velocidad()

                # Callback de progreso
                def on_progreso(wp_actual, wp_total, porcentaje):
                    self.gui.root.after(0, lambda: self._log(
                        f"Progreso: {wp_actual}/{wp_total} ({porcentaje:.0f}%)"
                    ))

                # Validador de geocage
                geocage_validator = None
                if hasattr(self.gui, 'geocage_activo') and self.gui.geocage_activo:
                    if hasattr(self.gui, '_punto_dentro_geocage'):
                        geocage_validator = self.gui._punto_dentro_geocage

                # ✅ NUEVO: Obtener pathfinder para evasión de obstáculos
                pathfinder = None
                if hasattr(self.gui, 'pathfinder'):
                    pathfinder = self.gui.pathfinder

                # Ejecutar
                exito = ejecutar_mision_interactiva(
                    dron=dron,
                    mission=mission,
                    camera=self.camera_extended,
                    velocidad=velocidad,
                    callback_posicion=self._actualizar_posicion if hasattr(self.gui, '_actualizar_posicion_real') else None,
                    callback_progreso=on_progreso,
                    geocage_validator=geocage_validator,
                    visualizador=self.gui.visualizador if hasattr(self.gui, 'visualizador') else None,
                    pathfinder=pathfinder  # ✅ NUEVO: Pasar pathfinder
                )

                if exito:
                    self.gui.root.after(0, lambda: self._log("✓ Ruta completada"))
                    self.gui.root.after(0, lambda: self._log("Aterrizando..."))

                    dron.Land()
                    time.sleep(3)

                    self.gui.root.after(0, lambda: self.gui.label_estado.config(
                        text="Estado: Ruta Completada ✓", fg="green"
                    ))

                    # Mostrar resumen de medios capturados
                    if self.camera_extended and hasattr(self.camera_extended, 'obtener_info_sesion'):
                        try:
                            info = self.camera_extended.obtener_info_sesion()
                            resumen = f"¡Ruta completada!\n\n📷 Fotos: {info['num_fotos']}\n🎬 Videos: {info['num_videos']}"
                        except:
                            resumen = "¡Ruta completada!"
                    else:
                        resumen = "¡Ruta completada!"
                    self.gui.root.after(0, lambda r=resumen: messagebox.showinfo("Éxito", r))

                    # Limpiar planificación
                    self.gui.root.after(0, self._limpiar_despues_ejecucion)
                else:
                    self.gui.root.after(0, lambda: self._log("❌ Error durante la ruta"))
                    self.gui.root.after(0, lambda: messagebox.showerror(
                        "Error", "La ruta no se completó correctamente"
                    ))

            except Exception as e:
                self.gui.root.after(0, lambda: self._log(f"❌ Error: {e}"))
                self.gui.root.after(0, lambda: messagebox.showerror("Error", f"Error: {e}"))

                # Intentar aterrizar
                try:
                    if self.gui.dron and self.gui.dron.state != "disconnected":
                        self.gui.dron.Land()
                except:
                    pass

            finally:
                self.gui.ejecutando_mision = False
                self.gui.root.after(0, lambda: self.btn_modo_interactivo.config(state=tk.NORMAL))
                self.gui.root.after(0, lambda: self._actualizar_botones())

        thread = threading.Thread(target=ejecutar_thread, daemon=True)
        thread.start()

    def _actualizar_posicion(self, x, y, z):
        """Actualiza la visualización de posición"""
        if hasattr(self.gui, '_actualizar_posicion_real'):
            self.gui._actualizar_posicion_real(x, y, z)

    def _limpiar_despues_ejecucion(self):
        """Limpia la planificación después de ejecutar"""
        if self.planner:
            self.planner.limpiar()
        self.label_waypoints_count.config(text="WPs: 0")
        self.btn_eliminar_ultimo.config(state=tk.DISABLED)
        self.btn_limpiar_interactivo.config(state=tk.DISABLED)
        self.btn_previsualizar.config(state=tk.DISABLED)
        self.btn_ejecutar_interactivo.config(state=tk.DISABLED)

        # Limpiar trayecto del visualizador
        if hasattr(self.gui, 'visualizador') and self.gui.visualizador:
            self.gui.visualizador.limpiar_trayecto()

    def _actualizar_botones(self):
        """Actualiza el estado de los botones según el estado actual"""
        tiene_waypoints = self.planner and self.planner.tiene_waypoints()

        # Verificar dron correctamente
        dron_listo = False
        if hasattr(self.gui, 'dron') and self.gui.dron is not None:
            try:
                dron_listo = self.gui.dron.state != "disconnected"
            except:
                dron_listo = False

        # Verificar si no está ejecutando
        # CORRECCIÓN: Si el dron no está volando y el flag está en True, resetearlo
        if hasattr(self.gui, 'ejecutando_mision') and self.gui.ejecutando_mision:
            try:
                if self.gui.dron and self.gui.dron.state not in ["flying", "armed"]:
                    # El dron no está en estado de misión, resetear flag
                    logging.info("[PlanificadorUI] Reseteando flag ejecutando_mision (dron no está en misión)")
                    self.gui.ejecutando_mision = False
            except:
                pass

        no_ejecutando = not (hasattr(self.gui, 'ejecutando_mision') and self.gui.ejecutando_mision)

        self.btn_eliminar_ultimo.config(state=tk.NORMAL if tiene_waypoints else tk.DISABLED)
        self.btn_limpiar_interactivo.config(state=tk.NORMAL if tiene_waypoints else tk.DISABLED)
        self.btn_previsualizar.config(state=tk.NORMAL if tiene_waypoints else tk.DISABLED)
        self.btn_ejecutar_interactivo.config(
            state=tk.NORMAL if (tiene_waypoints and dron_listo and no_ejecutando) else tk.DISABLED
        )

    def _log(self, mensaje):
        """Añade mensaje al log de la GUI principal"""
        if hasattr(self.gui, '_log'):
            self.gui._log(mensaje)
        else:
            logging.info(f"[PlanificadorUI] {mensaje}")


def integrar_planificador_interactivo(gui_instance) -> PlanificadorInteractivoUI:
    """
    Función de integración para añadir el planificador interactivo a la GUI existente.

    Args:
        gui_instance: Instancia de MissionPlannerGUI

    Returns:
        Instancia del PlanificadorInteractivoUI
    """
    return PlanificadorInteractivoUI(gui_instance)


# ============================================================
# INSTRUCCIONES DE INTEGRACIÓN
# ============================================================
"""
Para integrar este módulo en Demo_plan_de_vuelo.py:

1. Añadir al inicio del archivo (después de los otros imports):
   
   from integracion_planificador import integrar_planificador_interactivo

2. En la clase MissionPlannerGUI, al final del método __init__, añadir:

   # Integrar planificador interactivo
   self.planificador_interactivo = integrar_planificador_interactivo(self)

3. Asegurarse de que los módulos necesarios estén en el mismo directorio:
   - waypoint_config_dialog.py
   - mision_interactiva.py
   - dron_camera_extended.py
   - integracion_planificador.py (este archivo)

4. Los videos se guardarán en la carpeta "videos_vuelo" y las fotos en "fotos_vuelo"
"""
