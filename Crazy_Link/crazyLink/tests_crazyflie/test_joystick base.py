import pygame # instalar pygame
import time
import pywinusb.hid as hid

def cable ():
    global joystick
    pygame.event.pump()

    # Leer valores de los ejes
    axes = [joystick.get_axis(i) for i in range(joystick.get_numaxes())]
    # Leer estado de botones
    buttons = [joystick.get_button(i) for i in range(joystick.get_numbuttons())]
    # Leer hats (crucetas digitales)
    hats = [joystick.get_hat(i) for i in range(joystick.get_numhats())]
    return axes, buttons, hats

def inalambrico(data):
    # asegurarnos que el paquete tiene al menos 7 bytes
    if len(data) < 7:
        return

    # Sticks
    lx = data[3]
    ly = data[4]
    rx = data[1]
    ry = data[2]

    # Normalizar a -1..1
    def normalize(val):
        return (val - 128) / 128.0  # suponiendo rango 0–255

    axes = [normalize(lx), normalize(ly), normalize(rx), normalize(ry)]

    # Botones

    buttons = [0]*12
    if data[5] == 31:
        buttons[0] = 1
    if data[5] == 47:
        buttons[1] = 1
    if data[5] == 79:
        buttons[2] = 1
    if data[5] == 143:
        buttons[3] = 1
    if data[6] == 1:
        buttons[4] = 1
    if data[6] == 2:
        buttons[5] = 1
    if data[6] == 4:
        buttons[6] = 1
    if data[6] == 8:
        buttons[7] = 1
    if data[6] == 16:
        buttons[8] = 1
    if data[6] == 32:
        buttons[9] = 1
    if data[6] == 64:
        buttons[10] = 1
    if data[6] == 128:
        buttons[11] = 1


    # Hat/D-Pad
    hats = (0,0)
    if data[5] == 6:
        hats = (-1,0)
    if data[5] == 2:
        hats = (1, 0)
    if data[5] == 0:
        hats = (0,1)
    if data[5] == 4:
        hats = (0, -1)

    procesar(axes, buttons, hats)

def procesar (axes, buttons, hats):
    print("Ejes:", ["{:.2f}".format(a) for a in axes])
    print("Botones:", buttons)
    print("Hats:", hats)

    print("-" * 40)

# Inicializar pygame y el módulo de joystick
pygame.init()
pygame.joystick.init()

# Verificar si hay joysticks conectados
print ("Numero de joystics :", pygame.joystick.get_count())
if pygame.joystick.get_count() == 0:
    print("No hay joysticks conectados.")
    pygame.quit()
    exit()

# Obtener el primer joystick
joystick = pygame.joystick.Joystick(0)
joystick.init()
print(f"Joystick detectado: {joystick.get_name()}")
if joystick.get_name() == 'USB Gamepad' or joystick.get_name() == 'Generic USB Joystick':
    codificador = cable
    print("Joystick con cable")
    try:
        while True:
            axes, buttons, hats = codificador()
            procesar (axes, buttons, hats)
            time.sleep(0.1)  # Pequeña pausa para no saturar la consola

    except KeyboardInterrupt:
        print("\nPrograma terminado por el usuario.")

    finally:
        joystick.quit()
        pygame.quit()
elif joystick.get_name() == 'Twin USB Joystick':
    codificador = inalambrico
    print("Joystick inalambrico")
    all_hids = hid.HidDeviceFilter().get_devices()
    if not all_hids:
        print("⚠ No hay dispositivos HID.")
        exit()
    for dev in all_hids:
        if 'Twin' in dev.vendor_name:
            # devices.append (dev)
            device = dev
            device.open()
            device.set_raw_data_handler(inalambrico)

            try:
                while True:
                    time.sleep(0.5)
            except KeyboardInterrupt:
                device.close()
                # devices[1].close()
                print("Cerrado.")

            finally:
                joystick.quit()
                pygame.quit()
            break

else:
    print ("Joystick no reconocido")
