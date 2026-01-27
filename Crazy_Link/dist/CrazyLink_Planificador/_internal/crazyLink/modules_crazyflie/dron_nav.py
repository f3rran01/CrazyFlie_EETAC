
# Collection of methods for navigation according to cardinal directions.
# The drone must be in the 'flying' state.
# To start navigation, the startGo method must be executed,
# which starts the thread that maintains the heading.
# The heading can be changed using the go method, which receives
# the new heading as a parameter (right, forward, etc.).
# To end the navigation, the stopGo method must be executed.

import threading
import time
import logging
import math
from crazyLink.modules_crazyflie.dron_bottomGeofence import  _checkBottomGeofence
from crazyLink.modules_crazyflie.dron_topGeofence import _checkTopGeofence
from crazyLink.modules_crazyflie.dron_geofence import _checkSimpleScenario
from crazyLink.modules_crazyflie.dron_complex_geofence import _checkComplexScenario

# Function to change the drone speed (only in NAV script!!)
def changeNavSpeed (self, speed):
    logging.info(f"[Dron] Velocidad a {speed}.")
    self.navSpeed = speed
    logging.info(f"[Dron] Se ha cambiado la velocidad de navegacion.")

# Secondary function to make the drone fly in navigation
def _startGo(self):
    if self.state == 'flying':
        # Start NAV thread
        self.going = True

# Secondary function to make the drone stop in navigation
def _stopGo(self):
    # Stop the thread of NAV
    self.going = False
    time.sleep(0.3)

# Primary function to start the navigation mode, as input it needs a direction only
def go(self, direction, blocking = True):
    # Check the state of the drone
    if self.state == 'flying':
        if blocking:
            self._go(direction)
        else:
            changeHeadingThread = threading.Thread(target=self._go, args=[direction,])
            changeHeadingThread.start()
        return True
    else:
        logging.info(f"[Dron] No esta volando.")
        return False


# Secondary function, it moves the drone in a specific direction.
def _go(self, direction):

    # Check if the drone has previously moving in a direction, depending on the state it changes or starts moving.
    if not self.going:
        # Put the drone in navigation mode
        self._startGo()
    else:
        self._stopGo()
        self._startGo()
        logging.info(f"[Dron] Recomendación: Para el dron usando 'Stop' antes de ejecutar otra direccion.")

    # Identifies the direction
    self.direction = direction

    # Check the state of NAV
    if self.going:
        if direction == "North" or direction == "South" or direction == "East" or direction == "West" :
            logging.info(f"[Dron] No se ha podido mover el dron debido a que se estaria fuera del escenario simple.")
            return
        if direction == "NorthWest" or direction == "NorthEast" or direction == "SouthWest" or direction == "SouthEast":
            logging.info(f"[Dron] No se ha podido mover el dron debido a que se estaria fuera del escenario simple.")
            return

        # Moves the drone
        if direction == "Stop":
            self.mc.stop()
            self._stopGo()
        elif direction == "Forward":
            self.mc.start_linear_motion(self.navSpeed, 0, 0)
        elif direction == "Back":
            self.mc.start_linear_motion(-self.navSpeed, 0, 0)
        elif direction == "Left":
            self.mc.start_linear_motion(0, self.navSpeed, 0)
        elif direction == "Right":
            self.mc.start_linear_motion(0, -self.navSpeed, 0)
        elif direction == "Up":
            self.mc.start_linear_motion(0, 0, self.navSpeed)
        elif direction == "Down":
            self.mc.start_linear_motion(0, 0, -self.navSpeed)
        elif direction == "Forward-Right":
            self.mc.start_linear_motion(self.navSpeed*0.707, -self.navSpeed*0.707, 0)
        elif direction == "Forward-Left":
            self.mc.start_linear_motion(self.navSpeed*0.707, self.navSpeed*0.707, 0)
        elif direction == "Back-Right":
            self.mc.start_linear_motion(-self.navSpeed*0.707, -self.navSpeed*0.707,0)
        elif direction == "Back-Left":
            self.mc.start_linear_motion(-self.navSpeed*0.707, self.navSpeed*0.707,0)
        else:
            logging.info(f"[Dron] No se identifica direccion.")
            return

      # Starts the thread to check if the drone will be out of the bounds
        Thread_checkPosition = threading.Thread(target=self._checkPosition, args=[])
        Thread_checkPosition.start()

    return

