

import threading
import time
import logging
import math
import threading

from shapely.geometry import Point, Polygon, MultiPolygon
from shapely.ops import nearest_points

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.utils import uri_helper
from cflib.utils.multiranger import Multiranger


class Dron(object):

    def __init__(self, id=None):
        logging.basicConfig(level=logging.INFO)
        self.flightMode = 'loiter'  # It is not used
        self.id = id
        self.state = "disconnected"
        ''' the only ones:
                  connected
                  arming
                  armed
                  takingOff
                  flying
                  returning
                  landing
              '''

        # General drone data
        self.position = [0, 0, 0]
        self.velocity = [0, 0, 0]
        self.battery_level = 0

        self.alt = None
        self.flow_data = {}
        self.range_data = {}

        self.going = False       # Used in dron_nav
        self.navSpeed = 0.2      # Used in dron_nav (in meters per second)
        self.move_speed = 0.3    # General drone speed, Used in dron_mov, dron_altitude, etc (in meters per second)
        self.direction = 'Stop'  # Used in dron_nav

        # Geofence bottom and top
        self.checkMinAlt = False
        self.minAltGeofence  = None
        self.additional_data_bottom = []    # List used to communicate the geofence info with check function (all them inside the same script)

        self.checkMaxAlt = False
        self.maxAltGeofence  = None
        self.additional_data_top = []       # List used to communicate the geofence info with check function (all them inside the same script)

        # Geofence simple
        self.checksimpleGeofence = False
        self.simpleGeofence = None
        self.additional_data_simple = []    # List used to communicate the geofence info with check function (all them inside the same script)

        # Geofence complex
        self.checkcomplexGeofence = False
        self.complexGeofence = None
        self.additional_data_complex = []   # List used to communicate the geofence info with check function (all them inside the same script)

        self.step = 0.5             # Used in dron_mov. It represents the number of meters the drone moves in each step.
        self.frequency = 4          # Packet of telemetry per second (this is only declarative, to change go to connect function)
        self.sendLocalTelemetryInfo = False # For dron_local_telemetry
        self.sendParams = False     # For dron_parameters

        # There are other variables hidden in the functions, but not like general ones

    from crazyLink.modules_crazyflie.dron_connect import connect, disconnect, setup_attitude_log,setup_position_log,setup_flow_deck, log_attitude_callback,log_flow_callback,log_range_callback,log_zrange_callback,log_pos_callback,detect_and_configure_multiranger
    from crazyLink.modules_crazyflie.dron_arm import arm, _arm, reset_kalman
    from crazyLink.modules_crazyflie.dron_takeOff import takeOff, _takeOff
    from crazyLink.modules_crazyflie.dron_RTL_Land import RTL, Land, _goDown
    from crazyLink.modules_crazyflie.dron_nav import go, _go, _startGo, _stopGo, changeHeading, _changeHeading, changeNavSpeed,_checkPosition
    from crazyLink.modules_crazyflie.dron_goto import goto, _goto, _distanceToDestinationInMeters
    from crazyLink.modules_crazyflie.dron_custom_telemetry import getParams, _getParams, stop_sending_params
    from crazyLink.modules_crazyflie.dron_local_telemetry import send_local_telemetry_info, _send_local_telemetry_info, \
        stop_sending_local_telemetry_info
    from crazyLink.modules_crazyflie.dron_altitude import change_altitude, _change_altitude
    from crazyLink.modules_crazyflie.dron_move import move_distance, _move_distance, setMoveSpeed, _checkSpeedZero
    from crazyLink.modules_crazyflie.dron_RC_override_back import send_rc, _send_rc, rc_to_normalized
    from crazyLink.modules_crazyflie.dron_bottomGeofence import startBottomGeofence, stopBottomGeofence, \
        _moveBottomGeofence, _checkBottomGeofence
    from crazyLink.modules_crazyflie.dron_topGeofence import stopTopGeofence, startTopGeofence, _moveTopGeofence, \
        _checkTopGeofence
    from crazyLink.modules_crazyflie.dron_geofence import _watchSimpleScenario, _moveSimpleScenario, _checkSimpleScenario, \
        setSimpleScenario, deleteSimpleScenario
    from crazyLink.modules_crazyflie.dron_complex_geofence import _moveComplexScenario, _checkComplexScenario, _setComplexScenario, deleteComplexScenario, setComplexScenario

