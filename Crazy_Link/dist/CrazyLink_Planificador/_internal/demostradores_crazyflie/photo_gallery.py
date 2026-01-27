"""
Galería de Medios para Crazyflie
Permite visualizar, gestionar fotos y videos capturados durante vuelos
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import os
import logging
import subprocess
import platform
from datetime import datetime
from typing import List, Optional, Dict
import shutil


class MediaGallery:
    """
    Interfaz gráfica para gestionar la galería de fotos y videos
    """
    
    def __init__(self, carpeta_fotos: str = "fotos_vuelo", carpeta_videos: str = "videos_vuelo"):
        """
        Inicializa la galería de medios
        
        Args:
            carpeta_fotos: Carpeta raíz donde se guardan las fotos
            carpeta_videos: Carpeta raíz donde se guardan los videos
        """
        self.carpeta_fotos = carpeta_fotos
        self.carpeta_videos = carpeta_videos
        # NUEVO: Añadir carpetas de modo libre
        self.carpeta_fotos_libre = "fotos_vuelo_libre"
        self.carpeta_videos_libre = "videos_vuelo_libre"
        self.sesiones = []
        self.medios_actuales = []  # Lista de fotos y videos
        self.sesion_actual = None
        self.indice_actual = 0
        self.tipo_filtro = "todos"  # todos, fotos, videos
        
        self.ventana = None
        self.canvas_preview = None
        self.label_info = None
        self.listbox_sesiones = None
        self.listbox_medios = None
        self.photo = None  # Referencia para evitar garbage collection
        
        # Cargar sesiones disponibles
        self._cargar_sesiones()
    
    def _cargar_sesiones(self):
        """Carga todas las sesiones disponibles desde las carpetas de fotos y videos"""
        sesiones_dict = {}

        # NUEVO: Lista de carpetas a escanear (misión + libre)
        carpetas_fotos = [
            (self.carpeta_fotos, "misión"),
            (self.carpeta_fotos_libre, "libre")
        ]
        carpetas_videos = [
            (self.carpeta_videos, "misión"),
            (self.carpeta_videos_libre, "libre")
        ]

        # Cargar sesiones de fotos (misión + libre)
        for carpeta_base, tipo in carpetas_fotos:
            if os.path.exists(carpeta_base):
                for item in os.listdir(carpeta_base):
                    ruta_item = os.path.join(carpeta_base, item)
                    if os.path.isdir(ruta_item) and item.startswith('sesion_'):
                        fecha = item.replace('sesion_', '')
                        fotos = [f for f in os.listdir(ruta_item) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

                        if fecha not in sesiones_dict:
                            sesiones_dict[fecha] = {
                                'nombre': item,
                                'fecha': fecha,
                                'ruta_fotos': ruta_item if tipo == "misión" else None,
                                'ruta_fotos_libre': ruta_item if tipo == "libre" else None,
                                'ruta_videos': None,
                                'ruta_videos_libre': None,
                                'num_fotos': len(fotos) if tipo == "misión" else 0,
                                'num_fotos_libre': len(fotos) if tipo == "libre" else 0,
                                'num_videos': 0,
                                'num_videos_libre': 0
                            }
                        else:
                            if tipo == "misión":
                                sesiones_dict[fecha]['ruta_fotos'] = ruta_item
                                sesiones_dict[fecha]['num_fotos'] = len(fotos)
                            else:
                                sesiones_dict[fecha]['ruta_fotos_libre'] = ruta_item
                                sesiones_dict[fecha]['num_fotos_libre'] = len(fotos)

        # Cargar sesiones de videos (misión + libre)
        for carpeta_base, tipo in carpetas_videos:
            if os.path.exists(carpeta_base):
                for item in os.listdir(carpeta_base):
                    ruta_item = os.path.join(carpeta_base, item)
                    if os.path.isdir(ruta_item) and item.startswith('sesion_'):
                        fecha = item.replace('sesion_', '')
                        videos = [f for f in os.listdir(ruta_item) if f.lower().endswith(('.avi', '.mp4', '.mkv', '.mov'))]

                        if fecha not in sesiones_dict:
                            sesiones_dict[fecha] = {
                                'nombre': item,
                                'fecha': fecha,
                                'ruta_fotos': None,
                                'ruta_fotos_libre': None,
                                'ruta_videos': ruta_item if tipo == "misión" else None,
                                'ruta_videos_libre': ruta_item if tipo == "libre" else None,
                                'num_fotos': 0,
                                'num_fotos_libre': 0,
                                'num_videos': len(videos) if tipo == "misión" else 0,
                                'num_videos_libre': len(videos) if tipo == "libre" else 0
                            }
                        else:
                            if tipo == "misión":
                                sesiones_dict[fecha]['ruta_videos'] = ruta_item
                                sesiones_dict[fecha]['num_videos'] = len(videos)
                            else:
                                sesiones_dict[fecha]['ruta_videos_libre'] = ruta_item
                                sesiones_dict[fecha]['num_videos_libre'] = len(videos)

        # Convertir a lista, FILTRAR VACÍAS, y ordenar
        # NUEVO: Considerar fotos/videos de ambas fuentes
        self.sesiones = [s for s in sesiones_dict.values()
                        if (s['num_fotos'] + s['num_fotos_libre'] + s['num_videos'] + s['num_videos_libre']) > 0]
        self.sesiones.sort(key=lambda x: x['fecha'], reverse=True)
        
        # Eliminar carpetas vacías automáticamente
        self._limpiar_sesiones_vacias(sesiones_dict)
        
        logging.info(f"[MediaGallery] {len(self.sesiones)} sesiones con contenido encontradas")
    
    def _limpiar_sesiones_vacias(self, sesiones_dict: dict):
        """
        Elimina automáticamente las carpetas de sesiones vacías.

        Args:
            sesiones_dict: Diccionario con todas las sesiones encontradas
        """
        carpetas_eliminadas = 0

        for fecha, sesion in sesiones_dict.items():
            # NUEVO: Verificar si no tiene ningún medio (misión + libre)
            total_medios = (sesion['num_fotos'] + sesion['num_fotos_libre'] +
                           sesion['num_videos'] + sesion['num_videos_libre'])

            if total_medios == 0:
                try:
                    # Eliminar carpeta de fotos vacía (misión)
                    if sesion['ruta_fotos'] and os.path.exists(sesion['ruta_fotos']):
                        contenido = os.listdir(sesion['ruta_fotos'])
                        if len(contenido) == 0:
                            os.rmdir(sesion['ruta_fotos'])
                            carpetas_eliminadas += 1
                            logging.debug(f"[MediaGallery] Carpeta vacía eliminada: {sesion['ruta_fotos']}")

                    # Eliminar carpeta de fotos vacía (libre)
                    if sesion.get('ruta_fotos_libre') and os.path.exists(sesion['ruta_fotos_libre']):
                        contenido = os.listdir(sesion['ruta_fotos_libre'])
                        if len(contenido) == 0:
                            os.rmdir(sesion['ruta_fotos_libre'])
                            carpetas_eliminadas += 1
                            logging.debug(f"[MediaGallery] Carpeta vacía eliminada: {sesion['ruta_fotos_libre']}")

                    # Eliminar carpeta de videos vacía (misión)
                    if sesion['ruta_videos'] and os.path.exists(sesion['ruta_videos']):
                        contenido = os.listdir(sesion['ruta_videos'])
                        if len(contenido) == 0:
                            os.rmdir(sesion['ruta_videos'])
                            carpetas_eliminadas += 1
                            logging.debug(f"[MediaGallery] Carpeta vacía eliminada: {sesion['ruta_videos']}")

                    # Eliminar carpeta de videos vacía (libre)
                    if sesion.get('ruta_videos_libre') and os.path.exists(sesion['ruta_videos_libre']):
                        contenido = os.listdir(sesion['ruta_videos_libre'])
                        if len(contenido) == 0:
                            os.rmdir(sesion['ruta_videos_libre'])
                            carpetas_eliminadas += 1
                            logging.debug(f"[MediaGallery] Carpeta vacía eliminada: {sesion['ruta_videos_libre']}")

                except Exception as e:
                    logging.warning(f"[MediaGallery] No se pudo eliminar carpeta vacía: {e}")
        
        if carpetas_eliminadas > 0:
            logging.info(f"[MediaGallery] {carpetas_eliminadas} carpetas vacías eliminadas automáticamente")
    
    def abrir_galeria(self):
        """Abre la ventana de la galería"""
        if self.ventana is not None:
            self.ventana.lift()
            return
        
        self.ventana = tk.Toplevel()
        self.ventana.title("📷🎬 Galería de Medios - Vuelos Crazyflie")
        self.ventana.geometry("1300x750")
        
        # Manejar cierre de ventana
        self.ventana.protocol("WM_DELETE_WINDOW", self._cerrar_galeria)
        
        self._crear_interfaz()
        
        # Cargar última sesión si existe
        if self.sesiones:
            self.listbox_sesiones.selection_set(0)
            self._seleccionar_sesion()
    
    def _crear_interfaz(self):
        """Crea la interfaz de la galería"""
        # Panel superior - Información
        frame_info = tk.Frame(self.ventana, bg="#2c3e50", height=60)
        frame_info.pack(fill=tk.X)
        
        tk.Label(frame_info, text="📷🎬 Galería de Medios de Vuelo", 
                font=("Arial", 16, "bold"), bg="#2c3e50", fg="white").pack(pady=12)
        
        # Contenedor principal
        main_container = tk.Frame(self.ventana, bg="#ecf0f1")
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Panel izquierdo - Sesiones y lista de medios
        panel_izq = tk.Frame(main_container, width=320, bg="#ecf0f1")
        panel_izq.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        panel_izq.pack_propagate(False)
        
        # Frame de sesiones
        frame_sesiones = tk.LabelFrame(panel_izq, text="📁 Sesiones de Vuelo", 
                                        padx=5, pady=5, font=("Arial", 10, "bold"))
        frame_sesiones.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Scrollbar para sesiones
        scrollbar_sesiones = tk.Scrollbar(frame_sesiones)
        scrollbar_sesiones.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Listbox de sesiones
        self.listbox_sesiones = tk.Listbox(frame_sesiones, 
                                           yscrollcommand=scrollbar_sesiones.set,
                                           font=("Consolas", 9),
                                           selectbackground="#3498db",
                                           height=8)
        self.listbox_sesiones.pack(fill=tk.BOTH, expand=True)
        scrollbar_sesiones.config(command=self.listbox_sesiones.yview)
        
        # Cargar sesiones en listbox
        self._actualizar_listbox_sesiones()
        
        self.listbox_sesiones.bind('<<ListboxSelect>>', lambda e: self._seleccionar_sesion())
        
        # Frame de filtros
        frame_filtros = tk.Frame(panel_izq, bg="#ecf0f1")
        frame_filtros.pack(fill=tk.X, pady=5)
        
        tk.Label(frame_filtros, text="Filtrar:", bg="#ecf0f1", 
                font=("Arial", 9, "bold")).pack(side=tk.LEFT)
        
        self.filtro_var = tk.StringVar(value="todos")
        
        tk.Radiobutton(frame_filtros, text="Todos", variable=self.filtro_var, 
                       value="todos", bg="#ecf0f1", command=self._aplicar_filtro).pack(side=tk.LEFT)
        tk.Radiobutton(frame_filtros, text="📷 Fotos", variable=self.filtro_var, 
                       value="fotos", bg="#ecf0f1", command=self._aplicar_filtro).pack(side=tk.LEFT)
        tk.Radiobutton(frame_filtros, text="🎬 Videos", variable=self.filtro_var, 
                       value="videos", bg="#ecf0f1", command=self._aplicar_filtro).pack(side=tk.LEFT)
        
        # Frame de archivos de la sesión
        frame_medios = tk.LabelFrame(panel_izq, text="📂 Archivos de la Sesión", 
                                      padx=5, pady=5, font=("Arial", 10, "bold"))
        frame_medios.pack(fill=tk.BOTH, expand=True)
        
        scrollbar_medios = tk.Scrollbar(frame_medios)
        scrollbar_medios.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listbox_medios = tk.Listbox(frame_medios,
                                         yscrollcommand=scrollbar_medios.set,
                                         font=("Consolas", 9),
                                         selectbackground="#3498db")
        self.listbox_medios.pack(fill=tk.BOTH, expand=True)
        scrollbar_medios.config(command=self.listbox_medios.yview)
        
        self.listbox_medios.bind('<<ListboxSelect>>', lambda e: self._seleccionar_medio())
        self.listbox_medios.bind('<Double-Button-1>', lambda e: self._abrir_medio_externo())
        
        # Panel derecho - Visualización
        panel_der = tk.Frame(main_container, bg="#ecf0f1")
        panel_der.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Canvas para mostrar preview
        frame_canvas = tk.Frame(panel_der, bg="black", relief=tk.SUNKEN, bd=2)
        frame_canvas.pack(fill=tk.BOTH, expand=True)
        
        self.canvas_preview = tk.Canvas(frame_canvas, bg="#1a1a2e", highlightthickness=0)
        self.canvas_preview.pack(fill=tk.BOTH, expand=True)
        
        # Label de información
        self.label_info = tk.Label(panel_der, text="Selecciona una sesión y archivo", 
                                   font=("Arial", 10), bg="#34495e", fg="white", pady=8)
        self.label_info.pack(fill=tk.X)
        
        # Botones de navegación
        frame_nav = tk.Frame(panel_der, bg="#ecf0f1")
        frame_nav.pack(fill=tk.X, pady=8)
        
        tk.Button(frame_nav, text="⬅️ Anterior", 
                 command=self._medio_anterior,
                 bg="#3498db", fg="white", font=("Arial", 10, "bold"),
                 width=12, cursor="hand2").pack(side=tk.LEFT, padx=5)
        
        tk.Button(frame_nav, text="➡️ Siguiente", 
                 command=self._medio_siguiente,
                 bg="#3498db", fg="white", font=("Arial", 10, "bold"),
                 width=12, cursor="hand2").pack(side=tk.LEFT, padx=5)
        
        tk.Button(frame_nav, text="▶️ Reproducir", 
                 command=self._abrir_medio_externo,
                 bg="#9b59b6", fg="white", font=("Arial", 10, "bold"),
                 width=12, cursor="hand2").pack(side=tk.LEFT, padx=5)
        
        tk.Button(frame_nav, text="🗑️ Eliminar", 
                 command=self._eliminar_medio,
                 bg="#e74c3c", fg="white", font=("Arial", 10, "bold"),
                 width=12, cursor="hand2").pack(side=tk.LEFT, padx=5)
        
        tk.Button(frame_nav, text="💾 Exportar", 
                 command=self._exportar_sesion,
                 bg="#27ae60", fg="white", font=("Arial", 10, "bold"),
                 width=12, cursor="hand2").pack(side=tk.LEFT, padx=5)
        
        # Frame inferior - Botones de gestión
        frame_gestion = tk.Frame(self.ventana, bg="#bdc3c7")
        frame_gestion.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(frame_gestion, text="🗑️ Eliminar Sesión Completa",
                 command=self._eliminar_sesion,
                 bg="#c0392b", fg="white", font=("Arial", 10, "bold"),
                 width=25, cursor="hand2").pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Button(frame_gestion, text="🔄 Actualizar",
                 command=self._actualizar_galeria,
                 bg="#f39c12", fg="white", font=("Arial", 10, "bold"),
                 width=12, cursor="hand2").pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Button(frame_gestion, text="❌ Cerrar",
                 command=self._cerrar_galeria,
                 bg="#7f8c8d", fg="white", font=("Arial", 10, "bold"),
                 width=12, cursor="hand2").pack(side=tk.RIGHT, padx=5, pady=5)
    
    def _actualizar_listbox_sesiones(self):
        """Actualiza el listbox de sesiones"""
        self.listbox_sesiones.delete(0, tk.END)

        for sesion in self.sesiones:
            fecha_formateada = self._formatear_fecha(sesion['fecha'])

            # NUEVO: Sumar fotos/videos de ambas fuentes
            total_fotos = sesion['num_fotos'] + sesion['num_fotos_libre']
            total_videos = sesion['num_videos'] + sesion['num_videos_libre']

            # Mostrar contadores
            partes = []
            if total_fotos > 0:
                partes.append(f"{total_fotos} 📷")
            if total_videos > 0:
                partes.append(f"{total_videos} 🎬")

            if partes:
                texto = f"{fecha_formateada} ({', '.join(partes)})"
            else:
                texto = f"{fecha_formateada} (vacía)"

            self.listbox_sesiones.insert(tk.END, texto)
    
    def _formatear_fecha(self, fecha_str: str) -> str:
        """Formatea la fecha de la sesión"""
        try:
            if '_' in fecha_str:
                fecha, hora = fecha_str.split('_')
                fecha_formateada = f"{fecha[6:8]}/{fecha[4:6]}/{fecha[0:4]}"
                hora_formateada = f"{hora[0:2]}:{hora[2:4]}:{hora[4:6]}"
                return f"{fecha_formateada} {hora_formateada}"
            return fecha_str
        except:
            return fecha_str
    
    def _aplicar_filtro(self):
        """Aplica el filtro seleccionado"""
        self.tipo_filtro = self.filtro_var.get()
        self._cargar_medios_sesion()
    
    def _seleccionar_sesion(self):
        """Carga los medios de la sesión seleccionada"""
        seleccion = self.listbox_sesiones.curselection()
        if not seleccion:
            return
        
        indice = seleccion[0]
        self.sesion_actual = self.sesiones[indice]
        self._cargar_medios_sesion()
    
    def _cargar_medios_sesion(self):
        """Carga los archivos de la sesión actual según el filtro"""
        if not self.sesion_actual:
            return

        self.medios_actuales = []

        # NUEVO: Cargar fotos de ambas fuentes (misión + libre)
        if self.tipo_filtro in ["todos", "fotos"]:
            # Fotos de misión
            if self.sesion_actual['ruta_fotos']:
                if os.path.exists(self.sesion_actual['ruta_fotos']):
                    for archivo in sorted(os.listdir(self.sesion_actual['ruta_fotos'])):
                        if archivo.lower().endswith(('.jpg', '.jpeg', '.png')):
                            ruta = os.path.join(self.sesion_actual['ruta_fotos'], archivo)
                            self.medios_actuales.append({
                                'ruta': ruta,
                                'nombre': archivo,
                                'tipo': 'foto',
                                'origen': 'misión'  # NUEVO
                            })

            # Fotos de modo libre
            if self.sesion_actual.get('ruta_fotos_libre'):
                if os.path.exists(self.sesion_actual['ruta_fotos_libre']):
                    for archivo in sorted(os.listdir(self.sesion_actual['ruta_fotos_libre'])):
                        if archivo.lower().endswith(('.jpg', '.jpeg', '.png')):
                            ruta = os.path.join(self.sesion_actual['ruta_fotos_libre'], archivo)
                            self.medios_actuales.append({
                                'ruta': ruta,
                                'nombre': f"[Libre] {archivo}",  # NUEVO: Prefijo para distinguir
                                'tipo': 'foto',
                                'origen': 'libre'  # NUEVO
                            })

        # NUEVO: Cargar videos de ambas fuentes (misión + libre)
        if self.tipo_filtro in ["todos", "videos"]:
            # Videos de misión
            if self.sesion_actual['ruta_videos']:
                if os.path.exists(self.sesion_actual['ruta_videos']):
                    for archivo in sorted(os.listdir(self.sesion_actual['ruta_videos'])):
                        if archivo.lower().endswith(('.avi', '.mp4', '.mkv', '.mov')):
                            ruta = os.path.join(self.sesion_actual['ruta_videos'], archivo)
                            self.medios_actuales.append({
                                'ruta': ruta,
                                'nombre': archivo,
                                'tipo': 'video',
                                'origen': 'misión'  # NUEVO
                            })

            # Videos de modo libre
            if self.sesion_actual.get('ruta_videos_libre'):
                if os.path.exists(self.sesion_actual['ruta_videos_libre']):
                    for archivo in sorted(os.listdir(self.sesion_actual['ruta_videos_libre'])):
                        if archivo.lower().endswith(('.avi', '.mp4', '.mkv', '.mov')):
                            ruta = os.path.join(self.sesion_actual['ruta_videos_libre'], archivo)
                            self.medios_actuales.append({
                                'ruta': ruta,
                                'nombre': f"[Libre] {archivo}",  # NUEVO: Prefijo para distinguir
                                'tipo': 'video',
                                'origen': 'libre'  # NUEVO
                            })
        
        # Actualizar listbox
        self.listbox_medios.delete(0, tk.END)
        for i, medio in enumerate(self.medios_actuales):
            icono = "📷" if medio['tipo'] == 'foto' else "🎬"
            self.listbox_medios.insert(tk.END, f"{icono} {medio['nombre']}")
        
        # Seleccionar primer elemento
        if self.medios_actuales:
            self.listbox_medios.selection_set(0)
            self.indice_actual = 0
            self._mostrar_preview(0)
        else:
            self._mostrar_mensaje_vacio()
        
        logging.info(f"[MediaGallery] Sesión cargada: {len(self.medios_actuales)} archivos")
    
    def _seleccionar_medio(self):
        """Muestra el preview del medio seleccionado"""
        seleccion = self.listbox_medios.curselection()
        if not seleccion or not self.medios_actuales:
            return
        
        self.indice_actual = seleccion[0]
        self._mostrar_preview(self.indice_actual)
    
    def _mostrar_preview(self, indice: int):
        """Muestra preview del archivo"""
        if indice < 0 or indice >= len(self.medios_actuales):
            return
        
        medio = self.medios_actuales[indice]
        
        if medio['tipo'] == 'foto':
            self._mostrar_foto(medio)
        else:
            self._mostrar_preview_video(medio)
    
    def _mostrar_foto(self, medio: Dict):
        """Muestra una foto en el canvas"""
        try:
            imagen = Image.open(medio['ruta'])
            
            # Redimensionar
            canvas_width = self.canvas_preview.winfo_width()
            canvas_height = self.canvas_preview.winfo_height()
            
            if canvas_width <= 1:
                canvas_width = 800
            if canvas_height <= 1:
                canvas_height = 500
            
            img_width, img_height = imagen.size
            ratio = min(canvas_width/img_width, canvas_height/img_height) * 0.95
            new_width = int(img_width * ratio)
            new_height = int(img_height * ratio)
            
            imagen_redimensionada = imagen.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.photo = ImageTk.PhotoImage(imagen_redimensionada)
            
            # Mostrar
            self.canvas_preview.delete("all")
            x = canvas_width // 2
            y = canvas_height // 2
            self.canvas_preview.create_image(x, y, anchor=tk.CENTER, image=self.photo)
            
            # Info
            info = f"📷 Foto {self.indice_actual + 1}/{len(self.medios_actuales)} - {medio['nombre']} - {img_width}x{img_height}"
            self.label_info.config(text=info)
            
        except Exception as e:
            logging.error(f"[MediaGallery] Error al mostrar foto: {e}")
            self._mostrar_error(str(e))
    
    def _mostrar_preview_video(self, medio: Dict):
        """Muestra preview de video (thumbnail o icono)"""
        self.canvas_preview.delete("all")
        
        canvas_width = self.canvas_preview.winfo_width()
        canvas_height = self.canvas_preview.winfo_height()
        
        if canvas_width <= 1:
            canvas_width = 800
        if canvas_height <= 1:
            canvas_height = 500
        
        # Icono de video
        self.canvas_preview.create_text(
            canvas_width // 2,
            canvas_height // 2 - 40,
            text="🎬",
            font=("Arial", 72),
            fill="white"
        )
        
        self.canvas_preview.create_text(
            canvas_width // 2,
            canvas_height // 2 + 40,
            text=medio['nombre'],
            font=("Arial", 14, "bold"),
            fill="white"
        )
        
        self.canvas_preview.create_text(
            canvas_width // 2,
            canvas_height // 2 + 80,
            text="Doble click o pulsa ▶️ Reproducir para ver",
            font=("Arial", 11),
            fill="#95a5a6"
        )
        
        # Obtener tamaño del archivo
        try:
            size_bytes = os.path.getsize(medio['ruta'])
            if size_bytes > 1024 * 1024:
                size_str = f"{size_bytes / (1024*1024):.1f} MB"
            else:
                size_str = f"{size_bytes / 1024:.1f} KB"
        except:
            size_str = "?"
        
        info = f"🎬 Video {self.indice_actual + 1}/{len(self.medios_actuales)} - {medio['nombre']} - {size_str}"
        self.label_info.config(text=info)
    
    def _mostrar_mensaje_vacio(self):
        """Muestra mensaje cuando no hay archivos"""
        self.canvas_preview.delete("all")
        
        canvas_width = self.canvas_preview.winfo_width()
        canvas_height = self.canvas_preview.winfo_height()
        
        if canvas_width <= 1:
            canvas_width = 800
        if canvas_height <= 1:
            canvas_height = 500
        
        self.canvas_preview.create_text(
            canvas_width // 2,
            canvas_height // 2,
            text="📭 No hay archivos en esta sesión",
            font=("Arial", 16),
            fill="white"
        )
        self.label_info.config(text="No hay archivos para mostrar")
    
    def _mostrar_error(self, mensaje: str):
        """Muestra mensaje de error"""
        self.canvas_preview.delete("all")
        
        canvas_width = self.canvas_preview.winfo_width() or 800
        canvas_height = self.canvas_preview.winfo_height() or 500
        
        self.canvas_preview.create_text(
            canvas_width // 2,
            canvas_height // 2,
            text=f"❌ Error: {mensaje}",
            font=("Arial", 12),
            fill="#e74c3c"
        )
    
    def _abrir_medio_externo(self):
        """Abre el archivo con la aplicación del sistema"""
        if not self.medios_actuales or self.indice_actual >= len(self.medios_actuales):
            return
        
        medio = self.medios_actuales[self.indice_actual]
        ruta = medio['ruta']
        
        try:
            if platform.system() == 'Windows':
                os.startfile(ruta)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', ruta])
            else:  # Linux
                subprocess.run(['xdg-open', ruta])
            
            logging.info(f"[MediaGallery] Abriendo: {ruta}")
            
        except Exception as e:
            logging.error(f"[MediaGallery] Error al abrir archivo: {e}")
            messagebox.showerror("Error", f"No se pudo abrir el archivo:\n{e}")
    
    def _medio_anterior(self):
        """Muestra el medio anterior"""
        if not self.medios_actuales:
            return
        
        nuevo_indice = (self.indice_actual - 1) % len(self.medios_actuales)
        self.indice_actual = nuevo_indice
        self.listbox_medios.selection_clear(0, tk.END)
        self.listbox_medios.selection_set(nuevo_indice)
        self.listbox_medios.see(nuevo_indice)
        self._mostrar_preview(nuevo_indice)
    
    def _medio_siguiente(self):
        """Muestra el medio siguiente"""
        if not self.medios_actuales:
            return
        
        nuevo_indice = (self.indice_actual + 1) % len(self.medios_actuales)
        self.indice_actual = nuevo_indice
        self.listbox_medios.selection_clear(0, tk.END)
        self.listbox_medios.selection_set(nuevo_indice)
        self.listbox_medios.see(nuevo_indice)
        self._mostrar_preview(nuevo_indice)
    
    def _eliminar_medio(self):
        """Elimina el archivo actual"""
        if not self.medios_actuales or self.indice_actual >= len(self.medios_actuales):
            return
        
        medio = self.medios_actuales[self.indice_actual]
        tipo = "foto" if medio['tipo'] == 'foto' else "video"
        
        respuesta = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Eliminar este {tipo}?\n\n{medio['nombre']}\n\n"
            "Esta acción no se puede deshacer."
        )
        
        if respuesta:
            try:
                os.remove(medio['ruta'])
                logging.info(f"[MediaGallery] Eliminado: {medio['nombre']}")

                # Actualizar lista
                del self.medios_actuales[self.indice_actual]
                self.listbox_medios.delete(self.indice_actual)

                # NUEVO: Actualizar contadores de sesión según origen
                if medio['tipo'] == 'foto':
                    if medio.get('origen') == 'libre':
                        self.sesion_actual['num_fotos_libre'] -= 1
                    else:
                        self.sesion_actual['num_fotos'] -= 1
                else:
                    if medio.get('origen') == 'libre':
                        self.sesion_actual['num_videos_libre'] -= 1
                    else:
                        self.sesion_actual['num_videos'] -= 1
                
                # Mostrar siguiente
                if self.medios_actuales:
                    if self.indice_actual >= len(self.medios_actuales):
                        self.indice_actual = len(self.medios_actuales) - 1
                    self.listbox_medios.selection_set(self.indice_actual)
                    self._mostrar_preview(self.indice_actual)
                else:
                    self._mostrar_mensaje_vacio()
                
                messagebox.showinfo("Éxito", f"{tipo.capitalize()} eliminado correctamente")
                
            except Exception as e:
                logging.error(f"[MediaGallery] Error al eliminar: {e}")
                messagebox.showerror("Error", f"No se pudo eliminar:\n{e}")
    
    def _eliminar_sesion(self):
        """Elimina toda la sesión"""
        if not self.sesion_actual:
            messagebox.showwarning("Advertencia", "No hay sesión seleccionada")
            return
        
        total = self.sesion_actual['num_fotos'] + self.sesion_actual['num_videos']
        
        respuesta = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Eliminar TODA la sesión?\n\n"
            f"Fecha: {self._formatear_fecha(self.sesion_actual['fecha'])}\n"
            f"Fotos: {self.sesion_actual['num_fotos']}\n"
            f"Videos: {self.sesion_actual['num_videos']}\n\n"
            "Esta acción no se puede deshacer."
        )
        
        if respuesta:
            try:
                # Eliminar carpeta de fotos (misión)
                if self.sesion_actual['ruta_fotos'] and os.path.exists(self.sesion_actual['ruta_fotos']):
                    shutil.rmtree(self.sesion_actual['ruta_fotos'])

                # NUEVO: Eliminar carpeta de fotos (libre)
                if self.sesion_actual.get('ruta_fotos_libre') and os.path.exists(self.sesion_actual['ruta_fotos_libre']):
                    shutil.rmtree(self.sesion_actual['ruta_fotos_libre'])

                # Eliminar carpeta de videos (misión)
                if self.sesion_actual['ruta_videos'] and os.path.exists(self.sesion_actual['ruta_videos']):
                    shutil.rmtree(self.sesion_actual['ruta_videos'])

                # NUEVO: Eliminar carpeta de videos (libre)
                if self.sesion_actual.get('ruta_videos_libre') and os.path.exists(self.sesion_actual['ruta_videos_libre']):
                    shutil.rmtree(self.sesion_actual['ruta_videos_libre'])
                
                logging.info(f"[MediaGallery] Sesión eliminada: {self.sesion_actual['nombre']}")
                messagebox.showinfo("Éxito", "Sesión eliminada correctamente")
                
                self._actualizar_galeria()
                
            except Exception as e:
                logging.error(f"[MediaGallery] Error al eliminar sesión: {e}")
                messagebox.showerror("Error", f"No se pudo eliminar:\n{e}")
    
    def _exportar_sesion(self):
        """Exporta la sesión a una carpeta"""
        if not self.sesion_actual:
            messagebox.showwarning("Advertencia", "No hay sesión seleccionada")
            return
        
        carpeta_destino = filedialog.askdirectory(title="Selecciona carpeta de destino")
        if not carpeta_destino:
            return
        
        try:
            nombre_export = f"vuelo_{self.sesion_actual['fecha']}"
            ruta_export = os.path.join(carpeta_destino, nombre_export)
            
            if os.path.exists(ruta_export):
                if not messagebox.askyesno("Existe", "La carpeta ya existe. ¿Sobrescribir?"):
                    return
                shutil.rmtree(ruta_export)
            
            os.makedirs(ruta_export)

            # Copiar fotos
            fotos_copiadas = 0
            if self.sesion_actual['ruta_fotos'] and os.path.exists(self.sesion_actual['ruta_fotos']):
                carpeta_fotos = os.path.join(ruta_export, "fotos_mision")
                shutil.copytree(self.sesion_actual['ruta_fotos'], carpeta_fotos)
                fotos_copiadas += self.sesion_actual['num_fotos']

            # NUEVO: Copiar fotos de modo libre
            if self.sesion_actual.get('ruta_fotos_libre') and os.path.exists(self.sesion_actual['ruta_fotos_libre']):
                carpeta_fotos_libre = os.path.join(ruta_export, "fotos_libre")
                shutil.copytree(self.sesion_actual['ruta_fotos_libre'], carpeta_fotos_libre)
                fotos_copiadas += self.sesion_actual['num_fotos_libre']

            # Copiar videos
            videos_copiados = 0
            if self.sesion_actual['ruta_videos'] and os.path.exists(self.sesion_actual['ruta_videos']):
                carpeta_videos = os.path.join(ruta_export, "videos_mision")
                shutil.copytree(self.sesion_actual['ruta_videos'], carpeta_videos)
                videos_copiados += self.sesion_actual['num_videos']

            # NUEVO: Copiar videos de modo libre
            if self.sesion_actual.get('ruta_videos_libre') and os.path.exists(self.sesion_actual['ruta_videos_libre']):
                carpeta_videos_libre = os.path.join(ruta_export, "videos_libre")
                shutil.copytree(self.sesion_actual['ruta_videos_libre'], carpeta_videos_libre)
                videos_copiados += self.sesion_actual['num_videos_libre']
            
            messagebox.showinfo(
                "Éxito",
                f"Sesión exportada:\n\n{ruta_export}\n\n"
                f"📷 Fotos: {fotos_copiadas}\n"
                f"🎬 Videos: {videos_copiados}"
            )
            
            logging.info(f"[MediaGallery] Sesión exportada a: {ruta_export}")
            
        except Exception as e:
            logging.error(f"[MediaGallery] Error al exportar: {e}")
            messagebox.showerror("Error", f"No se pudo exportar:\n{e}")
    
    def _actualizar_galeria(self):
        """Actualiza toda la galería"""
        self._cargar_sesiones()
        self._actualizar_listbox_sesiones()
        
        self.medios_actuales = []
        self.sesion_actual = None
        self.listbox_medios.delete(0, tk.END)
        self.canvas_preview.delete("all")
        self.label_info.config(text="Selecciona una sesión y archivo")
        
        logging.info("[MediaGallery] Galería actualizada")
    
    def _cerrar_galeria(self):
        """Cierra la ventana"""
        if self.ventana:
            self.ventana.destroy()
            self.ventana = None
            logging.info("[MediaGallery] Galería cerrada")


# Mantener compatibilidad con PhotoGallery
class PhotoGallery(MediaGallery):
    """Alias para compatibilidad con código existente"""
    pass


def abrir_galeria_medios(carpeta_fotos: str = "fotos_vuelo", carpeta_videos: str = "videos_vuelo"):
    """
    Función auxiliar para abrir la galería de medios
    
    Args:
        carpeta_fotos: Carpeta de fotos
        carpeta_videos: Carpeta de videos
    """
    galeria = MediaGallery(carpeta_fotos, carpeta_videos)
    galeria.abrir_galeria()
    return galeria


# Compatibilidad
def abrir_galeria_fotos(carpeta_fotos: str = "fotos_vuelo"):
    """Función de compatibilidad"""
    return abrir_galeria_medios(carpeta_fotos)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    root = tk.Tk()
    root.withdraw()
    
    galeria = MediaGallery()
    galeria.abrir_galeria()
    
    root.mainloop()
