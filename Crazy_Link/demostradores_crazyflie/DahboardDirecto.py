import tkinter as tk
import threading
from crazyLink.Dron_crazyflie import Dron
import math
import logging

# It creates the object and try to connect, finally it sets the speed to 2 m/s
def connect ():
    global dron, speedSldr
    dron = Dron()
    dron.connect()
    # cambiamos el color del boton
    connectBtn['text'] = 'Conectado'
    connectBtn['fg'] = 'white'
    connectBtn['bg'] = 'green'
    # fijamos la velocidad por defecto en el slider
    speedSldr.set(0.2)

# Arm the drone
def arm ():
    global dron
    dron.arm()
    armBtn['text'] = 'Armado'
    armBtn['fg'] = 'white'
    armBtn['bg'] = 'green'

# When the action is finished it changes the color (state) of the button
def inTheAir ():
    # ya ha alcanzado la altura de despegue
    takeOffBtn['text'] = 'En el aire'
    takeOffBtn['fg'] = 'white'
    takeOffBtn['bg'] = 'green'

# It takes off the drone, without blocking the action and adding a callback when the action is finished
def takeoff ():
    global dron
    # llamada no bloqueante. Cuando alcance la altura indicada ejecutará la función inTheAir
    dron.takeOff (0.5, blocking = False,  callback = inTheAir)
    takeOffBtn['text'] = 'Despegando...'
    takeOffBtn['fg'] = 'black'
    takeOffBtn['bg'] = 'yellow'

# It changes the button state when the drone tries to land
def onEarth (op):
    # estamos en tierra
    if op == 'land':
        # venimos de un aterrizaje
        landBtn['text'] = 'En tierra'
        landBtn['fg'] = 'white'
        landBtn['bg'] = 'green'
    else:
        # venimos de un RTL
        RTLBtn['text'] = 'En tierra'
        RTLBtn['fg'] = 'white'
        RTLBtn['bg'] = 'green'

# It lands the drone, without blocking the action, adding a callback and specifying a land action
def land ():
    global dron
    # llamada no bloqueante. El parámetro nos permitirá saber en onEarth que venimos de Land
    dron.Land(blocking = False,  callback = onEarth, params = 'land')
    landBtn['text'] = 'Aterrizando...'
    landBtn['fg'] = 'black'
    landBtn['bg'] = 'yellow'

# It lands the drone, without blocking the action, adding a callback and specifying a RTL action
def RTL():
    global dron
    # llamada no bloqueante. El parámetro nos permitirá saber en onEarth que venimos de RTL
    dron.RTL(blocking = False,  callback = onEarth, params = 'RTL')
    RTLBtn['text'] = 'Retornando...'
    RTLBtn['fg'] = 'black'
    RTLBtn['bg'] = 'yellow'

# It makes the dron go in a specific direction without blocking the user
def go (direction, btn):
    global dron, previousBtn
    # cambio el color del anterior boton clicado (si lo hay)
    if previousBtn:
        previousBtn['fg'] = 'black'
        previousBtn['bg'] = 'dark orange'

    # navegamos en la dirección indicada
    dron.go (direction,blocking=False)
    # pongo en verde el boton clicado
    btn['fg'] = 'white'
    btn['bg'] = 'green'
    # tomo nota de que este es el último botón clicado
    previousBtn = btn

# It makes the dron go in a specific direction (0.5 m) without blocking the user
def go_move (direction, btn):
    global dron, previousBtn
    # cambio el color del anterior boton clicado (si lo hay)
    if previousBtn:
        previousBtn['fg'] = 'black'
        previousBtn['bg'] = 'dark orange'

    # navegamos en la dirección indicada
    dron.move_distance ( direction, 0.5,blocking=False)
    # pongo en verde el boton clicado
    btn['fg'] = 'white'
    btn['bg'] = 'green'
    # tomo nota de que este es el último botón clicado
    previousBtn = btn

# Function that starts sending info about the drone
def startTelem():
    global stateParams
    stateParams = True
    dron.send_local_telemetry_info(checkTelem) # Llamo en hilo a la funcion de abajo

