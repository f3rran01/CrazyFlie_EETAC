import logging
import sys
import time
import os
import tkinter as tk

from tkinter import ttk, messagebox
from tkinter import filedialog
from tkinter import Label

from turtledemo.penrose import start

import numpy as np
from shapely.geometry import Polygon
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from matplotlib.collections import LineCollection

import configparser
import math
from tkinter import messagebox


# NUEVAS FUNCIONES DE VALIDACIÓN - AGREGAR AQUÍ
def line_intersects(p1, p2, p3, p4):
    """Verifica si dos líneas se intersectan"""

    def orientation(p, q, r):
        val = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
        if val == 0:
            return 0  # colinear
        return 1 if val > 0 else 2  # clockwise or counterclockwise

    def on_segment(p, q, r):
        return (q[0] <= max(p[0], r[0]) and q[0] >= min(p[0], r[0]) and
                q[1] <= max(p[1], r[1]) and q[1] >= min(p[1], r[1]))

    o1 = orientation(p1, p2, p3)
    o2 = orientation(p1, p2, p4)
    o3 = orientation(p3, p4, p1)
    o4 = orientation(p3, p4, p2)

    # Caso general
    if o1 != o2 and o3 != o4:
        return True

    # Casos especiales para puntos colineales
    if (o1 == 0 and on_segment(p1, p3, p2)) or \
       (o2 == 0 and on_segment(p1, p4, p2)) or \
       (o3 == 0 and on_segment(p3, p1, p4)) or \
       (o4 == 0 and on_segment(p3, p2, p4)):
        return True

    return False


def would_create_intersection(x_coords, y_coords, new_x, new_y):
    """Validación mejorada que considera el cierre del polígono"""
    if len(x_coords) < 2:
        return False

    # Crear una copia temporal con el nuevo punto
    temp_x = x_coords.copy()
    temp_y = y_coords.copy()
    temp_x.append(new_x)
    temp_y.append(new_y)

    # Si tenemos 3 o más puntos, verificar también la línea de cierre
    if len(temp_x) >= 3:
        temp_x.append(temp_x[0])  # Cerrar el polígono
        temp_y.append(temp_y[0])

        # Verificar todas las intersecciones posibles
        return has_self_intersections(temp_x, temp_y)

    # Para menos de 3 puntos, verificar solo la nueva línea
    new_line_start = (x_coords[-1], y_coords[-1])
    new_line_end = (new_x, new_y)

    for i in range(len(x_coords) - 1):
        existing_line_start = (x_coords[i], y_coords[i])
        existing_line_end = (x_coords[i + 1], y_coords[i + 1])

        if line_intersects(new_line_start, new_line_end,
                           existing_line_start, existing_line_end):
            return True

    return False


def has_self_intersections(x_coords, y_coords):
    """Verifica si un polígono tiene auto-intersecciones"""
    if len(x_coords) < 4:
        return False

    n = len(x_coords) - 1  # Excluir el punto de cierre duplicado

    for i in range(n):
        line1_start = (x_coords[i], y_coords[i])
        line1_end = (x_coords[(i + 1) % n], y_coords[(i + 1) % n])

        for j in range(i + 2, n):
            # No verificar el último segmento con el primero (son adyacentes en polígono cerrado)
            if (i == 0 and j == n - 1):
                continue

            line2_start = (x_coords[j], y_coords[j])
            line2_end = (x_coords[(j + 1) % n], y_coords[(j + 1) % n])

            if line_intersects(line1_start, line1_end, line2_start, line2_end):
                return True

    return False
# FIN DE LAS NUEVAS FUNCIONES

# This function its main purpose is to change the color of the button when the cursor is over it
def on_enter(event, color):
            # Change background color when the cursor enters the button
            event.widget.config(bg=color)

# This function its main purpose is to change the color of the button when the  cursor leaves it
def on_leave(event, color):
            # Reset background color when the cursor leaves the button
            event.widget.config(bg=color)

