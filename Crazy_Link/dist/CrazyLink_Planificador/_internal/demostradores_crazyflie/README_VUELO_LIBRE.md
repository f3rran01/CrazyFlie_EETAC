# 🎮 Sistema de Vuelo Libre con Joystick - Control Total por Mando

Sistema completo de control del dron Crazyflie mediante joystick con visualización en tiempo real del trayecto.

**⚡ CONTROL TOTAL DESDE EL MANDO - Sin necesidad de tocar la interfaz ⚡**

## 📋 Características

- **Control 100% desde el Mando**: Todo se controla con los botones del joystick
- **Conexión Simplificada**: Un solo botón conecta mando y dron
- **Vuelo Libre Automático**: Se activa automáticamente al despegar
- **Visualización en Tiempo Real**: Ve el movimiento del dron en un mapa 2D con estela roja
- **Indicadores de Estado**: La interfaz muestra el estado de todos los sistemas
- **Telemetría en Vivo**: Muestra posición y batería del dron en tiempo real

## 🎯 Archivos del Sistema

### Archivos Principales

1. **vuelo_libre_joystick.py** - Demostrador principal con interfaz gráfica
2. **Joystick.py** - Clase de control del joystick (en `modules_crazyflie/`)
3. **test_joystick.py** - Script de prueba del joystick con el dron (sin interfaz)
4. **test_joystick base.py** - Script para verificar que los botones funcionan

### Archivos de Soporte

- **visualizador_trayecto_dron.py** - Visualizador del mapa con la estela
- **Dron_crazyflie.py** - Clase principal del dron

## 🚀 Instalación

### Requisitos

```bash
pip install pygame
pip install shapely
pip install cflib
```

### Joysticks Compatibles

El sistema detecta automáticamente los siguientes mandos:
- **USB Gamepad** (cable)
- **Generic USB Joystick** (cable)
- **Twin USB Joystick** (inalámbrico)

## 📖 Cómo Usar - NUEVO FLUJO SIMPLIFICADO

### 1. Ejecutar el Sistema

```bash
cd Crazy_Link/demostradores_crazyflie
python vuelo_libre_joystick.py
```

### 2. Secuencia de Operación (MUY SIMPLE)

#### ✅ Paso 1: Conectar el Mando por USB
Conecta físicamente el mando al ordenador

#### ✅ Paso 2: Click en "CONECTAR MANDO Y DRON" (único botón en la interfaz)
- Se conectará automáticamente el dron
- Se conectará automáticamente el mando
- Se iniciará la telemetría
- Verás todos los indicadores en verde ✅

#### ✅ Paso 3: Usar el MANDO para todo lo demás

**🔘 Botón SELECT (Botón 8)**
- Presiona para **ARMAR** el dron
- Verás: ✅ Armado: SÍ

**🔘 Botón START (Botón 9)**
- Presiona para **DESPEGAR** (sube a 1 metro)
- Verás: ✅ Vuelo: EN EL AIRE
- **El vuelo libre se activa AUTOMÁTICAMENTE** ✨

**🕹️ Controlar el dron libremente**
- Joystick izquierdo: Altura
- Joystick derecho: Movimiento (adelante/atrás/izquierda/derecha)
- El mapa muestra el trayecto en tiempo real 🗺️

**🔘 Botón 2**
- Presiona para **ATERRIZAR**
- El vuelo libre se desactiva automáticamente

### ¡ASÍ DE SIMPLE!

No necesitas tocar ningún otro botón de la interfaz. Todo se controla desde el mando.

## 🎮 Controles Completos del Mando

### Botones de Control

| Botón | Función | Descripción |
|-------|---------|-------------|
| **SELECT (8)** | 🔐 Armar | Arma el dron para vuelo |
| **START (9)** | 🚀 Despegar | Despega a 1 metro de altura |
| **Botón 2** | 🛬 Aterrizar | Aterriza el dron |
| **Botón 0** | 🏠 RTL | Return to Launch (vuelve al origen) |
| **Botón 1** | 🎯 Modo GUIDED | Cambia a modo control automático |
| **Botón 3** | 🎮 Modo LOITER | Cambia a modo control manual |
| **Botón 4** | 🆔 Identificar | Identifica el joystick en los logs |

### Joysticks (Palancas)

