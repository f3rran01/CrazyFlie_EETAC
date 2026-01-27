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
dron.setMoveSpeed(0.4)
time.sleep(1)
dron.takeOff (0.5)
print ('ya he alcanzado los 0.5 metros')
time.sleep(1)
dron.move_distance('Forward', 1.5)
print ('adelante 1.5 metros')
time.sleep(2)
dron.setSimpleScenario([1,1])
print ('He creado una jaula de 1x5 m en base al centro, debería moverme ')
time.sleep(7)
print ('ya estoy en tierra')
dron.Land()
