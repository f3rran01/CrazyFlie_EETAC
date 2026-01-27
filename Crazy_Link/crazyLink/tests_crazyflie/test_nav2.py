import tkinter as tk
import threading
from crazyLink.Dron_crazyflie import Dron
import math
import logging
import time


global dron
dron = Dron()
dron.connect()
print ('conectado')
dron.arm()
time.sleep(1)
dron.takeOff (0.5)
print ('ya he alcanzado los 0.5 metros')
dron.setSimpleScenario([1,4])   # Geofence de 1 m hacia adelante por 4 m de lateral
dron.changeHeading(90)
time.sleep(1)
dron.go('Left')
print ('voy hacia delante respecto la posición inicial hasta el fin del simple geofence')
time.sleep(10)
dron.RTL()
print ('ya estoy en tierra')
