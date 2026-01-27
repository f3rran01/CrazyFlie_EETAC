from crazyLink.Dron_crazyflie import Dron
import time


def procesar_parametros (params_info):
    print (params_info)

dron = Dron ()
dron.connect()
print ("conectado")
time.sleep(2)
# en parametros no incorporo 'range_data', ya que es opcional
parameters = [
    'position',
    'velocity',
    'battery',
    'attitude',
    'flow_data',
    'altitude',
]

result = dron.getParams(parameters,procesar_parametros)
print ('ya los tengo')
time.sleep(20)
dron.stop_sending_params()
dron.disconnect()