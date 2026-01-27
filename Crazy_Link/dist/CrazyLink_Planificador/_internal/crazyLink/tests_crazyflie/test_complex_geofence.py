import time
import logging

from crazyLink.Dron_crazyflie import Dron


def main():
    # Rectángulo , centrado en (0,0)
    half_w, half_h = 0.5, 1.0
    inside_polygon = [
        (-half_w, -half_h),
        (half_w, -half_h),
        (half_w, half_h),
        (-half_w, half_h)
    ]
    exclusion_zones = []  # sin huecos (más explicación en la libreria)


    dron = Dron()
    dron.connect()
    print('conectado')
    time.sleep(1)
    dron.arm()
    dron.changeNavSpeed(0.3)
    dron.takeOff(0.5)
    print('armado + velocidad 0.3 m/s + en aire')
    time.sleep(2)
    dron.move_distance('Forward-Right', 1.5)
    print('voy a 1.5 m adelante-izquierda')
    time.sleep(1)
    print('creo el complex geofence ')
    print('a partir de este momento debería moverme ya que estoy fuera del geofence')
    dron.setComplexScenario(
        inside_polygon=inside_polygon,
        exclusion=exclusion_zones
    )
    print('espero 6 segundo a ver que hace el dron')
    time.sleep(6)   # deberia ir a la izquierda
    print('Atterrizando...')
    dron.Land()
    time.sleep(3)
    dron.disconnect()


if __name__ == "__main__":
    main()
