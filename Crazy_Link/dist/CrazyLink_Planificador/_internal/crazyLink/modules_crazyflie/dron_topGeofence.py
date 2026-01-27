import logging
import time

# Secondary function that makes the action: startTopGeofence
def _checkTopGeofence (self, alt):
    # Check if the height of the drone is inside bounds.
    if self.checkMaxAlt == True:
        if alt >= self.maxAltGeofence:
                logging.warning("[Dron] Dentro de zona de exclusion superior.")

                callback, params = self.additional_data_top

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

                return True
        else:
                return False
    else:
            return False

# Alternative function in order to move the drone inside the Geofence
def _moveTopGeofence (self):
    if self.mc != None:
        if self.checkMaxAlt == True:
            if self.position[2] > self.maxAltGeofence:
                correction = abs(self.position[2] - self.maxAltGeofence)
                self.mc.down(correction)
                logging.warning("[Dron] Dentro de zona de exclusion superior, moviendo dron.")
                time.sleep(1.5)

# Primary function to start the top Geofence
# The callback is activated when the drone tries to move outside this geofence.
# Active movement of this geofence is not applied.
def startTopGeofence (self, maxAlt,callback=None, params = None):
    self.maxAltGeofence = maxAlt
    self.checkMaxAlt = True
    self.additional_data_top = [callback, params]

# Function to stop the top geofence
def stopTopGeofence (self):
    self.checkMinAlt = False
