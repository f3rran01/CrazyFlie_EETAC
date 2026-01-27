
#Módulo de Control por Voz para Crazyflie


import sounddevice as sd
from vosk import Model, KaldiRecognizer
import json
import queue
import re
from typing import Optional, Dict, List, Tuple
from pathlib import Path


# CONFIGURACIÓN


RUTAS_MODELO = [
    "../../vosk-model-small-es-0.42",
    "../vosk-model-small-es-0.42",
    "./vosk-model-small-es-0.42",
    "vosk-model-small-es-0.42"
]

# Mapeo de comandos de control
COMANDOS_CONTROL = {
    'conectar': ['conectar', 'conecta', 'conexión', 'conexion'],
    'armar': ['armar', 'arma', 'armado'],
    'despegar': ['despegar', 'despega', 'despegue', 'volar', 'vuela'],
    'aterrizar': ['aterrizar', 'aterriza', 'aterrizaje', 'aterrisa', 'bajar']
}

# Mapeo de patrones de vuelo
PATRONES = {
    'cuadrado': ['cuadrado', 'cuadrada'],
    'triangulo': ['triángulo', 'triangulo', 'triangular'],
    'circulo': ['círculo', 'circulo', 'circular'],
    'linea': ['línea', 'linea', 'recta']
}

# Mapeo de direcciones
DIRECCIONES = {
    'adelante': 'forward', 'recto': 'forward', 'frente': 'forward',
    'atrás': 'back', 'atras': 'back',
    'izquierda': 'left', 'derecha': 'right',
    'arriba': 'up', 'abajo': 'down'
}




class VoiceRecognitionSystem:
    """Sistema de reconocimiento de voz usando Vosk"""

    def __init__(self, model_path: Optional[str] = None):

        #Inicializa el sistema de reconocimiento de voz.

        self.samplerate = 16000
        self.model_path = model_path or self._buscar_modelo()

        if not self.model_path:
            raise FileNotFoundError(
                "No se encontró el modelo de Vosk. "
            )

        self._inicializar_modelo()
        self.audio_queue = queue.Queue()
        self.is_capturing = False
        self.stream = None

    def _inicializar_modelo(self):
        """Inicializa el modelo de Vosk"""
        try:

            self.model = Model(self.model_path)
            self.recognizer = KaldiRecognizer(self.model, self.samplerate)
            print("Sistema de voz inicializado")
        except Exception as e:
            raise RuntimeError(f"Error al inicializar Vosk: {e}")

    def _buscar_modelo(self) -> Optional[str]:
        """Busca el modelo de Vosk en rutas posibles"""
        # Buscar en rutas definidas
        for ruta in RUTAS_MODELO:
            path = Path(ruta).resolve()
            if path.exists():
                print(f"Modelo encontrado: {path}")
                return str(path)

        # Buscar en directorio del script
        script_dir = Path(__file__).parent
        for nombre in ["vosk-model-small-es-0.42", "vosk-model-es"]:
            for parent in [script_dir, script_dir.parent]:
                path = parent / nombre
                if path.exists():
                    print(f"Modelo encontrado: {path}")
                    return str(path)

        print("Modelo no encontrado")
        return None

    def _audio_callback(self, indata, frames, time, status):
        """Callback para procesar audio"""
        if status:
            print(f" Error de audio: {status}")
        if self.is_capturing:
            self.audio_queue.put(bytes(indata))

    def iniciar_captura(self):
        """Inicia captura de audio"""
        print("Grabando...")
        self.is_capturing = True
        try:
            self.stream = sd.InputStream(
                samplerate=self.samplerate,
                blocksize=8000,
                channels=1,
                dtype="int16",
                callback=self._audio_callback
            )
            self.stream.start()
        except Exception as e:
            self.is_capturing = False
            raise RuntimeError(f"Error al iniciar grabación: {e}")

    def detener_captura(self) -> str:
        #Detiene captura y retorna texto transcrito
        print("⏸Procesando...")
        self.is_capturing = False

        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        transcription = self._procesar_audio()
        self.audio_queue = queue.Queue()

        if transcription:
            print(f"Transcrito: '{transcription}'")
        else:
            print("No se detectó voz")

        return transcription

    def _procesar_audio(self) -> str:
        """Procesa el audio capturado y retorna el texto"""
        transcription = []

        while not self.audio_queue.empty():
            try:
                data = self.audio_queue.get()
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    if texto := result.get('text', '').strip():
                        transcription.append(texto)
            except Exception as e:
                print(f"Error procesando audio: {e}")

        # Resultado final
        try:
            final_result = json.loads(self.recognizer.FinalResult())
            if texto := final_result.get('text', '').strip():
                transcription.append(texto)
        except Exception as e:
            print(f"Error en resultado final: {e}")

        return ' '.join(transcription).strip()

    def cerrar(self):
        """Cierra el sistema de reconocimiento de voz"""
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        print("[Voz] Sistema cerrado")



# PROCESAMIENTO DE COMANDOS


def _detectar_comando_simple(texto: str, comandos: Dict[str, List[str]]) -> Optional[str]:
    """Detecta comandos simples basados en palabras clave"""
    for accion, palabras in comandos.items():
        if any(palabra in texto for palabra in palabras):
            return accion
    return None