# Main object to develop the complex geocage
class custom_circuit:
    # Init part, defines the main parameters and the basic layout
    def __init__(self, root, dron=None,on_save_callback=None):
        new_window_custom = tk.Toplevel(root)
        new_window_custom.title("Complex Geocage")
        new_window_custom.geometry("1000x600+300+200")
        new_window_custom.configure(bg="light gray")
        new_window_custom.focus_force()
        new_window_custom.grab_set()
        new_window_custom.resizable(False, False)


        self.dron = dron
        self.on_save_callback = on_save_callback
        self.window = new_window_custom  # Guardar referencia a la ventana

        # Cargar geocage y exclusiones existentes si ya existen
        if hasattr(dron, 'geocage') and dron.geocage is not None:
            # Convertir de lista de tuplas a listas separadas
            self.x_coor = [point[1] for point in dron.geocage]  # lateral
            self.y_coor = [point[0] for point in dron.geocage]  # transversal
            # Cerrar el polígono para visualización
            if len(self.x_coor) > 0:
                self.x_coor.append(self.x_coor[0])
                self.y_coor.append(self.y_coor[0])
            self.geocage = dron.geocage
        else:
            self.x_coor = []
            self.y_coor = []
            self.geocage = None

        if hasattr(dron, 'exclusion') and dron.exclusion:
            self.exclusion = dron.exclusion
        else:
            self.exclusion = []
        # Create a left frame for widgets inside the new window
        left_frame = tk.Frame(new_window_custom, bg="lightblue", width=300, height=400)
        left_frame.pack(side="left", fill="both", expand=True)

        # Create a right frame for the canvas inside the new window
        right_frame = tk.Frame(new_window_custom, bg="white", width=700, height=400)
        right_frame.pack(side="right", fill="both", expand=True)

        label = tk.Label(left_frame, text="Configurador Custom",
                         font=("Helvetica", 15, 'bold underline'), bg='light blue')
        label.place(relx=0.5, rely=0.05, anchor="center")

        self.combo = ttk.Combobox(left_frame, values=["Geocage", "Exclusion"],
                                  font=("Segoe UI", 14), width=23,
                                  height=5, state="readonly", justify="center")
        self.combo.set("Geocage")
        self.combo.place(relx=0.5, rely=0.12, anchor="center")


        label = tk.Label(left_frame, text="Tamaño del recinto:",
                         font=("Helvetica", 15, 'bold underline'), bg='light blue')
        label.place(relx=0.5, rely=0.2, anchor="center")

        label = tk.Label(left_frame, text="Anchura (x-axis) [m]:",
                         font=("Helvetica", 13, 'bold '), bg='light blue')
        label.place(relx=0.5, rely=0.25, anchor="center")

        label = tk.Label(left_frame, text="(+)",
                         font=("Helvetica", 15), bg='light blue')
        label.place(relx=0.25, rely=0.3, anchor="center")

        self.custom_entry_x_pos = tk.Spinbox(left_frame, from_=0, to=10, increment=0.2,
                                             textvariable=tk.StringVar(value='2'), font=("Helvetica", 14), width=10,
                                             justify="center", state="readonly")
        self.custom_entry_x_pos.place(relx=0.6, rely=0.3, anchor="center")

        label = tk.Label(left_frame, text="(-)",
                         font=("Helvetica", 15), bg='light blue')
        label.place(relx=0.25, rely=0.35, anchor="center")

        self.custom_entry_x_ne = tk.Spinbox(left_frame, from_=-10, to=0, increment=0.2,
                                            textvariable=tk.StringVar(value='-2'), font=("Helvetica", 14), width=10,
                                            justify="center", state="readonly")
        self.custom_entry_x_ne.place(relx=0.6, rely=0.35, anchor="center")


        label = tk.Label(left_frame, text="Profundidad (y-axis) [m]:",
                         font=("Helvetica", 13, 'bold '), bg='light blue')
        label.place(relx=0.5, rely=0.4, anchor="center")

        label = tk.Label(left_frame, text="(+)",
                         font=("Helvetica", 15), bg='light blue')
        label.place(relx=0.25, rely=0.45, anchor="center")

        self.custom_entry_y_pos = tk.Spinbox(left_frame, from_=0, to=10, increment=0.2,
                                             textvariable=tk.StringVar(value='2'), font=("Helvetica", 14), width=10,
                                             justify="center", state="readonly")
        self.custom_entry_y_pos.place(relx=0.6, rely=0.45, anchor="center")

        label = tk.Label(left_frame, text="(-)",
                         font=("Helvetica", 15), bg='light blue')
        label.place(relx=0.25, rely=0.5, anchor="center")

        self.custom_entry_y_ne = tk.Spinbox(left_frame, from_=-10, to=0, increment=0.2,
                                            textvariable=tk.StringVar(value='-2'), font=("Helvetica", 14), width=10,
                                            justify="center", state="readonly")
        self.custom_entry_y_ne.place(relx=0.6, rely=0.5, anchor="center")


        button_plot = tk.Button(left_frame, text="Actualitzar las dimensiones", font=("Helvetica", 14),
                                relief='groove', bg='light green', width=23, cursor='hand2',
                                command=lambda: self.InteractivePlot())
        button_plot.place(relx=0.5, rely=0.6, anchor="center")
        button_plot.bind("<Enter>", lambda event: on_enter(event, 'lime green'))
        button_plot.bind("<Leave>", lambda event: on_leave(event, 'light green'))

        button_delete = tk.Button(left_frame, text="Eliminar último paso", font=("Helvetica", 14),
                                       relief='groove', bg='brown2', width=23, cursor='hand2',command=lambda: self.delete_last_point())
        button_delete.place(relx=0.5, rely=0.7, anchor="center")
        button_delete.bind("<Enter>", lambda event: on_enter(event, 'brown3'))
        button_delete.bind("<Leave>", lambda event: on_leave(event, 'brown2'))

        button_save_custom = tk.Button(left_frame, text="Guardar configuración", font=("Helvetica", 15, 'bold'),
                                       relief='groove', bg='gold', width=23, cursor='hand2',command=lambda: self.safe_config_custom())
        button_save_custom.place(relx=0.5, rely=0.82, anchor="center")
        button_save_custom.bind("<Enter>", lambda event: on_enter(event, 'goldenrod'))
        button_save_custom.bind("<Leave>", lambda event: on_leave(event, 'gold'))

        button_close_custom = tk.Button(left_frame, text="Guardar todo y cerrar", font=("Helvetica", 15, 'bold '),
                                       relief='groove', bg='gold', width=23, cursor='hand2',command=lambda: self.save_all_custom(new_window_custom))
        button_close_custom.place(relx=0.5, rely=0.92, anchor="center")
        button_close_custom.bind("<Enter>", lambda event: on_enter(event, 'goldenrod'))
        button_close_custom.bind("<Leave>", lambda event: on_leave(event, 'gold'))

        # Set up the matplotlib figure and axis
        self.fig, self.ax = plt.subplots()

        # Set up the canvas for embedding the figure into the Tkinter window
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Bind mouse click event to the plot
        self.canvas.mpl_connect("button_press_event", self.on_click)

        self.update_plot()


