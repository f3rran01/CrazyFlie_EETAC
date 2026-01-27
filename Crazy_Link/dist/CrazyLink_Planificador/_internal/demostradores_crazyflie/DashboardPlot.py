import logging
import sys
import time
import math
import os

# Configurar matplotlib ANTES de importar tkinter o cualquier otro módulo
import matplotlib
matplotlib.use('TkAgg')  # Forzar el uso del backend TkAgg

import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter import messagebox
from tkinter import Label

from scipy.ndimage import gaussian_filter1d
import numpy as np
from threading import Event, Thread
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from mpl_toolkits.mplot3d import Axes3D

from demostradores_crazyflie.Complex_geocage_creator import custom_circuit
from crazyLink.Dron_crazyflie import Dron

# This function its main purpose is to change the color of the button when the cursor is over it
def on_enter(event, color):
            # Change background color when the cursor enters the button
            event.widget.config(bg=color)

# This function its main purpose is to change the color of the button when the  cursor leaves it
def on_leave(event, color):
            # Reset background color when the cursor leaves the button
            event.widget.config(bg=color)

# It tries to connect, starts the telem, finally it sets the speed to 2 m/s
def connect ():
    global dron, speedSldr
    try:
        dron.connect()

        # Verificar si la conexión fue exitosa
        if dron.state == "connected":
            startTelem()
            # change color of the button
            connectBtn['text'] = 'Conectado'
            connectBtn['fg'] = 'white'
            connectBtn['bg'] = 'green'
            # fix velocity
            speedSldr.set(0.2)
        else:
            # Si no está conectado, mostrar mensaje de error
            messagebox.showerror("Error de conexión",
                                 "No se pudo conectar al dron.\n"
                                 "Asegúrate de que el dron esté encendido.")
            connectBtn['text'] = 'Desconectado'
            connectBtn['fg'] = 'white'
            connectBtn['bg'] = 'red'
    except Exception as e:
        # En caso de cualquier error durante la conexión
        messagebox.showerror("Error de conexión",
                             f"No se pudo conectar al dron.\n"
                             f"Error: {str(e)}\n\n"
                             "Asegúrate de que el dron esté encendido.")
        connectBtn['text'] = 'Desconectado'
        connectBtn['fg'] = 'white'
        connectBtn['bg'] = 'red'
    # fix velocity
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
    # Non-blocking call. When it reaches the specified altitude, it will execute the inTheAir function
    dron.takeOff (0.5, blocking = False,  callback = inTheAir)
    takeOffBtn['text'] = 'Despegando...'
    takeOffBtn['fg'] = 'black'
    takeOffBtn['bg'] = 'yellow'

# It changes the button state when the drone tries to land
def onEarth (op):
    """Función modificada que pregunta sobre limpiar trayectoria después de RTL"""
    global RTLBtn, landBtn

    if op == 'land':
        # Venimos de un aterrizaje normal
        landBtn['text'] = 'En tierra'
        landBtn['fg'] = 'white'
        landBtn['bg'] = 'green'
    else:
        # Venimos de un RTL
        RTLBtn['text'] = 'En tierra'
        RTLBtn['fg'] = 'white'
        RTLBtn['bg'] = 'green'

        # Después de un pequeño delay, preguntar sobre limpiar trayectoria
        RTLBtn.after(1000, ask_clear_trajectory)  # Esperar 1 segundo

# It lands the drone, without blocking the action, adding a callback and specifying a land action
def land ():
    global dron
    # Non-blocking call. The parameter will allow us to know in onEarth that we are coming from Land.
    dron.Land(blocking = False,  callback = onEarth, params = 'land')
    landBtn['text'] = 'Aterrizando...'
    landBtn['fg'] = 'black'
    landBtn['bg'] = 'yellow'

def clear_trajectory():
    """Función para limpiar la trayectoria del drone"""
    global x_coords, y_coords
    x_coords.clear()
    y_coords.clear()
    update_plot()

def ask_clear_trajectory():
    """Pregunta al usuario si quiere limpiar la trayectoria después del RTL"""
    result = messagebox.askyesno("Limpiar trayectoria",
                                "El drone ha aterrizado en el punto de origen.\n\n"
                                "¿Deseas limpiar la trayectoria del vuelo y empezar "
                                "con un gráfico limpio?\n\n")

    if result:
        clear_trajectory()
        messagebox.showinfo("Trayectoria limpiada", "El gráfico ha sido reiniciado.")

