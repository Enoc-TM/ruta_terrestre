"""
Generador de Datasets de Paquetes y Exportador/Importador CSV.
Genera datos de entrega para Ibagué (Tolima) con las columnas requeridas:
Peso, Altura, Ancho, Profundidad, Tipo, Latitud, Longitud, Hora de salida y llegada.
"""
import csv
import random
from typing import List
from .models import Package


# Catálogo representativo de mercancías reales del sector logístico
CATALOGO_PRODUCTOS = [
    # 1. Sobres y Documentos (Ultraligeros)
    {"desc": "Sobre Documentos Notariales", "tipo": "sobre", "peso": (0.1, 0.4), "alto": (1, 3), "ancho": (18, 24), "profundidad": (25, 32)},
    {"desc": "Tarjeta de Crédito y Token", "tipo": "sobre", "peso": (0.05, 0.2), "alto": (1, 2), "ancho": (10, 15), "profundidad": (15, 20)},
    {"desc": "Contrato Comercial y Póliza", "tipo": "sobre", "peso": (0.2, 0.5), "alto": (1, 4), "ancho": (20, 25), "profundidad": (28, 35)},
    
    # 2. Cajas Pequeñas (Paquetería urbana ligera)
    {"desc": "Smartphone y Funda Protectora", "tipo": "caja_pequena", "peso": (0.4, 0.9), "alto": (6, 10), "ancho": (12, 16), "profundidad": (18, 22)},
    {"desc": "Set de Cosméticos y Perfumería", "tipo": "caja_pequena", "peso": (0.8, 1.8), "alto": (10, 15), "ancho": (16, 22), "profundidad": (22, 28)},
    {"desc": "Auriculares Bluetooth Noise Cancelling", "tipo": "caja_pequena", "peso": (0.5, 1.2), "alto": (8, 12), "ancho": (15, 20), "profundidad": (20, 25)},
    {"desc": "Medicamentos y Vitaminas", "tipo": "caja_pequena", "peso": (0.3, 1.0), "alto": (8, 14), "ancho": (12, 18), "profundidad": (16, 22)},
    
    # 3. Cajas Medianas (Mercancía estándar para Vans)
    {"desc": "Zapatos Deportivos y Ropa", "tipo": "caja_mediana", "peso": (2.0, 4.5), "alto": (15, 22), "ancho": (25, 32), "profundidad": (35, 42)},
    {"desc": "Freidora de Aire Digital 5L", "tipo": "caja_mediana", "peso": (4.5, 7.5), "alto": (32, 40), "ancho": (30, 38), "profundidad": (32, 40)},
    {"desc": "Cafetera Espresso y Pocillos", "tipo": "caja_mediana", "peso": (3.5, 6.0), "alto": (28, 36), "ancho": (24, 30), "profundidad": (30, 38)},
    {"desc": "Impresora Multifuncional WiFi", "tipo": "caja_mediana", "peso": (6.0, 10.5), "alto": (22, 30), "ancho": (35, 42), "profundidad": (42, 50)},
    
    # 4. Cajas Grandes (Paquetería voluminosa para Vans y Turbos)
    {"desc": "Monitor Gamer Curvo 34 Pulgadas", "tipo": "caja_grande", "peso": (9.0, 15.0), "alto": (48, 56), "ancho": (22, 30), "profundidad": (85, 95)},
    {"desc": "Vajilla Completa 24 Piezas Porcelana", "tipo": "caja_grande", "peso": (12.0, 18.0), "alto": (35, 45), "ancho": (40, 50), "profundidad": (50, 60)},
    {"desc": "Juego de Herramientas Eléctricas", "tipo": "caja_grande", "peso": (14.0, 24.0), "alto": (30, 40), "ancho": (38, 48), "profundidad": (55, 65)},
    
    # 5. Electrodomésticos y Carga Pesada (EXCLUSIVO para Camiones Turbos)
    {"desc": "Nevera No Frost 380 Litros Inox", "tipo": "electrodomestico", "peso": (65.0, 85.0), "alto": (175, 188), "ancho": (65, 72), "profundidad": (68, 75)},
    {"desc": "Lavadora Carga Frontal 19 Kg", "tipo": "electrodomestico", "peso": (70.0, 82.0), "alto": (98, 108), "ancho": (66, 72), "profundidad": (68, 74)},
    {"desc": "Televisor Smart TV OLED 65 Pulgadas", "tipo": "electrodomestico", "peso": (26.0, 36.0), "alto": (95, 105), "ancho": (18, 26), "profundidad": (155, 165)},
    {"desc": "Estufa de Gas 4 Puestos con Horno", "tipo": "electrodomestico", "peso": (42.0, 55.0), "alto": (90, 98), "ancho": (58, 65), "profundidad": (58, 65)}
]

