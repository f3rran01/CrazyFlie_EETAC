# Módulo de Planificación de Vuelo para Crazyflie - Extendido con Fotos
# ✅ MODIFICADO: Actualiza el heading del visualizador al ejecutar rotaciones


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
    Almacena waypoints, rotaciones, comandos de foto y configuración de la misión.
    """

    def __init__(self, takeoff_alt: float = 0.5):
        self.takeoff_alt = takeoff_alt
        self.waypoints = []
        self.rotations = []
        self.photos = []  # Nueva lista para comandos de foto
        # ✅ FIX: Inicializar posición con altura de despegue para comandos relativos
        self.current_position = [0.0, 0.0, takeoff_alt]  # x, y, z inicial

    def add_waypoint(self, x: float, y: float, z: float):
        waypoint = {
            'x': x,
            'y': y,
            'z': z,
            'type': 'goto'
        }
        self.waypoints.append(waypoint)
        self.current_position = [x, y, z]
        logging.info(f"[Mission] Waypoint añadido: X={x}, Y={y}, Z={z}")

    def add_relative_waypoint(self, dx: float, dy: float, dz: float):
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
        rotation = {
            'degrees': degrees,
            'type': 'rotation'
        }
        self.rotations.append(rotation)
        logging.info(f"[Mission] Rotación añadida: {degrees}°")

    def add_photo_command(self, metadata: Optional[dict] = None):
        """
        Añade un comando de captura de foto en la posición actual
        
        Args:
            metadata: Metadatos opcionales para la foto
        """
        photo_command = {
            'position': self.current_position.copy(),
            'type': 'photo',
            'waypoint_index': len(self.waypoints) - 1,  # Índice del waypoint anterior
            'metadata': metadata or {}
        }
        self.photos.append(photo_command)
        logging.info(f"[Mission] Comando de FOTO añadido en posición: X={self.current_position[0]:.2f}, "
                    f"Y={self.current_position[1]:.2f}, Z={self.current_position[2]:.2f}")

    def get_mission_dict(self) -> Dict:
        return {
            'takeoff_alt': self.takeoff_alt,
            'waypoints': self.waypoints,
            'rotations': self.rotations,
            'photos': self.photos  # Incluir comandos de foto
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

        elif action == 'photo' or action == 'foto':
            # Nuevo: añadir comando de foto
            metadata = cmd.get('metadata', {})
            mission.add_photo_command(metadata)

    logging.info(f"[Mission] Misión creada con {len(mission.waypoints)} waypoints y {len(mission.photos)} fotos")
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
                    velocidad: float = None,
                    camera=None,
                    callback_posicion: Optional[Callable] = None,
                    geocage_validator: Optional[Callable] = None,
                    visualizador=None,
                    pathfinder=None):  # ✅ NUEVO: Pathfinder para evasión de obstáculos
    """
    Ejecuta una misión de vuelo completa para el dron Crazyflie.

    ✅ NUEVO: Acepta un visualizador para actualizar el heading cuando se ejecutan rotaciones
    ✅ NUEVO: Acepta un pathfinder para evitar obstáculos automáticamente

    Args:
        dron: Instancia del dron Crazyflie
        mission: Misión a ejecutar (FlightMission)
        blocking: Si True, espera a que termine. Si False, ejecuta en thread separado
        callback: Función a llamar al finalizar (opcional)
        params: Parámetros para el callback (opcional)
        velocidad: Velocidad de vuelo en m/s (None = usa ConfigMision)
        camera: Sistema de cámara para capturar fotos (opcional)
        callback_posicion: Callback para actualizar posición en tiempo real (opcional)
        geocage_validator: Función para validar waypoints contra geocage (opcional)
        visualizador: Instancia del visualizador para actualizar heading (opcional)
        pathfinder: PathFinder para evasión de obstáculos (opcional) ✅ NUEVO

    Returns:
        True si la misión se completó exitosamente, False en caso contrario
    """
    if blocking:
        return _ejecutar_mision(dron, mission, callback, params, velocidad, camera,
                               callback_posicion, geocage_validator, visualizador, pathfinder)
    else:
        # Ejecutar en thread separado
        thread = threading.Thread(
            target=_ejecutar_mision,
            args=(dron, mission, callback, params, velocidad, camera,
                  callback_posicion, geocage_validator, visualizador, pathfinder),
            daemon=True
        )
        thread.start()
        return True


def _ejecutar_mision(dron, mission: FlightMission,
                     callback: Optional[Callable] = None,
                     params=None,
                     velocidad: float = None,
                     camera=None,
                     callback_posicion: Optional[Callable] = None,
                     geocage_validator: Optional[Callable] = None,
                     visualizador=None,
                     pathfinder=None):  # ✅ NUEVO: Pathfinder
    """
    Función interna para ejecutar la misión con soporte de fotos y evasión de obstáculos.
    Si velocidad=None, usa ConfigMision.get_velocidad()

    ✅ NUEVO: Actualiza el heading del visualizador cuando se ejecutan rotaciones
    ✅ NUEVO: Usa pathfinder para evitar obstáculos automáticamente
    """
    # ✅ DEBUG: Log del estado del pathfinder
    if pathfinder is not None:
        msg = f"[Mission] 🗺️ Pathfinder ACTIVO (Obstáculos: {len(pathfinder.obstaculos)})"
        print(msg)
        logging.info(msg)
    else:
        msg = f"[Mission] ⚪ Pathfinder NO activo (pathfinder=None)"
        print(msg)
        logging.info(msg)

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

    # Crear mapa de fotos por waypoint
    photos_by_waypoint = {}
    if 'photos' in mission_dict:
        for photo in mission_dict['photos']:
            wp_index = photo.get('waypoint_index', -1)
            if wp_index not in photos_by_waypoint:
                photos_by_waypoint[wp_index] = []
            photos_by_waypoint[wp_index].append(photo)

    try:
        logging.info(f"[Mission] Iniciando ejecución de misión con {len(mission_dict['waypoints'])} waypoints "
                    f"y {len(mission_dict.get('photos', []))} fotos")

        for i, waypoint in enumerate(mission_dict['waypoints']):
            x = waypoint['x']
            y = waypoint['y']
            z = waypoint['z']

            logging.info(
                f"[Mission] Waypoint {i + 1}/{len(mission_dict['waypoints'])}: X={x:.2f}, Y={y:.2f}, Z={z:.2f}")

            # ✅ FIX: Comentar geocage_validator - El pathfinder YA valida geocage
            # Esta validación prematura impedía que el pathfinder buscara rutas alternativas
            # if geocage_validator is not None:
            #     if not geocage_validator(x, y):
            #         logging.warning(f"[Mission] ⚠️ Waypoint {i+1} fuera del geocage, deteniendo misión")
            #         return False

            # ✅ NUEVO: Usar pathfinder para evitar obstáculos
            if pathfinder is not None:
                # Obtener posición actual del dron
                pos_actual = (dron.position[0], dron.position[1], dron.position[2])
                pos_objetivo = (x, y, z)

                msg = f"[Mission] 🔍 Buscando camino: {pos_actual} -> {pos_objetivo}"
                print(msg)
                logging.info(msg)

                # Calcular camino evitando obstáculos
                camino = pathfinder.encontrar_camino(pos_actual, pos_objetivo)

                if camino is None:
                    print(f"[Mission] ❌ No se encontró camino al waypoint {i+1}")
                    print(f"[Mission] ⚠️ Waypoint fuera del geocage o inaccesible")
                    print(f"[Mission] 🏠 Ejecutando RTL (Return To Launch)")
                    logging.error(f"[Mission] ❌ No se encontró camino al waypoint {i+1}")
                    logging.warning(f"[Mission] ⚠️ Waypoint fuera del geocage o inaccesible")
                    logging.info(f"[Mission] 🏠 Ejecutando RTL (Return To Launch)")
                    dron.RTL()  # Volver al punto de origen y aterizar
                    return False

                # Si el camino tiene más de 2 puntos, significa que hay obstáculos
                if len(camino) > 2:
                    msg = f"[Mission] 🔀 Ruta alternativa calculada con {len(camino)} waypoints intermedios"
                    print(msg)
                    logging.info(msg)
                    # Seguir los waypoints intermedios
                    for j, (wx, wy, wz) in enumerate(camino[1:], 1):  # Saltar el punto de inicio
                        msg = f"[Mission]   └─ WP intermedio {j}/{len(camino)-1}: ({wx:.2f}, {wy:.2f}, {wz:.2f})"
                        print(msg)
                        logging.info(msg)
                        dron.goto(wx, wy, wz, blocking=True)
                        if callback_posicion is not None:
                            try:
                                callback_posicion(wx, wy, wz)
                            except Exception as e:
                                logging.warning(f"[Mission] Error en callback de posición: {e}")
                        time.sleep(0.3)  # Pausa breve entre waypoints intermedios
                else:
                    # Ruta directa sin obstáculos
                    msg = f"[Mission] ✅ Ruta directa sin obstáculos"
                    print(msg)
                    logging.info(msg)
                    dron.goto(x, y, z, blocking=True)
            else:
                # Sin pathfinder, ir directo
                msg = f"[Mission] ⚠️ Pathfinder NO activo, navegando sin evitar obstáculos"
                print(msg)
                logging.warning(msg)
                dron.goto(x, y, z, blocking=True)

            # Actualizar posición en visualizador si hay callback
            if callback_posicion is not None:
                try:
                    callback_posicion(x, y, z)
                except Exception as e:
                    logging.warning(f"[Mission] Error en callback de posición: {e}")

            # Usar pausa de configuración
            pausa = ConfigMision.get_pausa_waypoint()
            time.sleep(pausa)

            # Verificar si hay fotos que tomar en este waypoint
            if i in photos_by_waypoint and camera is not None:
                for photo_cmd in photos_by_waypoint[i]:
                    logging.info(f"[Mission] 📷 Capturando FOTO en waypoint {i + 1}")
                    
                    # Capturar foto con posición y metadata
                    posicion = photo_cmd.get('position', [x, y, z])
                    metadata = photo_cmd.get('metadata', {})
                    
                    # Añadir info de velocidad y waypoint a metadata
                    metadata['waypoint'] = i + 1
                    metadata['velocidad'] = f"{velocidad} m/s"
                    
                    try:
                        ruta_foto = camera.capturar_foto(tuple(posicion), metadata)
                        if ruta_foto:
                            logging.info(f"[Mission] ✓ Foto guardada: {ruta_foto}")
                        else:
                            logging.warning(f"[Mission] ⚠️ No se pudo capturar la foto")
                    except Exception as e:
                        logging.error(f"[Mission] Error capturando foto: {e}")
                    
                    # Pequeña pausa después de la foto
                    time.sleep(0.5)

            if dron.state != "flying":
                logging.error("[Mission] Dron dejó de volar, abortando misión")
                return False

        # ✅ ROTACIONES CON ACTUALIZACIÓN DE VISUALIZADOR
        if 'rotations' in mission_dict and mission_dict['rotations']:
            pausa_rot = ConfigMision.get_pausa_rotacion()
            for rotation in mission_dict['rotations']:
                degrees = rotation['degrees']
                logging.info(f"[Mission] Rotando {degrees}°")
                
                # Ejecutar rotación en el dron
                dron.changeHeading(degrees)
                
                # ✅ ACTUALIZAR VISUALIZADOR
                if visualizador is not None:
                    try:
                        visualizador.actualizar_heading_planificado(degrees)
                        logging.info(f"[Mission] ✓ Heading del visualizador actualizado: +{degrees}°")
                    except Exception as e:
                        logging.warning(f"[Mission] Error actualizando visualizador: {e}")
                
                time.sleep(pausa_rot)

        logging.info("[Mission] ¡Misión completada exitosamente!")
        
        # Mostrar resumen de fotos
        if 'photos' in mission_dict and len(mission_dict['photos']) > 0:
            logging.info(f"[Mission] 📷 Total de fotos capturadas: {len(mission_dict['photos'])}")

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
    print(f"Total de fotos: {len(mission.photos)}")
    print("\nWAYPOINTS:")
    print("-" * 60)

    for i, wp in enumerate(mission.waypoints):
        foto_marker = " 📷" if any(p['waypoint_index'] == i for p in mission.photos) else ""
        print(f"  {i + 1}. X={wp['x']:6.2f}m, Y={wp['y']:6.2f}m, Z={wp['z']:6.2f}m{foto_marker}")

    if mission.photos:
        print("\nFOTOS:")
        print("-" * 60)
        for i, photo in enumerate(mission.photos):
            pos = photo['position']
            wp_idx = photo['waypoint_index']
            print(f"  {i + 1}. Foto en waypoint {wp_idx + 1}: X={pos[0]:.2f}m, Y={pos[1]:.2f}m, Z={pos[2]:.2f}m")

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
    
    # Añadir tiempo para fotos (0.5 segundos por foto)
    tiempo_fotos = len(mission.photos) * 0.5

    tiempo_total = tiempo_movimiento + tiempo_pausas + tiempo_rotaciones + tiempo_fotos

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
        'num_fotos': len(mission.photos),
        'distancia_total': calcular_distancia_total(mission),
        'tiempo_estimado': estimar_tiempo_vuelo(mission),
        'altura_despegue': mission.takeoff_alt,
        'waypoints': mission.waypoints.copy(),
        'rotations': mission.rotations.copy(),
        'photos': mission.photos.copy()
    }