# It lands the drone, without blocking the action, adding a callback and specifying a RTL action
def RTL():
    """RTL con opción de limpiar trayectoria al finalizar"""
    global dron
    # Llamada no bloqueante. El parámetro nos permitirá saber en onEarth que venimos de RTL
    dron.RTL(blocking=False, callback=onEarth, params='RTL')
    RTLBtn['text'] = 'Retornando...'
    RTLBtn['fg'] = 'black'
    RTLBtn['bg'] = 'yellow'

# It makes the dron go in a specific direction without blocking the user
def go (direction, btn):
    global dron, previousBtn
    # color change last button
    if previousBtn:
        previousBtn['fg'] = 'black'
        previousBtn['bg'] = 'dark orange'

    # nav thought the given direction
    dron.go (direction,blocking=False)
    # put in green last button clicked
    btn['fg'] = 'white'
    btn['bg'] = 'green'
    #  Take note from last button clicked
    previousBtn = btn

# It makes the dron go in a specific direction (0.5 m) without blocking the user
def go_move (direction, btn):
    global dron, previousBtn
    # color change last button
    if previousBtn:
        previousBtn['fg'] = 'black'
        previousBtn['bg'] = 'dark orange'

    # nav thought the given direction
    dron.move_distance ( direction, 0.5,blocking=False)
    # put in green last button clicked
    btn['fg'] = 'white'
    btn['bg'] = 'green'
    # Take note from last button clicked
    previousBtn = btn

# Function that starts sending info about the drone
def startTelem():
    global stateParams
    stateParams = True
    dron.send_local_telemetry_info(checkTelem)

# This function obtains the data and shows it on the display.
def checkTelem(data):
    global altShowLbl, headingShowLbl, speedShowLbl, batShowLbl, x_coords, y_coords

    x_coords.append(data.get('posX',0))
    y_coords.append(data.get('posY',0))
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

# It updates every 150 ms from the main window, the  plot with the drone position
def update_plot():
    global dron, data, fig, ax, right_frame, canvas, x_coords, y_coords
    global geocage_polygon, exclusion_polygons

    ax.clear()

    # Dibujar trayectoria
    if len(x_coords) > 1:
        ax.plot(
            gaussian_filter1d(y_coords, 2),
            gaussian_filter1d(x_coords, 2),
            c='r', linestyle='-', linewidth=2, label='Trayectoria'
        )

    # DIBUJAR GEOCAGE
    if geocage_polygon is not None:
        poly_x = [point[1] for point in geocage_polygon]
        poly_y = [point[0] for point in geocage_polygon]
        poly_x_closed = poly_x + [poly_x[0]]
        poly_y_closed = poly_y + [poly_y[0]]

        ax.plot(poly_x_closed, poly_y_closed,
                c='green', linestyle='--', linewidth=2.5,
                label='Geocage', alpha=0.8)
        ax.fill(poly_x_closed, poly_y_closed, color='green', alpha=0.1)

    # DIBUJAR EXCLUSIONES
    if exclusion_polygons:
        for i, exclusion in enumerate(exclusion_polygons):
            ex_x = [point[1] for point in exclusion]
            ex_y = [point[0] for point in exclusion]
            ex_x_closed = ex_x + [ex_x[0]]
            ex_y_closed = ex_y + [ex_y[0]]

            ax.plot(ex_x_closed, ex_y_closed,
                    c='red', linestyle='--', linewidth=2,
                    label=f'Exclusión {i + 1}', alpha=0.8)
            ax.fill(ex_x_closed, ex_y_closed, color='red', alpha=0.15, hatch='///')

    # Punto inicio
    ax.scatter(0, 0, color='blue', s=150, marker='o',
               edgecolors='black', linewidths=2, label='Inicio', zorder=5)

    ax.set_xlabel("Esquerra/Dreta [m]", fontsize=11)
    ax.set_ylabel("Darrere/Endavant [m]", fontsize=11)
    ax.set_title('Vol Dron', fontsize=20, fontweight='bold')
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.7)
    ax.tick_params(axis='both', labelsize=9)

    # Ajustar límites
    if len(x_coords) > 0 or geocage_polygon is not None:
        all_x = list(y_coords) if y_coords else []
        all_y = list(x_coords) if x_coords else []

        if geocage_polygon:
            all_x.extend([p[1] for p in geocage_polygon])
            all_y.extend([p[0] for p in geocage_polygon])

        if all_x and all_y:
            margin = 0.5
            ax.set_xlim(min(all_x) - margin, max(all_x) + margin)
            ax.set_ylim(min(all_y) - margin, max(all_y) + margin)
    else:
        ax.set_xlim(-1, 1)
        ax.set_ylim(-1, 1)

    ax.legend(loc='upper right', fontsize=9, framealpha=0.9)
    canvas.draw()
    right_frame.after(150, update_plot)

