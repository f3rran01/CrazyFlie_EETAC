import time


from crazyLink.Dron_crazyflie import Dron

def procesar_telemetria (telemetry_info):
    print (telemetry_info)

# Tanto local_telemetry como telemetry (version small) se pueden usar
dron = Dron ()
dron.connect(freq=10)   # Cambio a frecuencia 10 datos por segundo)
print ('conectado')
time.sleep(2)
print ('ya he armado')
dron.send_local_telemetry_info(procesar_telemetria)
time.sleep(100)
dron.stop_sending_local_telemetry_info()
dron.disconnect()