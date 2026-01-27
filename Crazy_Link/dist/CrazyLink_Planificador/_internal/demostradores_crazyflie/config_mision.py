"""
Configuración de Parámetros de Misión
Ajusta estos valores para controlar la velocidad y tiempos de espera
"""


class ConfigMision:
    """
    Configuración centralizada para el comportamiento del dron

    ⚡ PERFILES PREDEFINIDOS:
    - RAPIDO: Máxima velocidad (puede perder paquetes)
    - NORMAL: Balance óptimo velocidad/estabilidad (RECOMENDADO)
    - ESTABLE: Máxima estabilidad (más lento)
    """

    # ============================================
    #  PERFIL RÁPIDO (experimental)
    # ============================================
    RAPIDO = {
        'velocidad': 0.4,  # m/s - velocidad de movimiento
        'pausa_waypoint': 0.2,  # segundos entre waypoints
        'pausa_rotacion': 0.3,  # segundos para rotaciones
        'tolerancia': 0.25,  # metros - distancia para "llegada"
        'timeout_waypoint': 2.0,  # segundos - timeout por waypoint
        'intervalo_check': 0.03,  # segundos - frecuencia de verificación
    }

    # ============================================
    # ️ PERFIL NORMAL (RECOMENDADO)
    # ============================================
    NORMAL = {
        'velocidad': 0.3,  # m/s - buen balance
        'pausa_waypoint': 0.3,  # segundos entre waypoints
        'pausa_rotacion': 0.5,  # segundos para rotaciones
        'tolerancia': 0.2,  # metros - distancia para "llegada"
        'timeout_waypoint': 3.0,  # segundos - timeout por waypoint
        'intervalo_check': 0.05,  # segundos - frecuencia de verificación
    }

    # ============================================
    # PERFIL ESTABLE (máxima fiabilidad)
    # ============================================
    ESTABLE = {
        'velocidad': 0.2,  # m/s - velocidad conservadora
        'pausa_waypoint': 0.5,  # segundos entre waypoints
        'pausa_rotacion': 0.8,  # segundos para rotaciones
        'tolerancia': 0.15,  # metros - más preciso
        'timeout_waypoint': 5.0,  # segundos - más tiempo de espera
        'intervalo_check': 0.1,  # segundos - checks menos frecuentes
    }

    # ============================================
    #  PERFIL ACTIVO (cambiar aquí)
    # ============================================
    ACTIVO = NORMAL  #  Cambia a RAPIDO, NORMAL o ESTABLE

    # ============================================
    #  MÉTODOS DE ACCESO
    # ============================================
    @classmethod
    def get(cls, parametro: str, default=None):
        """Obtiene un parámetro de configuración"""
        return cls.ACTIVO.get(parametro, default)

    @classmethod
    def get_velocidad(cls) -> float:
        """Velocidad de movimiento en m/s"""
        return cls.ACTIVO['velocidad']

    @classmethod
    def get_pausa_waypoint(cls) -> float:
        """Tiempo de pausa entre waypoints en segundos"""
        return cls.ACTIVO['pausa_waypoint']

    @classmethod
    def get_pausa_rotacion(cls) -> float:
        """Tiempo de pausa para rotaciones en segundos"""
        return cls.ACTIVO['pausa_rotacion']

    @classmethod
    def get_tolerancia(cls) -> float:
        """Tolerancia de llegada en metros"""
        return cls.ACTIVO['tolerancia']

    @classmethod
    def get_timeout_waypoint(cls) -> float:
        """Timeout por waypoint en segundos"""
        return cls.ACTIVO['timeout_waypoint']

    @classmethod
    def get_intervalo_check(cls) -> float:
        """Intervalo entre verificaciones en segundos"""
        return cls.ACTIVO['intervalo_check']

    @classmethod
    def mostrar_config(cls):
        """Imprime la configuración activa"""
        print("\n" + "=" * 50)
        print("⚙️  CONFIGURACIÓN ACTIVA DE MISIÓN")
        print("=" * 50)
        for key, value in cls.ACTIVO.items():
            print(f"  {key:20s}: {value}")
        print("=" * 50 + "\n")

    @classmethod
    def estimar_tiempo_mision(cls, num_waypoints: int, distancia_total: float) -> float:
        """
        Estima el tiempo total de una misión

        Args:
            num_waypoints: Número de waypoints
            distancia_total: Distancia total en metros

        Returns:
            Tiempo estimado en segundos
        """
        velocidad = cls.get_velocidad()
        pausa_wp = cls.get_pausa_waypoint()

        tiempo_movimiento = distancia_total / velocidad
        tiempo_pausas = num_waypoints * pausa_wp

        return tiempo_movimiento + tiempo_pausas


# ============================================
# 🧪 PRUEBAS DE CONFIGURACIÓN
# ============================================
if __name__ == "__main__":
    print("\n PROBANDO PERFILES DE CONFIGURACIÓN\n")

    # Probar cada perfil
    for nombre_perfil in ['RAPIDO', 'NORMAL', 'ESTABLE']:
        ConfigMision.ACTIVO = getattr(ConfigMision, nombre_perfil)
        print(f"\n📋 PERFIL: {nombre_perfil}")
        ConfigMision.mostrar_config()

        # Estimar tiempo para misión ejemplo
        tiempo = ConfigMision.estimar_tiempo_mision(
            num_waypoints=5,
            distancia_total=8.0  # 8 metros total
        )
        print(f"⏱️  Tiempo estimado (5 waypoints, 8m): {tiempo:.1f}s")
        print("-" * 50)

    # Restaurar perfil normal
    ConfigMision.ACTIVO = ConfigMision.NORMAL

    print("\n✅ Para usar en tu código:")
    print("   from config_mision import ConfigMision")
    print("   velocidad = ConfigMision.get_velocidad()")
    print("   pausa = ConfigMision.get_pausa_waypoint()")