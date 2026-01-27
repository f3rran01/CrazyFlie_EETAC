
import time
from crazyLink.Dron_crazyflie import Dron

dron = Dron()
dron.connect()
print ('conectado')
dron.arm()
# dron.setSimpleScenario([1,1]) # Opcional, para test
dron.changeNavSpeed(0.3)    # Cambio la velocidad a 0.3 m/s
time.sleep (1)
dron.takeOff (0.5)
print ('Navego hacia delante 2 segundos')
dron.go('Forward')
time.sleep(2)
dron.go('Forward')
time.sleep (2)
dron.go('Back')
time.sleep (3)
dron.go('Stop')
time.sleep (3)
dron.Land()


