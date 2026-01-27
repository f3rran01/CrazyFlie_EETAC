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
#dron.setSimpleScenario([2,1])  #  opcional para hacer test
time.sleep(1)
dron.changeHeading(270)
time.sleep(1)
dron.goto(1.7,0,0.5)
print ('voy hacia 1.7 m adelante, 0 de lateral y 0.5 m de altura')    # el dron debería moverse sin hacer caso al heading
time.sleep(2)
dron.Land()
print ('ya estoy en tierra')
