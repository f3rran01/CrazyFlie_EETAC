
import threading
import logging
import time
from cflib.positioning.motion_commander import MotionCommander

# Secondary function that makes the action: arm
def _arm(self, callback=None, params=None):
    try:
        # Select estimator; it is recommended to use the Kalman EKF (partially linear) "2" or the Kalman UKF (nonlinear) "3"
        self.cf.param.set_value('stabilizer.estimator', '2')

        # Restarts Kalman (estimator)
        self.reset_kalman()
        time.sleep(0.5)  # wait to stabilize

        # Create the MotionCommander (high-level controller) after setting up the estimator and Kalman
        self.mc = MotionCommander(self.cf_ctrl)
        # Change state of the drone
        self.state = "armed"
        logging.info("[Dron] Dron armado.")
    except Exception as e:
        logging.error(f"[Dron] Error al armar: {e}")

    if callback:
        if self.id is None:
            callback() if params is None else callback(params)
        else:
            callback(self.id) if params is None else callback(self.id, params)

# Primary function to arm te drone
def arm(self, blocking=True, callback=None, params=None):
    # Check the state
    if self.state == "connected":
        if blocking:
            self._arm(callback, params)
        else:
            arm_thread = threading.Thread(target=self._arm, args=(callback, params))
            arm_thread.start()
        return True
    else:
        logging.warning("[Dron] No conectado. No se puede armar.")
        return False

# Function to reset the filter of the drone
def reset_kalman(self):
    logging.info("[Dron] Reiniciando estimador Kalman...")
    self.cf.param.set_value('kalman.resetEstimation', '1')
    time.sleep(0.2)
    self.cf.param.set_value('kalman.resetEstimation', '0')
    time.sleep(0.2)
    logging.info("[Dron] Estimador Kalman reiniciado.")
