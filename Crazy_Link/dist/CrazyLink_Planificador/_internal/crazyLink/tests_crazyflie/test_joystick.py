
from crazyLink.Dron_crazyflie import Dron
import keyboard # instalar keyboard

from crazyLink.modules_crazyflie.Joystick import Joystick


def identifica (id):
    print ("Soy el joystick: ", id)

def printear (parametro):
    print(parametro)


dron = Dron ()
dron.connect ()
print ("Conectado al dron")
joystick = Joystick (0, dron, identifica)
#dron.setSimpleScenario([1,1], callback=printear, params='ejemplo2')
while True:
    #time.sleep(1)
    if keyboard.is_pressed('p'):
        break
joystick.stop()
print ("Fin")