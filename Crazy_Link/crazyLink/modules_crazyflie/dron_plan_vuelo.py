# Módulo de Planificación de Vuelo para Crazyflie


import math
import time
import logging
import threading
from typing import List, Dict, Optional, Callable, Tuple

try:
    from config_mision import ConfigMision

    USAR_CONFIG = True
    logging.info("[PlanVuelo] Configuración personalizada cargada")
except ImportError:
    USAR_CONFIG = False
    logging.warning("[PlanVuelo] Usando configuración por defecto")


    # Valores por defecto si no existe config_mision.py
    class ConfigMision:
        @staticmethod
        def get_velocidad(): return 0.3

        @staticmethod
        def get_pausa_waypoint(): return 0.3

        @staticmethod
        def get_pausa_rotacion(): return 0.5

        @staticmethod
        def get_tolerancia(): return 0.2

        @staticmethod
        def get_timeout_waypoint(): return 3.0

        @staticmethod
        def get_intervalo_check(): return 0.05

class FlightMission:
    """
    Clase para gestionar misiones de vuelo del Crazyflie.
    Almacena waypoints, rotaciones y configuración de la misión.
    """

    def __init__(self, takeoff_alt: float = 0.5):
        self.takeoff_alt = takeoff_alt
        self.waypoints = []
        self.rotations = []
        self.current_position = [0.0, 0.0, 0.0]  # x, y, z inicial

    def add_waypoint(self, x: float, y: float, z: float):
        waypoint = {
            'x': x,
            'y': y,
            'z': z,
            'type': 'goto'
        }
        self.waypoints.append(waypoint)
        logging.info(f"[Mission] Waypoint añadido: X={x}, Y={y}, Z={z}")

    def add_relative_waypoint(self, dx: float, dy: float, dz: float):
        new_x = self.current_position[0] + dx
        new_y = self.current_position[1] + dy
        new_z = self.current_position[2] + dz

        self.add_waypoint(new_x, new_y, new_z)
        self.current_position = [new_x, new_y, new_z]

    def add_rotation(self, degrees: float):
        rotation = {
            'degrees': degrees,
            'type': 'rotation'
        }
        self.rotations.append(rotation)
        logging.info(f"[Mission] Rotación añadida: {degrees}°")

    def get_mission_dict(self) -> Dict:
        return {
            'takeoff_alt': self.takeoff_alt,
            'waypoints': self.waypoints,
            'rotations': self.rotations
        }


def crear_mision_desde_comandos(comandos: List[Dict], posicion_inicial: List[float] = None) -> FlightMission:

    mission = FlightMission(takeoff_alt=0.5)

    if posicion_inicial:
        mission.current_position = posicion_inicial.copy()
    else:
        mission.current_position = [0.0, 0.0, mission.takeoff_alt]

    logging.info(f"[Mission] Creando misión desde posición inicial: {mission.current_position}")

    for cmd in comandos:
        action = cmd.get('action', '').lower()

        if action == 'move':
            direction = cmd.get('direction', '').lower()
            distance = float(cmd.get('distance', 1.0))
            dx, dy, dz = _calcular_desplazamiento(direction, distance)
            mission.add_relative_waypoint(dx, dy, dz)

        elif action == 'rotate' or action == 'rotar':
            degrees = float(cmd.get('degrees', 0))
            mission.add_rotation(degrees)

        elif action == 'goto':
            x = float(cmd.get('x', 0))
            y = float(cmd.get('y', 0))
            z = float(cmd.get('z', mission.takeoff_alt))
            mission.add_waypoint(x, y, z)
            mission.current_position = [x, y, z]

    logging.info(f"[Mission] Misión creada con {len(mission.waypoints)} waypoints")
    return mission


