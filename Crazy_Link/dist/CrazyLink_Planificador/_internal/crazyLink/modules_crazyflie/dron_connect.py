import time
import logging
import math
import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie

# Primary function to connect the dron, the frequency of actualization of data and the radio sik
def connect(self,freq = 4, cf_uri="radio://0/80/2M/E7E7E7E7E7"):
    #print ("Entramos en conectar")
    self.frequency = freq

    try:
        # Initialize the drivers CRTP (Crazyflie)
        cflib.crtp.init_drivers()
        # Create Crazyflie and SyncCrazyflie
        self.cf = Crazyflie(rw_cache='./cache')
        self.cf_ctrl = SyncCrazyflie(cf_uri, cf=self.cf)
        self.cf_ctrl.open_link()
        self.mc = None  # With arm function, it is modified; it is the drone's actuator (high-level) (the low-level actuator is not recommended)

        # Check the connection with is_link_open()
        if self.cf_ctrl.is_link_open():
            logging.info(f"[Dron] Conectado a Crazyflie ({cf_uri}).")

            # Configurar los distintos logs
            self.setup_position_log()  # Mandatory to self-positioning
            self.setup_attitude_log()  # Mandatory to self-positioning

            self.setup_flow_deck()              # Optional though deck (FlowV2) is mandatory
            self.detect_and_configure_multiranger()   # Optional (the log of the Multi-RangeFinder is detected and applied)

            logging.info("[Dron] Listo para armar.")
            self.state = "connected"

        else:
            logging.error("[Dron] No se pudo conectar al Crazyflie.")
            self.state = "disconnected"

    except Exception as e:
        logging.error("No se pudo conectar al Crazyflie o radio desconectada.")
        self.state = "disconnected"

# In order to disconnect the drone
def disconnect(self):
    logging.info("[Dron] Cerrando conexión con Crazyflie.")
    self.cf_ctrl.close_link()
    self.state = "disconnected"
    return True

# Secondary function to log the main variables of the drone
def setup_position_log(self):
        # Declare the variables
        logging.info("[Dron] Configurando log de posición y velocidad.")
        log_pos = LogConfig(name='Position', period_in_ms=200)
        log_pos.add_variable('stateEstimate.x', 'float')
        log_pos.add_variable('stateEstimate.y', 'float')
        log_pos.add_variable('stateEstimate.z', 'float')
        log_pos.add_variable('stateEstimate.vx', 'float')
        log_pos.add_variable('stateEstimate.vy', 'float')
        log_pos.add_variable('stateEstimate.vz', 'float')

        log_bat = LogConfig(name='Battery', period_in_ms=200)
        log_bat.add_variable('pm.vbat', 'float')

        try:
            # Try to start the callback function
            self.cf.log.add_config(log_pos)
            log_pos.data_received_cb.add_callback(
                lambda timestamp, data, logconf: self.log_pos_callback(timestamp, data, logconf))

            self.cf.log.add_config(log_bat)
            log_bat.data_received_cb.add_callback(
                lambda timestamp, data, logconf: self.log_pos_callback(timestamp, data,logconf))

            log_pos.start()
            log_bat.start()

        except Exception as e:
            logging.error(f"[Dron] Error configurando log de posición: {e}")

# Main callback function of the battery and the position
def log_pos_callback(self, timestamp, data, logconf):
        # Occasionally it may return data equal to position 0, which is impossible.
        if data.get('stateEstimate.x', 0) != 0 and data.get('stateEstimate.y', 0) != 0 and data.get('stateEstimate.z', 0) != 0:
            self.position = [
                round(data.get('stateEstimate.x', 0), 3),
                round(data.get('stateEstimate.y', 0), 3),
                round(data.get('stateEstimate.z', 0), 3)
            ]

            self.velocity = [
                round(data.get('stateEstimate.vx', 0), 3),
                round(data.get('stateEstimate.vy', 0), 3),
                round(data.get('stateEstimate.vz', 0), 3)
            ]
        self.battery_level = round(data.get('pm.vbat', 0), 2)
        # logging.info(f"Posición: {self.position}, Batería: {self.battery_level}V")

    # --------------------------------------------------------------------------------------#
