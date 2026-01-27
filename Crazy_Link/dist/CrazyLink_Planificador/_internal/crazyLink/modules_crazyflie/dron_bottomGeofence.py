import logging
import time

# Secondary function that makes the action: startBottomGeofence
def _checkBottomGeofence (self, alt):
    # Check if the height of the drone is inside bounds.
    if self.checkMinAlt == True:
        if alt <= self.minAltGeofence:
                logging.warning("[Dron] Dentro de zona de exclusion inferior.")

                callback, params = self.additional_data_bottom
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
def _moveBottomGeofence (self):
    if self.mc != None:
        if self.checkMinAlt == True:
            if self.position[2] < self.minAltGeofence:
                correction = abs(self.position[2] - self.minAltGeofence)
                self.mc.up(correction)
                logging.warning("[Dron] Dentro de zona de exclusion inferior, moviendo dron.")
                time.sleep(1.5)

# Primary function to start the bottom Geofence
# The callback is activated when the drone tries to move outside this geofence.
# Active movement of this geofence is not applied.
def startBottomGeofence (self, minAlt,callback=None, params = None):
    self.minAltGeofence = minAlt
    self.checkMinAlt = True
    self.additional_data_bottom=[callback,params]

# Function to stop the bottom geofence
def stopBottomGeofence (self):
    self.checkMinAlt = False
