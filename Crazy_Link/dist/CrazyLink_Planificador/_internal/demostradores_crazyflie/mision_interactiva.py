"""
Módulo de Misión Interactiva para Crazyflie
Extiende el sistema de misiones para soportar waypoints configurados interactivamente
con acciones de foto, video corto y video de ruta.
"""

import time
import logging
import math
from typing import List, Dict, Optional, Callable, Tuple

try:
    from config_mision import ConfigMision
    USAR_CONFIG = True
except ImportError:
    USAR_CONFIG = False
    class ConfigMision:
        @staticmethod
        def get_velocidad(): return 0.3
        @staticmethod
        def get_pausa_waypoint(): return 0.3
        @staticmethod
        def get_pausa_rotacion(): return 0.5


class InteractiveMission:
    """
    Clase para gestionar misiones de vuelo creadas interactivamente.
    Soporta waypoints con configuración completa incluyendo:
    - Altura variable por waypoint
    - Rotaciones
    - Fotos
    - Videos cortos
    - Videos de ruta
    """

    def __init__(self, takeoff_alt: float = 0.5):
        """
        Inicializa la misión interactiva.

        Args:
            takeoff_alt: Altura de despegue por defecto
        """
        self.takeoff_alt = takeoff_alt
        self.waypoints_config = []  # Lista de configuraciones completas
        self.current_position = [0.0, 0.0, takeoff_alt]

    def add_configured_waypoint(self, config: Dict):
        """
        Añade un waypoint con su configuración completa.

        Args:
            config: Diccionario con la configuración del waypoint
                   Debe incluir: x, y, z, rotacion, foto, video_corto, video_ruta
        """
        # Asegurar que tiene todos los campos necesarios
        wp_config = {
            'x': config.get('x', 0.0),
            'y': config.get('y', 0.0),
            'z': config.get('z', self.takeoff_alt),
            'rotacion': config.get('rotacion', 0.0),
            'foto': config.get('foto', False),
            'video_corto': config.get('video_corto', False),
            'video_ruta': config.get('video_ruta', False),
            'waypoint_number': config.get('waypoint_number', len(self.waypoints_config) + 1)
        }

        self.waypoints_config.append(wp_config)
        self.current_position = [wp_config['x'], wp_config['y'], wp_config['z']]

        logging.info(f"[InteractiveMission] Waypoint {wp_config['waypoint_number']} añadido: "
                    f"({wp_config['x']:.2f}, {wp_config['y']:.2f}, {wp_config['z']:.2f})")

    def add_waypoints_from_planner(self, waypoints_list: List[Dict]):
        """
        Añade múltiples waypoints desde el planificador interactivo.

        Args:
            waypoints_list: Lista de configuraciones de waypoints
        """
        for config in waypoints_list:
            self.add_configured_waypoint(config)

        logging.info(f"[InteractiveMission] {len(waypoints_list)} waypoints añadidos desde planificador")

    def get_simple_waypoints(self) -> List[Dict]:
        """
        Retorna solo las coordenadas de los waypoints (para compatibilidad).

        Returns:
            Lista de diccionarios con x, y, z
        """
        return [{'x': wp['x'], 'y': wp['y'], 'z': wp['z']} for wp in self.waypoints_config]

    def get_mission_summary(self) -> Dict:
        """
        Obtiene un resumen de la misión.

        Returns:
            Diccionario con estadísticas de la misión
        """
        num_fotos = sum(1 for wp in self.waypoints_config if wp['foto'])
        num_videos_cortos = sum(1 for wp in self.waypoints_config if wp['video_corto'])
        tiene_video_ruta = any(wp['video_ruta'] for wp in self.waypoints_config)
        num_rotaciones = sum(1 for wp in self.waypoints_config if wp['rotacion'] != 0)

        return {
            'num_waypoints': len(self.waypoints_config),
            'num_fotos': num_fotos,
            'num_videos_cortos': num_videos_cortos,
            'tiene_video_ruta': tiene_video_ruta,
            'num_rotaciones': num_rotaciones,
            'distancia_total': self._calcular_distancia_total(),
            'tiempo_estimado': self._estimar_tiempo()
        }

    def _calcular_distancia_total(self) -> float:
        """Calcula la distancia total de la misión"""
        if len(self.waypoints_config) == 0:
            return 0.0

        distancia = 0.0
        pos_anterior = [0.0, 0.0, self.takeoff_alt]

        for wp in self.waypoints_config:
            dx = wp['x'] - pos_anterior[0]
            dy = wp['y'] - pos_anterior[1]
            dz = wp['z'] - pos_anterior[2]
            distancia += math.sqrt(dx**2 + dy**2 + dz**2)
            pos_anterior = [wp['x'], wp['y'], wp['z']]

        return distancia

    def _estimar_tiempo(self) -> float:
        """Estima el tiempo total de la misión"""
        velocidad = ConfigMision.get_velocidad()
        distancia = self._calcular_distancia_total()
        tiempo_movimiento = distancia / velocidad if velocidad > 0 else 0

        # Pausas en waypoints
        tiempo_pausas = len(self.waypoints_config) * ConfigMision.get_pausa_waypoint()

        # Tiempo para fotos (0.5s cada una)
        num_fotos = sum(1 for wp in self.waypoints_config if wp['foto'])
        tiempo_fotos = num_fotos * 0.5

        # Tiempo para videos cortos (10s cada uno)
        num_videos = sum(1 for wp in self.waypoints_config if wp['video_corto'])
        tiempo_videos = num_videos * 10

        # Tiempo para rotaciones
        num_rotaciones = sum(1 for wp in self.waypoints_config if wp['rotacion'] != 0)
        tiempo_rotaciones = num_rotaciones * ConfigMision.get_pausa_rotacion()

        return tiempo_movimiento + tiempo_pausas + tiempo_fotos + tiempo_videos + tiempo_rotaciones

    def clear(self):
        """Limpia la misión"""
        self.waypoints_config = []
        self.current_position = [0.0, 0.0, self.takeoff_alt]
        logging.info("[InteractiveMission] Misión limpiada")


