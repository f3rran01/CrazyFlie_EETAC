import threading
import time
import logging
import math
from shapely.geometry import Point, Polygon, MultiPolygon
from shapely.ops import nearest_points
from crazyLink.modules_crazyflie.dron_RTL_Land import _goDown
"""
Example of input

# Main polygon  (x,y) (in comparison with dron coordinates [lateral, transversal])
inside_polygon = [
    (0.0, 0.0),(20.0, 0.0),(20.0, 20.0),(0.0, 20.0)
]

# Exclusion zones (optional): each hole/zone at least +3 vertices
exclusion = [
    [(2.0, 2.0),(5.0, 2.0),(5.0, 5.0),(2.0, 5.0)],
    [(12.0, 12.0),(18.0, 12.0),(18.0, 18.0),(12.0, 18.0)]
]
"""
# Primary function to set the complex geofence, as input it admits a flyable polygon and
# optionally a list of exclusion holes/zones. Exclusion zones/holes rarely don't work, need further research/tests.
# The watchdog as the simple geofence, enables to check periodically the position of the drone and it case of, move the drone.
# Type can be None to return to the closest geofence point, as 'LAND' to make a landing or as 'RTL', to return to launch.
def setComplexScenario (self,inside_polygon, exclusion,type=None, blocking=True, callback=None, params = None, watchdog=True):
    # Pass all the data within a list to checkComplexScenario using a bypass.
    self.additional_data_complex = [type, callback, params]
    # Check the watchdog and the blocking action
    if blocking and watchdog==False:

        logging.info(f"[Dron] Geofence complejo creado.")
        self.checkcomplexGeofence = True
        self.complexGeofence = None
        self._setComplexScenario(inside_polygon, exclusion,type, watchdog, callback, params)
        return True
    else:
        logging.info(f"[Dron] Geofence complejo creado.")
        self.checkcomplexGeofence = True
        self.complexGeofence = None
        scenarioThread = threading.Thread(target=self._setComplexScenario, args=[inside_polygon, exclusion,type, watchdog, callback, params])
        scenarioThread.start()
        return True

# Primary function to disable the complex geofence
def deleteComplexScenario (self):
    self.checkcomplexGeofence = False
    return True

# Secondary function, it compiles all the data proportionate of polygons and acts in base of that
def _setComplexScenario(self, inside_polygon=None, exclusion=None, type=None, watchdog=True, callback=None, params=None):

    # Check if the polygon has enough vertices
    if inside_polygon is None or len(inside_polygon) < 3:
        logging.info(f"[Dron] Los datos proporcionados son incorrectos")
        return

    # Create the multipolygon depending on if the holes are proportionate
    try:
        if exclusion is None:
            poly = Polygon(inside_polygon)
        else:
            valid_holes = [hole for hole in exclusion if len(hole) >= 3]
            poly = Polygon(inside_polygon, holes=valid_holes)

        multi_poly = MultiPolygon([poly])

        self.complexGeofence = multi_poly
    except Exception as e:
        logging.error(f"[Dron] Error al crear el polígono: {e}")
        return

    # Start a watchdog to check periodically the state of the drone
    if watchdog:
        while self.checkcomplexGeofence:
            self._moveComplexScenario(type,callback, params)
            time.sleep(0.3)
    else:
        self._moveComplexScenario(type,callback, params)
        time.sleep(0.3)
    return

# Tertiary function, it is used to check the position of the drone and also to move it
def _moveComplexScenario(self, type=None, callback=None, params = None):

    # Check the state of the drone
    if self.state == "flying" and self.checkcomplexGeofence == True:
        # Obtain the position of the drone
        x, y, z = self.position
        y = -y  # correction

        # Y is the lateral drone (x-axis of the point), X is the transversal of the drone (y-axis of the point)
        p = Point(y, x)

        # Retrieve data of the polygons used
        multi_poly = self.complexGeofence
        area_principal = multi_poly.geoms[0]
        zonas_exclusion = multi_poly.geoms[1:] if len(multi_poly.geoms) > 1 else []

        # Calculate the truly safe area: the main zone minus all the exclusions
        zona_segura = area_principal
        for zona in zonas_exclusion:
            zona_segura = zona_segura.difference(zona)

        # The point is either outside or in an exclusion zone
        if not zona_segura.contains(p):
            # Check the nearest point if it is not in the safe zone and the distance
            nearest_point = nearest_points(p, zona_segura)[1]
            dist = p.distance(nearest_point)

            # Divide if it is an exclusion zone or outside form the safe and the exclusion one
            if any(zona.contains(p) for zona in zonas_exclusion):
                status = "zona_exclusion"
            else:
                status = "fuera"

            # If the distance is greater than 20 cm, act, otherwise it doesn't (just a buffer zone) (it can be changed)
            if dist < 0.2:

                return

            else:
                # Stop the drone
                self.mc.stop()
                time.sleep(0.5)

                # Apply different actions depending on the type
                if type == 'LAND' or type == 'RTL':
                    self._goDown(self, type, callback, params)
                    return
                else:
                    # Calculate the deviation between the position and the nearest point inside the geofence multiplied by a factor
                    # This factor 1.1 can be changed, I used 1.1, it is small thought not too much
                    dx_w= (nearest_point.y - x)*1.1
                    dy_w = (nearest_point.x - y)*1.1

                    # Obtain the heading and correct it
                    yaw_rad = -math.radians(self.attitude[2])

                    # Rotation based on the drone's coordinate axis. (Room --> drone)
                    dx_body = dx_w * math.cos(yaw_rad) + dy_w * math.sin(yaw_rad)
                    dy_body = -dx_w * math.sin(yaw_rad) + dy_w * math.cos(yaw_rad)

                    # Move the drone (plus a negative correction of the move)
                    self.mc.move_distance(dx_body,-dy_body , 0, self.move_speed)

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
                    return
    return


# Secondary function to check if the drone is inside or outside the complex geofence
# As input the transversal position and the lateral position of the drone
def _checkComplexScenario(self, transversal, lateral):
    # Check if the geofence is active
    if self.checkcomplexGeofence:
        # We create a point with the data (lateral == x, tranversal == y)
        p = Point(lateral, transversal)

        # Obtain the geometrical figures
        multi_poly = self.complexGeofence
        area_principal = multi_poly.geoms[0]
        zonas_exclusion = multi_poly.geoms[1:] if len(multi_poly.geoms) > 1 else []

        # Calculate the truly safe area: the main zone minus all the exclusions
        zona_segura = area_principal
        for zona in zonas_exclusion:
            zona_segura = zona_segura.difference(zona)

        # The point is either outside or in an exclusion zone
        if not zona_segura.contains(p):
            # Check the nearest point if it is not in the safe zone and the distance
            nearest_point = nearest_points(p, zona_segura)[1]
            dist = p.distance(nearest_point)

            # Divide if it is an exclusion zone or outside form the safe and the exclusion one
            if any(zona.contains(p) for zona in zonas_exclusion):
                status = "zona_exclusion"
            else:
                status = "fuera"
            # Obtain data from bypass from setComplexScenario
            type, callback, params = self.additional_data_complex
            # Apply this data coming from the list
            if type == 'LAND' or type == 'RTL':
                self._goDown(self, type, callback, params)
            else:
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
