
import math
import heapq
from typing import List, Tuple, Optional, Dict
import logging



# CLASES AUXILIARES


class Nodo:
    """Representa un nodo en el grid de navegación"""

    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z
        self.g = float('inf')  # Costo desde inicio
        self.h = 0  # Heurística al objetivo
        self.f = float('inf')  # f = g + h
        self.padre = None

    def __lt__(self, otro):
        return self.f < otro.f

    def __eq__(self, otro):
        if not isinstance(otro, Nodo):
            return False
        return (abs(self.x - otro.x) < 0.1 and
                abs(self.y - otro.y) < 0.1 and
                abs(self.z - otro.z) < 0.1)

    def __hash__(self):
        return hash((round(self.x, 1), round(self.y, 1), round(self.z, 1)))

    def distancia(self, otro) -> float:
        """Distancia euclidiana entre dos nodos"""
        dx = self.x - otro.x
        dy = self.y - otro.y
        dz = self.z - otro.z
        return math.sqrt(dx * dx + dy * dy + dz * dz)


class Obstaculo:
    """Representa un obstáculo poligonal"""

    def __init__(self, puntos: List[Tuple[float, float]]):

        self.puntos = puntos
        self.x_coords = [p[0] for p in puntos]
        self.y_coords = [p[1] for p in puntos]
        self.margen_seguridad = 0.3  # metros

    def punto_dentro(self, x: float, y: float) -> bool:

        n = len(self.puntos)
        inside = False

        p1x, p1y = self.puntos[0]
        for i in range(1, n + 1):
            p2x, p2y = self.puntos[i % n]

            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside

            p1x, p1y = p2x, p2y

        return inside

    def punto_cerca(self, x: float, y: float) -> bool:
        """Verifica si un punto está cerca del obstáculo (dentro del margen)"""
        # Primero verificar si está dentro
        if self.punto_dentro(x, y):
            return True

        # Verificar distancia a cada borde
        for i in range(len(self.puntos)):
            p1 = self.puntos[i]
            p2 = self.puntos[(i + 1) % len(self.puntos)]

            distancia = self._distancia_punto_segmento(x, y, p1[0], p1[1], p2[0], p2[1])
            if distancia < self.margen_seguridad:
                return True

        return False

    def _distancia_punto_segmento(self, px, py, x1, y1, x2, y2) -> float:
        """Calcula la distancia mínima de un punto a un segmento"""
        # Vector del segmento
        dx = x2 - x1
        dy = y2 - y1

        if dx == 0 and dy == 0:
            # El segmento es un punto
            return math.sqrt((px - x1) ** 2 + (py - y1) ** 2)

        # Parámetro t del punto más cercano en el segmento
        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))

        # Punto más cercano en el segmento
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy

        # Distancia al punto más cercano
        return math.sqrt((px - closest_x) ** 2 + (py - closest_y) ** 2)



# CLASE PRINCIPAL


