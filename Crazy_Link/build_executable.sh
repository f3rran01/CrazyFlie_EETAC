#!/bin/bash
# Script de construcción del ejecutable CrazyLink Dashboard para Linux/Mac

echo "=========================================="
echo "  CrazyLink Dashboard - Build Script"
echo "=========================================="
echo ""

# Verificar que PyInstaller está instalado
if ! command -v pyinstaller &> /dev/null
then
    echo "❌ PyInstaller no está instalado"
    echo "📦 Instalando PyInstaller..."
    pip install pyinstaller
    if [ $? -ne 0 ]; then
        echo "❌ Error al instalar PyInstaller"
        exit 1
    fi
    echo "✅ PyInstaller instalado correctamente"
fi

echo "🔨 Generando ejecutable..."
echo ""

# Ejecutar PyInstaller
pyinstaller --onefile \
            --windowed \
            --name="CrazyLink_Dashboard" \
            --paths=. \
            --add-data="crazyLink:crazyLink" \
            --add-data="demostradores_crazyflie:demostradores_crazyflie" \
            demostradores_crazyflie/DashboardPlot.py

# Verificar si la construcción fue exitosa
if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ Ejecutable generado exitosamente"
    echo "=========================================="
    echo ""
    echo "📁 Ubicación: dist/CrazyLink_Dashboard"
    echo ""
    echo "Para ejecutar la aplicación:"
    echo "   cd dist"
    echo "   ./CrazyLink_Dashboard"
    echo ""
    echo "Para más información, consulta README_EJECUTABLE.md"
    echo ""
else
    echo ""
    echo "❌ Error al generar el ejecutable"
    echo "Revisa los mensajes de error arriba"
    exit 1
fi
