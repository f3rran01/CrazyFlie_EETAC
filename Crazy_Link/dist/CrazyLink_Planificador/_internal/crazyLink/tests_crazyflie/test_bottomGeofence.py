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
dron.startBottomGeofence(0.5) # BottomGeofence a 0.5 m
print ('creo un bottom geofence a 0.5 m')
dron.arm()
dron.takeOff (0.7)
print ('ya he alcanzado los 0.7 metros')
time.sleep(2)
dron.change_altitude(0.4)    # El dron deberia responder sin actuar a la altura
print ('he intentado ir a 0.4 m altitud')
time.sleep(2)
dron.Land()
print ('he aterrizado')

