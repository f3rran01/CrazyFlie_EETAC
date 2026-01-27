import json
import math
import threading
import time

# Secondary function: It obtains the basic parameters of the drone flight
def _send_local_telemetry_info(self, process_local_telemetry_info):
    self.sendLocalTelemetryInfo = True
    while self.sendLocalTelemetryInfo:
        local_telemetry_info = {
            'state': self.state,
            'posX': self.position[0],
            'posY': -self.position[1],  # corrected value
            'posZ': self.position[2],
            'velX': self.velocity[0],
            'velY': -self.velocity[1],  # corrected value
            'velZ': self.velocity[2],
            'batt': self.battery_level,
            'pitch': self.attitude[1],
            'roll': self.attitude[0],
            'yaw': -self.attitude[2]     # corrected value
        }
        if self.id == None:
            process_local_telemetry_info (local_telemetry_info)
        else:
            process_local_telemetry_info (self.id, local_telemetry_info)
        time.sleep (1/self.frequency)

# Primary function to check the basic parameters of the drone
def send_local_telemetry_info(self, process_local_telemetry_info):
    telemetryThread = threading.Thread(target=self._send_local_telemetry_info, args = [process_local_telemetry_info,] )
    telemetryThread.start()

# Stop function of the primary one
def stop_sending_local_telemetry_info(self):
    self.sendLocalTelemetryInfo = False