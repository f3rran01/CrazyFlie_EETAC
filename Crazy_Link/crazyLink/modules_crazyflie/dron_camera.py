"""
Módulo de Cámara Extendido para Crazyflie
Permite capturar fotos Y grabar videos durante la ejecución de misiones de vuelo
VERSIÓN EXTENDIDA con soporte para:
- Fotos individuales
- Videos cortos (duración fija)
- Videos de ruta (desde un punto hasta el final)
"""

import cv2
import os
import time
import logging
import threading
from datetime import datetime
from typing import Optional, Tuple
import numpy as np


class DroneCamera:
    """
    Clase extendida para gestionar la captura de fotos y videos durante el vuelo.
    Incluye soporte para videos cortos y videos de ruta completa.
    """

    def __init__(self, carpeta_fotos: str = "fotos_vuelo", carpeta_videos: str = "videos_vuelo"):
        """
        Inicializa el sistema de cámara extendido.

        Args:
            carpeta_fotos: Carpeta donde se guardarán las fotos
            carpeta_videos: Carpeta donde se guardarán los videos
        """
        self.carpeta_fotos = carpeta_fotos
        self.carpeta_videos = carpeta_videos
        self.camera = None
        self.camera_index = 0
        self.foto_contador = 0
        self.video_contador = 0
        self.session_id = None
        self.modo_simulacion = False

        # Estado de grabación de video
        self.grabando_video = False
        self.video_writer = None
        self.video_thread = None
        self.video_stop_event = threading.Event()
        self.video_ruta_activo = False
        self.video_actual_path = None

        # Configuración de video
        self.video_fps = 15
        self.video_resolution = (1280, 720)

        # Crear carpetas si no existen
        for carpeta in [self.carpeta_fotos, self.carpeta_videos]:
            if not os.path.exists(carpeta):
                os.makedirs(carpeta)
                logging.info(f"[CameraExt] Carpeta creada: {carpeta}")

        # Iniciar nueva sesión
        self._iniciar_sesion()

        logging.info("[CameraExt] Sistema de cámara extendido inicializado")

    def _iniciar_sesion(self):
        """Inicia una nueva sesión con timestamp único"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_id = f"sesion_{timestamp}"
        # Las carpetas se crean bajo demanda cuando se necesiten
        logging.info(f"[CameraExt] Nueva sesión iniciada: {self.session_id}")
    
    def _asegurar_carpeta_sesion(self, tipo: str) -> str:
        """
        Crea la carpeta de sesión solo cuando se necesita.
        
        Args:
            tipo: 'fotos' o 'videos'
            
        Returns:
            Ruta de la carpeta de sesión
        """
        if tipo == 'fotos':
            carpeta_base = self.carpeta_fotos
        else:
            carpeta_base = self.carpeta_videos
        
        carpeta_sesion = os.path.join(carpeta_base, self.session_id)
        
        if not os.path.exists(carpeta_sesion):
            os.makedirs(carpeta_sesion)
            logging.info(f"[CameraExt] Carpeta de sesión creada: {carpeta_sesion}")
        
        return carpeta_sesion

    def abrir_camara(self, camera_index: int = 0) -> bool:
        """
        Abre la cámara del sistema de forma compatible con todos los OS.

        Args:
            camera_index: Índice de la cámara (0 para cámara principal)

        Returns:
            True si se abrió correctamente, False en caso contrario
        """
        try:
            # Si la cámara ya está abierta, verificar que funciona
            if self.camera is not None and self.camera.isOpened():
                ret, frame = self.camera.read()
                if ret and frame is not None:
                    return True
                # Si no funciona, cerrarla
                self.camera.release()
                self.camera = None

            self.camera_index = camera_index

            # Intentar diferentes backends según el sistema operativo
            import platform
            sistema = platform.system()

            backends_a_probar = []

            if sistema == "Windows":
                backends_a_probar = [
                    ("CAP_DSHOW", cv2.CAP_DSHOW),
                    ("CAP_MSMF", cv2.CAP_MSMF),
                    ("CAP_ANY", cv2.CAP_ANY)
                ]
            elif sistema == "Linux":
                backends_a_probar = [
                    ("CAP_V4L2", cv2.CAP_V4L2),
                    ("CAP_ANY", cv2.CAP_ANY)
                ]
            else:  # macOS
                backends_a_probar = [
                    ("CAP_AVFOUNDATION", cv2.CAP_AVFOUNDATION),
                    ("CAP_ANY", cv2.CAP_ANY)
                ]

            for nombre_backend, backend_id in backends_a_probar:
                try:
                    logging.info(f"[CameraExt] Intentando backend {nombre_backend}...")

                    self.camera = cv2.VideoCapture(self.camera_index, backend_id)

                    if not self.camera.isOpened():
                        continue

                    # Configurar cámara
                    self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.video_resolution[0])
                    self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.video_resolution[1])
                    self.camera.set(cv2.CAP_PROP_FPS, self.video_fps)

                    # Dar tiempo de inicialización
                    time.sleep(0.5)

                    # Descartar primeros frames
                    for _ in range(5):
                        self.camera.read()
                        time.sleep(0.05)

                    # Verificar captura
                    ret, frame = self.camera.read()
                    if ret and frame is not None and np.mean(frame) > 5:
                        logging.info(f"[CameraExt] ✓ Cámara funcionando con {nombre_backend}")
                        return True

                    self.camera.release()
                    self.camera = None

                except Exception as e:
                    logging.warning(f"[CameraExt] Backend {nombre_backend} falló: {e}")
                    if self.camera is not None:
                        self.camera.release()
                        self.camera = None

            logging.warning("[CameraExt] No se pudo abrir cámara, activando modo simulación")
            self.modo_simulacion = True
            return False

        except Exception as e:
            logging.error(f"[CameraExt] Error general: {e}")
            self.modo_simulacion = True
            return False

    def cerrar_camara(self):
        """Cierra la cámara"""
        # Detener cualquier grabación en curso
        if self.grabando_video:
            self.detener_video()

        if self.camera is not None:
            self.camera.release()
            self.camera = None
            logging.info("[CameraExt] Cámara cerrada")

    def capturar_foto(self, posicion: Optional[Tuple[float, float, float]] = None,
                      metadata: Optional[dict] = None) -> Optional[str]:
        try:
            # Generar nombre de archivo
            self.foto_contador += 1
            timestamp = datetime.now().strftime("%H%M%S")
            nombre_archivo = f"foto_{self.foto_contador:03d}_{timestamp}.jpg"

            # Crear carpeta de sesión solo si es necesario
            carpeta_sesion = self._asegurar_carpeta_sesion('fotos')
            ruta_completa = os.path.join(carpeta_sesion, nombre_archivo)

            # Intentar abrir cámara si no está abierta
            if self.camera is None or not self.camera.isOpened():
                if not self.abrir_camara():
                    logging.warning("[CameraExt] No se pudo abrir cámara para foto, usando simulación")
                    self.modo_simulacion = True

            # Capturar frame
            frame = None
            if not self.modo_simulacion and self.camera is not None and self.camera.isOpened():
                ret, frame = self.camera.read()
                if not ret or frame is None:
                    logging.warning("[CameraExt] No se pudo capturar frame, usando simulación")
                    self.modo_simulacion = True
                    frame = None

            # Crear imagen simulada si es necesario
            if self.modo_simulacion or frame is None:
                frame = self._crear_frame_simulado("FOTO", posicion)

            # Añadir información de posición
            if posicion is not None:
                frame = self._anadir_info_imagen(frame, posicion, metadata)

            # Guardar imagen
            cv2.imwrite(ruta_completa, frame)

            logging.info(f"[CameraExt] 📷 Foto guardada: {nombre_archivo}")
            return ruta_completa

        except Exception as e:
            logging.error(f"[CameraExt] Error al capturar foto: {e}")
            return None

    def iniciar_video_corto(self, duracion: int = 10,
                            posicion: Optional[Tuple[float, float, float]] = None,
                            metadata: Optional[dict] = None) -> Optional[str]:
        if self.grabando_video:
            logging.warning("[CameraExt] Ya hay una grabación en curso")
            return None

        try:
            # Generar nombre de archivo
            self.video_contador += 1
            timestamp = datetime.now().strftime("%H%M%S")
            nombre_archivo = f"video_corto_{self.video_contador:03d}_{timestamp}.avi"

            # Crear carpeta de sesión solo si es necesario
            carpeta_sesion = self._asegurar_carpeta_sesion('videos')
            ruta_completa = os.path.join(carpeta_sesion, nombre_archivo)

            # Intentar abrir cámara
            if self.camera is None or not self.camera.isOpened():
                if not self.abrir_camara():
                    logging.error("[CameraExt] No se pudo abrir la cámara para video")
                    self.modo_simulacion = True

            if self.modo_simulacion:
                # Crear video simulado
                return self._crear_video_simulado(ruta_completa, duracion, "VIDEO CORTO", posicion)

            # Obtener resolución REAL de la cámara
            actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            if actual_width == 0 or actual_height == 0:
                actual_width, actual_height = 640, 480  # Fallback
                logging.warning(f"[CameraExt] Usando resolución fallback: {actual_width}x{actual_height}")
            else:
                logging.info(f"[CameraExt] Resolución de cámara: {actual_width}x{actual_height}")

            # Configurar grabación con resolución REAL
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            self.video_writer = cv2.VideoWriter(
                ruta_completa, fourcc, self.video_fps, (actual_width, actual_height)
            )

            if not self.video_writer.isOpened():
                logging.error(f"[CameraExt] No se pudo crear VideoWriter para video corto")
                logging.error(f"[CameraExt] Intentando resolución 640x480...")
                self.video_writer = cv2.VideoWriter(
                    ruta_completa, fourcc, self.video_fps, (640, 480)
                )
                if not self.video_writer.isOpened():
                    logging.error("[CameraExt] Fallback también falló, usando simulación")
                    self.modo_simulacion = True
                    return self._crear_video_simulado(ruta_completa, duracion, "VIDEO CORTO", posicion)

            self.grabando_video = True
            self.video_actual_path = ruta_completa
            self.video_stop_event.clear()

            # Iniciar thread de grabación
            self.video_thread = threading.Thread(
                target=self._grabar_video_duracion,
                args=(duracion, posicion, metadata)
            )
            self.video_thread.start()

            logging.info(f"[CameraExt] 🎬 Iniciando video corto ({duracion}s): {nombre_archivo}")
            return ruta_completa

        except Exception as e:
            logging.error(f"[CameraExt] Error al iniciar video corto: {e}")
            return None

    def _grabar_video_duracion(self, duracion: int, posicion, metadata):
        """Thread que graba video durante una duración específica"""
        frames_totales = duracion * self.video_fps
        frames_grabados = 0
        frames_fallidos = 0
        inicio = time.time()

        try:
            while frames_grabados < frames_totales and not self.video_stop_event.is_set():
                if self.camera is not None and self.camera.isOpened():
                    ret, frame = self.camera.read()
                    if ret and frame is not None:
                        # Añadir timestamp al frame
                        frame = self._anadir_timestamp_video(frame, frames_grabados, frames_totales)
                        self.video_writer.write(frame)
                        frames_grabados += 1
                    else:
                        frames_fallidos += 1
                        if frames_fallidos > 30:  # Si falla muchos frames seguidos
                            logging.warning(f"[CameraExt] Demasiados frames fallidos ({frames_fallidos})")
                            break
                else:
                    logging.warning("[CameraExt] Cámara no disponible durante grabación")
                    break

                # Controlar FPS
                elapsed = time.time() - inicio
                expected_elapsed = frames_grabados / self.video_fps
                if expected_elapsed > elapsed:
                    time.sleep(expected_elapsed - elapsed)

        except Exception as e:
            logging.error(f"[CameraExt] Error durante grabación: {e}")

        finally:
            self._finalizar_video()
            logging.info(f"[CameraExt] ✓ Video corto completado: {frames_grabados} frames grabados")

    def iniciar_video_ruta(self, posicion: Optional[Tuple[float, float, float]] = None,
                           metadata: Optional[dict] = None) -> Optional[str]:
        """
        Inicia la grabación de un video de ruta (hasta que se detenga manualmente).

        Args:
            posicion: Posición inicial del dron
            metadata: Metadatos adicionales

        Returns:
            Ruta del video o None si falla
        """
        if self.grabando_video:
            logging.warning("[CameraExt] Ya hay una grabación en curso")
            return None

        try:
            # Generar nombre de archivo
            self.video_contador += 1
            timestamp = datetime.now().strftime("%H%M%S")
            nombre_archivo = f"video_ruta_{self.video_contador:03d}_{timestamp}.avi"

            # Crear carpeta de sesión solo si es necesario
            carpeta_sesion = self._asegurar_carpeta_sesion('videos')
            ruta_completa = os.path.join(carpeta_sesion, nombre_archivo)

            # Intentar abrir cámara
            if self.camera is None or not self.camera.isOpened():
                if not self.abrir_camara():
                    logging.error("[CameraExt] No se pudo abrir la cámara para video de ruta")
                    self.modo_simulacion = True

            if self.modo_simulacion:
                logging.warning("[CameraExt] Video de ruta en modo simulación")
                self.video_ruta_activo = True
                self.video_actual_path = ruta_completa
                return ruta_completa

            # Obtener resolución REAL de la cámara
            actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            if actual_width == 0 or actual_height == 0:
                actual_width, actual_height = 640, 480  # Fallback
                logging.warning(f"[CameraExt] Usando resolución fallback: {actual_width}x{actual_height}")
            else:
                logging.info(f"[CameraExt] Resolución de cámara: {actual_width}x{actual_height}")

            # Configurar grabación con resolución REAL
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            self.video_writer = cv2.VideoWriter(
                ruta_completa, fourcc, self.video_fps, (actual_width, actual_height)
            )

            if not self.video_writer.isOpened():
                logging.error("[CameraExt] No se pudo crear VideoWriter para video de ruta")
                logging.error("[CameraExt] Intentando resolución 640x480...")
                self.video_writer = cv2.VideoWriter(
                    ruta_completa, fourcc, self.video_fps, (640, 480)
                )
                if not self.video_writer.isOpened():
                    logging.error("[CameraExt] Fallback también falló")
                    return None

            self.grabando_video = True
            self.video_ruta_activo = True
            self.video_actual_path = ruta_completa
            self.video_stop_event.clear()

            # Iniciar thread de grabación continua
            self.video_thread = threading.Thread(
                target=self._grabar_video_continuo,
                args=(posicion, metadata)
            )
            self.video_thread.start()

            logging.info(f"[CameraExt] 🎥 Iniciando video de ruta: {nombre_archivo}")
            return ruta_completa

        except Exception as e:
            logging.error(f"[CameraExt] Error al iniciar video de ruta: {e}")
            return None

    def _grabar_video_continuo(self, posicion, metadata):
        """Thread que graba video continuamente hasta que se detenga"""
        frames_grabados = 0
        inicio = time.time()

        try:
            while not self.video_stop_event.is_set():
                if self.camera is not None and self.camera.isOpened():
                    ret, frame = self.camera.read()
                    if ret and frame is not None:
                        # Añadir indicador de grabación
                        frame = self._anadir_indicador_grabacion(frame, frames_grabados)
                        self.video_writer.write(frame)
                        frames_grabados += 1

                # Controlar FPS
                elapsed = time.time() - inicio
                expected_elapsed = frames_grabados / self.video_fps
                if expected_elapsed > elapsed:
                    time.sleep(expected_elapsed - elapsed)

        except Exception as e:
            logging.error(f"[CameraExt] Error durante grabación de ruta: {e}")

        finally:
            self._finalizar_video()
            duracion = frames_grabados / self.video_fps
            logging.info(f"[CameraExt] ✓ Video de ruta completado: {duracion:.1f}s, {frames_grabados} frames")

    def detener_video(self) -> Optional[str]:
        """
        Detiene cualquier grabación de video en curso.

        Returns:
            Ruta del video guardado o None si no había grabación
        """
        if not self.grabando_video and not self.video_ruta_activo:
            return None

        ruta = self.video_actual_path

        # Señalar al thread que debe detenerse
        self.video_stop_event.set()

        # Esperar a que termine el thread
        if self.video_thread is not None and self.video_thread.is_alive():
            self.video_thread.join(timeout=2.0)

        self.video_ruta_activo = False

        logging.info(f"[CameraExt] Video detenido: {ruta}")
        return ruta

    def _finalizar_video(self):
        """Finaliza la grabación de video y libera recursos"""
        if self.video_writer is not None:
            self.video_writer.release()
            self.video_writer = None

        self.grabando_video = False

    def _crear_frame_simulado(self, tipo: str, posicion) -> np.ndarray:
        """Crea un frame simulado cuando no hay cámara"""
        frame = np.zeros((self.video_resolution[1], self.video_resolution[0], 3), dtype=np.uint8)

        # Fondo degradado
        for i in range(frame.shape[0]):
            frame[i, :] = [30 + i // 10, 30 + i // 15, 50 + i // 8]

        # Texto de simulación
        cv2.putText(frame, f"MODO SIMULACION - {tipo}",
                    (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 165, 255), 3)

        if posicion:
            cv2.putText(frame, f"Posicion: X={posicion[0]:.2f} Y={posicion[1]:.2f} Z={posicion[2]:.2f}",
                        (50, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        return frame

    def _crear_video_simulado(self, ruta: str, duracion: int, tipo: str, posicion) -> str:
        """Crea un video simulado cuando no hay cámara"""
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        writer = cv2.VideoWriter(ruta, fourcc, self.video_fps, self.video_resolution)

        frames_totales = duracion * self.video_fps

        for i in range(frames_totales):
            frame = self._crear_frame_simulado(tipo, posicion)

            # Añadir contador de frames
            cv2.putText(frame, f"Frame: {i + 1}/{frames_totales}",
                        (50, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            writer.write(frame)

        writer.release()
        logging.info(f"[CameraExt] Video simulado creado: {ruta}")
        return ruta

    def _anadir_info_imagen(self, frame: np.ndarray, posicion: Tuple[float, float, float],
                            metadata: Optional[dict] = None) -> np.ndarray:
        """Añade información de posición y metadata a la imagen"""
        img = frame.copy()

        # Configuración del texto
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        color = (0, 255, 0)
        thickness = 2

        # Añadir fondo semitransparente
        overlay = img.copy()
        cv2.rectangle(overlay, (0, 0), (400, 120), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, img, 0.3, 0, img)

        # Información
        y_offset = 25
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(img, f"Timestamp: {timestamp}",
                    (10, y_offset), font, font_scale, color, thickness)

        y_offset += 25
        x, y, z = posicion
        cv2.putText(img, f"Posicion: X={x:.2f}m Y={y:.2f}m Z={z:.2f}m",
                    (10, y_offset), font, font_scale, color, thickness)

        if metadata:
            for key, value in list(metadata.items())[:3]:
                y_offset += 25
                cv2.putText(img, f"{key}: {value}",
                            (10, y_offset), font, font_scale, color, thickness)

        return img

    def _anadir_timestamp_video(self, frame: np.ndarray, frame_actual: int,
                                 frames_totales: int) -> np.ndarray:
        """Añade timestamp y progreso al frame de video"""
        img = frame.copy()

        # Barra de progreso
        progreso = frame_actual / frames_totales
        barra_ancho = 200
        barra_x = img.shape[1] - barra_ancho - 20
        barra_y = 20

        cv2.rectangle(img, (barra_x, barra_y), (barra_x + barra_ancho, barra_y + 15),
                      (50, 50, 50), -1)
        cv2.rectangle(img, (barra_x, barra_y),
                      (barra_x + int(barra_ancho * progreso), barra_y + 15),
                      (0, 255, 0), -1)

        # Texto de tiempo
        tiempo_actual = frame_actual / self.video_fps
        tiempo_total = frames_totales / self.video_fps
        cv2.putText(img, f"{tiempo_actual:.1f}s / {tiempo_total:.1f}s",
                    (barra_x, barra_y + 35), cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (255, 255, 255), 1)

        return img

    def _anadir_indicador_grabacion(self, frame: np.ndarray, frames: int) -> np.ndarray:
        """Añade indicador de grabación al frame"""
        img = frame.copy()

        # Círculo rojo parpadeante
        if (frames // 15) % 2 == 0:
            cv2.circle(img, (30, 30), 15, (0, 0, 255), -1)

        # Texto REC
        cv2.putText(img, "REC", (55, 40), cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (0, 0, 255), 2)

        # Tiempo de grabación
        tiempo = frames / self.video_fps
        cv2.putText(img, f"{tiempo:.1f}s", (110, 40), cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (255, 255, 255), 1)

        return img

    def esta_grabando(self) -> bool:
        """Verifica si hay una grabación en curso"""
        return self.grabando_video or self.video_ruta_activo

    def obtener_info_sesion(self) -> dict:
        """Obtiene información sobre la sesión actual"""
        carpeta_fotos = os.path.join(self.carpeta_fotos, self.session_id)
        carpeta_videos = os.path.join(self.carpeta_videos, self.session_id)

        fotos = []
        videos = []

        if os.path.exists(carpeta_fotos):
            fotos = [f for f in os.listdir(carpeta_fotos) if f.endswith('.jpg')]

        if os.path.exists(carpeta_videos):
            videos = [f for f in os.listdir(carpeta_videos) if f.endswith('.avi')]

        return {
            'session_id': self.session_id,
            'carpeta_fotos': carpeta_fotos,
            'carpeta_videos': carpeta_videos,
            'num_fotos': len(fotos),
            'num_videos': len(videos),
            'fotos': fotos,
            'videos': videos,
            'grabando': self.esta_grabando()
        }

    def __del__(self):
        """Destructor para asegurar que la cámara se cierra"""
        self.cerrar_camara()


# Funciones auxiliares para integración

def crear_comando_video_corto(duracion: int = 10, metadata: Optional[dict] = None) -> dict:
    """Crea un comando para grabar un video corto"""
    return {
        'action': 'video_corto',
        'type': 'video',
        'duracion': duracion,
        'metadata': metadata or {}
    }


def crear_comando_video_ruta(metadata: Optional[dict] = None) -> dict:
    """Crea un comando para iniciar video de ruta"""
    return {
        'action': 'video_ruta_inicio',
        'type': 'video',
        'metadata': metadata or {}
    }


def crear_comando_detener_video() -> dict:
    """Crea un comando para detener video de ruta"""
    return {
        'action': 'video_ruta_fin',
        'type': 'video'
    }