def ejecutar_mision_interactiva(
        dron,
        mission: InteractiveMission,
        camera=None,
        velocidad: float = None,
        callback_posicion: Optional[Callable] = None,
        callback_progreso: Optional[Callable] = None,
        geocage_validator: Optional[Callable] = None,
        visualizador=None,
        pathfinder=None  # ✅ NUEVO: Pathfinder para evasión de obstáculos
) -> bool:
    """
    Ejecuta una misión interactiva con soporte para todas las acciones.

    Args:
        dron: Instancia del dron
        mission: Misión interactiva a ejecutar
        camera: Instancia de DroneCameraExtended para fotos/videos
        velocidad: Velocidad de vuelo (m/s)
        callback_posicion: Callback para actualizar visualización
        callback_progreso: Callback para reportar progreso
        geocage_validator: Función para validar geocage
        visualizador: Instancia del visualizador para actualizar heading
        pathfinder: PathFinder para evasión de obstáculos (opcional) ✅ NUEVO

    Returns:
        True si la misión se completó correctamente
    """
    if not dron or dron.state == "disconnected":
        logging.error("[InteractiveMission] Dron no conectado")
        return False

    waypoints = mission.waypoints_config

    if len(waypoints) == 0:
        logging.warning("[InteractiveMission] Misión sin waypoints")
        return False

    # Configurar velocidad
    if velocidad is None:
        velocidad = ConfigMision.get_velocidad()

    dron.setMoveSpeed(velocidad)
    logging.info(f"[InteractiveMission] Velocidad: {velocidad} m/s")

    # ✅ DEBUG: Log del estado del pathfinder
    if pathfinder is not None:
        msg = f"[InteractiveMission] 🗺️ Pathfinder ACTIVO (Obstáculos: {len(pathfinder.obstaculos)})"
        print(msg)
        logging.info(msg)
    else:
        msg = f"[InteractiveMission] ⚪ Pathfinder NO activo (pathfinder=None)"
        print(msg)
        logging.info(msg)

    # Variables de estado
    video_ruta_iniciado = False
    video_ruta_path = None

    try:
        total_waypoints = len(waypoints)
        logging.info(f"[InteractiveMission] Iniciando misión con {total_waypoints} waypoints")

        for i, wp_config in enumerate(waypoints):
            x = wp_config['x']
            y = wp_config['y']
            z = wp_config['z']

            logging.info(f"[InteractiveMission] Waypoint {i + 1}/{total_waypoints}: "
                        f"({x:.2f}, {y:.2f}, {z:.2f})")

            # ✅ FIX: Comentar geocage_validator - El pathfinder YA valida geocage
            # Esta validación prematura impedía que el pathfinder buscara rutas alternativas
            # if geocage_validator and not geocage_validator(x, y):
            #     logging.warning(f"[InteractiveMission] Waypoint {i + 1} fuera del geocage")
            #     return False

            # ✅ NUEVO: Usar pathfinder para evitar obstáculos
            if pathfinder is not None:
                # Obtener posición actual del dron
                pos_actual = (dron.position[0], dron.position[1], dron.position[2])
                pos_objetivo = (x, y, z)

                msg = f"[InteractiveMission] 🔍 Buscando camino: {pos_actual} -> {pos_objetivo}"
                print(msg)
                logging.info(msg)

                # Calcular camino evitando obstáculos
                camino = pathfinder.encontrar_camino(pos_actual, pos_objetivo)

                if camino is None:
                    print(f"[InteractiveMission] ❌ No se encontró camino al waypoint {i+1}")
                    print(f"[InteractiveMission] ⚠️ Waypoint fuera del geocage o inaccesible")
                    print(f"[InteractiveMission] 🏠 Ejecutando RTL (Return To Launch)")
                    logging.error(f"[InteractiveMission] ❌ No se encontró camino al waypoint {i+1}")
                    logging.warning(f"[InteractiveMission] ⚠️ Waypoint fuera del geocage o inaccesible")
                    logging.info(f"[InteractiveMission] 🏠 Ejecutando RTL (Return To Launch)")
                    # Detener video si está activo
                    if video_ruta_iniciado and camera:
                        camera.detener_video()
                    # Ejecutar RTL
                    dron.RTL()
                    return False

                # Si el camino tiene más de 2 puntos, significa que hay obstáculos
                if len(camino) > 2:
                    msg = f"[InteractiveMission] 🔀 Ruta alternativa calculada con {len(camino)} waypoints intermedios"
                    print(msg)
                    logging.info(msg)
                    # Seguir los waypoints intermedios
                    for j, (wx, wy, wz) in enumerate(camino[1:], 1):  # Saltar el punto de inicio
                        msg = f"[InteractiveMission]   └─ WP intermedio {j}/{len(camino)-1}: ({wx:.2f}, {wy:.2f}, {wz:.2f})"
                        print(msg)
                        logging.info(msg)
                        dron.goto(wx, wy, wz, blocking=True)
                        if callback_posicion:
                            try:
                                callback_posicion(wx, wy, wz)
                            except Exception as e:
                                logging.warning(f"[InteractiveMission] Error en callback_posicion: {e}")
                        time.sleep(0.3)  # Pausa breve entre waypoints intermedios
                else:
                    # Ruta directa sin obstáculos
                    msg = f"[InteractiveMission] ✅ Ruta directa sin obstáculos"
                    print(msg)
                    logging.info(msg)
                    dron.goto(x, y, z, blocking=True)
            else:
                # Sin pathfinder, ir directo
                msg = f"[InteractiveMission] ⚠️ Pathfinder NO activo, navegando sin evitar obstáculos"
                print(msg)
                logging.warning(msg)
                dron.goto(x, y, z, blocking=True)

            # Actualizar visualización
            if callback_posicion:
                try:
                    callback_posicion(x, y, z)
                except Exception as e:
                    logging.warning(f"[InteractiveMission] Error en callback_posicion: {e}")

            # Reportar progreso
            if callback_progreso:
                progreso = (i + 1) / total_waypoints * 100
                callback_progreso(i + 1, total_waypoints, progreso)

            # Pausa en waypoint
            time.sleep(ConfigMision.get_pausa_waypoint())

            # === EJECUTAR ACCIONES DEL WAYPOINT ===

            # Rotación
            if wp_config['rotacion'] != 0:
                logging.info(f"[InteractiveMission] Rotando {wp_config['rotacion']}°")
                dron.changeHeading(wp_config['rotacion'])

                # Actualizar visualizador
                if visualizador and hasattr(visualizador, 'actualizar_heading_planificado'):
                    visualizador.actualizar_heading_planificado(wp_config['rotacion'])

                time.sleep(ConfigMision.get_pausa_rotacion())

            # Video de ruta (iniciar)
            if wp_config['video_ruta'] and camera and not video_ruta_iniciado:
                logging.info(f"[InteractiveMission] 🎥 Iniciando video de ruta")
                video_ruta_path = camera.iniciar_video_ruta(
                    posicion=(x, y, z),
                    metadata={'waypoint_inicio': i + 1}
                )
                video_ruta_iniciado = True
                time.sleep(0.3)

            # Video corto
            if wp_config['video_corto'] and camera:
                logging.info(f"[InteractiveMission] 🎬 Grabando video corto (10s)")
                camera.iniciar_video_corto(
                    duracion=10,
                    posicion=(x, y, z),
                    metadata={'waypoint': i + 1}
                )
                # Esperar a que termine el video corto
                time.sleep(11)

            # Foto
            if wp_config['foto'] and camera:
                logging.info(f"[InteractiveMission] 📷 Capturando foto")
                camera.capturar_foto(
                    posicion=(x, y, z),
                    metadata={'waypoint': i + 1, 'velocidad': f'{velocidad} m/s'}
                )
                time.sleep(0.5)

            # Verificar estado del dron
            if dron.state != "flying":
                logging.error("[InteractiveMission] Dron dejó de volar")
                # Detener video de ruta si está activo
                if video_ruta_iniciado and camera:
                    camera.detener_video()
                return False

        # Misión completada - detener video de ruta si está activo
        if video_ruta_iniciado and camera:
            logging.info("[InteractiveMission] 🎥 Finalizando video de ruta")
            camera.detener_video()

        logging.info("[InteractiveMission] ¡Misión completada exitosamente!")
        return True

    except Exception as e:
        logging.error(f"[InteractiveMission] Error durante ejecución: {e}")

        # Asegurar que el video de ruta se detenga
        if video_ruta_iniciado and camera:
            try:
                camera.detener_video()
            except:
                pass

        return False