# Secondary function to log the attitude variables
def setup_attitude_log(self):
        # Declare the variables
        logging.info("[Dron] Configurando log de actitud (roll, pitch, yaw).")
        log_attitude = LogConfig(name='Attitude', period_in_ms=200)
        log_attitude.add_variable('stateEstimate.roll', 'float')
        log_attitude.add_variable('stateEstimate.pitch', 'float')
        log_attitude.add_variable('stateEstimate.yaw', 'float')

        try:
            # Try to start the callback function
            self.cf.log.add_config(log_attitude)
            log_attitude.data_received_cb.add_callback(
                lambda timestamp, data, logconf: self.log_attitude_callback(timestamp, data, logconf))
            log_attitude.start()
        except Exception as e:
            logging.error(f"[Dron] Error configurando log de actitud: {e}")

# Main callback function of the attitude
def log_attitude_callback(self, timestamp, data, logconf):
    self.attitude = [
        round(data.get('stateEstimate.roll', 0), 3),
        round(data.get('stateEstimate.pitch', 0), 3),
        round(data.get('stateEstimate.yaw', 0), 3)
    ]

    yaw_rad = data.get('stateEstimate.yaw', 0)
    self.heading = math.degrees(yaw_rad)


# --------------------------------------------------------------------------------------#

# Secondary function to log the FlowDeckV2 parameters
def setup_flow_deck(self):
    logging.info("[Dron] Configurando Flow Deck V2 (motion + z‑range).")

    # Brute optical flow (deltaX, deltaY)
    log_flow = LogConfig(name='FlowDeckV2_Motion', period_in_ms=200)
    
    # motion.deltaX, motion.deltaY (ticks of the optical flow)
    log_flow.add_variable('motion.deltaX', 'int16_t')
    log_flow.add_variable('motion.deltaY', 'int16_t')

    # Height coming from laser ranger at flow deck v2
    log_z = LogConfig(name='FlowDeckV2_Zrange', period_in_ms=200)
    log_z.add_variable('range.zrange', 'float')  # mm

    try:
        # Try to start the callback function
        self.cf.log.add_config(log_flow)
        log_flow.data_received_cb.add_callback(self.log_flow_callback)
        log_flow.start()

        
        self.cf.log.add_config(log_z)
        log_z.data_received_cb.add_callback(self.log_zrange_callback)
        log_z.start()

    except Exception:
        logging.exception("[Dron] Error configurando Flow‑Deck V2")


def log_flow_callback(self, timestamp, data, logconf):
    # print(f"{logconf.name} keys:", list(data.keys()))
    self.flow_data = {
        'deltaX': data.get('motion.deltaX', 0),
        'deltaY': data.get('motion.deltaY', 0)
    }


def log_zrange_callback(self, timestamp, data, logconf):
    # print(f"{logconf.name} zrange raw:", data.get('range.zrange'))
    self.alt = round(data.get('range.zrange', 0.0) / 1000.0, 3)  # convierte mm a m

    # --------------------------------------------------------------------------------------#

# Secondary function to log the FlowDeckV2 parameters
def detect_and_configure_multiranger(self):

    try:
        # Detect if deck is presence
        val = self.cf.param.get_value('deck.bcMultiranger')
        if val == '1':
            self.has_range_deck = True
            logging.info("[Dron] MultiRanger Deck detectado.")
        else:
            self.has_range_deck = False
            logging.info("[Dron] MultiRanger Deck NO detectado.")

    except Exception:
        logging.info("[Dron] deck.presence no disponible. Saltando MultiRanger.")
        self.has_range_deck = False
        return

    if self.has_range_deck:
        logging.info("[Dron] MultiRanger Deck detectado. Configurando log de rangos.")
        log_range = LogConfig(name='RangeFinder', period_in_ms=100)
        for var in ('range.front', 'range.back', 'range.left', 'range.right'):
            log_range.add_variable(var, 'float')
        try:
            # Try to initiate callback
            self.cf.log.add_config(log_range)
            log_range.data_received_cb.add_callback(self.log_range_callback)
            log_range.start()
            logging.info("[Dron] MultiRanger Deck: log iniciado correctamente.")
        except Exception:
            logging.exception("[Dron] Error configurando MultiRanger Deck")
    else:
        logging.info("[Dron] MultiRanger Deck NO detectado.")
        self.has_range_deck = False


def log_range_callback(self, timestamp, data, logconf):
    # Return if deck is not presence
    if not getattr(self, 'has_range_deck', False):
        return

    self.range_data = {
        'front': data.get('range.front', None),
        'back': data.get('range.back', None),
        'left': data.get('range.left', None),
        'right': data.get('range.right', None),
    }

