import tkinter as tk
import threading
from crazyLink.Dron_crazyflie import Dron
import math
import logging
import time

def printear (parametro):
    print(parametro)

# ---------------------------------Ejemplo 1-------------------------------------:
# Estando dentro de la zona de vuelo
global dron
dron = Dron()
dron.connect()
print ('conectado')
dron.arm()
dron.setMoveSpeed(0.4)
dron.changeNavSpeed (0.3)
dron.setSimpleScenario([1,1], type='LAND', callback=printear, params='ejemplo1')
time.sleep(1)
dron.takeOff (0.5)
print ('ya he alcanzado los 0.5 metros de altura')
time.sleep(1)
dron.go('Forward')
print ('adelante')
print ('Deberia de aterrizar al llegar al limite ')
time.sleep(10)
print ('ya estoy en tierra')
# Función Land no podria activarse
dron.Land()

# ---------------------------------Ejemplo 2-------------------------------------:
# Estando dentro de la zona de vuelo
"""""
global dron
dron = Dron()
dron.connect()
print ('conectado')
dron.arm()
dron.setMoveSpeed(0.4)
dron.changeNavSpeed (0.3)
dron.setSimpleScenario([1,1], type='RTL', callback=printear, params='ejemplo2')
time.sleep(1)
dron.takeOff (0.5)
print ('ya he alcanzado los 0.5 metros de altura')
time.sleep(1)
dron.go('Forward')
print ('adelante')
print ('Deberia de aplicar RTL al llegar al limite ')
time.sleep(10)
print ('ya estoy en tierra')
# Función Land no podria activarse
dron.Land()
"""""
# ---------------------------------Ejemplo 3-------------------------------------:
# Estando fuera de la zona de vuelo/geofence
"""""
global dron
dron = Dron()
dron.connect()
print ('conectado')
dron.arm()
dron.setMoveSpeed(0.4)
time.sleep(1)
dron.takeOff (0.5)
print ('ya he alcanzado los 0.5 metros de altura')
time.sleep(1)
dron.move_distance('Forward',1.6)
print ('adelante')
time.sleep(3)
dron.setSimpleScenario([1,1], type='LAND', callback=printear, params='ejemplo3')
print ('Deberia de aplicar RTL al llegar al limite ')
time.sleep(10)
print ('ya estoy en tierra')
# Función Land no podria activarse
dron.Land()
"""""