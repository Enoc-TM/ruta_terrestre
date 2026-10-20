"""
Gestor de Flota de Transporte Heterogénea.
Configura vehículos con sus límites de carga, cubicaje, dimensiones 3D y restricciones operativas.
Permite configurar N turbos, N vans y N motos.
"""
from typing import List
from .models import Vehicle


# Paleta de colores distintivos para las rutas de los vehículos
COLORES_VEHICULOS = [
    "#2563EB",  # Azul eléctrico
    "#DC2626",  # Rojo carmesí
    "#16A34A",  # Verde esmeralda
    "#9333EA",  # Púrpura intenso
    "#EA580C",  # Naranja ámbar
    "#0891B2",  # Cyan oscuro
    "#D97706",  # Amarillo ocre
    "#BE185D",  # Magenta / Rosa oscuro
    "#4F46E5",  # Índigo
    "#059669",  # Verde azulado
    "#B91C1C",  # Rojo ladrillo
    "#7C3AED",  # Violeta
    "#C2410C",  # Óxido
    "#0284C7",  # Celeste
    "#475569"   # Gris pizarra
]


def create_default_fleet(num_turbos: int = 3, num_vans: int = 8, num_motos: int = 4) -> List[Vehicle]:
    """
    Crea la flota inicial parametrizada según el enunciado:
    - Turbos (3): Camiones de 3.5 Toneladas (3,500 kg, 18.9 m³) para cargas pesadas y electrodomésticos.
    - Vans (8): Furgones de 850 kg (5.2 m³) para paquetería mediana y estándar urbana.
    - Motos (4): Motocicletas ágiles de 35 kg (0.064 m³) para sobres y paquetes ultraligeros (<= 8 kg).
    """
    fleet: List[Vehicle] = []
    color_idx = 0

    # 1. Crear Camiones Turbos
    for i in range(1, num_turbos + 1):
        v = Vehicle(
            id=f"TRB-{i:02d}",
            nombre=f"Camión Turbo {i}",
            tipo="turbo",
            placa=f"TRB-{500 + i}",
            capacidad_peso_kg=3500.0,
            compartimiento_alto_cm=200.0,
            compartimiento_ancho_cm=210.0,
            compartimiento_profundidad_cm=450.0,
            capacidad_volumen_m3=18.9,
            peso_max_paquete_individual_kg=500.0,
            tipos_permitidos=["sobre", "caja_pequena", "caja_mediana", "caja_grande", "electrodomestico"],
            hora_salida="08:00 AM",
            color_hex=COLORES_VEHICULOS[color_idx % len(COLORES_VEHICULOS)]
        )
        fleet.append(v)
        color_idx += 1

    # 2. Crear Furgonetas Vans
    for i in range(1, num_vans + 1):
        v = Vehicle(
            id=f"VAN-{i:02d}",
            nombre=f"Camioneta Van {i}",
            tipo="van",
            placa=f"VAN-{200 + i}",
            capacidad_peso_kg=850.0,
            compartimiento_alto_cm=145.0,
            compartimiento_ancho_cm=150.0,
            compartimiento_profundidad_cm=240.0,
            capacidad_volumen_m3=5.2,
            peso_max_paquete_individual_kg=60.0,
            tipos_permitidos=["sobre", "caja_pequena", "caja_mediana", "caja_grande"],
            hora_salida="08:15 AM",
            color_hex=COLORES_VEHICULOS[color_idx % len(COLORES_VEHICULOS)]
        )
        fleet.append(v)
        color_idx += 1

    # 3. Crear Motos de Reparto
    for i in range(1, num_motos + 1):
        v = Vehicle(
            id=f"MOT-{i:02d}",
            nombre=f"Moto de Reparto {i}",
            tipo="moto",
            placa=f"MOT-{10 + i}X",
            capacidad_peso_kg=35.0,
            compartimiento_alto_cm=40.0,
            compartimiento_ancho_cm=40.0,
            compartimiento_profundidad_cm=40.0,
            capacidad_volumen_m3=0.064,  # Baúl estándar de 64 litros
            peso_max_paquete_individual_kg=8.0,
            tipos_permitidos=["sobre", "caja_pequena"],
            hora_salida="08:30 AM",
            color_hex=COLORES_VEHICULOS[color_idx % len(COLORES_VEHICULOS)]
        )
        fleet.append(v)
        color_idx += 1

    return fleet
