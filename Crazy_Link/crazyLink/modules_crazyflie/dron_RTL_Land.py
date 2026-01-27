import threading
import time
import logging
import math

# Secondary function in order to land or do RTL
def _goDown(self, mode, callback=None, params = None):
    # Select the mode
    if mode == 'LAND':
        self.state = 'landing' # For double check, and for RC script
        # Stop the drone and land directly
        self.mc.stop()
        self.going = False  # in case of staying in nav mode
        time.sleep(0.2)
        velocity = self.move_speed
        self.mc.land(velocity)
        self.state = "connected"
    else:
        self.state = 'returning'  # For double check, and for RC script
        self.going = False # in case of staying in nav mode
        time.sleep(0.2)
        # Obtain the position of the drone respect the room frame
        x, y, z = self.position
        dx_w = -x
        dy_w = y

        # Obtain the heading of the drone (inverted)
        yaw_rad = -math.radians(self.attitude[2])

        # Change the frame of the room into the drones frame
        dx_body = dx_w * math.cos(yaw_rad) + dy_w * math.sin(yaw_rad)
        dy_body = -dx_w * math.sin(yaw_rad) + dy_w * math.cos(yaw_rad)

        # Obtain the speed, stop the drone and wait
        velocity = self.move_speed
        self.mc.stop()
        time.sleep(0.5)

        # Move the drone to the estimated center of the room
        self.mc.move_distance(dx_body, -dy_body,0, velocity)   # Change the sign due Crazyflie library

        # Allow time to reach the target
        timeout = 6
        start_time = time.time()
        while time.time() - start_time < timeout:
            if abs(x) < 0.4 and abs(y) < 0.4:
                time.sleep(1)
                break
            time.sleep(1)
            logging.info(f"[Dron] Moviendo el dron al punto estimado de aterrizaje.")

        self.state = 'landing'
        self.mc.stop()
        time.sleep(0.2)
        self.mc.land(velocity)
        time.sleep(1)
        logging.info(f"[Dron] Aterrizado.")
        self.state = "connected"

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

# Primary function in order to do an RTL (this RTL will take the actual altitude without geocage consideration)
def RTL (self, blocking=True, callback=None, params = None):
    # Check the state
    if self.state == 'flying':
        self.state = 'returning'
        logging.info(f"[Dron] Aterrizando en RTL.")
        if blocking:
            self._goDown('RTL', callback, params)
        else:
            goingDownThread = threading.Thread(target=self._goDown, args=['RTL', callback, params,])
            goingDownThread.start()
        return True
    else:
        return False

# Primary function in order to do a LAND (this landing will be without geocage consideration)
def Land (self, blocking=True, callback=None, params = None):
    # Check the state
    if self.state == 'flying' or self.state == 'returning':
        self.state = 'landing'
        logging.info(f"[Dron] Aterrizando.")
        if blocking:
            self._goDown('LAND', callback, params)
        else:
            goingDownThread = threading.Thread(target=self._goDown, args=['LAND', callback, params,])
            goingDownThread.start()
        return True
    else:
        return False

