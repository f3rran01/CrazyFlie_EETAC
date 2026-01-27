"""
Wrapper para Demo_plan_de_vuelo.py que maneja rutas correctamente en PyInstaller
"""
import sys
import os
import traceback

# Configurar rutas para PyInstaller
if getattr(sys, 'frozen', False):
    # Estamos ejecutando desde el ejecutable de PyInstaller
    application_path = sys._MEIPASS
    print(f"[WRAPPER] Ejecutando desde PyInstaller")
    print(f"[WRAPPER] _MEIPASS: {application_path}")
else:
    # Estamos ejecutando desde Python normal
    application_path = os.path.dirname(os.path.abspath(__file__))
    print(f"[WRAPPER] Ejecutando desde Python")
    print(f"[WRAPPER] Path: {application_path}")

# Cambiar al directorio de la aplicación
os.chdir(application_path)
print(f"[WRAPPER] Directorio de trabajo cambiado a: {os.getcwd()}")

# Agregar rutas al path
demostradores_path = os.path.join(application_path, 'demostradores_crazyflie')
crazylink_path = os.path.join(application_path, 'crazyLink')
vosk_model_path = os.path.join(application_path, 'vosk-model-small-es-0.42')

if os.path.exists(demostradores_path):
    sys.path.insert(0, demostradores_path)
    print(f"[WRAPPER] ✓ Agregado al path: {demostradores_path}")

if os.path.exists(crazylink_path):
    sys.path.insert(0, crazylink_path)
    print(f"[WRAPPER] ✓ Agregado al path: {crazylink_path}")

# Configurar la ruta del modelo de voz para que el código lo encuentre
if os.path.exists(vosk_model_path):
    os.environ['VOSK_MODEL_PATH'] = vosk_model_path
    print(f"[WRAPPER] ✓ Modelo de voz encontrado: {vosk_model_path}")
else:
    print(f"[WRAPPER] ⚠ Modelo de voz NO encontrado en: {vosk_model_path}")
    print(f"[WRAPPER] Contenido de {application_path}:")
    try:
        for item in os.listdir(application_path):
            print(f"[WRAPPER]   - {item}")
    except Exception as e:
        print(f"[WRAPPER] Error listando archivos: {e}")

print(f"[WRAPPER] sys.path configurado")

try:
    print("[WRAPPER] Importando módulos de Demo_plan_de_vuelo...")

    # Ejecutar el código principal
    import tkinter as tk

    # Parchear el módulo de voz ANTES de cambiar de directorio
    # IMPORTANTE: El sistema de voz es OPCIONAL - la app debe funcionar sin él
    if os.path.exists(vosk_model_path):
        try:
            print(f"[WRAPPER] Importando voz_crazyflie...")
            import voz_crazyflie

            # OPCIÓN 1: Reemplazar RUTAS_MODELO
            voz_crazyflie.RUTAS_MODELO = [vosk_model_path]
            print(f"[WRAPPER] ✓ RUTAS_MODELO reemplazado con: {vosk_model_path}")

            # OPCIÓN 2: Parchear la función _buscar_modelo para que retorne inmediatamente
            def _buscar_modelo_parcheado(self):
                print(f"[WRAPPER] _buscar_modelo parcheado retornando: {vosk_model_path}")
                return vosk_model_path
            voz_crazyflie.VoiceRecognitionSystem._buscar_modelo = _buscar_modelo_parcheado
            print(f"[WRAPPER] ✓ Función _buscar_modelo parcheada")

        except (ImportError, OSError) as e:
            print(f"[WRAPPER] ⚠ No se pudo cargar voz_crazyflie: {e}")
            print(f"[WRAPPER] La aplicación continuará SIN soporte de voz")
            # NO ES UN ERROR CRÍTICO - continuamos sin voz
        except Exception as e:
            print(f"[WRAPPER] ⚠ Error inesperado con voz_crazyflie: {e}")
            print(f"[WRAPPER] La aplicación continuará SIN soporte de voz")
            # NO ES UN ERROR CRÍTICO - continuamos sin voz

    # AHORA cambiar al directorio demostradores
    if os.path.exists(demostradores_path):
        os.chdir(demostradores_path)
        print(f"[WRAPPER] Cambiado a: {os.getcwd()}")

    # Importar Demo_plan_de_vuelo como módulo
    import Demo_plan_de_vuelo

    print("[WRAPPER] Módulo importado correctamente")
    print("[WRAPPER] Iniciando aplicación...")

    # Crear la aplicación
    root = tk.Tk()
    app = Demo_plan_de_vuelo.MissionPlannerGUI(root)
    root.mainloop()

except Exception as e:
    print(f"\n[WRAPPER] ❌ ERROR CRÍTICO:")
    print(f"[WRAPPER] {type(e).__name__}: {e}")
    print(f"[WRAPPER] Traceback completo:")
    traceback.print_exc()
    input("\n[WRAPPER] Presiona Enter para cerrar...")