def previsualizar_mision_interactiva(mission: InteractiveMission):
    """
    Imprime una previsualización de la misión interactiva.

    Args:
        mission: Misión a previsualizar
    """
    summary = mission.get_mission_summary()

    print("\n" + "=" * 70)
    print("PREVISUALIZACIÓN DE MISIÓN INTERACTIVA")
    print("=" * 70)

    print(f"\n📊 RESUMEN:")
    print(f"   • Waypoints: {summary['num_waypoints']}")
    print(f"   • Fotos programadas: {summary['num_fotos']}")
    print(f"   • Videos cortos: {summary['num_videos_cortos']}")
    print(f"   • Video de ruta: {'Sí' if summary['tiene_video_ruta'] else 'No'}")
    print(f"   • Rotaciones: {summary['num_rotaciones']}")
    print(f"   • Distancia total: {summary['distancia_total']:.2f} m")
    print(f"   • Tiempo estimado: {summary['tiempo_estimado']:.1f} s")

    print(f"\n📍 WAYPOINTS:")
    print("-" * 70)

    for i, wp in enumerate(mission.waypoints_config):
        # Construir iconos de acciones
        iconos = []
        if wp['foto']:
            iconos.append("📷")
        if wp['video_corto']:
            iconos.append("🎬")
        if wp['video_ruta']:
            iconos.append("🎥")
        if wp['rotacion'] != 0:
            iconos.append(f"↻{wp['rotacion']:+.0f}°")

        iconos_str = " ".join(iconos) if iconos else "-"

        print(f"  {i + 1:2d}. X={wp['x']:6.2f}m  Y={wp['y']:6.2f}m  Z={wp['z']:4.2f}m  │ {iconos_str}")

    print("=" * 70 + "\n")