# This function create a simple window in order to create a simple geocage
def simple_cage(ventana):
    global dron
    # Creates a new level  window
    new_ventana = tk.Toplevel(ventana)
    new_ventana.title("Configurador Simple")
    new_ventana.geometry("450x300+600+350")
    new_ventana.configure(background="white")
    new_ventana.resizable(False, False)

    label = tk.Label(new_ventana, text="Transversal des del centro del Geocage (m):", font=("Arial", 14), fg="blue")
    label.place(relx=0.1, rely=0.1)

    spinbox_trans = tk.Spinbox(new_ventana, from_=1.2, to=15,increment=0.2, font=("Arial", 14),justify='center',state='readonly')
    spinbox_trans.place(relx=0.3, rely=0.25)

    label = tk.Label(new_ventana, text="Lateral des del centro del Geocage (m):", font=("Arial", 14), fg="blue")
    label.place(relx=0.1, rely=0.4)

    spinbox_lat = tk.Spinbox(new_ventana,  from_=1.2, to=15,increment=0.2, font=("Arial", 14),justify='center',state='readonly')
    spinbox_lat.place(relx=0.3, rely=0.55)

    simple_cageBtn = tk.Button(new_ventana, text="Aceptar", font=("Arial", 14), bg="dark orange", command=lambda: simple_cage_accept(spinbox_trans.get(),spinbox_lat.get(),new_ventana))
    simple_cageBtn.place(relx=0.4, rely=0.75)

# This creates the main geocage, deleting the previous
def simple_cage_accept(trans,lat,ventana):
    global dron
    try:
        dron.deleteSimpleScenario()
        dron.setSimpleScenario([float(trans),float(lat)])
        messagebox.showinfo('Info','Simple escenario creado')
    except:
        print('Error de Simple Geofence')

    ventana.destroy()
    return

# This function calls another script to configure the complex geocage.
def complex_cage(ventana):
    global dron, geocage_polygon, exclusion_polygons

    if dron is None or dron.state == "disconnected":
        messagebox.showwarning("Drone no conectado",
                               "Debes conectar el drone primero.")
        return

    # NUEVO: Verificar si ya existe un geocage
    if geocage_polygon is not None or (hasattr(dron, 'geocage') and dron.geocage is not None):
        messagebox.showwarning("Geocage existente",
                               "Ya existe un geocage configurado.\n\n"
                               "Primero debes eliminar el geocage actual usando el botón 'Limpiar Geocage'.")
        return

    # Función callback que se ejecutará cuando se guarde
    def on_geocage_saved():
        global geocage_polygon, exclusion_polygons

        if hasattr(dron, 'geocage') and dron.geocage is not None:
            geocage_polygon = dron.geocage
            print(f"Geocage cargado: {len(geocage_polygon)} vértices")

        if hasattr(dron, 'exclusion') and dron.exclusion:
            exclusion_polygons = dron.exclusion
            print(f"Exclusiones cargadas: {len(exclusion_polygons)}")

        # Forzar actualización inmediata del gráfico
        update_plot()

    # Abrir el editor pasándole el callback
    custom_circuit(ventana, dron, on_save_callback=on_geocage_saved)

    # Función para actualizar después de cerrar la ventana
    def update_after_close():
        global geocage_polygon, exclusion_polygons  # IMPORTANTE: Declarar global aquí también

        if hasattr(dron, 'geocage') and dron.geocage is not None:
            geocage_polygon = dron.geocage
            print(f"Geocage cargado: {len(geocage_polygon)} vértices")

        if hasattr(dron, 'exclusion') and dron.exclusion:
            exclusion_polygons = dron.exclusion
            print(f"Exclusiones cargadas: {len(exclusion_polygons)}")

        # Forzar actualización inmediata del gráfico
        update_plot()

    # Esperar un poco y luego actualizar
    ventana.after(500, update_after_close)


def update_geocage_display():
    """Actualizar visualización del geocage desde el drone"""
    global dron, geocage_polygon, exclusion_polygons

    if dron is not None:
        if hasattr(dron, 'geocage') and dron.geocage is not None:
            geocage_polygon = dron.geocage
            print(f"Geocage cargado: {len(geocage_polygon)} vértices")  # Debug

        if hasattr(dron, 'exclusion') and dron.exclusion:
            exclusion_polygons = dron.exclusion
            print(f"Exclusiones cargadas: {len(exclusion_polygons)}")  # Debug

        # Forzar actualización inmediata del plot
        update_plot()


