"""
Runtime hook para configurar matplotlib correctamente en PyInstaller
"""
import sys
import os

# Configurar matplotlib antes de cualquier import
os.environ['MPLBACKEND'] = 'TkAgg'

# Asegurar que matplotlib puede encontrar sus archivos
if hasattr(sys, '_MEIPASS'):
    # Estamos en un ejecutable de PyInstaller
    os.environ['MATPLOTLIBDATA'] = os.path.join(sys._MEIPASS, 'matplotlib', 'mpl-data')
