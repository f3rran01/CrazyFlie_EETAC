#!/usr/bin/env python3
"""
Script para probar y ajustar la configuración de la cámara
Intenta diferentes configuraciones para solucionar imagen negra
"""

import cv2
import time
import numpy as np

print("=" * 80)
print("CONFIGURADOR Y PROBADOR DE CÁMARA")
print("=" * 80)
print()

# Intentar con el backend que sabemos que funciona: MSMF
print("Abriendo cámara con backend MSMF...")
cap = cv2.VideoCapture(0, cv2.CAP_MSMF)

if not cap.isOpened():
    print("No se pudo abrir la cámara")
    exit(1)

print("Cámara abierta")
print()

# Obtener propiedades actuales
print("CONFIGURACIÓN ACTUAL:")
print("-" * 80)
width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
fps = cap.get(cv2.CAP_PROP_FPS)
brightness = cap.get(cv2.CAP_PROP_BRIGHTNESS)
contrast = cap.get(cv2.CAP_PROP_CONTRAST)
exposure = cap.get(cv2.CAP_PROP_EXPOSURE)

print(f"  Resolución: {int(width)}x{int(height)}")
print(f"  FPS: {fps}")
print(f"  Brillo: {brightness}")
print(f"  Contraste: {contrast}")
print(f"  Exposición: {exposure}")
print()

# Intentar ajustar configuración
print("AJUSTANDO CONFIGURACIÓN...")
print("-" * 80)

# Intentar aumentar resolución
print("  • Intentando cambiar resolución a 1280x720...")
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# Ajustar brillo y contraste
#print("  • Ajustando brillo y contraste...")
#cap.set(cv2.CAP_PROP_BRIGHTNESS, 128)  # Rango típico 0-255
#cap.set(cv2.CAP_PROP_CONTRAST, 128)

# Intentar ajustar exposición (puede no funcionar en todas las cámaras)
print("  • Intentando ajustar exposición...")
cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)  # Auto exposure ON
cap.set(cv2.CAP_PROP_EXPOSURE, -5)  # Valor típico

print()

# Dar tiempo a la cámara para ajustarse
print("Esperando a que la cámara se ajuste (3 segundos)...")
time.sleep(3)

# Descartar primeros frames (a veces están en negro)
print("Descartando primeros 10 frames...")
for i in range(10):
    ret, frame = cap.read()
    time.sleep(0.1)

print()
print("=" * 80)
print("CAPTURANDO FRAMES DE PRUEBA")
print("=" * 80)
print()

# Capturar y analizar varios frames
frames_negros = 0
frames_ok = 0

for i in range(5):
    ret, frame = cap.read()
    
    if ret and frame is not None:
        # Calcular brillo promedio del frame
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brillo_promedio = np.mean(gray)
        brillo_max = np.max(gray)
        
        print(f"Frame {i+1}/5:")
        print(f"  • Tamaño: {frame.shape[1]}x{frame.shape[0]}")
        print(f"  • Brillo promedio: {brillo_promedio:.2f} / 255")
        print(f"  • Brillo máximo: {brillo_max} / 255")
        
        if brillo_promedio < 10:
            print(f"  • Estado:  CASI NEGRO (muy oscuro)")
            frames_negros += 1
        elif brillo_promedio < 30:
            print(f"  • Estado:  MUY OSCURO")
            frames_negros += 1
        else:
            print(f"  • Estado: OK (tiene contenido)")
            frames_ok += 1
        
        # Guardar frame para inspección
        filename = f"test_frame_{i+1}.jpg"
        cv2.imwrite(filename, frame)
        print(f"  • Guardado: {filename}")
        print()
        
        time.sleep(0.5)
    else:
        print(f"Frame {i+1}/5: Error al capturar")
        print()

cap.release()

print("=" * 80)
print("DIAGNÓSTICO FINAL")
print("=" * 80)
print()

if frames_negros == 5:
    print(" TODOS LOS FRAMES ESTÁN NEGROS/MUY OSCUROS")
    print()

elif frames_ok > 0:
    print("LA CÁMARA ESTÁ FUNCIONANDO")
    print()
    print(f"  • Frames correctos: {frames_ok}/5")
    print(f"  • Frames oscuros: {frames_negros}/5")
    print()
    print("La cámara funciona pero puede estar en un lugar oscuro.")
    print("Revisa las imágenes guardadas: test_frame_1.jpg, test_frame_2.jpg, etc.")
    print()
    
else:
    print(" RESULTADOS MIXTOS")
    print()
    print("La cámara captura frames pero están muy oscuros.")
    print("Posibles soluciones:")
    print("  • Aumentar iluminación de la habitación")
    print("  • Verificar que no haya tapa física")
    print("  • Apuntar la cámara hacia algo iluminado")
    print()