def _calcular_desplazamiento(direccion: str, distancia: float) -> Tuple[float, float, float]:

    dx, dy, dz = 0.0, 0.0, 0.0

    # Mapeo de direcciones
    if direccion in ['forward', 'adelante', 'recto']:
        dx = distancia
    elif direccion in ['back', 'atrás', 'atras']:
        dx = -distancia
    elif direccion in ['left', 'izquierda']:
        dy = -distancia
    elif direccion in ['right', 'derecha']:
        dy = distancia
    elif direccion in ['up', 'arriba']:
        dz = distancia
    elif direccion in ['down', 'abajo']:
        dz = -distancia

    return dx, dy, dz


def crear_mision_patron(patron: str, tamaño: float = 2.0, altura: float = 0.5) -> FlightMission:#Crea una misión predefinida con patrones geométricos.
    mission = FlightMission(takeoff_alt=altura)
    mission.current_position = [0.0, 0.0, altura]

    if patron == 'cuadrado':
        mission.add_relative_waypoint(tamaño, 0, 0)
        mission.add_relative_waypoint(0, tamaño, 0)
        mission.add_relative_waypoint(-tamaño, 0, 0)
        mission.add_relative_waypoint(0, -tamaño, 0)
        logging.info(f"[Mission] Patrón cuadrado de {tamaño}m creado")

    elif patron == 'triangulo':
        mission.add_relative_waypoint(tamaño, 0, 0)
        mission.add_relative_waypoint(-tamaño / 2, tamaño * 0.866, 0)
        mission.add_relative_waypoint(-tamaño / 2, -tamaño * 0.866, 0)
        logging.info(f"[Mission] Patrón triángulo de {tamaño}m creado")

    elif patron == 'circulo':
        num_puntos = 8
        angulo_incremento = 360 / num_puntos
        radio = tamaño / 2

        for i in range(num_puntos + 1):
            angulo = math.radians(i * angulo_incremento)
            x = radio * math.cos(angulo)
            y = radio * math.sin(angulo)
            mission.add_waypoint(x, y, altura)
        logging.info(f"[Mission] Patrón círculo de radio {radio}m creado")

    elif patron == 'linea':
        mission.add_relative_waypoint(tamaño, 0, 0)
        mission.add_relative_waypoint(-tamaño, 0, 0)
        logging.info(f"[Mission] Patrón línea de {tamaño}m creado")

    return mission


def ejecutar_mision(dron, mission: FlightMission,
                    blocking: bool = True,
                    callback: Optional[Callable] = None,
                    params=None,
                    velocidad: float = None):
    if blocking:
        return _ejecutar_mision(dron, mission, callback, params, velocidad)
    else:
        mission_thread = threading.Thread(
            target=_ejecutar_mision,
            args=[dron, mission, callback, params, velocidad],
            daemon=True  # Thread daemon para que se cierre con la app
        )
        mission_thread.start()
        return True


def _ejecutar_mision(dron, mission: FlightMission,
                     callback: Optional[Callable] = None,
                     params=None,
                     velocidad: float = None):
    """
    Función interna para ejecutar la misión.
    Si velocidad=None, usa ConfigMision.get_velocidad()
    """
    if dron.state != "flying":
        logging.error("[Mission] El dron no está volando. Primero despega.")
        return False

    if isinstance(mission, FlightMission):
        mission_dict = mission.get_mission_dict()
    else:
        mission_dict = mission

    # Usar configuración si no se especifica velocidad
    if velocidad is None:
        velocidad = ConfigMision.get_velocidad()

    dron.setMoveSpeed(velocidad)
    logging.info(f"[Mission] Velocidad: {velocidad} m/s")

    try:
        logging.info(f"[Mission] Iniciando ejecución de misión con {len(mission_dict['waypoints'])} waypoints")

        for i, waypoint in enumerate(mission_dict['waypoints']):
            x = waypoint['x']
            y = waypoint['y']
            z = waypoint['z']

            logging.info(
                f"[Mission] Waypoint {i + 1}/{len(mission_dict['waypoints'])}: X={x:.2f}, Y={y:.2f}, Z={z:.2f}")

            dron.goto(x, y, z, blocking=True)

            # Usar pausa de configuración
            pausa = ConfigMision.get_pausa_waypoint()
            time.sleep(pausa)

            if dron.state != "flying":
                logging.error("[Mission] Dron dejó de volar, abortando misión")
                return False

        # Rotaciones
        if 'rotations' in mission_dict and mission_dict['rotations']:
            pausa_rot = ConfigMision.get_pausa_rotacion()
            for rotation in mission_dict['rotations']:
                degrees = rotation['degrees']
                logging.info(f"[Mission] Rotando {degrees}°")
                dron.changeHeading(degrees)
                time.sleep(pausa_rot)

        logging.info("[Mission] ¡Misión completada exitosamente!")

        if callback is not None:
            if hasattr(dron, 'id') and dron.id is not None:
                callback(dron.id) if params is None else callback(dron.id, params)
            else:
                callback() if params is None else callback(params)

        return True

    except Exception as e:
        logging.error(f"[Mission] Error al ejecutar misión: {str(e)}")
        return False


