"""
Sistema de Planificación de Vuelo para Crazyflie - CORREGIDO
Soluciona problemas de ejecución de waypoints y cierre de aplicación
"""

import math
import time
import logging
import threading
from typing import List, Dict, Optional, Callable

try:
    from config_mision import ConfigMision

    USAR_CONFIG = True
    print("✓ Configuración personalizada cargada")
    ConfigMision.mostrar_config()
except ImportError:
    USAR_CONFIG = False
    print("⚠ Usando configuración por defecto")


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
    Almacena waypoints y configuración de la misión.
    """

    def __init__(self, takeoff_alt: float = 0.5):
        """
        Inicializa una nueva misión de vuelo.

        Args:
            takeoff_alt: Altura de despegue en metros (por defecto 0.5m)
        """
        self.takeoff_alt = takeoff_alt
        self.waypoints = []
        self.rotations = []
        self.current_position = [0.0, 0.0, 0.0]  # x, y, z inicial

    def add_waypoint(self, x: float, y: float, z: float):
        """
        Añade un waypoint absoluto a la misión.

        Args:
            x: Coordenada X en metros (adelante/atrás)
            y: Coordenada Y en metros (izquierda/derecha)
            z: Coordenada Z en metros (altura)
        """
        waypoint = {
            'x': x,
            'y': y,
            'z': z,
            'type': 'goto'
        }
        self.waypoints.append(waypoint)
        logging.info(f"[Mission] Waypoint añadido: X={x}, Y={y}, Z={z}")

    def add_relative_waypoint(self, dx: float, dy: float, dz: float):
        """
        Añade un waypoint relativo a la posición actual.

        Args:
            dx: Desplazamiento en X (metros)
            dy: Desplazamiento en Y (metros)
            dz: Desplazamiento en Z (metros)
        """
        new_x = self.current_position[0] + dx
        new_y = self.current_position[1] + dy
        new_z = self.current_position[2] + dz

        self.add_waypoint(new_x, new_y, new_z)
        self.current_position = [new_x, new_y, new_z]

    def add_relative_move(self, dx: float, dy: float, dz: float):
        """
        Alias para add_relative_waypoint - mantiene compatibilidad
        """
        self.add_relative_waypoint(dx, dy, dz)

    def add_rotation(self, degrees: float):
        """
        Añade una rotación a la misión.

        Args:
            degrees: Grados a rotar (0-360)
        """
        rotation = {
            'degrees': degrees,
            'type': 'rotation'
        }
        self.rotations.append(rotation)
        logging.info(f"[Mission] Rotación añadida: {degrees}°")

    def get_mission_dict(self) -> Dict:
        """
        Retorna la misión en formato diccionario.

        Returns:
            Diccionario con toda la información de la misión
        """
        return {
            'takeoff_alt': self.takeoff_alt,
            'waypoints': self.waypoints,
            'rotations': self.rotations
        }


def crear_mision_desde_comandos(comandos: List[Dict], posicion_inicial: List[float] = None) -> FlightMission:
    """
    Crea una misión de vuelo a partir de una lista de comandos de voz.

    Args:
        comandos: Lista de diccionarios con comandos
        posicion_inicial: Posición inicial [x, y, z]. Si None, usa [0, 0, altura_despegue]

    Returns:
        Objeto FlightMission con los waypoints calculados
    """
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


def _calcular_desplazamiento(direccion: str, distancia: float) -> tuple:
    """
    Calcula el desplazamiento (dx, dy, dz) según la dirección.

    Args:
        direccion: Dirección del movimiento
        distancia: Distancia en metros

    Returns:
        Tupla (dx, dy, dz) con los desplazamientos
    """
    dx, dy, dz = 0.0, 0.0, 0.0

    # Mapeo corregido de direcciones
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


def crear_mision_patron(patron: str, tamaño: float = 2.0, altura: float = 0.5) -> FlightMission:
    """
    Crea una misión predefinida con patrones geométricos.

    Args:
        patron: Tipo de patrón ('cuadrado', 'triangulo', 'circulo', 'linea')
        tamaño: Tamaño del patrón en metros
        altura: Altura de vuelo en metros

    Returns:
        Objeto FlightMission con el patrón definido
    """
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
                    velocidad: float = 0.3):
    """
    Ejecuta una misión de vuelo en el dron Crazyflie.

    Args:
        dron: Instancia del objeto Dron (Crazyflie)
        mission: Objeto FlightMission o diccionario con la misión
        blocking: Si True, espera a que termine la misión
        callback: Función a ejecutar al terminar (modo no bloqueante)
        params: Parámetros adicionales para el callback
        velocidad: Velocidad de movimiento en m/s

    Returns:
        True si la ejecución fue exitosa, False en caso contrario
    """
    if blocking:
        return _ejecutar_mision(dron, mission, callback, params, velocidad)
    else:
        mission_thread = threading.Thread(
            target=_ejecutar_mision,
            args=[dron, mission, callback, params, velocidad],
            daemon=True  # IMPORTANTE: Thread daemon para que se cierre con la app
        )
        mission_thread.start()
        return True


def _ejecutar_mision(dron, mission: FlightMission,
                     callback: Optional[Callable] = None,
                     params=None,
                     velocidad: float = None):  # ⚡ None para usar config
    """
    Función interna para ejecutar la misión - USA CONFIGURACIÓN.

    Si velocidad=None, usa ConfigMision.get_velocidad()
    """
    if dron.state != "flying":
        logging.error("[Mission] El dron no está volando. Primero despega.")
        return False

    if isinstance(mission, FlightMission):
        mission_dict = mission.get_mission_dict()
    else:
        mission_dict = mission

    # ⚡ Usar configuración si no se especifica velocidad
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

            # ⚡ Usar pausa de configuración
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
            if dron.id is None:
                callback() if params is None else callback(params)
            else:
                callback(dron.id) if params is None else callback(dron.id, params)

        return True

    except Exception as e:
        logging.error(f"[Mission] Error al ejecutar misión: {str(e)}")
        return False


def previsualizar_mision(mission: FlightMission):
    """
    Imprime por consola una previsualización de la misión.

    Args:
        mission: Misión a previsualizar
    """
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


def calcular_distancia_total(mission: FlightMission) -> float:
    """
    Calcula la distancia total que recorrerá el dron.

    Args:
        mission: Misión a analizar

    Returns:
        Distancia total en metros
    """
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


def estimar_tiempo_vuelo(mission: FlightMission, velocidad: float = None) -> float:
    """
    Estima el tiempo total de vuelo de la misión.
    Si velocidad=None, usa ConfigMision.get_velocidad()
    """
    if velocidad is None:
        velocidad = ConfigMision.get_velocidad()

    distancia = calcular_distancia_total(mission)
    tiempo_movimiento = distancia / velocidad

    # Usar pausas de configuración
    tiempo_pausas = len(mission.waypoints) * ConfigMision.get_pausa_waypoint()
    tiempo_rotaciones = len(mission.rotations) * ConfigMision.get_pausa_rotacion()

    tiempo_total = tiempo_movimiento + tiempo_pausas + tiempo_rotaciones

    return tiempo_total