# This function obtains the data and shows it on the display.
def checkTelem(data):
    global altShowLbl, headingShowLbl, speedShowLbl, batShowLbl

    z = data.get('posZ', 0)
    vx = data.get('velX', 0)
    vy = data.get('velY', 0)
    vz = data.get('velZ', 0)
    speed = math.sqrt(vx**2 + vy**2 + vz**2)
    bat = data.get('batt', 0)
    heading = data.get('yaw', 0)

    if z is not None and vx is not None and vy is not None and vz is not None and heading is not None:
        altShowLbl['text'] = round(z, 2)
        headingShowLbl['text'] = round(heading, 2)
        speedShowLbl['text'] = round(speed, 2)
        batShowLbl['text'] = round(bat, 2)

# This function stops the telemetry sending
def stopTelem():
    global stateParams, dron
    stateParams = False
    dron.stop_sending_local_telemetry_info()

# This function makes the drone to change its heading
def changeHeading (heading):
    global dron
    global gradesSldr
    # cambiamos el heading según se haya seleccionado en el slider
    dron.changeHeading(int (heading),blocking=False)

# This function changes the speed of the drone
def changeNavSpeed (speed):
    global dron
    global speedSldr
    # cambiamos la velocidad de navegación/movimiento según se haya seleccionado en el slider
    dron.changeNavSpeed(float(speed))
    dron.setMoveSpeed(float(speed))

