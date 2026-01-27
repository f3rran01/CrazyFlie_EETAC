import threading
import time
# This script gives a more complex data of the drone situation in comparison with Local_telemetry

# Secondary function, it gives the parameters, as a results it gives a dictionary
def _getParams(self, parameters, process_params):
    self.sendParams = True

    while  self.sendParams:
        result = {}  # Flat dictionary
        for param in parameters:
            if param == 'position':
                result['Position x'] = self.position[0]
                result['Position y'] = -self.position[1]  # corrected value
                result['Position z'] = self.position[2]

            if param == 'velocity':
                result['Velocity x'] = self.velocity[0]
                result['Velocity y'] = -self.velocity[1]  # corrected value
                result['Velocity z'] = self.velocity[2]

            if param == 'battery':
                result['Battery'] = self.battery_level

            if param == 'attitude':
                result['Pitch'] = self.attitude[1]
                result['Roll'] = self.attitude[0]
                result['Yaw'] = -self.attitude[2]     # corrected value

            if param == 'flow_data':
                result['Flow velocity x'] = self.flow_data['deltaX']
                result['Flow velocity y'] = self.flow_data['deltaY']

            if param == 'altitude':
                result['Altitude z'] = self.alt

            # Check if the object has been created (in case the drone does not have the Range Finder deck)
            if param == 'range_data' and  self.has_range_deck == True:
                result['Range front'] = self.range_data['front']
                result['Range back'] = self.range_data['back']
                result['Range left'] = self.range_data['left']
                result['Range right'] = self.range_data['right']


        # If there is no function as input, return directly without nothing, otherwise the function
        if process_params is None:
            self.sendParams = False
            return
        else:
            if self.id == None:
                process_params(result)
            else:
                process_params(self.id, result)

        time.sleep(1 / self.frequency)

    return

# Primary function to start sending parameters, as input a list of the desired parameters
def getParams(self, parameters, process_params=None):
        getParamsThread = threading.Thread(target=self._getParams, args=[parameters,process_params,])
        getParamsThread.start()

# Function to stop sending paramters
def stop_sending_params(self):
    self.sendParams = False
