
import math
import threading
import time
import logging
from crazyLink.modules_crazyflie.dron_bottomGeofence import  _checkBottomGeofence
from crazyLink.modules_crazyflie.dron_topGeofence import _checkTopGeofence
from crazyLink.modules_crazyflie.dron_geofence import _checkSimpleScenario
from crazyLink.modules_crazyflie.dron_complex_geofence import _checkComplexScenario

# Function to check the drone's velocity, if it is zero (personally I would not use it)
def _checkSpeedZero (self):

    vx, vy, vz = self.velocity
    speed = math.sqrt(vx * vx + vy * vy + vz * vz)
    if speed < 0.1:
        return True
    else:
        return False

# Secondary function, used to move the drone: giving a certain distance and direction
def _move_distance (self, direction, distance = 0.0, callback=None, params = None):

   # Declaration of the variables
    dx_body = 0
    dy_body = 0
    dz_body = 0

    # Check direction
    if direction == "Forward":
        dx_body = distance
    elif direction == "Back":
        dx_body = -distance
    elif direction == "Left":
        dy_body = -distance
    elif direction == "Right":
        dy_body = distance
    elif direction == "Up":
        dz_body = distance
    elif direction == "Down":
        dz_body = -distance
    elif direction == "Forward-Left":
        dx_body = distance*0.707
        dy_body = -distance*0.707
    elif direction == "Forward-Right":
        dx_body = distance*0.707
        dy_body = distance*0.707
    elif direction == "Back-Left":
        dx_body = -distance*0.707
        dy_body = -distance*0.707
    elif direction == "Back-Right":
        dx_body = -distance*0.707
        dy_body = distance*0.707
    elif direction == "Stop":
        self.mc.stop()
        return
    elif direction == "North" or direction == "South" or direction == "East" or direction == "West":
        logging.info(f"[Dron] No se puede seguir direcciones magneticas.")
        return
    elif direction == "NorthWest" or direction == "NorthEast" or direction == "SouthWest" or direction == "SouthEast":
        logging.info(f"[Dron] No se puede seguir direcciones magneticas.")
        return
    else:
        logging.info(f"[Dron] No se puede seguir direcciones dadas.")
        return

    # Obtain the heading of the drone (inverted)
    yaw_rad = -math.radians(self.attitude[2])

    # Transform the data to the room frame with the heading
    dx_global = dx_body * math.cos(yaw_rad) - dy_body * math.sin(yaw_rad)
    dy_global = dx_body * math.sin(yaw_rad) + dy_body * math.cos(yaw_rad)

    # Calculate the estimated position
    x_new = self.position[0] + dx_global
    y_new = -self.position[1] + dy_global
    z_new = self.position[2] + dz_body

    # Check if the estimated position is out of borders
    if _checkSimpleScenario(self, x_new, y_new) or _checkBottomGeofence(self, z_new) or _checkTopGeofence(self, z_new):
        logging.info( f"[Dron] No se ha podido mover el dron debido ya que se estaria fuera del escenario simple-top-bot.")
        return
    elif _checkComplexScenario(self, x_new, y_new):
        logging.info(f"[Dron] No se ha podido mover el dron debido ya que se estaria fuera del escenario complejo.")
        return

    # Obtain the velocity
    velocity = self.move_speed

    # Hover and stop the drone
    self.mc.stop()
    time.sleep(0.5)

    # Move the drone depending on the direction
    if direction == "Forward":
        self.mc.forward(distance, velocity)
    elif direction == "Back":
        self.mc.back(distance, velocity)
    elif direction == "Left":
        self.mc.left(distance, velocity)
    elif direction == "Right":
        self.mc.right(distance, velocity)
    elif direction == "Up":
        self.mc.up(distance, velocity)
    elif direction == "Down":
        self.mc.down(distance, velocity)
    elif direction == "Forward-Left":
        self.mc.move_distance(distance * 0.707, distance * 0.707,0, velocity)
    elif direction == "Forward-Right":
        self.mc.move_distance(distance * 0.707, -distance * 0.707, 0, velocity)
    elif direction == "Back-Left":
        self.mc.move_distance(-distance * 0.707, distance * 0.707, 0, velocity)
    elif direction == "Back-Right":
        self.mc.move_distance(-distance * 0.707, -distance * 0.707, 0, velocity)

    # Check if the drone is in position
    timeout = 5
    start_time = time.time()
    while time.time() - start_time < timeout:
        if abs(self.position[0]-x_new) < 0.4 and abs(-self.position[1]-y_new) < 0.4 and abs(self.position[2]-z_new) < 0.4 :
            time.sleep(0.5)
            break
        time.sleep(1)
        logging.info(f"[Dron] Esperando a llegar a destino")


    logging.info(f"[Dron] En posicion indicada.")

    # Callback
    if callback != None:
        if self.id == None:
            if params == None:
                callback()
            else:
                callback(params)
        else:
            if params == None:
                callback(self.id)
            else:
                callback(self.id, params)

# Primary function to move a certain distance with the drone
def move_distance(self, direction, distance, blocking=True, callback=None, params = None):
    # Check the state of the drone
    if self.state == "flying":
        logging.info(f"[Dron] Moviendo el dron.")

        if blocking:
            self._move_distance(direction, distance)
        else:
            moveThread = threading.Thread(target=self._move_distance, args=[direction, distance, callback, params,])
            moveThread.start()
            return True
    else:
        logging.info(f"[Dron] No esta volando.")


# Function to change the main used velocity of the drone (by default it is 0.2 m/s)
def setMoveSpeed (self, speed):
    logging.info(f"[Dron] Velocidad a {speed}.")
    self.move_speed=speed
    logging.info(f"[Dron] Se ha cambiado la velocidad de movimiento.")


