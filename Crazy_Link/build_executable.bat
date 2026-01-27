@echo off
REM Script de construcción del ejecutable CrazyLink Dashboard para Windows

echo ==========================================
echo   CrazyLink Dashboard - Build Script
echo ==========================================
echo.

REM Verificar que PyInstaller está instalado
python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo X PyInstaller no esta instalado
    echo Instalando PyInstaller...
    python -m pip install pyinstaller
    if errorlevel 1 (
        echo X Error al instalar PyInstaller
        pause
        exit /b 1
    )
    echo PyInstaller instalado correctamente
)

echo Generando ejecutable...
echo.

REM Limpiar builds anteriores
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Ejecutar PyInstaller usando el archivo .spec
python -m PyInstaller --clean --noconfirm CrazyLink_Dashboard.spec

REM Verificar si la construcción fue exitosa
if %errorlevel% equ 0 (
    echo.
    echo ==========================================
    echo Ejecutable generado exitosamente
    echo ==========================================
    echo.
    echo Ubicacion: dist\CrazyLink_Planificador\CrazyLink_Planificador.exe
    echo.
    echo Para ejecutar la aplicacion:
    echo    cd dist\CrazyLink_Planificador
    echo    CrazyLink_Planificador.exe
    echo.
    echo O navega a dist\CrazyLink_Planificador y haz doble clic en el archivo.
    echo.
    echo Para mas informacion, consulta README_EJECUTABLE.md
    echo.
) else (
    echo.
    echo X Error al generar el ejecutable
    echo Revisa los mensajes de error arriba
    pause
    exit /b 1
)

pause