# This function creates a new window to select a new top-bot cage
# Indeed this GUI cannot move the dron vertically, despite that, this is a mere example of a posible config
def top_bot_cage(ventana):
    global dron

    new_ventana = tk.Toplevel(ventana)
    new_ventana.title("Configurador Top y Bot")
    new_ventana.geometry("450x350+600+350")
    new_ventana.configure(background="white")

    label = tk.Label(new_ventana, text="Techo del Geocage (m):", font=("Arial", 14), fg="blue")
    label.place(relx=0.1, rely=0.1)

    spinbox_top = tk.Spinbox(new_ventana, from_=1, to=15,increment=0.2, font=("Arial", 14),justify='center',state='readonly')
    spinbox_top.place(relx=0.3, rely=0.25)

    label = tk.Label(new_ventana, text="Suelo del Geocage (m):", font=("Arial", 14), fg="blue")
    label.place(relx=0.1, rely=0.4)

    spinbox_bot = tk.Spinbox(new_ventana,  from_=0.2, to=15,increment=0.2, font=("Arial", 14),justify='center',state='readonly')
    spinbox_bot.place(relx=0.3, rely=0.55)

    top_botBtn = tk.Button(new_ventana, text="Aceptar", bg="dark orange", font=("Arial", 14), command=lambda: top_bot_cage_accept(spinbox_top.get(),spinbox_bot.get(),new_ventana))
    top_botBtn.place(relx=0.4, rely=0.75)

# It deletes all the top, bot surfaces and creates new ones
def top_bot_cage_accept(top,bot,ventana):
    global dron
    try:
        dron.stopTopGeofence()
        dron.stopBottomGeofence()
        dron.startBottomGeofence(float(bot))
        dron.startTopGeofence(float(top))
        messagebox.showinfo('Info','Top-Bot escenario creado')
    except:
        print('Error de Top-Bot Geofence')

    ventana.destroy()
    return


def clear_geocage():
    """Función para eliminar el geocage actual"""
    global geocage_polygon, exclusion_polygons, dron

    result = messagebox.askyesno("Limpiar Geocage",
                                 "¿Deseas eliminar el geocage actual?\n\n")

    if result:
        geocage_polygon = None
        exclusion_polygons = []
        if dron:
            dron.deleteComplexScenario()
            # Limpiar también los atributos del dron
            if hasattr(dron, 'geocage'):
                dron.geocage = None
            if hasattr(dron, 'exclusion'):
                dron.exclusion = []

        update_plot()
        messagebox.showinfo("Geocage eliminado", "Geocage eliminado correctamente.\n"
                                                 "Ahora puedes crear uno nuevo.")