# This function creates the main window of the app
def crear_ventana():
    # Determine global variables
    global dron
    global altShowLbl, headingShowLbl,  speedSldr, gradesSldr, speedShowLbl,batShowLbl
    global connectBtn, armBtn, takeOffBtn, landBtn, RTLBtn
    global previousBtn # aqui guardaré el ultimo boton de navegación clicado
    global stateParams  # defino un valor de activacion de bucle para obtener parametros

    # Determine the class dron with None as a previous state
    dron = None
    # Button state
    previousBtn = None
    # Gives the state if tha pp gives the parametes
    stateParams = False

    # Creates the main window and divides it into a grid 11x2
    ventana = tk.Tk()
    ventana.title("Dashboard con conexión directa")
    # la interfaz tiene 10 filas y dos columnas
    ventana.rowconfigure(0, weight=1)
    ventana.rowconfigure(1, weight=1)
    ventana.rowconfigure(2, weight=1)
    ventana.rowconfigure(3, weight=1)
    ventana.rowconfigure(4, weight=1)
    ventana.rowconfigure(5, weight=1)
    ventana.rowconfigure(6, weight=1)
    ventana.rowconfigure(7, weight=1)
    ventana.rowconfigure(8, weight=1)
    ventana.rowconfigure(9, weight=1)
    ventana.rowconfigure(10, weight=1)
    ventana.columnconfigure(0, weight=1)
    ventana.columnconfigure(1, weight=1)

    # Disponemos los botones, indicando qué función ejecutar cuando se clica cada uno de ellos
    # Los tres primeros ocupan las dos columnas de la fila en la que se colocan
    connectBtn = tk.Button(ventana, text="Conectar", bg="dark orange", command = connect)
    connectBtn.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

    armBtn = tk.Button(ventana, text="Armar", bg="dark orange", command=arm)
    armBtn.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

    takeOffBtn = tk.Button(ventana, text="Despegar", bg="dark orange", command=takeoff)
    takeOffBtn.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

    # --------------------------------------------------------------------------------------#

    movFrame = tk.LabelFrame (ventana, text = "Mover 0.5 m")
    movFrame.grid(row=3, column=0, columnspan = 2, padx=50, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

    movFrame.rowconfigure(0, weight=1)
    movFrame.rowconfigure(1, weight=1)
    movFrame.rowconfigure(2, weight=1)
    movFrame.columnconfigure(0, weight=1)
    movFrame.columnconfigure(1, weight=1)
    movFrame.columnconfigure(2, weight=1)

    NWBtm = tk.Button(movFrame, text="Rec-Iz", bg="dark orange",
                      command=lambda: go_move("Forward-Left", NWBtm))
    NWBtm.grid(row=0, column=0, padx=2, pady=2, sticky=tk.N + tk.S + tk.E + tk.W)

    NoBtm = tk.Button(movFrame, text="Recto", bg="dark orange",
                      command=lambda: go_move("Forward", NoBtm))
    NoBtm.grid(row=0, column=1, padx=2, pady=2, sticky=tk.N + tk.S + tk.E + tk.W)

    NEBtm = tk.Button(movFrame, text="Rec-Der", bg="dark orange",
                      command=lambda: go_move("Forward-Right", NEBtm))
    NEBtm.grid(row=0, column=2, padx=2, pady=2, sticky=tk.N + tk.S + tk.E + tk.W)

    WeBtm = tk.Button(movFrame, text="Izquierda", bg="dark orange",
                      command=lambda: go_move("Left", WeBtm))
    WeBtm.grid(row=1, column=0, padx=2, pady=2, sticky=tk.N + tk.S + tk.E + tk.W)

    StopBtm = tk.Button(movFrame, text="Stop", bg="dark orange",
                        command=lambda: go_move("Stop", StopBtm))
    StopBtm.grid(row=1, column=1, padx=2, pady=2, sticky=tk.N + tk.S + tk.E + tk.W)

    EaBtm = tk.Button(movFrame, text="Derecha", bg="dark orange",
                      command=lambda: go_move("Right", EaBtm))
    EaBtm.grid(row=1, column=2, padx=2, pady=2, sticky=tk.N + tk.S + tk.E + tk.W)

    SWBtm = tk.Button(movFrame, text="Atras-Iz", bg="dark orange",
                      # command=lambda: go("SouthWest", SWBtn))
                      command=lambda: go_move("Back-Left", SWBtm))
    SWBtm.grid(row=2, column=0, padx=2, pady=2, sticky=tk.N + tk.S + tk.E + tk.W)

    SoBtm = tk.Button(movFrame, text="Atras", bg="dark orange",
                      command=lambda: go_move("Back", SoBtm))
    SoBtm.grid(row=2, column=1, padx=2, pady=2, sticky=tk.N + tk.S + tk.E + tk.W)

    SEBtm = tk.Button(movFrame, text="Atras-Der", bg="dark orange",
                      # command=lambda: go("SouthEast", SEBtn))
                      command=lambda: go_move("Back-Right", SEBtm))
    SEBtm.grid(row=2, column=2, padx=2, pady=2, sticky=tk.N + tk.S + tk.E + tk.W)

    # --------------------------------------------------------------------------------------#

    # Slider para seleccionar el heading
    gradesSldr = tk.Scale(ventana, label="Grados:", resolution=45, from_=0, to=360, tickinterval=45,
                              orient=tk.HORIZONTAL, command = changeHeading)
    gradesSldr.grid(row=4, column=0, columnspan=2,padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

    # los dos siguientes también están en la misma fila
    landBtn = tk.Button(ventana, text="Aterrizar", bg="dark orange", command=land)
    landBtn.grid(row=5, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

    RTLBtn = tk.Button(ventana, text="RTL", bg="dark orange", command=RTL)
    RTLBtn.grid(row=5, column=1, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

    # --------------------------------------------------------------------------------------#

    # este es el frame para la navegación. Pequeña matriz de 3 x 3 botones
    navFrame = tk.LabelFrame (ventana, text = "Navegación")
    navFrame.grid(row=6, column=0, columnspan = 2, padx=50, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

    navFrame.rowconfigure(0, weight=1)
    navFrame.rowconfigure(1, weight=1)
    navFrame.rowconfigure(2, weight=1)
    navFrame.columnconfigure(0, weight=1)
    navFrame.columnconfigure(1, weight=1)
    navFrame.columnconfigure(2, weight=1)

    # al clicar en cualquiera de los botones se activa la función go a la que se le pasa la dirección
    # en la que hay que navegar y el boton clicado, para que la función le cambie el color
    NWBtn = tk.Button(navFrame, text="Rec-Iz", bg="dark orange",
                        command= lambda: go("Forward-Left", NWBtn))
    NWBtn.grid(row=0, column=0, padx=2, pady=2, sticky=tk.N + tk.S + tk.E + tk.W)

    NoBtn = tk.Button(navFrame, text="Recto", bg="dark orange",
                        command= lambda: go("Forward", NoBtn))
    NoBtn.grid(row=0, column=1, padx=2, pady=2, sticky=tk.N + tk.S + tk.E + tk.W)

    NEBtn = tk.Button(navFrame, text="Rec-Der", bg="dark orange",
                        command= lambda: go("Forward-Right", NEBtn))
    NEBtn.grid(row=0, column=2, padx=2, pady=2, sticky=tk.N + tk.S + tk.E + tk.W)

    WeBtn = tk.Button(navFrame, text="Izquierda", bg="dark orange",
                        command=lambda: go("Left", WeBtn))
    WeBtn.grid(row=1, column=0, padx=2, pady=2, sticky=tk.N + tk.S + tk.E + tk.W)

    StopBtn = tk.Button(navFrame, text="Stop", bg="dark orange",
                        command=lambda: go("Stop", StopBtn))
    StopBtn.grid(row=1, column=1, padx=2, pady=2, sticky=tk.N + tk.S + tk.E + tk.W)

    EaBtn = tk.Button(navFrame, text="Derecha", bg="dark orange",
                        command=lambda: go("Right", EaBtn))
    EaBtn.grid(row=1, column=2, padx=2, pady=2, sticky=tk.N + tk.S + tk.E + tk.W)

    SWBtn = tk.Button(navFrame, text="Atras-Iz", bg="dark orange",
                        #command=lambda: go("SouthWest", SWBtn))
                        command = lambda: go("Back-Left", SWBtn))
    SWBtn.grid(row=2, column=0, padx=2, pady=2, sticky=tk.N + tk.S + tk.E + tk.W)

    SoBtn = tk.Button(navFrame, text="Atras", bg="dark orange",
                        command=lambda: go("Back", SoBtn))
    SoBtn.grid(row=2, column=1, padx=2, pady=2, sticky=tk.N + tk.S + tk.E + tk.W)

    SEBtn = tk.Button(navFrame, text="Atras-Der", bg="dark orange",
                        #command=lambda: go("SouthEast", SEBtn))
                        command = lambda: go("Back-Right", SEBtn))
    SEBtn.grid(row=2, column=2, padx=2, pady=2, sticky=tk.N + tk.S + tk.E + tk.W)

    # --------------------------------------------------------------------------------------#
    # slider para elegir la velocidad de navegación
    speedSldr = tk.Scale(ventana, label="Velocidad Nav/Mov (m/s):", resolution=0.1, from_=0, to=1, tickinterval=0.1,
                          orient=tk.HORIZONTAL, command = changeNavSpeed)
    speedSldr.grid(row=7, column=0, columnspan=2, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

    # --------------------------------------------------------------------------------------#

    # botones para pedir/parar datos de telemetría
    StartTelemBtn = tk.Button(ventana, text="Empezar a enviar telemetría", bg="dark orange", command=startTelem)
    StartTelemBtn.grid(row=8, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

    StopTelemBtn = tk.Button(ventana, text="Parar de enviar telemetría", bg="dark orange", command=stopTelem)
    StopTelemBtn.grid(row=8, column=1, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

    # Este es el frame para mostrar los datos de telemetría
    # Contiene etiquetas para informar de qué datos son y los valores. Solo nos interesan 3 datos de telemetría
    telemetryFrame = tk.LabelFrame(ventana, text="Telemetría")
    telemetryFrame.grid(row=9, column=0, columnspan=2, padx=10, pady=10, sticky=tk.N + tk.S + tk.E + tk.W)

    telemetryFrame.rowconfigure(0, weight=1)
    telemetryFrame.rowconfigure(1, weight=1)

    telemetryFrame.columnconfigure(0, weight=1)
    telemetryFrame.columnconfigure(1, weight=1)
    telemetryFrame.columnconfigure(2, weight=1)

    # etiquetas informativas
    altLbl = tk.Label(telemetryFrame, text='Altitud')
    altLbl.grid(row=0, column=0,  padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

    headingLbl = tk.Label(telemetryFrame, text='Heading')
    headingLbl.grid(row=0, column=1,  padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

    speedLbl = tk.Label(telemetryFrame, text='Speed')
    speedLbl.grid(row=0, column=2,  padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

    # etiquetas para colocar aqui los datos cuando se reciben
    altShowLbl = tk.Label(telemetryFrame, text='')
    altShowLbl.grid(row=1, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

    headingShowLbl = tk.Label(telemetryFrame, text='')
    headingShowLbl.grid(row=1, column=1,  padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

    speedShowLbl = tk.Label(telemetryFrame, text='')
    speedShowLbl.grid(row=1, column=2, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

    batShowLbl = tk.Label(telemetryFrame, text='Bateria:')
    batShowLbl.grid(row=2, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

    batShowLbl = tk.Label(telemetryFrame, text='')
    batShowLbl.grid(row=2, column=1, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

    return ventana

if __name__ == "__main__":
    ventana = crear_ventana()
    ventana.mainloop()
