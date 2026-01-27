import time
from time import sleep

from crazyLink.Dron_crazyflie import Dron

# Test general
dron = Dron ()
dron.connect()
print ('conectado')
dron.arm()
print ('ya he armado')
dron.takeOff (0.7)
time.sleep (5)
dron.go('Forward')
time.sleep(1)
print ('ya he alcanzado el punto indicado')
dron.change_altitude(0.5)
print ('ya he alcanzado la nueva altitud')
dron.go ('Right')
print ('voy a la derecha')
time.sleep (2)
dron.Land()
print ('ya estoy en tierra')
dron.disconnect()
