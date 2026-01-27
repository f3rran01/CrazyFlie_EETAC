# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all, collect_submodules, collect_data_files

# Recolectar todos los módulos y datos de matplotlib
matplotlib_datas, matplotlib_binaries, matplotlib_hiddenimports = collect_all('matplotlib')

# Recolectar submódulos adicionales
hiddenimports_extra = (
    collect_submodules('scipy') +
    collect_submodules('numpy') +
    collect_submodules('matplotlib') +
    collect_submodules('mpl_toolkits') +
    collect_submodules('cflib') +
    ['matplotlib.backends.backend_tkagg']
)

a = Analysis(
    ['pyinstaller_wrapper.py'],
    pathex=['.'],
    binaries=matplotlib_binaries,
    datas=[
        ('crazyLink', 'crazyLink'),
        ('demostradores_crazyflie', 'demostradores_crazyflie'),
        ('vosk-model-small-es-0.42', 'vosk-model-small-es-0.42'),
    ] + matplotlib_datas + collect_data_files('matplotlib'),
    hiddenimports=[
        'PIL',
        'PIL._tkinter_finder',
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
        'tkinter.filedialog',
        'shapely',
        'shapely.geometry',
        'shapely.ops',
        'shapely.affinity',
        'cflib',
        'cv2',
        'pygame',
        'vosk',
        'sounddevice',
        'queue',
    ] + matplotlib_hiddenimports + hiddenimports_extra,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['runtime_hook.py'],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CrazyLink_Planificador',
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CrazyLink_Planificador',
)