class PathFinder:

    def __init__(self, geocage_puntos: List[Tuple[float, float]],
                 obstaculos: List[Dict] = None,
                 resolucion: float = 0.2):

        self.geocage_puntos = geocage_puntos
        self.geocage_x = [p[0] for p in geocage_puntos]
        self.geocage_y = [p[1] for p in geocage_puntos]

        # Crear objetos Obstaculo
        self.obstaculos = []
        if obstaculos:
            for obs_data in obstaculos:
                puntos = obs_data.get('points', [])
                if puntos:
                    self.obstaculos.append(Obstaculo(puntos))

        self.resolucion = resolucion

        # Calcular límites
        self._calcular_limites()

        logging.info(f"[PathFinder] Inicializado - Obstáculos: {len(self.obstaculos)}, Resolución: {resolucion}m")

    def _calcular_limites(self):
        """Calcula los límites del área de vuelo"""
        self.x_min = min(self.geocage_x)
        self.x_max = max(self.geocage_x)
        self.y_min = min(self.geocage_y)
        self.y_max = max(self.geocage_y)

    def punto_valido(self, x: float, y: float, z: float) -> bool:
        """Verifica si un punto es válido (dentro del geocage y fuera de obstáculos)"""
        # Verificar que está dentro del geocage
        if not self._punto_dentro_geocage(x, y):
            return False

        # Verificar que no colisiona con obstáculos
        for obstaculo in self.obstaculos:
            if obstaculo.punto_cerca(x, y):
                return False

        return True

    def _punto_dentro_geocage(self, x: float, y: float) -> bool:
        """Verifica si un punto está dentro del geocage"""
        n = len(self.geocage_puntos)
        inside = False

        p1x, p1y = self.geocage_puntos[0]
        for i in range(1, n + 1):
            p2x, p2y = self.geocage_puntos[i % n]

            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside

            p1x, p1y = p2x, p2y

        return inside

    def encontrar_camino(self, inicio: Tuple[float, float, float],
                         objetivo: Tuple[float, float, float]) -> Optional[List[Tuple[float, float, float]]]:

        nodo_inicio = Nodo(*inicio)
        nodo_objetivo = Nodo(*objetivo)

        # Verificar que inicio y objetivo son válidos
        if not self.punto_valido(inicio[0], inicio[1], inicio[2]):
            logging.warning(f"[PathFinder] Punto de inicio inválido: {inicio}")
            return None

        if not self.punto_valido(objetivo[0], objetivo[1], objetivo[2]):
            logging.warning(f"[PathFinder] Punto objetivo inválido: {objetivo}")
            return None

        # Si no hay obstáculos, devolver línea directa
        if not self.obstaculos:
            return [inicio, objetivo]

        # Verificar si hay línea de visión directa
        if self._linea_libre(inicio, objetivo):
            logging.info(f"[PathFinder] Línea directa sin obstáculos")
            return [inicio, objetivo]

        # Ejecutar A*
        logging.info(f"[PathFinder] Buscando camino alternativo...")
        camino = self._astar(nodo_inicio, nodo_objetivo)

        if camino:
            logging.info(f"[PathFinder] Camino encontrado con {len(camino)} waypoints")
            # Simplificar camino
            camino_simplificado = self._simplificar_camino(camino)
            logging.info(f"[PathFinder] Camino simplificado a {len(camino_simplificado)} waypoints")
            return camino_simplificado
        else:
            logging.warning(f"[PathFinder] No se encontró camino")
            return None

    def _linea_libre(self, p1: Tuple[float, float, float],
                     p2: Tuple[float, float, float]) -> bool:
        """Verifica si hay línea de visión libre entre dos puntos"""
        # Número de puntos a verificar
        distancia_2d = math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)
        num_checks = int(math.ceil(distancia_2d / (self.resolucion * 0.5)))
        num_checks = max(num_checks, 2)

        for i in range(num_checks + 1):
            t = i / num_checks
            x = p1[0] + t * (p2[0] - p1[0])
            y = p1[1] + t * (p2[1] - p1[1])
            z = p1[2] + t * (p2[2] - p1[2])

            if not self.punto_valido(x, y, z):
                return False

        return True

    def _astar(self, inicio: Nodo, objetivo: Nodo) -> Optional[List[Tuple[float, float, float]]]:
        """Implementación del algoritmo A*"""
        # Inicializar
        inicio.g = 0
        inicio.h = inicio.distancia(objetivo)
        inicio.f = inicio.g + inicio.h

        abiertos = []
        heapq.heappush(abiertos, inicio)
        cerrados = set()
        nodos_visitados = {inicio: inicio}

        iteraciones = 0
        max_iteraciones = 5000

        while abiertos and iteraciones < max_iteraciones:
            iteraciones += 1

            # Obtener nodo con menor f
            actual = heapq.heappop(abiertos)

            # ¿Llegamos al objetivo?
            if actual.distancia(objetivo) < self.resolucion:
                return self._reconstruir_camino(actual)

            cerrados.add(actual)

            # Explorar vecinos
            for vecino in self._obtener_vecinos(actual):
                if vecino in cerrados:
                    continue

                # Calcular nuevo g
                nuevo_g = actual.g + actual.distancia(vecino)

                # Si encontramos un mejor camino a este vecino
                if vecino not in nodos_visitados:
                    nodos_visitados[vecino] = vecino
                    vecino_existente = vecino
                else:
                    vecino_existente = nodos_visitados[vecino]

                if nuevo_g < vecino_existente.g:
                    vecino_existente.g = nuevo_g
                    vecino_existente.h = vecino_existente.distancia(objetivo)
                    vecino_existente.f = vecino_existente.g + vecino_existente.h
                    vecino_existente.padre = actual

                    if vecino_existente not in abiertos:
                        heapq.heappush(abiertos, vecino_existente)

        logging.info(f"[PathFinder] A* finalizado - Iteraciones: {iteraciones}")
        return None

    def _obtener_vecinos(self, nodo: Nodo) -> List[Nodo]:
        """Obtiene los vecinos válidos de un nodo"""
        vecinos = []

        # 8 direcciones en 2D + mantener altura
        direcciones = [
            (self.resolucion, 0),
            (-self.resolucion, 0),
            (0, self.resolucion),
            (0, -self.resolucion),
            (self.resolucion, self.resolucion),
            (self.resolucion, -self.resolucion),
            (-self.resolucion, self.resolucion),
            (-self.resolucion, -self.resolucion)
        ]

        for dx, dy in direcciones:
            nuevo_x = nodo.x + dx
            nuevo_y = nodo.y + dy
            nuevo_z = nodo.z

            if self.punto_valido(nuevo_x, nuevo_y, nuevo_z):
                vecinos.append(Nodo(nuevo_x, nuevo_y, nuevo_z))

        return vecinos

    def _reconstruir_camino(self, nodo_final: Nodo) -> List[Tuple[float, float, float]]:
        """Reconstruye el camino desde el nodo final hasta el inicio"""
        camino = []
        actual = nodo_final

        while actual is not None:
            camino.append((actual.x, actual.y, actual.z))
            actual = actual.padre

        camino.reverse()
        return camino

    def _simplificar_camino(self, camino: List[Tuple[float, float, float]]) -> List[Tuple[float, float, float]]:
        if len(camino) <= 2:
            return camino

        simplificado = [camino[0]]
        i = 0

        while i < len(camino) - 1:
            # Intentar saltar lo más lejos posible
            j = len(camino) - 1
            while j > i + 1:
                if self._linea_libre(camino[i], camino[j]):
                    simplificado.append(camino[j])
                    i = j
                    break
                j -= 1
            else:
                # No se pudo saltar, avanzar un paso
                i += 1
                if i < len(camino):
                    simplificado.append(camino[i])

        # Asegurar que el último punto esté incluido
        if simplificado[-1] != camino[-1]:
            simplificado.append(camino[-1])

        return simplificado

    def validar_mision(self, waypoints: List[Tuple[float, float, float]]) -> Dict:

        problemas = []
        waypoints_corregidos = []

        # Verificar cada waypoint
        for i, wp in enumerate(waypoints):
            if not self.punto_valido(wp[0], wp[1], wp[2]):
                problemas.append(f"Waypoint {i + 1} en zona prohibida: {wp}")

        # Verificar cada segmento
        for i in range(len(waypoints) - 1):
            if not self._linea_libre(waypoints[i], waypoints[i + 1]):
                problemas.append(f"Segmento {i + 1}-{i + 2} atraviesa obstáculo")

                # Intentar encontrar camino alternativo
                camino_alt = self.encontrar_camino(waypoints[i], waypoints[i + 1])
                if camino_alt:
                    # Insertar waypoints intermedios
                    if i == 0:
                        waypoints_corregidos = camino_alt[:-1]
                    else:
                        waypoints_corregidos.extend(camino_alt[1:-1])

        # Si hay problemas pero no se pudieron corregir
        if problemas and not waypoints_corregidos:
            return {
                'valido': False,
                'problemas': problemas,
                'waypoints_corregidos': None
            }

        # Si hay correcciones
        if waypoints_corregidos:
            waypoints_corregidos.append(waypoints[-1])
            return {
                'valido': False,
                'problemas': problemas,
                'waypoints_corregidos': waypoints_corregidos
            }

        # Todo OK
        return {
            'valido': True,
            'problemas': [],
            'waypoints_corregidos': waypoints
        }


def crear_pathfinder_desde_mapa(config: Dict, resolucion: float = 0.2) -> Optional[PathFinder]:
    geocage = config.get('geocage', [])
    if not geocage:
        logging.warning("[PathFinder] No hay geocage en la configuración")
        return None

    obstaculos = config.get('obstaculos', [])

    return PathFinder(geocage, obstaculos, resolucion)


def validar_punto_seguro(pathfinder: PathFinder, x: float, y: float, z: float) -> Dict:
    #Valida si un punto es seguro para volar.
    if not pathfinder.punto_valido(x, y, z):
        # Determinar razón
        if not pathfinder._punto_dentro_geocage(x, y):
            return {
                'seguro': False,
                'razon': 'fuera_geocage',
                'mensaje': 'El punto está fuera del área de vuelo permitida'
            }
        else:
            return {
                'seguro': False,
                'razon': 'obstaculo',
                'mensaje': 'El punto está demasiado cerca de un obstáculo'
            }

    return {
        'seguro': True,
        'razon': 'ok',
        'mensaje': 'Punto seguro'
    }