def _extraer_numero(texto: str, patron: str, default: float, min_val: float, max_val: float) -> float:
    """Extrae y valida un número del texto"""
    if match := re.search(patron, texto):
        try:
            valor = float(match.group(1))
            return max(min_val, min(valor, max_val))
        except ValueError:
            pass
    return default


def procesar_comando_completo(texto: str) -> Optional[Dict]:
    #Procesa comandos de voz y retorna diccionario con tipo y parámetros.
    texto = texto.lower().strip()

    # COMANDOS DE CONTROL
    if accion := _detectar_comando_simple(texto, COMANDOS_CONTROL):
        print(f"Comando: {accion.upper()}")

        resultado = {'tipo': 'control', 'accion': accion}

        # Altura para despegue
        if accion == 'despegar':
            altura = _extraer_numero(texto, r'(\d+\.?\d*)\s*(?:metros?|m\b)', 0.5, 0.3, 2.0)
            resultado['altura'] = altura
            print(f"  Altura: {altura}m")

        return resultado

    # COMANDOS DE MISIÓN
    if 'ejecutar' in texto and any(palabra in texto for palabra in ['misión', 'mision', 'plan']):
        print("Comando: EJECUTAR MISIÓN")
        return {'tipo': 'mision', 'accion': 'ejecutar'}

    if any(palabra in texto for palabra in ['limpiar', 'borrar']) and \
            any(palabra in texto for palabra in ['misión', 'mision', 'plan']):
        print("Comando: LIMPIAR MISIÓN")
        return {'tipo': 'mision', 'accion': 'limpiar'}

    # COMANDOS DE PATRÓN
    if 'crear' in texto or 'patrón' in texto or 'patron' in texto:
        for patron_key, palabras in PATRONES.items():
            if any(palabra in texto for palabra in palabras):
                tamaño = _extraer_numero(texto, r'(\d+\.?\d*)\s*(?:metros?|m\b)', 2.0, 0.5, 3.0)
                print(f"Comando: PATRÓN {patron_key.upper()} ({tamaño}m)")
                return {
                    'tipo': 'patron',
                    'accion': 'crear',
                    'patron': patron_key,
                    'tamaño': tamaño
                }

    # COMANDOS DE MOVIMIENTO
    for palabra, direccion in DIRECCIONES.items():
        if palabra in texto:
            distancia = _extraer_numero(texto, r'(\d+\.?\d*)\s*(?:metros?|m\b)', 1.0, 0.1, 3.0)
            print(f"Comando: MOVER {direccion.upper()} ({distancia}m)")
            return {
                'tipo': 'movimiento',
                'accion': 'move',
                'direction': direccion,
                'distance': distancia
            }

    # COMANDOS DE ROTACIÓN
    if 'rota' in texto or 'gira' in texto:
        sentido = -1 if any(p in texto for p in ['izquierda', 'antihorario', 'anti horario']) else 1

        if match := re.search(r'(\d+)\s*grados?', texto):
            grados = int(match.group(1)) * sentido
        else:
            grados = 90 * sentido

        print(f"Comando: ROTAR {grados}°")
        return {
            'tipo': 'movimiento',
            'accion': 'rotate',
            'degrees': grados
        }

    print(f"Comando no reconocido: '{texto}'")
    return None


def procesar_comando_basico(texto: str) -> List[Dict]:
    if comando := procesar_comando_completo(texto):
        if comando['tipo'] == 'movimiento':
            return [{
                'action': comando['accion'],
                'direction': comando.get('direction'),
                'distance': comando.get('distance'),
                'degrees': comando.get('degrees')
            }]
    return []



# FUNCIONES DE UTILIDAD


def validar_comando(comando: Dict) -> Tuple[bool, str]:

    if not isinstance(comando, dict):
        return False, "El comando debe ser un diccionario"

    if 'tipo' not in comando:
        return False, "Falta el campo 'tipo'"

    if 'accion' not in comando:
        return False, "Falta el campo 'accion'"

    tipo = comando['tipo']

    if tipo == 'movimiento':
        if comando['accion'] == 'move' and 'direction' not in comando:
            return False, "Comando 'move' requiere 'direction'"
        if comando['accion'] == 'rotate' and 'degrees' not in comando:
            return False, "Comando 'rotate' requiere 'degrees'"

    return True, "OK"


def obtener_descripcion_comando(comando: Dict) -> str:

    tipo = comando.get('tipo', 'desconocido')
    accion = comando.get('accion', 'desconocida')

    if tipo == 'control':
        if accion == 'despegar':
            altura = comando.get('altura', 0.5)
            return f"Despegar a {altura}m"
        return f"Control: {accion}"

    elif tipo == 'movimiento':
        if accion == 'move':
            direccion = comando.get('direction', '?')
            distancia = comando.get('distance', 0)
            return f"Mover {direccion} {distancia}m"
        elif accion == 'rotate':
            grados = comando.get('degrees', 0)
            return f"Rotar {grados}°"

    elif tipo == 'patron':
        patron = comando.get('patron', '?')
        tamaño = comando.get('tamaño', 0)
        return f"Patrón {patron} de {tamaño}m"

    elif tipo == 'mision':
        return f"Misión: {accion}"

    return f"{tipo}: {accion}"
