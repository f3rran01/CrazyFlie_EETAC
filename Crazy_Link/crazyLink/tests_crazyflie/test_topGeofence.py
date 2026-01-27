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
dron.startTopGeofence(0.7) # BottomGeofence a 0.7 m
time.sleep(2)
dron.arm()
dron.takeOff (0.5)
print ('ya he alcanzado los 0.5 metros')
time.sleep(2)
print ('no deberia subir')
dron.change_altitude(1)    # El dron deberia responder sin actuar a la altura
time.sleep(2)
dron.Land()
print ('he aterrizado')