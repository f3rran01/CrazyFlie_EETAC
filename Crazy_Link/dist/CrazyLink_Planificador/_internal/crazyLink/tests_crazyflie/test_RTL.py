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
dron.takeOff (0.5)
print ('ya he alcanzado los 0.5 metros')
dron.changeHeading(25)
time.sleep(2)
dron.move_distance('Forward',1)
time.sleep(2)
dron.RTL()
print ('ya estoy en tierra')