# Tertiary function to check if the drone will be out of the geocage
def _checkPosition(self):
    # Check if the drone is flying
    while self.going == True:

        # Obtain the direction
        direction = self.direction
        # Declaration of the variables
        dx_body = 0
        dy_body = 0
        dz_body = 0

        # Estimate the future position of the dron by a factor of 0.4 (4 times the sample freq)
        if direction == "Forward":
            dx_body = self.navSpeed*0.4
        elif direction == "Back":
            dx_body = -self.navSpeed*0.4
        elif direction == "Left":
            dy_body = -self.navSpeed*0.4
        elif direction == "Right":
            dy_body = self.navSpeed*0.4
        elif direction == "Up":
            dz_body = self.navSpeed*0.4
        elif direction == "Down":
            dz_body = -self.navSpeed*0.4
        elif direction == "Forward-Left":
            dx_body = self.navSpeed*0.4 * 0.707
            dy_body = -self.navSpeed*0.4 * 0.707
        elif direction == "Forward-Right":
            dx_body = self.navSpeed*0.4 * 0.707
            dy_body = self.navSpeed*0.4 * 0.707
        elif direction == "Back-Left":
            dx_body = -self.navSpeed*0.4 * 0.707
            dy_body = -self.navSpeed*0.4 * 0.707
        elif direction == "Back-Right":
            dx_body = -self.navSpeed*0.4 * 0.707
            dy_body = self.navSpeed*0.4 * 0.707
        else:
            self.mc.stop()
            self._stopGo()
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

        # Check if the drone is out of bounds
        if _checkSimpleScenario(self, x_new, y_new) or _checkBottomGeofence(self, z_new) or _checkTopGeofence(self,z_new):
            logging.info(f"[Dron] Cambiando la direccion. Fuera del Geofence.")
            if self.going != False: self.mc.stop()
            self._stopGo()

        elif _checkComplexScenario(self, x_new, y_new):
            logging.info(f"[Dron] Cambiando la direccion. Fuera del Geofence.")
            if self.going != False: self.mc.stop()
            self._stopGo()

        time.sleep(0.1) # to not saturate the code



# Primary function to change the heading of the drone (absolute values 0 - 360) (though maybe it can admit -180 to 180)
def changeHeading (self, absoluteDegrees, blocking=True, callback=None, params = None):
    if self.state == 'flying':
        if blocking:
            self._changeHeading(absoluteDegrees)
        else:
            changeHeadingThread = threading.Thread(target=self._changeHeading, args=[absoluteDegrees, callback, params])
            changeHeadingThread.start()
        logging.info(f"[Dron] Cambiando la direccion.")
        return True
    else:
        logging.info(f"[Dron] No esta volando.")
        return False

# Secondary function to change the heading of the drone (absolute values 0 - 360) (though maybe it can admit -180 to 180)
def _changeHeading(self, absoluteDegrees, callback=None, params=None):
    # Actual yaw in degrees (-180 a +180) (inverted)
    current_yaw = -self.attitude[2]

    # Check the direction and correct
    if current_yaw < 0:
        current_yaw += 360
    if absoluteDegrees < 0:
        absoluteDegrees += 360
    target_yaw = absoluteDegrees % 360

    # Calculate the minimum delta in the range (-180, +180]
    delta = (target_yaw - current_yaw + 540) % 360 - 180

    # Rotate in the direction of the delta (5-degree margin)
    if delta > 5:
        # positive delta → left
        self.mc.turn_right(delta)
    elif delta < -5:
        # negative delta → right
        self.mc.turn_left(-delta)
    # if delta == 0 → already facing the heading

    # Wait a bit to change direction
    time.sleep(1)

    # Callback
    if callback:
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

