import json
import time
from crazyLink.Dron_crazyflie import Dron

dron = Dron()
dron.connect()
print ('conectado')
dron.arm()
dron.takeOff (0.5)
time.sleep(2)
print ('Voy hacia delante 1.5 metros')
dron.move_distance ('Forward', 1.5)
print ('Voy hacia la izquierda 1 metros')
dron.move_distance ('Left', 1)
print ('me muevo arriba 0.2 metros')
dron.move_distance ('Up', 0.2)
print ('Voy atras 1 metros')
dron.move_distance ('Back', 1)
print ('cambio de heading')
dron.changeHeading(275) # Heading de 0 a 180 o 0 a -180
print ('me muevo a la izquierda 2 metros')
dron.move_distance ('Left', 2)
print ('aterrizo')
#dron.RTL() # Opcional, para test
dron.Land()
dron.disconnect()