# This function basically tries to save all the configuration and close this object/window to get back to the previous
    def save_all_custom(self, new_window_custom):
        try:
            if self.dron is None:
                messagebox.showerror("Error",
                                     "No hay conexión con el drone.\n"
                                     "Conecta el drone antes de guardar el geocage.")
                return

            if self.geocage is not None:
                # Guardar en el objeto dron
                self.dron.geocage = self.geocage
                self.dron.exclusion = self.exclusion

                # Aplicar el geocage al sistema de control
                self.dron.setComplexScenario(
                    inside_polygon=self.geocage,
                    exclusion=self.exclusion)

                # Llamar al callback si existe
                if self.on_save_callback is not None:
                    self.on_save_callback()

                # CERRAR LA VENTANA (sin limpieza manual)
                new_window_custom.destroy()

                # Mostrar mensaje de éxito
                messagebox.showinfo("Geocage guardado",
                                    "El geocage se ha configurado y es visible en el gráfico.")
            else:
                messagebox.showinfo("Advertencia", "No se ha definido ningún Geocage.")

        except Exception as e:
            messagebox.showerror("Error al guardar Geocage/Zona de exclusión", str(e))



# This function basically tries to save the coordinates into the selected geocage or exclusion list
    def safe_config_custom(self):
        """Validación final antes de guardar"""
        try:
            if len(self.x_coor) < 3:
                messagebox.showwarning("Polígono incompleto",
                                       "Necesitas al menos 3 puntos para formar un polígono válido.")
                return

            # Preparar coordenadas sin duplicado de cierre
            temp_x = self.x_coor[:-1] if (len(self.x_coor) > 0 and
                                          self.x_coor[-1] == self.x_coor[0]) else self.x_coor
            temp_y = self.y_coor[:-1] if (len(self.y_coor) > 0 and
                                          self.y_coor[-1] == self.y_coor[0]) else self.y_coor

            if len(temp_x) < 3:
                messagebox.showwarning("Polígono incompleto",
                                       "Necesitas al menos 3 puntos únicos.")
                return

            # Validación final de intersecciones
            test_x = temp_x + [temp_x[0]]
            test_y = temp_y + [temp_y[0]]

            if has_self_intersections(test_x, test_y):
                messagebox.showerror("Polígono inválido",
                                     "El polígono tiene líneas que se cruzan.\n"
                                     "Elimina algunos puntos para crear un polígono simple.")
                return

            coords = list(zip(temp_x, temp_y))

            if self.combo.get() == "Geocage":
                self.geocage = coords
                messagebox.showinfo("Geocage Creado",
                                    f"Geocage válido creado con {len(coords)} vértices.")
            else:
                self.exclusion.append(coords)
                messagebox.showinfo("Zona de exclusión creada",
                                    f"Zona de exclusión añadida con {len(coords)} vértices.")

        except Exception as e:
            messagebox.showerror("Error", f"Error al crear polígono: {str(e)}")

