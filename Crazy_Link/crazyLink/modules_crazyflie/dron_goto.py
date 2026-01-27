import math
import threading
import time
import logging
from crazyLink.modules_crazyflie.dron_bottomGeofence import  _checkBottomGeofence
from crazyLink.modules_crazyflie.dron_topGeofence import _checkTopGeofence
from crazyLink.modules_crazyflie.dron_geofence import _checkSimpleScenario
from crazyLink.modules_crazyflie.dron_complex_geofence import _checkComplexScenario

# Function to determine the distance  between the actual position and the desired one
def _distanceToDestinationInMeters(self, transversal, lateral):
    dlat = transversal - self.position[0]
    dlong = lateral - self.position[1]  # CORRECCIÓN: Restar en lugar de sumar
    return math.sqrt((dlat * dlat) + (dlong * dlong))

# Secondary function to move the drone
def _goto (self, transversal, lateral, alt, callback=None, params = None):

    # Checks if the desired position is outside the geocage.
    if _checkSimpleScenario(self, transversal, lateral) or _checkBottomGeofence(self, alt) or _checkTopGeofence(self, alt):
        logging.info(f"[Dron] Funcion goto fuera del escenario de exclusion simple (geofence simple-top-bot).")
        # Callback
        if callback is not None:
            if self.id is None:
                if params is None:
                    callback()
                else:
                    callback(params)
            else:
                if params is None:
                    callback(self.id)
                else:
                    callback(self.id, params)

    elif _checkComplexScenario(self, transversal, lateral):
        logging.info(f"[Dron] Funcion goto fuera del escenario de exclusion complejo (geofence complejo).")
        # Callback
        if callback is not None:
            if self.id is None:
                if params is None:
                    callback()
                else:
                    callback(params)
            else:
                if params is None:
                    callback(self.id)
                else:
                    callback(self.id, params)
    else:
        # If the drone can be moved
        logging.info("[Dron] Moviendo.")
        x, y, z = self.position
        # CORRECCIÓN: Eliminar doble negación de Y (ya se niega en move_distance)

        # Position difference
        dx_w = transversal - x
        dy_w = lateral - y
        dz = alt - z

        # If the variation is not enough (margin of 15 cm)
        if abs(dx_w) <= 0.15 and abs(dy_w) <= 0.15 and abs(dz) <= 0.15:
            logging.info("[Dron] En la misma posición.")
            return

        # Obtain the heading (inverted)
        yaw_rad = -math.radians(self.attitude[2])

        # Convert to  body frame (from room frame to drone frame)
        dx_body = dx_w * math.cos(yaw_rad) + dy_w * math.sin(yaw_rad)
        dy_body = -dx_w * math.sin(yaw_rad) + dy_w * math.cos(yaw_rad)

        # Obtain the velocity, hover the drone in mid-air, and then move the drone
        velocity = self.move_speed
        self.mc.stop()
        time.sleep(0.5)

        # Move the drone
        # CORRECCIÓN: Eliminar negación de dy_body (ya que eliminamos y = -y)
        self.mc.move_distance(dx_body, dy_body, dz, velocity)

        # Check if the drone is in position
        timeout = 3
        start_time = time.time()
        while time.time() - start_time < timeout:
            if abs(self.position[0] - transversal) < 0.4 and abs(self.position[1] - lateral) < 0.4 and abs(self.position[2] - alt) < 0.4:
                time.sleep(0.5)
                break
            time.sleep(1)
            logging.info(f"[Dron] Esperando a llegar a destino")

        logging.info(f"[Dron] En posicion indicada.")
        # Callback
        if callback is not None:
            if self.id is None:
                if params is None:
                    callback()
                else:
                    callback(params)
            else:
                if params is None:
                    callback(self.id)
                else:
                    callback(self.id, params)

# Primary function to move the drone: the input should be a position of the room
# If there's a complex geofence activated and this function is activated, maybe in case of crossing a restricted area,
# to go a flyable area.
# There are 2 possibilities, cross the area with no problems (unlikely to happen) or
# have problems to access due geofence (most likely stop in mid-air and come back to the unrestricted zone)
def goto(self, transversal, lateral, alt, blocking=True, callback=None, params = None):
    # Check the state of the drone
    if self.state == "flying":
        if blocking:
            self._goto(transversal, lateral, alt)
        else:
            gotoThread = threading.Thread(target=self._goto, args=[transversal, lateral, alt, callback, params])
            gotoThread.start()
    else:
        logging.info(f"[Dron] No esta volando.")