def previsualizar_mision(mission: FlightMission):#Imprime por consola una previsualización de la misión.

    print("\n" + "=" * 60)
    print("PREVISUALIZACIÓN DE MISIÓN")
    print("=" * 60)
    print(f"Altura de despegue: {mission.takeoff_alt}m")
    print(f"Total de waypoints: {len(mission.waypoints)}")
    print(f"Total de rotaciones: {len(mission.rotations)}")
    print("\nWAYPOINTS:")
    print("-" * 60)

    for i, wp in enumerate(mission.waypoints):
        print(f"  {i + 1}. X={wp['x']:6.2f}m, Y={wp['y']:6.2f}m, Z={wp['z']:6.2f}m")

    if mission.rotations:
        print("\nROTACIONES:")
        print("-" * 60)
        for i, rot in enumerate(mission.rotations):
            print(f"  {i + 1}. Rotar {rot['degrees']}°")

    print("=" * 60 + "\n")


def calcular_distancia_total(mission: FlightMission) -> float:#Calcula la distancia total que recorrerá el dron.

    if len(mission.waypoints) < 2:
        return 0.0

    distancia_total = 0.0
    pos_anterior = [0.0, 0.0, mission.takeoff_alt]

    for wp in mission.waypoints:
        dx = wp['x'] - pos_anterior[0]
        dy = wp['y'] - pos_anterior[1]
        dz = wp['z'] - pos_anterior[2]

        distancia = math.sqrt(dx ** 2 + dy ** 2 + dz ** 2)
        distancia_total += distancia

        pos_anterior = [wp['x'], wp['y'], wp['z']]

    return distancia_total


def estimar_tiempo_vuelo(mission: FlightMission, velocidad: float = None) -> float:#Estima el tiempo total de vuelo de la misión.

    if velocidad is None:
        velocidad = ConfigMision.get_velocidad()

    distancia = calcular_distancia_total(mission)
    tiempo_movimiento = distancia / velocidad

    # Usar pausas de configuración
    tiempo_pausas = len(mission.waypoints) * ConfigMision.get_pausa_waypoint()
    tiempo_rotaciones = len(mission.rotations) * ConfigMision.get_pausa_rotacion()

    tiempo_total = tiempo_movimiento + tiempo_pausas + tiempo_rotaciones

    return tiempo_total

def crear_mision_simple(waypoints: List[Tuple[float, float, float]], altura_despegue: float = 0.5) -> FlightMission: #Crea una misión simple desde una lista de waypoints.

    mission = FlightMission(takeoff_alt=altura_despegue)
    for x, y, z in waypoints:
        mission.add_waypoint(x, y, z)
    return mission


def obtener_informacion_mision(mission: FlightMission) -> Dict: #Obtiene información completa de una misión.

    return {
        'num_waypoints': len(mission.waypoints),
        'num_rotaciones': len(mission.rotations),
        'distancia_total': calcular_distancia_total(mission),
        'tiempo_estimado': estimar_tiempo_vuelo(mission),
        'altura_despegue': mission.takeoff_alt,
        'waypoints': mission.waypoints.copy(),
        'rotations': mission.rotations.copy()
    }
