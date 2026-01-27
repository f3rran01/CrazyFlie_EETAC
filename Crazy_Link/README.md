# CrazyLink - Biblioteca de Control para Drones Crazyflie

CrazyLink es una biblioteca completa diseñada para facilitar el desarrollo de aplicaciones de control para el dron Crazyflie. 
## Descripción

CrazyLink proporciona una interfaz de alto nivel para controlar el dron Crazyflie 2.1. La biblioteca está inspirada en DroneLink y ha sido extendida con múltiples funcionalidades avanzadas para aplicaciones de investigación y neurorehabilitation.



---

## Índice

- [Inicio Rápido](#-inicio-rápido)
- [Características Principales](#-características-principales)
- [Instalación](#-instalación)
- [Uso Básico](#-uso-básico)
- [Funcionalidades Avanzadas](#-funcionalidades-avanzadas)
- [Demostradores](#-demostradores)
- [API Reference](#-api-reference)
- [Configuración del Hardware](#-configuración-del-hardware)
- [Videos](#-videos)

---

##  Inicio Rápido

### Versión Ejecutable (Recomendado)

**NUEVO:** Ahora puedes ejecutar el Dashboard de CrazyLink sin necesidad de instalar Python o dependencias.

#### Opción 1: Usar el Ejecutable Pre-compilado

1. Navega a la carpeta `dist/`
2. Ejecuta:
   - **Windows:** Doble click en `CrazyLink_Dashboard.exe`
   - **Linux/Mac:** `./CrazyLink_Dashboard`

#### Opción 2: Compilar tu Propio Ejecutable

**Windows:**
```cmd
build_executable.bat
```

**Linux/Mac:**
```bash
chmod +x build_executable.sh
./build_executable.sh
```
---

##  Características Principales

###  Sistema de Cámara
- **Captura de Fotos:** Fotos con geotag automático (X, Y, Z)
- **Grabación de Videos:** Videos cortos y videos de ruta completa
- **Galería de Fotos:** Visualización interactiva con metadatos
- **Organización Automática:** Carpetas por sesión con timestamps

###  Pathfinding y Evitación de Obstáculos
- **Algoritmo A*:** Planificación de rutas óptimas
- **Detección de Obstáculos:** Obstáculos poligonales configurables
- **Validación de Misiones:** Detección automática de conflictos
- **Margen de Seguridad:** Buffer configurable alrededor de obstáculos

###  Planificación de Vuelo
- **Misiones Predefinidas:** Cuadrado, triángulo, círculo, línea
- **Waypoints Personalizados:** Absolutos y relativos
- **Acciones por Waypoint:**
  - Captura de fotos
  - Grabación de videos
  - Rotaciones del dron
  - Pausas configurables
- **Análisis de Misión:** Cálculo de distancia y tiempo estimado

###  Control por Voz
- **Reconocimiento Offline:** Sistema Vosk en español
- **Comandos de Control:** Conectar, armar, despegar, aterrizar
- **Movimientos por Voz:** Adelante, atrás, izquierda, derecha, arriba, abajo
- **Patrones por Voz:** Cuadrado, triángulo, círculo con tamaño configurable
- **Rotaciones:** Especifica grados y dirección por voz

###  Control por Joystick
- **Soporte Multi-Mando:** USB Gamepad, Generic USB Joystick, Twin USB Joystick
- **Control Total:** Todo desde el mando sin tocar la interfaz
- **Mapeo Configurable:** Ejes y botones personalizables
- **Vuelo Libre:** Activación automática al despegar

###  Visualización de Telemetría
- **Telemetría en Tiempo Real:** Posición, velocidad, actitud, batería
- **Visualización 2D:** Trayecto con estela del dron
- **Gráficos Interactivos:** Zoom automático y cuadrícula de referencia
- **Múltiples Sensores:** Flow deck, Multi-ranger, estimador de posición

###  Geofencing (Protección de Área)
- **Geofence Simple:** Áreas rectangulares/cuadradas
- **Geofence Complejo:** Múltiples polígonos con exclusiones
- **Límites de Altitud:** Mínimo y máximo configurables
- **Buffer de Seguridad:** Zona de transición entre área segura y restringida
- **Editor Visual:** Crea y edita geocages interactivamente

###  Interfaces Gráficas
- **Dashboard Directo:** Control simple en tiempo real
- **Dashboard Plot:** Control avanzado con visualización 2D
- **Vuelo Libre Joystick:** Control 100% por mando con visualización
- **Planificador de Misiones:** Editor interactivo de waypoints
- **Geocage Creator:** Editor visual de áreas de vuelo

---


---

##  Instalación

### Requisitos Previos

- **Python 3.10 o superior**
- **Crazyradio PA o Crazyradio 2.0** (hardware requerido)
- **Dron Crazyflie 2.x** con Flow v2 deck y Multi-ranger deck

### Dependencias de Python

```bash
pip install cflib==0.1.27
pip install shapely==2.1.1
pip install matplotlib==3.9.3
pip install tkintermapview==1.29
pip install ttkbootstrap==1.10.1
pip install customtkinter==5.2.2
pip install numpy==1.26.4
pip install scipy==1.14.1
pip install pygame  # Para control por joystick
pip install opencv-python  # Para cámara
pip install sounddevice  # Para control por voz
pip install vosk  # Para reconocimiento de voz
```

### Instalación del Cliente Crazyflie (cfclient)

**Windows:**
```cmd
pip3 install cfclient
```

**Linux/Mac:**
```bash
pip3 install cfclient
```

Para verificar la instalación:
```bash
cfclient
```

---

##  Uso Básico

### Ejemplo Simple

```python
import time
from crazyLink.Dron_crazyflie import Dron

# Crear objeto dron
dron = Dron()

# Conectar al dron
dron.connect()
print('Conectado')

# Armar el dron
dron.arm()
print('Armado')

# Despegar a 0.7 metros
dron.takeOff(0.7)
time.sleep(5)

# Moverse hacia adelante
dron.go('Forward')
time.sleep(1)

# Cambiar altitud a 0.5 metros
dron.change_altitude(0.5)

# Moverse a la derecha
dron.go('Right')
time.sleep(2)

# Aterrizar
dron.Land()
print('En tierra')

# Desconectar
dron.disconnect()
```

### Ejemplo con Waypoints

```python
from crazyLink.Dron_crazyflie import Dron

dron = Dron()
dron.connect()
dron.arm()
dron.takeOff(0.7)

# Ir a coordenadas específicas (x, y, z) en metros
dron.goto(1.0, 0.5, 0.7)  # x=1m, y=0.5m, z=0.7m
dron.goto(1.0, 1.0, 0.7)
dron.goto(0.0, 1.0, 0.7)
dron.goto(0.0, 0.0, 0.7)  # Volver al origen

dron.Land()
dron.disconnect()
```

### Ejemplo con Cámara

```python
from crazyLink.Dron_crazyflie import Dron
from crazyLink.modules_crazyflie.dron_camera import DroneCamera

dron = Dron()
camera = DroneCamera(dron, camera_id=0)

dron.connect()
dron.arm()
dron.takeOff(0.7)

# Capturar una foto
camera.take_photo()

# Iniciar grabación de video corto (10 segundos)
camera.start_short_video(duration=10)

# O iniciar video de ruta (hasta que se detenga manualmente)
camera.start_route_video()
dron.goto(1.0, 1.0, 0.7)
camera.stop_route_video()

dron.Land()
dron.disconnect()

# Obtener información de la sesión
session_info = camera.get_session_info()
print(f"Fotos capturadas: {session_info['photo_count']}")
print(f"Videos grabados: {session_info['video_count']}")
```

---

##  Funcionalidades Avanzadas

### 1. Planificación de Vuelo con Pathfinding

```python
from crazyLink.Dron_crazyflie import Dron
from crazyLink.modules_crazyflie.dron_pathfinding import PlanificadorRuta
from shapely.geometry import Polygon

dron = Dron()
dron.connect()

# Definir geocage (área de vuelo)
geocage = Polygon([(-2, -2), (2, -2), (2, 2), (-2, 2)])

# Definir obstáculos
obstaculo1 = Polygon([(0.5, 0.5), (1.5, 0.5), (1.5, 1.5), (0.5, 1.5)])
obstaculos = [obstaculo1]

# Crear planificador
planificador = PlanificadorRuta(geocage, obstaculos)

# Planificar ruta desde origen a destino
origen = (0, 0, 0.7)
destino = (1.8, 1.8, 0.7)
camino = planificador.planificar_ruta(origen, destino, altura=0.7)

if camino:
    print(f"Ruta encontrada con {len(camino)} waypoints")

    dron.arm()
    dron.takeOff(0.7)

    # Ejecutar ruta
    for waypoint in camino:
        dron.goto(waypoint[0], waypoint[1], waypoint[2])

    dron.Land()
else:
    print("No se encontró ruta válida")

dron.disconnect()
```

### 2. Control por Voz

```python
from crazyLink.Dron_crazyflie import Dron
from crazyLink.modules_crazyflie.dron_voz import DroneVoiceController

dron = Dron()
voice_controller = DroneVoiceController(dron)

# Iniciar reconocimiento de voz
voice_controller.start_listening()

# Comandos disponibles por voz:
# - "conectar" o "conexión"
# - "armar" o "armado"
# - "despegar" o "despegar a X metros"
# - "adelante X metros" (o "atrás", "izquierda", "derecha", "arriba", "abajo")
# - "girar X grados" (o "girar X grados horario/antihorario")
# - "cuadrado de X metros" (o "triángulo", "círculo", "línea")
# - "aterrizar" o "aterrizaje"

# El sistema escuchará y ejecutará comandos automáticamente
# Presiona 'q' para salir

voice_controller.stop_listening()
```

### 3. Misión Interactiva con Acciones

```python
from crazyLink.Dron_crazyflie import Dron
from crazyLink.modules_crazyflie.dron_camera import DroneCamera

dron = Dron()
camera = DroneCamera(dron)

# Definir misión con acciones por waypoint
mission = [
    {
        'waypoint': (1.0, 0.0, 0.7),
        'action': 'photo',
        'pause': 2.0
    },
    {
        'waypoint': (1.0, 1.0, 0.7),
        'action': 'short_video',
        'duration': 5,
        'pause': 1.0
    },
    {
        'waypoint': (0.0, 1.0, 0.7),
        'action': 'rotate',
        'degrees': 90,
        'pause': 2.0
    },
    {
        'waypoint': (0.0, 0.0, 0.7),
        'action': None,
        'pause': 1.0
    }
]

dron.connect()
dron.arm()
dron.takeOff(0.7)

# Ejecutar misión
for step in mission:
    # Ir al waypoint
    dron.goto(step['waypoint'][0], step['waypoint'][1], step['waypoint'][2])

    # Ejecutar acción
    if step['action'] == 'photo':
        camera.take_photo()
    elif step['action'] == 'short_video':
        camera.start_short_video(duration=step.get('duration', 10))
    elif step['action'] == 'rotate':
        dron.changeHeading(step['degrees'])

    # Pausa después de la acción
    if step['pause']:
        time.sleep(step['pause'])

dron.Land()
dron.disconnect()
```

### 4. Geofencing Complejo

```python
from crazyLink.Dron_crazyflie import Dron
from shapely.geometry import Polygon

dron = Dron()
dron.connect()

# Definir área de vuelo permitida (polígono exterior)
area_permitida = [(-2, -2), (2, -2), (2, 2), (-2, 2)]

# Definir zonas de exclusión (obstáculos internos)
zona_exclusion1 = [(0.5, 0.5), (1.0, 0.5), (1.0, 1.0), (0.5, 1.0)]
zona_exclusion2 = [(-1.0, -1.0), (-0.5, -1.0), (-0.5, -0.5), (-1.0, -0.5)]

exclusiones = [zona_exclusion1, zona_exclusion2]

# Activar geofence complejo
dron.setComplexScenario(
    inside_polygon=area_permitida,
    exclusion=exclusiones,
    type='complex',
    watchdog=True
)

# El dron ahora evitará automáticamente las zonas de exclusión
dron.arm()
dron.takeOff(0.7)

# Si el dron intenta entrar en zona prohibida, será redirigido automáticamente
dron.goto(0.7, 0.7, 0.7)  # Intentaría entrar en exclusion1, será bloqueado

dron.Land()
dron.deleteComplexScenario()
dron.disconnect()
```

### 5. Control por Joystick Programático

```python
from crazyLink.Dron_crazyflie import Dron
from crazyLink.modules_crazyflie.Joystick import Joystick

dron = Dron()
dron.connect()

# Inicializar joystick (índice 0 = primer joystick conectado)
joystick = Joystick(joystick_index=0, dron=dron, identificar="MiJoystick")

# Conectar joystick
if joystick.connect_joystick():
    print("Joystick conectado")

    dron.arm()
    dron.takeOff(0.7)

    # Activar control por joystick
    joystick.start_control()

    # El dron ahora responde a los ejes del joystick
    # Presiona botón 2 para aterrizar desde el joystick

    input("Presiona Enter para detener el control por joystick...")

    joystick.stop_control()
    dron.Land()
else:
    print("No se pudo conectar el joystick")

dron.disconnect()
```

---

##  Demostradores

###1. Vuelo Libre con Joystick

```bash
cd Crazy_Link/demostradores_crazyflie
python vuelo_libre_joystick.py
```

**Funcionalidades:**
- Control 100% desde el mando
- Un solo botón para conectar mando y dron
- Vuelo libre automático al despegar
- Visualización del trayecto en tiempo real
- Indicadores de estado en pantalla

**Controles:**
- **SELECT (Botón 8):** Armar
- **START (Botón 9):** Despegar (activa vuelo libre automáticamente)
- **Botón 2:** Aterrizar (desactiva vuelo libre automáticamente)
- **Joystick izquierdo:** Altura
- **Joystick derecho:** Movimiento (adelante/atrás/izquierda/derecha)

Para más detalles, consulta [README_VUELO_LIBRE.md](demostradores_crazyflie/README_VUELO_LIBRE.md)

### 2. Planificador de Misiones

```bash
cd Crazy_Link/demostradores_crazyflie
python Demo_plan_de_vuelo.py
```

**Funcionalidades:**
- Creación interactiva de waypoints
- Configuración de acciones por waypoint (fotos, videos, rotaciones)
- Análisis de misión (distancia, tiempo estimado)
- Previsualización del plan de vuelo
- Exportar/importar misiones

### 3. Geocage Creator con Obstáculos

```bash
cd Crazy_Link/demostradores_crazyflie
python geocage_creator_con_obstaculos.py
```

**Funcionalidades:**
- Dibuja polígonos de área de vuelo
- Añade obstáculos interactivamente
- Valida geometría automáticamente
- Exporta configuración para uso en código
- Visualización gráfica del geocage

### 4. Control por Voz

```bash
cd Crazy_Link/demostradores_crazyflie
python voz_crazyflie.py
```

**Funcionalidades:**
- Reconocimiento de voz en tiempo real
- Comandos en español
- Feedback visual de comandos reconocidos
- No requiere conexión a internet

### 5. Pathfinding con Obstáculos

```bash
cd Crazy_Link/demostradores_crazyflie
python pathfinding_obstaculos.py
```

**Funcionalidades:**
- Demostración visual del algoritmo A*
- Definición de obstáculos
- Cálculo de ruta óptima
- Visualización del camino calculado
- Ejecución del vuelo siguiendo la ruta

---

##  API Reference

### Funciones de Inicio

#### `connect(freq=4, cf_uri="radio://0/80/2M/E7E7E7E7E7")`
Conecta al dron Crazyflie.

**Parámetros:**
- `freq` (int): Frecuencia de actualización de telemetría (Hz)
- `cf_uri` (str): URI de conexión del Crazyradio

**Ejemplo:**
```python
dron.connect(freq=10)  # Actualización a 10 Hz
```

#### `arm(blocking=True, callback=None, params=None)`
Arma el dron para prepararlo para el vuelo.

**Parámetros:**
- `blocking` (bool): Si True, espera a que complete
- `callback` (function): Función a llamar al completar
- `params` (dict): Parámetros adicionales para el callback

#### `takeOff(aTargetAltitude, blocking=True, callback=None, params=None)`
Despega a la altitud especificada.

**Parámetros:**
- `aTargetAltitude` (float): Altitud objetivo en metros
- `blocking` (bool): Si True, espera a que complete
- `callback` (function): Función a llamar al completar
- `params` (dict): Parámetros adicionales

**Ejemplo:**
```python
dron.takeOff(0.7)  # Despega a 0.7 metros
```

#### `Land(blocking=True, callback=None, params=None)`
Aterriza el dron.

#### `RTL(blocking=True, callback=None, params=None)`
Return to Launch - vuelve al punto de despegue y aterriza.

### Funciones de Movimiento

#### `goto(transversal, lateral, alt, blocking=True, callback=None, params=None)`
Mueve el dron a una coordenada específica.

**Parámetros:**
- `transversal` (float): Coordenada X en metros
- `lateral` (float): Coordenada Y en metros
- `alt` (float): Altitud Z en metros
- `blocking` (bool): Si True, espera a que complete

**Ejemplo:**
```python
dron.goto(1.0, 0.5, 0.7)  # x=1m, y=0.5m, z=0.7m
```

#### `move_distance(direction, distance, blocking=True, callback=None, params=None)`
Mueve el dron una distancia específica en una dirección.

**Parámetros:**
- `direction` (str): 'Forward', 'Backward', 'Left', 'Right', 'Up', 'Down'
- `distance` (float): Distancia en metros
- `blocking` (bool): Si True, espera a que complete

**Ejemplo:**
```python
dron.move_distance('Forward', 1.5)  # Avanza 1.5 metros
```

#### `go(direction, blocking=True)`
Inicia movimiento continuo en una dirección.

**Parámetros:**
- `direction` (str): 'Forward', 'Backward', 'Left', 'Right', 'Up', 'Down', 'Stop'

**Nota:** Para detener el movimiento, usa `dron.go('Stop')`

#### `change_altitude(altitude, blocking=True, callback=None, params=None)`
Cambia la altitud del dron.

**Parámetros:**
- `altitude` (float): Nueva altitud en metros

#### `changeHeading(absoluteDegrees, blocking=True, callback=None, params=None)`
Rota el dron a una orientación específica.

**Parámetros:**
- `absoluteDegrees` (float): Ángulo en grados (0-360)

**Ejemplo:**
```python
dron.changeHeading(90)  # Rota hacia el este
```

#### `setMoveSpeed(speed)`
Configura la velocidad de movimiento del dron.

**Parámetros:**
- `speed` (float): Velocidad en m/s (recomendado: 0.1-0.5)

#### `changeNavSpeed(speed)`
Configura la velocidad de navegación.

**Parámetros:**
- `speed` (float): Velocidad en m/s

#### `send_rc(roll, pitch, throttle, yaw, blocking=True, bare_mode=False, velocity_horizontal=0.3, velocity_vertical=0.2, yaw_velo=20)`
Envía comandos RC directos al dron.

**Parámetros:**
- `roll` (int): Valor RC para roll (1000-2000)
- `pitch` (int): Valor RC para pitch (1000-2000)
- `throttle` (int): Valor RC para throttle (1000-2000)
- `yaw` (int): Valor RC para yaw (1000-2000)
- `bare_mode` (bool): Si True, usa valores raw
- `velocity_horizontal` (float): Velocidad horizontal máxima (m/s)
- `velocity_vertical` (float): Velocidad vertical máxima (m/s)
- `yaw_velo` (float): Velocidad de rotación (grados/s)

### Funciones de Geofencing

#### `setSimpleScenario(scenario, type=None, blocking=True, callback=None, params=None, watchdog=True)`
Configura un geofence simple (rectangular/cuadrado).

**Parámetros:**
- `scenario` (list): Lista de coordenadas del polígono [(x1,y1), (x2,y2), ...]
- `type` (str): Tipo de geofence ('simple')
- `watchdog` (bool): Si True, monitorea constantemente

**Ejemplo:**
```python
area = [(-1, -1), (1, -1), (1, 1), (-1, 1)]  # Cuadrado de 2x2 metros
dron.setSimpleScenario(area, watchdog=True)
```

#### `deleteSimpleScenario()`
Elimina el geofence simple activo.

#### `setComplexScenario(inside_polygon, exclusion, type=None, blocking=True, callback=None, params=None, watchdog=True)`
Configura un geofence complejo con zonas de exclusión.

**Parámetros:**
- `inside_polygon` (list): Polígono del área permitida
- `exclusion` (list): Lista de polígonos de zonas prohibidas
- `watchdog` (bool): Si True, monitorea constantemente

**Ejemplo:**
```python
area_permitida = [(-2, -2), (2, -2), (2, 2), (-2, 2)]
exclusion1 = [(0.5, 0.5), (1, 0.5), (1, 1), (0.5, 1)]
dron.setComplexScenario(area_permitida, [exclusion1], watchdog=True)
```

#### `deleteComplexScenario()`
Elimina el geofence complejo activo.

#### `startBottomGeofence(minAlt, callback=None, params=None)`
Activa un límite inferior de altitud.

**Parámetros:**
- `minAlt` (float): Altitud mínima en metros

#### `stopBottomGeofence()`
Desactiva el límite inferior.

#### `startTopGeofence(maxAlt, callback=None, params=None)`
Activa un límite superior de altitud.

**Parámetros:**
- `maxAlt` (float): Altitud máxima en metros

#### `stopTopGeofence()`
Desactiva el límite superior.

### Funciones de Telemetría

#### `send_local_telemetry_info(process_local_telemetry_info)`
Activa el envío de telemetría básica.

**Parámetros:**
- `process_local_telemetry_info` (function): Función callback que recibe los datos

**Ejemplo:**
```python
def procesar_telemetria(telemetry_info):
    print(f"Posición: {telemetry_info['position']}")
    print(f"Velocidad: {telemetry_info['velocity']}")
    print(f"Batería: {telemetry_info['battery']} V")

dron.send_local_telemetry_info(procesar_telemetria)
```

**Datos en `telemetry_info`:**
- `position`: [x, y, z] en metros
- `velocity`: [vx, vy, vz] en m/s
- `attitude`: [roll, pitch, yaw] en grados
- `battery`: Voltaje en voltios
- `state`: Estado del dron ('connected', 'armed', 'flying', etc.)

#### `stop_sending_local_telemetry_info()`
Detiene el envío de telemetría básica.

#### `getParams(parameters, process_params=None)`
Obtiene parámetros personalizados del dron.

**Parámetros:**
- `parameters` (list): Lista de nombres de parámetros a obtener
- `process_params` (function): Función callback para procesar

**Ejemplo:**
```python
params = ['stateEstimate.x', 'stateEstimate.y', 'stateEstimate.z', 'pm.vbat']

def procesar_params(params_data):
    print(f"Parámetros: {params_data}")

dron.getParams(params, procesar_params)
```

#### `stop_sending_params()`
Detiene el envío de parámetros personalizados.

### Propiedades del Dron

#### `dron.position`
Posición actual del dron [x, y, z] en metros.

#### `dron.velocity`
Velocidad actual [vx, vy, vz] en m/s.

#### `dron.battery_level`
Nivel de batería (voltaje).

#### `dron.state`
Estado actual del dron:
- `"disconnected"`: Desconectado
- `"connected"`: Conectado
- `"arming"`: Armando
- `"armed"`: Armado
- `"takingOff"`: Despegando
- `"flying"`: Volando
- `"returning"`: Regresando (RTL)
- `"landing"`: Aterrizando

#### `dron.flightMode`
Modo de vuelo actual (no implementado completamente).

---

##  Configuración del Hardware

### Crazyradio Setup

#### Crazyradio PA

1. **Instalación de drivers (Windows):**
   - Mismos pasos que Crazyradio 2.0 usando Zadig
   - Selecciona "libusb-win32" o "libusb"
   - Instala el driver

**Linux/Mac:**
No se requiere instalación de drivers adicionales.

### Actualización del Firmware del Crazyflie

**IMPORTANTE:** Conecta todos los decks (Flow v2, Multi-ranger) ANTES de actualizar el firmware.

1. Abre cfclient:
   ```bash
   cfclient
   ```

2. Ve a **Connect → Bootloader**

3. Enciende el Crazyflie y conéctalo

4. En "From release", selecciona la última versión de firmware para **cf2** (Crazyflie 2.x)
   - Si no aparece, descarga desde: https://github.com/bitcraze/crazyflie-release/releases
   - Usa "From file" para cargar el firmware descargado

5. Haz click en **"Program"** y espera

6. El dron se reiniciará varias veces automáticamente (NO lo toques)

7. Cuando la barra azul se complete, la actualización está completa

### Verificación de la Conexión

1. Enciende el Crazyflie

2. Conecta el Crazyradio al ordenador

3. Abre cfclient:
   ```bash
   cfclient
   ```

4. Haz click en **"Scan"** en la esquina superior izquierda

5. Selecciona el dron detectado

6. Haz click en **"Connect"**

7. Si conecta correctamente, verás:
   - Telemetría en tiempo real
   - Estado del dron
   - Nivel de batería

---


---

##  Solución de Problemas

### El dron no conecta

**Verificaciones:**
1. ¿Está el dron encendido? (luz azul parpadeando)
2. ¿Está el Crazyradio conectado al USB?
3. ¿Están instalados los drivers de Crazyradio? (Windows)
4. ¿Funciona la conexión con cfclient?

**Soluciones:**
- Reinicia el dron y el ordenador
- Reinstala los drivers con Zadig (Windows)
- Verifica que no haya otros programas usando el Crazyradio
- Prueba con otro puerto USB

### El dron se desconecta durante el vuelo

**Posibles causas:**
- Batería baja (< 3.5V)
- Demasiada distancia del Crazyradio (máximo 20 metros)
- Interferencias de radio (WiFi, Bluetooth)

**Soluciones:**
- Carga la batería completamente
- Mantén el dron cerca del Crazyradio
- Apaga dispositivos que causen interferencias

### El dron no despega

**Verificaciones:**
1. ¿Está armado el dron? (`dron.arm()`)
2. ¿Tiene batería suficiente? (> 3.7V)
3. ¿Están los motores funcionando?

**Soluciones:**
- Verifica que llamaste a `dron.arm()` antes de `dron.takeOff()`
- Carga la batería
- Calibra el dron en cfclient

### El Flow Deck no funciona

**Verificaciones:**
1. ¿Hay suficiente luz en el área de vuelo?
2. ¿Hay textura en el suelo? (no superficies lisas/brillantes)
3. ¿Está el Flow Deck correctamente instalado?

**Soluciones:**
- Vuela en área bien iluminada
- Usa superficie con textura (alfombra, suelo con diseño)
- Mantén altura entre 0.3m y 2m

### El joystick no se detecta

**Verificaciones:**
1. ¿Está pygame instalado? (`pip install pygame`)
2. ¿Está el joystick conectado antes de ejecutar el script?
3. ¿Funciona el joystick en otros programas?

**Soluciones:**
```bash
# Test de detección de joystick
cd Crazy_Link/crazyLink/tests_crazyflie
python "test_joystick base.py"
```

### El reconocimiento de voz no funciona

**Verificaciones:**
1. ¿Está vosk instalado? (`pip install vosk`)
2. ¿Existe la carpeta `vosk-model-small-es-0.42/`?
3. ¿Está el micrófono conectado y funcionando?

**Soluciones:**
- Descarga el modelo: https://alphacephei.com/vosk/models
- Coloca el modelo en la carpeta del proyecto
- Verifica permisos del micrófono en el sistema

### Error de cámara "Cannot open camera"

**Verificaciones:**
1. ¿Está la cámara conectada?
2. ¿Está siendo usada por otro programa?
3. ¿Está opencv-python instalado?

**Soluciones:**
```bash
pip install opencv-python
```
- Cierra otros programas que usen la cámara (Zoom, Teams, etc.)
- Prueba con otro índice de cámara: `DroneCamera(dron, camera_id=1)`

---

---

##  Referencias

- **Crazyflie Documentation:** https://www.bitcraze.io/documentation/
- **cflib GitHub:** https://github.com/bitcraze/crazyflie-lib-python
- **Vosk Models:** https://alphacephei.com/vosk/models
- **Shapely Documentation:** https://shapely.readthedocs.io/

---

**Versión:** 2.0 - Enero 2026

**Estado:** Proyecto Completo - Versión Final
