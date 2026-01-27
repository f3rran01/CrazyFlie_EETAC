import pygame
import time
from crazyLink.Dron_crazyflie import Dron
import time

# Initialize Pygame and the joystick
pygame.init()
pygame.joystick.init()

# Check if joystick is connected
if pygame.joystick.get_count() == 0:
    print("No joystick connected")
    exit()

# Initiate joystick
joystick = pygame.joystick.Joystick(0)
joystick.init()
print(f"Joystick detected: {joystick.get_name()}")

# Convert axis value (-1 to 1) to 1000-2000 PWM
def axis_to_pwm(value):
    return int(1500 + value * 500)

# Define flight states
takingoff = False
landing = False

# Create drone object, connect,arm and optionally create geofences
try:
    dron = Dron()
    dron.connect()
    print ('conectado')
    time.sleep(2)
    #dron.setSimpleScenario([1,1])   # Simple geofence at 1 m pitch, 1 m roll
    #dron.startTopGeofence(0.75)     # Top geofence at 0.75 m
    dron.arm()
    print ('armado')
    dron.takeOff(1)
    takingoff == True
    time.sleep(2)
except:
    pass

# Check periodically joystick data and move the drone accordingly
try:
    while True:
        pygame.event.pump()  # Update joystick events

        # Read axes
        left_x = joystick.get_axis(2)   # Roll
        left_y = joystick.get_axis(1)   # Throttle
        right_x = joystick.get_axis(0)  # Yaw
        right_y = joystick.get_axis(3)  # Pitch

        # Convert axes to PWM (1000-2000)
        roll = axis_to_pwm(left_x)
        throttle = axis_to_pwm(-left_y)
        yaw = axis_to_pwm(right_x)
        pitch = axis_to_pwm(-right_y)

        # Print values
        print(f"Throttle: {throttle}, Roll: {roll}, Pitch: {pitch}, Yaw: {yaw}")
        
        # Detect buttons for takeoff and landing
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0 and takingoff == False:  # A button (xbox controller)
                    print("A button pressed")
                    takingoff = True
                    dron.takeOff(0.5)

            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 1 and landing == False:  # B button (xbox controller) 
                    print("B button pressed")
                    landing = True
                    dron.Land()

            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 3 and landing == False:  # Y button (xbox controller)
                    print("Y button pressed")
                    landing = True
                    dron.RTL()
                    
        # When the drone is airborne, allow drone movement.
        if takingoff == True and landing == False:
            dron.send_rc(roll, pitch, throttle, yaw)

        time.sleep(0.1)

except KeyboardInterrupt:
    print("end")

finally:
    pygame.quit()
