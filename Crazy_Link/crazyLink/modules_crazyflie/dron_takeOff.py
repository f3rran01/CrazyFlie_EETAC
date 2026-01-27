import logging
import time
import threading

# Secondary function to take off the drone
def _takeOff(self, aTargetAltitude, callback=None, params=None):
    # Apply a state and obtain the velocity
    logging.info(f"[Dron] Iniciando despegue a {aTargetAltitude} metros.")
    self.state = "taking off"
    velocity = self.move_speed

    self.mc.take_off(aTargetAltitude,velocity)
    time.sleep(2)

    # Simple verification
    timeout = 5
    start_time = time.time()
    while time.time() - start_time < timeout:
        if abs(self.position[2] - aTargetAltitude) < 0.4:
            time.sleep(0.5)
            break
        time.sleep(1)
        logging.info(f"[Dron] Subiendo.")

    # Change state of the drone and give the actual altitude
    self.state = "flying"
    logging.info(f"[Dron] Despegue completado. Altitud actual: {self.position[2]:2f}m")

    # Callback
    if callback:
        if self.id is None:
            callback() if params is None else callback(params)
        else:
            callback(self.id) if params is None else callback(self.id, params)

# Primary function to take off the drone, the input is only a target altitude to reach when take off
def takeOff(self, aTargetAltitude, blocking=True, callback=None, params=None):
    # Check if the drone is armed or not
    if  self.state == "armed" and self.mc != None:
        if blocking:
            self._takeOff(aTargetAltitude, callback, params)
        else:
            takeOffThread = threading.Thread(
                target=self._takeOff,
                args=(aTargetAltitude, callback, params))
            takeOffThread.start()
        return True
    else:
        logging.warning("[Dron] No está armado o conectado. No puede despegar.")
        return False