# Zonas geográficas reales de Ibagué (Tolima) con coordenadas delimitadas
ZONAS_IBAGUE = [
    {"barrio": "Centro / La Pola", "lat_range": (4.4370, 4.4460), "lng_range": (-75.2410, -75.2310), "calle_base": "Carrera 3"},
    {"barrio": "Belén / Calambeo", "lat_range": (4.4430, 4.4530), "lng_range": (-75.2480, -75.2360), "calle_base": "Calle 10"},
    {"barrio": "Cádiz / San Simón", "lat_range": (4.4320, 4.4410), "lng_range": (-75.2280, -75.2180), "calle_base": "Carrera 5"},
    {"barrio": "Piedra Pintada / Santa Helena", "lat_range": (4.4280, 4.4380), "lng_range": (-75.2130, -75.2020), "calle_base": "Calle 60"},
    {"barrio": "La Macarena / Arkacentro", "lat_range": (4.4330, 4.4430), "lng_range": (-75.2160, -75.2050), "calle_base": "Av. Guabinal"},
    {"barrio": "El Jordán (Etapas 1 a 9)", "lat_range": (4.4220, 4.4350), "lng_range": (-75.1980, -75.1820), "calle_base": "Av. Ferrocarril"},
    {"barrio": "Santa Ana / El Salado", "lat_range": (4.4530, 4.4720), "lng_range": (-75.1680, -75.1480), "calle_base": "Av. Ambalá"},
    {"barrio": "El Vergel / Ambalá Norte", "lat_range": (4.4460, 4.4620), "lng_range": (-75.2080, -75.1910), "calle_base": "Calle 80"},
    {"barrio": "Picaleña / Zona Industrial El Papayo", "lat_range": (4.4080, 4.4260), "lng_range": (-75.1920, -75.1680), "calle_base": "Av. Mirolindo"},
    {"barrio": "El Refugio / Ricaurte", "lat_range": (4.4120, 4.4270), "lng_range": (-75.2350, -75.2180), "calle_base": "Calle 25 Sur"}
]
ZONAS_BOGOTA = ZONAS_IBAGUE  # Alias de compatibilidad


def generate_package_dataset(num_packages: int = 200, seed: int = 42) -> List[Package]:
    """
    Genera un listado de N paquetes con variedad controlada de dimensiones físicas 3D,
    pesos, tipos de carga, coordenadas en Ibagué y horarios.
    """
    random.seed(seed)
    packages: List[Package] = []

    for i in range(1, num_packages + 1):
        pkg_id = f"PKG-{i:03d}"
        template = random.choice(CATALOGO_PRODUCTOS)
        zona = random.choice(ZONAS_IBAGUE)

        peso = round(random.uniform(*template["peso"]), 2)
        alto = round(random.uniform(*template["alto"]), 1)
        ancho = round(random.uniform(*template["ancho"]), 1)
        profundidad = round(random.uniform(*template["profundidad"]), 1)

        lat = round(random.uniform(*zona["lat_range"]), 6)
        lng = round(random.uniform(*zona["lng_range"]), 6)

        num_cruce = random.randint(1, 99)
        num_puerta = random.randint(2, 80)
        direccion = f"{zona['calle_base']} #{num_cruce}-{num_puerta}"

        prioridad = random.choices(["normal", "alta", "urgente"], weights=[0.75, 0.20, 0.05])[0]

        pkg = Package(
            id=pkg_id,
            descripcion=template["desc"],
            tipo=template["tipo"],
            peso_kg=peso,
            alto_cm=alto,
            ancho_cm=ancho,
            profundidad_cm=profundidad,
            latitud=lat,
            longitud=lng,
            hora_salida="08:00 AM",
            hora_llegada="Pendiente",
            direccion=direccion,
            barrio=zona["barrio"],
            prioridad=prioridad
        )
        packages.append(pkg)

    return packages


