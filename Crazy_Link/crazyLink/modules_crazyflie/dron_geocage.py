
#Módulo de Gestión de Geocage y Obstáculos para Crazyflie

import json
import math
from typing import List, Tuple, Dict, Optional
from datetime import datetime
from pathlib import Path
import logging



# CLASE DE MAPA DE VUELO


class MapaVuelo:
    """Clase para almacenar configuración completa de un mapa de vuelo"""

    def __init__(self, nombre: str = "Sin nombre"):
        self.nombre = nombre
        self.fecha_creacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.geocage = []  # Lista de puntos (x, y)
        self.obstaculos = []  # Lista de obstáculos (cada uno es lista de puntos)
        self.descripcion = ""

    def to_dict(self) -> Dict:
        """Convierte el mapa a diccionario para guardar"""
        return {
            'nombre': self.nombre,
            'fecha_creacion': self.fecha_creacion,
            'geocage': self.geocage,
            'obstaculos': self.obstaculos,
            'descripcion': self.descripcion
        }

    @classmethod
    def from_dict(cls, data: Dict):
        """Crea un MapaVuelo desde un diccionario"""
        mapa = cls(data.get('nombre', 'Sin nombre'))
        mapa.fecha_creacion = data.get('fecha_creacion', '')
        mapa.geocage = data.get('geocage', [])
        mapa.obstaculos = data.get('obstaculos', [])
        mapa.descripcion = data.get('descripcion', '')
        return mapa

    def guardar(self, ruta: str) -> bool:
        """
        Guarda el mapa en un archivo JSON.

        Args:
            ruta: Ruta del archivo

        Returns:
            True si se guardó correctamente
        """
        try:
            with open(ruta, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
            logging.info(f"[MapaVuelo] Guardado en: {ruta}")
            return True
        except Exception as e:
            logging.error(f"[MapaVuelo] Error guardando: {e}")
            return False

    @classmethod
    def cargar(cls, ruta: str):
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logging.info(f"[MapaVuelo] Cargado desde: {ruta}")
            return cls.from_dict(data)
        except Exception as e:
            logging.error(f"[MapaVuelo] Error cargando: {e}")
            return None



# CLASE DE VALIDACIÓN GEOMÉTRICA


class ValidadorGeometria:
    """Validador de geometría para geocage y obstáculos"""

    @staticmethod
    def punto_dentro_poligono(x: float, y: float,
                              poligono_x: List[float],
                              poligono_y: List[float]) -> bool:

        n = len(poligono_x)
        inside = False

        p1x, p1y = poligono_x[0], poligono_y[0]
        for i in range(1, n + 1):
            p2x, p2y = poligono_x[i % n], poligono_y[i % n]

            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside

            p1x, p1y = p2x, p2y

        return inside

    @staticmethod
    def lineas_se_intersectan(p1: Tuple[float, float], p2: Tuple[float, float],
                              p3: Tuple[float, float], p4: Tuple[float, float]) -> bool:

        def orientation(p, q, r):
            val = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
            if val == 0:
                return 0
            return 1 if val > 0 else 2

        def on_segment(p, q, r):
            return (q[0] <= max(p[0], r[0]) and q[0] >= min(p[0], r[0]) and
                    q[1] <= max(p[1], r[1]) and q[1] >= min(p[1], r[1]))

        o1 = orientation(p1, p2, p3)
        o2 = orientation(p1, p2, p4)
        o3 = orientation(p3, p4, p1)
        o4 = orientation(p3, p4, p2)

        if o1 != o2 and o3 != o4:
            return True

        if (o1 == 0 and on_segment(p1, p3, p2)) or \
                (o2 == 0 and on_segment(p1, p4, p2)) or \
                (o3 == 0 and on_segment(p3, p1, p4)) or \
                (o4 == 0 and on_segment(p3, p2, p4)):
            return True

        return False

    @staticmethod
    def calcular_area_poligono(puntos_x: List[float], puntos_y: List[float]) -> float:
        n = len(puntos_x)
        area = 0.0

        for i in range(n):
            j = (i + 1) % n
            area += puntos_x[i] * puntos_y[j]
            area -= puntos_x[j] * puntos_y[i]

        return abs(area) / 2.0

    @staticmethod
    def calcular_centroide(puntos_x: List[float], puntos_y: List[float]) -> Tuple[float, float]:
        n = len(puntos_x)
        cx = sum(puntos_x) / n
        cy = sum(puntos_y) / n
        return cx, cy



# CLASE DE CONFIGURACIÓN DE GEOCAGE


class ConfiguracionGeocage:
    def __init__(self):
        self.geocage_puntos = []
        self.obstaculos = []
        self.validador = ValidadorGeometria()

    def establecer_geocage(self, puntos: List[Tuple[float, float]]) -> bool:
        if len(puntos) < 3:
            logging.warning("[Geocage] Se necesitan al menos 3 puntos")
            return False

        self.geocage_puntos = puntos
        logging.info(f"[Geocage] Establecido con {len(puntos)} puntos")
        return True

    def agregar_obstaculo(self, puntos: List[Tuple[float, float]]) -> bool:
        if len(puntos) < 3:
            logging.warning("[Geocage] Obstáculo necesita al menos 3 puntos")
            return False

        self.obstaculos.append({'points': puntos})
        logging.info(f"[Geocage] Obstáculo {len(self.obstaculos)} agregado")
        return True

    def validar_configuracion(self) -> Dict:
        errores = []
        advertencias = []

        # Validar geocage
        if not self.geocage_puntos:
            errores.append("No hay geocage definido")
        elif len(self.geocage_puntos) < 3:
            errores.append("Geocage necesita al menos 3 puntos")
        else:
            # Verificar que el origen está dentro
            x_coords = [p[0] for p in self.geocage_puntos]
            y_coords = [p[1] for p in self.geocage_puntos]

            if not self.validador.punto_dentro_poligono(0, 0, x_coords, y_coords):
                errores.append("El origen (0,0) está fuera del geocage")

            # Calcular área
            area = self.validador.calcular_area_poligono(x_coords, y_coords)
            if area < 1.0:
                advertencias.append(f"Área pequeña: {area:.2f}m²")

        # Validar obstáculos
        for i, obs in enumerate(self.obstaculos):
            puntos = obs.get('points', [])
            if len(puntos) < 3:
                errores.append(f"Obstáculo {i + 1} tiene menos de 3 puntos")

        return {
            'valido': len(errores) == 0,
            'errores': errores,
            'advertencias': advertencias
        }

    def obtener_configuracion(self) -> Dict:
        return {
            'geocage': self.geocage_puntos.copy(),
            'obstaculos': [obs.copy() for obs in self.obstaculos]
        }

    def limpiar(self):
        """Limpia toda la configuración"""
        self.geocage_puntos = []
        self.obstaculos = []
        logging.info("[Geocage] Configuración limpiada")

    def punto_valido(self, x: float, y: float) -> Dict:
        if not self.geocage_puntos:
            return {'valido': False, 'razon': 'no_geocage'}

        # Verificar geocage
        x_coords = [p[0] for p in self.geocage_puntos]
        y_coords = [p[1] for p in self.geocage_puntos]

        if not self.validador.punto_dentro_poligono(x, y, x_coords, y_coords):
            return {'valido': False, 'razon': 'fuera_geocage'}

        # Verificar obstáculos
        for i, obs in enumerate(self.obstaculos):
            puntos = obs.get('points', [])
            obs_x = [p[0] for p in puntos]
            obs_y = [p[1] for p in puntos]

            if self.validador.punto_dentro_poligono(x, y, obs_x, obs_y):
                return {'valido': False, 'razon': f'dentro_obstaculo_{i + 1}'}

        return {'valido': True, 'razon': 'ok'}

    def obtener_estadisticas(self) -> Dict:
        if not self.geocage_puntos:
            return {}

        x_coords = [p[0] for p in self.geocage_puntos]
        y_coords = [p[1] for p in self.geocage_puntos]

        area = self.validador.calcular_area_poligono(x_coords, y_coords)
        centroide = self.validador.calcular_centroide(x_coords, y_coords)

        return {
            'num_vertices': len(self.geocage_puntos),
            'num_obstaculos': len(self.obstaculos),
            'area_total': area,
            'centroide': centroide,
            'x_min': min(x_coords),
            'x_max': max(x_coords),
            'y_min': min(y_coords),
            'y_max': max(y_coords)
        }



# FUNCIONES DE UTILIDAD


def crear_geocage_rectangular(ancho: float, largo: float,
                              centrado: bool = True) -> List[Tuple[float, float]]:
    if centrado:
        x1, x2 = -ancho / 2, ancho / 2
        y1, y2 = -largo / 2, largo / 2
    else:
        x1, x2 = 0, ancho
        y1, y2 = 0, largo

    return [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]


def crear_geocage_circular(radio: float, num_puntos: int = 8) -> List[Tuple[float, float]]:
    puntos = []
    for i in range(num_puntos):
        angulo = 2 * math.pi * i / num_puntos
        x = radio * math.cos(angulo)
        y = radio * math.sin(angulo)
        puntos.append((x, y))
    return puntos


def cargar_mapa_desde_archivo(ruta: str) -> Optional[Dict]:
    mapa = MapaVuelo.cargar(ruta)
    if mapa:
        return {
            'geocage': mapa.geocage,
            'obstaculos': mapa.obstaculos,
            'nombre': mapa.nombre,
            'descripcion': mapa.descripcion
        }
    return None


def guardar_configuracion_en_archivo(config: Dict, ruta: str, nombre: str = "Mapa") -> bool:
    mapa = MapaVuelo(nombre)
    mapa.geocage = config.get('geocage', [])
    mapa.obstaculos = config.get('obstaculos', [])
    mapa.descripcion = config.get('descripcion', '')

    return mapa.guardar(ruta)


def listar_mapas_guardados(directorio: str = "./mapas_vuelo") -> List[Dict]:
    dir_path = Path(directorio)
    if not dir_path.exists():
        return []

    mapas = []
    for archivo in dir_path.glob("*.json"):
        try:
            mapa = MapaVuelo.cargar(str(archivo))
            if mapa:
                mapas.append({
                    'nombre': mapa.nombre,
                    'archivo': archivo.name,
                    'ruta': str(archivo),
                    'fecha': mapa.fecha_creacion,
                    'num_vertices': len(mapa.geocage),
                    'num_obstaculos': len(mapa.obstaculos)
                })
        except Exception as e:
            logging.warning(f"Error leyendo {archivo}: {e}")

    return mapas