# This function creates the main window of the app
def crear_ventana():
    # Determine global variables
    global dron, data,fig, ax, right_frame,canvas,x_coords, y_coords
    global altShowLbl, headingShowLbl, speedSldr, gradesSldr, speedShowLbl, batShowLbl
    global connectBtn, armBtn, takeOffBtn, landBtn, RTLBtn
    global previousBtn  # aqui guardaré el ultimo boton de navegación clicado
    global stateParams  # defino un valor de activacion de bucle para obtener parametros
    global geocage_polygon, exclusion_polygons

    # Determine the class dron as a previous state
    dron = None
    dron = Dron()
    # Button state
    previousBtn = None
    # This list saves the position of the drone
    data = []
    # Gives the state if tha pp gives the parametes
    stateParams = False
    # Create a list for every coordinate (telem will fill the list with the data)
    x_coords = []
    y_coords = []
    geocage_polygon = None
    exclusion_polygons = []
    # Creates the main window
    ventana = tk.Tk()
    ventana.title("Demostracion")
    ventana.geometry("1920x1080")
    ventana.configure(background="white")

    # Defines grid: 9 rows, 3 columns
    for i in range(9):
        ventana.rowconfigure(i, weight=1)
    for j in range(3):
        ventana.columnconfigure(j, weight=(5 if j == 2 else 1))

    # Create the right frame (the graph)
    right_frame = tk.Frame(ventana, bg="white")
    right_frame.grid(row=3, column=2, rowspan=10, sticky="nsew")

    # Create and display graph in right_frame
    fig, ax = plt.subplots(figsize=(5, 5))
    canvas = FigureCanvasTkAgg(fig, master=right_frame)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # Updates the plot
    update_plot()

    simplecageBtn = tk.Button(ventana, text="Config. Simple", bg="dark orange", command= lambda :simple_cage(ventana))
    simplecageBtn.grid(row=0, column=2, columnspan=2, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

    complexcageBtn = tk.Button(ventana, text="Config. Complex", bg="dark orange", command= lambda :complex_cage(ventana))
    complexcageBtn.grid(row=1, column=2, columnspan=2, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

    topbotBtn = tk.Button(ventana, text="Config. Top-Bot", bg="dark orange", command= lambda :top_bot_cage(ventana))
    topbotBtn.grid(row=2, column=2, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

    clearGeocageBtn = tk.Button(ventana, text="Limpiar Geocage",bg="dark orange", fg="black",font=("Helvetica", 9),command=clear_geocage)
    clearGeocageBtn.grid(row=2, column=3, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)


    # Arrange the buttons, specifying which function to execute when each one is clicked
    # The first three occupy both columns of the row in which they are placed
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
                      command=lambda: go_move("Back-Left", SWBtm))
    SWBtm.grid(row=2, column=0, padx=2, pady=2, sticky=tk.N + tk.S + tk.E + tk.W)
    SoBtm = tk.Button(movFrame, text="Atras", bg="dark orange",
                      command=lambda: go_move("Back", SoBtm))
    SoBtm.grid(row=2, column=1, padx=2, pady=2, sticky=tk.N + tk.S + tk.E + tk.W)
    SEBtm = tk.Button(movFrame, text="Atras-Der", bg="dark orange",
                      command=lambda: go_move("Back-Right", SEBtm))
    SEBtm.grid(row=2, column=2, padx=2, pady=2, sticky=tk.N + tk.S + tk.E + tk.W)
    # --------------------------------------------------------------------------------------#
    # Slider fir the heading
    gradesSldr = tk.Scale(ventana, label="Grados:", resolution=45, from_=0, to=360, tickinterval=45,
                              orient=tk.HORIZONTAL, command = changeHeading)
    gradesSldr.grid(row=4, column=0, columnspan=2,padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

    landBtn = tk.Button(ventana, text="Aterrizar", bg="dark orange", command=land)
    landBtn.grid(row=5, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)
    RTLBtn = tk.Button(ventana, text="RTL", bg="dark orange", command=RTL)
    RTLBtn.grid(row=5, column=1, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)
    # --------------------------------------------------------------------------------------#
    # This is the frame for navigation. Small 3 x 3 button matrix
    navFrame = tk.LabelFrame (ventana, text = "Navegación")
    navFrame.grid(row=6, column=0, columnspan = 2, padx=50, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)
    navFrame.rowconfigure(0, weight=1)
    navFrame.rowconfigure(1, weight=1)
    navFrame.rowconfigure(2, weight=1)
    navFrame.columnconfigure(0, weight=1)
    navFrame.columnconfigure(1, weight=1)
    navFrame.columnconfigure(2, weight=1)
    # When any of the buttons is clicked, the 'go' function is triggered,
    # receiving the direction to navigate and the clicked button,
    # so that the function can change its color
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
    # slider for velocity
    speedSldr = tk.Scale(ventana, label="Velocidad Nav/Mov (m/s):", resolution=0.1, from_=0, to=1, tickinterval=0.1,
                          orient=tk.HORIZONTAL, command = changeNavSpeed)
    speedSldr.grid(row=7, column=0, columnspan=2, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)
    # --------------------------------------------------------------------------------------#

    # This is the frame to display telemetry data
    # It contains labels to indicate what data they are and their values.
    telemetryFrame = tk.LabelFrame(ventana, text="Telemetría")
    telemetryFrame.grid(row=8, column=0, columnspan=2, padx=10, pady=10, sticky=tk.N + tk.S + tk.E + tk.W)
    telemetryFrame.rowconfigure(0, weight=1)
    telemetryFrame.rowconfigure(1, weight=1)
    telemetryFrame.columnconfigure(0, weight=1)
    telemetryFrame.columnconfigure(1, weight=1)
    telemetryFrame.columnconfigure(2, weight=1)

    altLbl = tk.Label(telemetryFrame, text='Altitud')
    altLbl.grid(row=0, column=0,  padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)
    headingLbl = tk.Label(telemetryFrame, text='Heading')
    headingLbl.grid(row=0, column=1,  padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)
    speedLbl = tk.Label(telemetryFrame, text='Speed')
    speedLbl.grid(row=0, column=2,  padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

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