def save_packages_to_csv(packages: List[Package], filepath: str):
    """
    Exporta la lista de paquetes al formato CSV exacto con las columnas solicitadas:
    id_paquete, descripcion, tipo, peso_kg, alto_cm, ancho_cm, profundidad_cm,
    volumen_m3, latitud, longitud, direccion, barrio, hora_salida, hora_llegada, prioridad
    """
    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "id_paquete",
            "descripcion",
            "tipo",
            "peso_kg",
            "alto_cm",
            "ancho_cm",
            "profundidad_cm",
            "volumen_m3",
            "latitud",
            "longitud",
            "direccion",
            "barrio",
            "hora_salida",
            "hora_llegada",
            "prioridad"
        ])
        for p in packages:
            writer.writerow([
                p.id,
                p.descripcion,
                p.tipo,
                p.peso_kg,
                p.alto_cm,
                p.ancho_cm,
                p.profundidad_cm,
                p.volumen_m3,
                p.latitud,
                p.longitud,
                p.direccion,
                p.barrio,
                p.hora_salida,
                p.hora_llegada,
                p.prioridad
            ])


def load_packages_from_csv(filepath: str) -> List[Package]:
    """
    Carga paquetes desde un archivo CSV con soporte para nombres de columnas
    nuevos y anteriores (compatibilidad).
    """
    packages: List[Package] = []
    with open(filepath, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Compatibilidad entre profundidad_cm y largo_cm
            profundidad = float(row.get("profundidad_cm") or row.get("largo_cm") or 20.0)
            alto = float(row.get("alto_cm") or 15.0)
            ancho = float(row.get("ancho_cm") or 15.0)
            volumen = float(row.get("volumen_m3") or 0.0)

            pkg = Package(
                id=row["id_paquete"],
                descripcion=row.get("descripcion", "Paquete"),
                tipo=row.get("tipo", "caja_pequena").strip().lower(),
                peso_kg=float(row["peso_kg"]),
                alto_cm=alto,
                ancho_cm=ancho,
                profundidad_cm=profundidad,
                volumen_m3=volumen,
                latitud=float(row["latitud"]),
                longitud=float(row["longitud"]),
                hora_salida=row.get("hora_salida", "08:00 AM"),
                hora_llegada=row.get("hora_llegada", "Pendiente"),
                direccion=row.get("direccion", "Dirección Urbana"),
                barrio=row.get("barrio", "Sector Urbano"),
                prioridad=row.get("prioridad", "normal")
            )
            packages.append(pkg)
    return packages


def export_route_results_to_csv(vehicles: List[Vehicle], unassigned: List[Package], filepath: str):
    """
    Exporta el resultado final optimizado de las rutas a un archivo CSV.
    Permite visualizar qué vehículo transporta cada paquete, su orden de entrega,
    la hora exacta de salida y la hora exacta de llegada/entrega.
    """
    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "id_paquete",
            "vehiculo_asignado",
            "tipo_vehiculo",
            "placa_vehiculo",
            "orden_entrega",
            "descripcion",
            "tipo",
            "peso_kg",
            "alto_cm",
            "ancho_cm",
            "profundidad_cm",
            "volumen_m3",
            "direccion",
            "barrio",
            "latitud",
            "longitud",
            "hora_salida",
            "hora_llegada",
            "estado"
        ])

        # Paquetes asignados y enrutados
        for v in vehicles:
            for p in v.paquetes_asignados:
                writer.writerow([
                    p.id,
                    v.nombre,
                    v.tipo,
                    v.placa,
                    p.orden_entrega or 0,
                    p.descripcion,
                    p.tipo,
                    p.peso_kg,
                    p.alto_cm,
                    p.ancho_cm,
                    p.profundidad_cm,
                    p.volumen_m3,
                    p.direccion,
                    p.barrio,
                    p.latitud,
                    p.longitud,
                    p.hora_salida,
                    p.hora_llegada,
                    "Asignado y Enrutado"
                ])

        # Paquetes pendientes / no asignados
        for p in unassigned:
            writer.writerow([
                p.id,
                "Sin Vehículo",
                "N/A",
                "N/A",
                0,
                p.descripcion,
                p.tipo,
                p.peso_kg,
                p.alto_cm,
                p.ancho_cm,
                p.profundidad_cm,
                p.volumen_m3,
                p.direccion,
                p.barrio,
                p.latitud,
                p.longitud,
                p.hora_salida,
                "No Asignado",
                "Pendiente por Capacidad de Flota"
            ])