**🕹️ Joystick IZQUIERDO**
- **Arriba**: Subir altura
- **Abajo**: Bajar altura
- **Centro**: Mantener altura actual

**🕹️ Joystick DERECHO**
- **Arriba**: Adelante
- **Abajo**: Atrás
- **Izquierda**: Movimiento lateral izquierda (+ rotación)
- **Derecha**: Movimiento lateral derecha (+ rotación)

## 📊 Interfaz Gráfica - Panel de Información

La interfaz **NO tiene botones** (excepto el de conexión inicial). Solo muestra información:

### Indicadores de Estado

- **❌/✅ Mando**: Conectado/Desconectado
- **❌/✅ Dron**: Conectado/Desconectado
- **⚪/✅ Armado**: No armado / Armado
- **⚪/✅ Vuelo**: En tierra / EN EL AIRE
- **⚪/✅ Vuelo Libre**: Inactivo / ACTIVO
- **Modo**: GUIDED / LOITER

### Telemetría en Vivo

- **Posición (X, Y, Z)**: Coordenadas del dron en metros
- **Batería**: Nivel de carga en porcentaje

### 🗺️ Visualizador de Trayecto

El mapa en el lado derecho muestra:

- **Ejes**: X (rojo) e Y (verde)
- **Cuadrícula**: Cada cuadrado = 0.5 metros
- **Dron**: Círculo azul con cruz blanca
- **Trayecto**: Línea roja que marca el camino recorrido
- **Área de vuelo**: 4m × 4m

**Botones del mapa:**
- **🗑 Limpiar Trayecto**: Borra la estela roja (sin afectar el vuelo)

## ⚠️ Mensajes de Error

### "Mando no conectado"
Conecta físicamente el mando por USB antes de hacer click en el botón de conexión.

### "Error de conexión al dron"
- Verifica que el dron esté encendido
- Verifica que esté en rango de conexión
- Revisa los logs para más detalles

## 🔧 Modo de Prueba Sin Interfaz

Si prefieres un control más directo sin interfaz gráfica:

```bash
cd Crazy_Link/crazyLink/tests_crazyflie
python test_joystick.py
```

Este modo:
- Conecta automáticamente al dron
- Inicia el control por joystick inmediatamente
- Presiona 'P' para terminar

## 🏗️ Arquitectura del Sistema

```
vuelo_libre_joystick.py (Interfaz)
    │
    ├─> JoystickExtendido (Control del mando + callbacks)
    │   └─> pygame (Lectura de ejes y botones)
    │   └─> Callbacks para actualizar interfaz
    │
    ├─> Dron_crazyflie.py (Control del dron)
    │   └─> Módulos de control (nav, goto, RC, etc.)
    │   └─> Monitoreo de estado (armed, flying, etc.)
    │
    └─> VisualizadorTrayecto3D (Mapa)
        └─> tkinter Canvas (Renderizado)
        └─> Actualización en tiempo real del trayecto
```

## 🔄 Flujo de Estados del Sistema

```
1. DESCONECTADO
   ↓ [Click en "Conectar Mando y Dron"]

2. CONECTADO (Dron + Mando)
   ↓ [Presionar SELECT en el mando]

3. ARMADO
   ↓ [Presionar START en el mando]

4. DESPEGANDO
   ↓ [Automático]

5. EN EL AIRE + VUELO LIBRE ACTIVO ✅
   ↓ [Controlar con joysticks libremente]
   ↓ [El mapa se actualiza en tiempo real]
   ↓ [Presionar Botón 2 en el mando]

6. ATERRIZANDO
   ↓ [Automático]

7. EN TIERRA (Vuelo libre desactivado)
   ↓ [Repetir desde paso 3 si quieres volar de nuevo]
```

## 🐛 Solución de Problemas

### El dron no responde al mando
1. Verifica que el vuelo libre esté **ACTIVO** (indicador verde en la interfaz)
2. Asegúrate de que el dron esté en modo **LOITER** (mira el indicador "Modo:")
3. Revisa los logs en la consola para ver los valores de los ejes

### La estela no se dibuja en el mapa
1. Verifica que la telemetría esté funcionando (panel muestra posición actualizándose)
2. El dron debe estar en el aire para que se dibuje el trayecto
3. El vuelo libre debe estar activo

