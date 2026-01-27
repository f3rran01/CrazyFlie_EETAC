import threading
import time
import logging
from crazyLink.modules_crazyflie.dron_bottomGeofence import  _checkBottomGeofence
from crazyLink.modules_crazyflie.dron_topGeofence import _checkTopGeofence
from crazyLink.modules_crazyflie.dron_geofence import _checkSimpleScenario
from crazyLink.modules_crazyflie.dron_complex_geofence import _checkComplexScenario
import math
import threading

# Primary function to move the drone using PWM and velocities
# This functions allows the user to give a PWM pulse of 1000 min - 2000 max microseconds, for roll, pitch, throttle and yaw.
# Additionally, permits to make it blocking or not, choose between bare mode or not (I recommend to leave it this) and modify movement velocities.
def send_rc(self, roll, pitch, throttle, yaw, blocking=True, bare_mode=False, velocity_horizontal=0.3, velocity_vertical=0.2, yaw_velo=20):
    # Check the state of the drone
    if self.state == "flying":
        logging.info(f"[Dron] Moviendo el dron.")

        if blocking:
            self._send_rc(roll, pitch, throttle, yaw, bare_mode, velocity_horizontal, velocity_vertical, yaw_velo)
        else:
            rcThread = threading.Thread(target=self._send_rc, args=[roll, pitch, throttle, yaw, bare_mode, velocity_horizontal, velocity_vertical, yaw_velo,])
            rcThread.start()
            return True
    else:
        logging.info(f"[Dron] No esta volando.")


# Secondary function, input trim values of a controller
# Allows 2 methods, second method is more recommended, additionally, optional velocities can be applied.
def _send_rc(self, roll, pitch, throttle, yaw, bare_mode=False, velocity_horizontal=0.3, velocity_vertical=0.2, yaw_velo=20):

    if bare_mode:
        # First mode
        # Send normalized RC commands to the drone via MotionCommander.
        # roll, pitch, yaw in [-1,1], throttle in [0,1]
        try:
            # Normalizes values
            roll_n = rc_to_normalized(roll, 'rc')
            pitch_n = rc_to_normalized(pitch, 'rc')
            yaw_n = rc_to_normalized(yaw, 'rc')
            throttle_n = rc_to_normalized(throttle, 'throttle')

            # Sends setpoints
            self.mc.commander.send_setpoint(roll_n, pitch_n, yaw_n, throttle_n)

            return True

        except Exception as e:
            print(f"Error enviando comando RC: {e}")
            return False
    else:
        # Second mode
        try:
            # Check if the controller has any drift and compensate
            if 1600 > throttle > 1400:
                throttle = 1500

            if 1600 >  roll > 1400:
                roll = 1500

            if 1600 > pitch > 1400:
                pitch = 1500

            if 1600 > yaw > 1400:
                yaw = 1500

            # Calculate a proportional controller
            roll = (roll - 1500)
            if roll != 0:
                roll = roll/500

            pitch = (pitch - 1500)
            if pitch != 0:
                pitch = pitch / 500

            yaw = (yaw - 1500)
            if yaw != 0:
                yaw = yaw / 500

            throttle = (throttle - 1500)
            if throttle != 0:
                throttle = throttle / 500

            # If the distance to the ground is so small don't allow the user go down.
            if self.position[2] < 0.05:
                if throttle < 0:
                    throttle = 0

            # Check if the drone is out of bounds and permit to move in action
            # Declaration of the variables
            dx_body = 0
            dy_body = 0
            dz_body = 0

            # Estimate the future position (2-4 times the sample frequency) (arbitrary number)
            dx_body = velocity_horizontal * pitch * 0.4
            dy_body = velocity_horizontal * roll * 0.4
            dz_body = velocity_vertical * throttle * 0.4

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
            if _checkSimpleScenario(self, x_new, y_new) or _checkBottomGeofence(self,z_new) or _checkTopGeofence(self, z_new):
                logging.info(f"[Dron] Fuera del Geofence.")
                if self.state == 'flying': self.mc.stop()

            elif _checkComplexScenario(self, x_new, y_new):
                logging.info(f"[Dron] Fuera del Geofence.")
                if self.state == 'flying': self.mc.stop()

            else:
                # Starts linear movements
                self.mc.start_linear_motion(velocity_horizontal*pitch, -velocity_horizontal*roll, velocity_vertical*throttle, yaw_velo*yaw)  # Change sign in lateral due frame convention

        except Exception as e:
            print(f"Error enviando comando RC: {e}")
            return False

# Tertiary function to normalize trim values
def rc_to_normalized(value, channel='throttle'):
    # Converts a typical RC value (1000–2000) to a normalized value for Crazyflie.
    # For roll, pitch, yaw: scales to [-1, 1]
    # For throttle: scales to [0, 1]
    if channel == 'throttle':
        # throttle usually ranges from 1000 (min) to 2000 (max) -> 0 to 1
        normalized = (value - 1000) / 1000
        # Limit to [0, 1]
        return max(0.0, min(1.0, normalized))
    else:
        # roll, pitch, yaw: 1000 (min) -> -1, 1500 (center) -> 0, 2000 (max) -> +1
        normalized = (value - 1500) / 500
        # Limit to [-1, 1]
        return max(-1.0, min(1.0, normalized))




