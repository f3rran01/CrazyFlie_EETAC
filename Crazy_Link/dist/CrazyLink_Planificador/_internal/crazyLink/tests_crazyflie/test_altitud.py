import tkinter as tk
import threading
from crazyLink.Dron_crazyflie import Dron
import math
import logging
import time

global dron

dron = Dron ()
time.sleep(2)
dron.connect()
print('conectado')
time.sleep(2)
dron.arm()
print('armado')
time.sleep(2)
dron.takeOff (0.7)
print('ya he alcanzado los 0.7 metros')
time.sleep(2)
dron.change_altitude(0.5)
print('ya he alcanzado los 0.5 metros')
time.sleep(2)
dron.change_altitude(0.5)
print('estoy en la misma posición')
time.sleep(2)
dron.change_altitude(0.7)
print('ya he subido a los 0.7 metros')
time.sleep(2)
dron.Land()
print('ya estoy en tierra')