### El mando no se detecta
1. Usa `test_joystick base.py` para verificar la detección
2. Asegúrate de tener pygame instalado: `pip install pygame`
3. Prueba con otro puerto USB
4. Verifica que el mando funcione en otros programas

### El dron no arma cuando presiono SELECT
1. Verifica que el dron esté conectado (indicador verde)
2. Espera 2-3 segundos después de la conexión inicial
3. Revisa los logs para ver mensajes de error

## 📝 Notas Importantes

### Modos de Vuelo

- **LOITER**: Modo de control manual con el mando (vuelo libre)
- **GUIDED**: Modo de control automático/programático
- El sistema cambia automáticamente entre estos modos

### Seguridad

- **Siempre vuela en un área segura** y despejada
- **Monitorea constantemente el nivel de batería**
- El botón **"🚨 DESCONECTAR TODO"** detiene todo el sistema en caso de emergencia

### Comportamiento Automático

- **Vuelo libre se activa** automáticamente cuando el dron despega
- **Vuelo libre se desactiva** automáticamente cuando el dron aterriza
- **El sistema monitorea constantemente** el estado del dron
- **El mapa se actualiza** cada 100ms mientras el vuelo libre está activo

## 🎓 Para Desarrolladores

### Modificar los Botones del Mando

Edita `vuelo_libre_joystick.py`, clase `JoystickExtendido`, método `control_loop`:

```python
# BOTÓN X: TU FUNCIÓN
if self.joystick.get_button(X) == 1:
    # Tu código aquí
    print("🔘 Botón X presionado")
    time.sleep(0.5)  # Evitar múltiples pulsaciones
```

### Modificar los Ejes del Joystick

En `Joystick.py` líneas 578-581:

```python
roll = self.map_axis(self.joystick.get_axis(3))      # Eje 3
pitch = self.map_axis(self.joystick.get_axis(2))     # Eje 2
throttle = self.map_axis(-self.joystick.get_axis(1)) # Eje 1 (invertido)
yaw = self.map_axis(self.joystick.get_axis(0))       # Eje 0
```

### Añadir Callbacks de Estado

El sistema usa callbacks para comunicar eventos del joystick a la interfaz:

```python
def mi_callback(evento, datos=None):
    if evento == "armado":
        print("El dron se armó!")
    elif evento == "despegue_iniciado":
        print("El dron está despegando!")
    # etc.

joystick = JoystickExtendido(0, dron, identificar, callback_estado=mi_callback)
```

### Personalizar el Visualizador

Edita `visualizador_trayecto_dron.py`:
- `espacio_vuelo`: Cambia el área de vuelo (default: 4.0 metros)
- Colores de la estela: `fill="#f44336"` (rojo)
- Tamaño del dron: `radio = 8` (píxeles)

## 🆘 Soporte

Si encuentras problemas:
1. Revisa los logs en la consola (muestra todos los eventos)
2. Verifica que todos los requisitos estén instalados
3. Prueba el script `test_joystick base.py` primero para verificar el mando
4. Consulta la documentación de cflib: https://www.bitcraze.io/

## ✨ Ventajas del Nuevo Sistema

✅ **Más intuitivo**: Todo desde el mando, como un videojuego
✅ **Menos clicks**: Solo 1 click en la interfaz para empezar
✅ **Más rápido**: No necesitas alternar entre mando e interfaz
✅ **Más seguro**: El control está siempre en tus manos
✅ **Más natural**: Vuelo libre como una consola de juegos

## 🎯 Comparación: Versión Antigua vs Nueva

### ❌ Versión Antigua
1. Click "Conectar Dron"
2. Click "Armar Dron"
3. Click "Despegar"
4. Click "Conectar Joystick"
5. Click "Iniciar Vuelo Libre"
6. Volar con el mando
7. Click "Detener Vuelo Libre"
8. Click "Aterrizar"

**Total: 8 pasos, 8 clicks**

### ✅ Versión Nueva
1. Click "Conectar Mando y Dron"
2. Presionar SELECT en el mando (armar)
3. Presionar START en el mando (despegar + vuelo libre automático)
4. Volar con el mando
5. Presionar Botón 2 en el mando (aterrizar + desactivar vuelo libre automático)

**Total: 5 pasos, 1 click, 3 botones del mando**

---

**¡Disfruta del vuelo libre total por mando con tu Crazyflie! 🎮🚁✨**