def convertir_a_mision_simple(mission: InteractiveMission):
    """
    Convierte una misión interactiva a formato simple (FlightMission).
    Útil para compatibilidad con el sistema existente.

    Args:
        mission: Misión interactiva

    Returns:
        Diccionario compatible con el sistema de misiones existente
    """
    from dron_plan_vuelo_extended import FlightMission

    simple_mission = FlightMission(takeoff_alt=mission.takeoff_alt)

    for wp in mission.waypoints_config:
        simple_mission.add_waypoint(wp['x'], wp['y'], wp['z'])

        if wp['rotacion'] != 0:
            simple_mission.add_rotation(wp['rotacion'])

        if wp['foto']:
            simple_mission.add_photo_command({'waypoint': wp['waypoint_number']})

    return simple_mission


if __name__ == "__main__":
    # Prueba del módulo
    logging.basicConfig(level=logging.INFO)

    print("=== PRUEBA DEL MÓDULO DE MISIÓN INTERACTIVA ===\n")

    # Crear misión de prueba
    mission = InteractiveMission()

    # Simular waypoints del planificador interactivo
    waypoints_test = [
        {'x': 1.0, 'y': 0.0, 'z': 0.5, 'rotacion': 0, 'foto': True, 'video_corto': False, 'video_ruta': False},
        {'x': 1.0, 'y': 1.0, 'z': 0.8, 'rotacion': 90, 'foto': False, 'video_corto': False, 'video_ruta': True},
        {'x': 0.0, 'y': 1.0, 'z': 0.5, 'rotacion': 0, 'foto': True, 'video_corto': True, 'video_ruta': False},
        {'x': 0.0, 'y': 0.0, 'z': 0.5, 'rotacion': -90, 'foto': True, 'video_corto': False, 'video_ruta': False},
    ]

    mission.add_waypoints_from_planner(waypoints_test)

    # Previsualizar
    previsualizar_mision_interactiva(mission)

    print("\n✓ Prueba completada")