# This function tries to update the dimensions of the plot
    def InteractivePlot(self):
        # Display the plot
        self.update_plot()

# This function plot the cage/exclusion everytime it is clicked
    def on_click(self, event):
        # Get the mouse click position on the plot
        """Versión modificada con validación de intersecciones"""
        """Método on_click con validación robusta"""
        if event.xdata is not None and event.ydata is not None:
            round_x_coor = round(event.xdata, 1)
            round_y_coor = round(event.ydata, 1)

            # Remover punto de cierre si existe
            if len(self.x_coor) > 2:
                if self.x_coor[-1] == self.x_coor[0] and self.y_coor[-1] == self.y_coor[0]:
                    self.x_coor.pop()
                    self.y_coor.pop()

            # Ajuste de decimales
            decimal_str_x = str(round_x_coor).split('.')[-1]
            if decimal_str_x and int(decimal_str_x[-1]) % 2 != 0:
                round_x_coor += 0.1

            decimal_str_y = str(round_y_coor).split('.')[-1]
            if decimal_str_y and int(decimal_str_y[-1]) % 2 != 0:
                round_y_coor += 0.1

            # Verificar punto duplicado
            if (round_x_coor, round_y_coor) in zip(self.x_coor, self.y_coor):
                return

            # VALIDACIÓN PRINCIPAL: Verificar intersecciones
            if would_create_intersection(self.x_coor, self.y_coor, round_x_coor, round_y_coor):
                messagebox.showwarning("Polígono inválido",
                                       "Este punto crearía líneas que se cruzan.\n"
                                       "El polígono debe ser simple sin auto-intersecciones.")
                return

            # Agregar el punto
            self.x_coor.append(round_x_coor)
            self.y_coor.append(round_y_coor)

            self.x_coor = [round(num, 1) for num in self.x_coor]
            self.y_coor = [round(num, 1) for num in self.y_coor]

            # Cerrar polígono para visualización
            if len(self.x_coor) > 2:
                self.x_coor.append(self.x_coor[0])
                self.y_coor.append(self.y_coor[0])

            self.update_plot()

# Simple, it is what it is
    def delete_last_point(self):

        if len(self.x_coor)>0:
            self.x_coor.pop()
            self.y_coor.pop()

        self.update_plot()

# This function shows the main panel, with everything
    def update_plot(self):
        # Clear the previous plot
        self.ax.clear()

        # Set axis limits
        self.ax.set_xlim(float(self.custom_entry_x_ne.get()) - 0.6, float(self.custom_entry_x_pos.get()) + 0.6)
        self.ax.set_ylim(float(self.custom_entry_y_ne.get()) - 0.6, float(self.custom_entry_y_pos.get()) + 0.6)

        # Set ticks at every 0.2 meters
        self.ax.set_xticks([round(i, 2) for i in np.arange(float(self.custom_entry_x_ne.get()) - 0.6,
                                                           float(self.custom_entry_x_pos.get()) + 0.6, 0.2)])
        self.ax.set_yticks([round(i, 2) for i in np.arange(float(self.custom_entry_y_ne.get()) - 0.6,
                                                           float(self.custom_entry_y_pos.get()) + 0.6, 0.2)])
        # Mark start
        self.ax.scatter(0, 0, color="green", s=100, label="Start", edgecolors="black", zorder=3)

        # Add annotations
        self.ax.annotate("Inicio", (0, 0), textcoords="offset points", xytext=(-20, -10),
                         ha="center", fontsize=10, color="green")

        # Adjust tick label size
        self.ax.tick_params(axis='x', labelrotation=-60)  # Rotate x-axis label
        self.ax.tick_params(axis='both', labelsize=7)

        # Draw grid
        self.ax.grid(True, linestyle="--", linewidth=0.5)

        self.ax.set_title('Dibuja el poligono')
        # Add axis labels
        self.ax.set_xlabel("Izquierda/Derecha [m]")
        self.ax.set_ylabel("Atrás/Delante [m]")

        # Plot the points as a line
        self.ax.plot(self.x_coor, self.y_coor, marker='o', color='b', linestyle='-', markersize=5)

        # Redraw the canvas
        self.canvas.draw()

# This is just to make tests
if __name__ == "__main__":
    root=tk.Tk()
    app = custom_circuit(root)
    root.mainloop()