import time
import threading
import logging

# Secondary function that makes the action: change altitude
def _change_altitude(self, altitude, callback=None, params=None):
    logging.info(f"[Dron] Iniciando cambio de altitud a {altitude} m.")

    # Change state of the drone + obtain the desired speed and the actual position
    self.state = "changing_altitude"
    velocity = self.move_speed
    altura_actual = self.position[2]

    # Obtain the variation between the desired and the actual altitude
    variacion_altura = altitude - altura_actual

    # Depending on the variation do an action
    if variacion_altura > 0.1:
        logging.info(f"[Dron] Subiendo {variacion_altura:.2f} m.")
        self.mc.up(variacion_altura,velocity)
    elif variacion_altura < -0.1:
        logging.info(f"[Dron] Bajando {abs(variacion_altura):.2f} m.")
        self.mc.down(abs(variacion_altura),velocity)
    else:
        logging.info(f"[Dron] Ya estamos en {altitude} m.")
        self.state = "flying"
        # Callback
        if callback:
            if self.id is None:
                callback() if params is None else callback(params)
            else:
                callback(self.id) if params is None else callback(self.id, params)
        return

    # Check if we reach the altitude with a deviation of 30 cm
    timeout = 3.0  # time of wait
    start_t = time.time()
    while time.time() - start_t < timeout:
        time.sleep(0.3)
        if abs(self.position[2] - altitude) < 0.30: # Band of 30 cm
            break

    # Change again state of the drone
    time.sleep(0.3)
    self.state = "flying"
    logging.info(f"[Dron] Altitud actual: {self.position[2]:.2f} m.")
    if callback:
        if self.id is None:
            callback() if params is None else callback(params)
        else:
            callback(self.id) if params is None else callback(self.id, params)

# Primary function to change the altitude
def change_altitude(self, altitude, blocking=True, callback=None, params=None):
    # Check the state
    if self.state == "flying":
        # Seek if the altitude is out of bounds
        if self.checkMinAlt == True and self.minAltGeofence >= altitude:
            logging.warning("[Dron] No se puede cambiar altitud (dentro de zona de exclusion).")
            return False

        if self.checkMaxAlt == True and self.maxAltGeofence <= altitude:
            logging.warning("[Dron] No se puede cambiar altitud (dentro de zona de exclusion).")
            return False
        # Take action
        if blocking:
            self._change_altitude(altitude, callback, params)
        else:
            t = threading.Thread(
                target=self._change_altitude,
                args=(altitude, callback, params),
            )
            t.start()
        return True
    else:
        logging.warning("[Dron] No está volando. No se puede cambiar altitud.")
        return False