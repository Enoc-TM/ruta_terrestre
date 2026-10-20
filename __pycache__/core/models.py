"""
Modelos de datos para el sistema de optimización de carga y rutas de transporte.
Estructuras para Paquetes, Vehículos y Depósito Central.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class Package:
    id: str                                  # Identificador único (ej: PKG-001)
    descripcion: str                         # Descripción del contenido
    tipo: str                                # 'sobre', 'caja_pequena', 'caja_mediana', 'caja_grande', 'electrodomestico'
    peso_kg: float                           # Peso en kilogramos
    alto_cm: float                           # Altura en cm
    ancho_cm: float                          # Ancho en cm
    profundidad_cm: float                    # Profundidad (o largo) en cm
    latitud: float                           # Coordenada geográfica (Latitud)
    longitud: float                          # Coordenada geográfica (Longitud)
    hora_salida: str = "08:00 AM"            # Hora de salida de la flota
    hora_llegada: str = "Pendiente"          # Hora de llegada / entrega calculada
    direccion: str = ""                      # Dirección urbana
    barrio: str = ""                         # Barrio o zona de entrega
    prioridad: str = "normal"                # 'baja', 'normal', 'alta', 'urgente'
    volumen_m3: float = 0.0                  # Volumen calculado en m³
    vehiculo_asignado: Optional[str] = None  # ID del vehículo asignado
    orden_entrega: Optional[int] = None      # Número de parada en la ruta

    @property
    def largo_cm(self) -> float:
        """Alias para profundidad_cm según terminología de transporte."""
        return self.profundidad_cm

    @largo_cm.setter
    def largo_cm(self, valor: float):
        self.profundidad_cm = valor

    @property
    def hora_estimada_entrega(self) -> str:
        """Alias para hora_llegada."""
        return self.hora_llegada

    @hora_estimada_entrega.setter
    def hora_estimada_entrega(self, valor: str):
        self.hora_llegada = valor

    def __post_init__(self):
        if self.volumen_m3 <= 0:
            # Volumen en m³: (alto * ancho * profundidad en cm) / 1,000,000
            self.volumen_m3 = round((self.alto_cm * self.ancho_cm * self.profundidad_cm) / 1_000_000.0, 4)

    def puede_caber_en(self, v_profundidad: float, v_ancho: float, v_alto: float, peso_max_indiv: float) -> bool:
        """
        Verifica si las dimensiones físicas 3D (Alto, Ancho, Profundidad) y el peso individual
        del paquete caben físicamente en el compartimiento de carga (considerando rotaciones).
        """
        if self.peso_kg > peso_max_indiv:
            return False

        # Dimensiones del paquete ordenadas de menor a mayor
        pkg_dims = sorted([self.alto_cm, self.ancho_cm, self.profundidad_cm])
        # Dimensiones del compartimiento ordenadas de menor a mayor
        veh_dims = sorted([v_profundidad, v_ancho, v_alto])

        # Cada dimensión física debe ser menor o igual a la del compartimiento
        return all(p <= v for p, v in zip(pkg_dims, veh_dims))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id_paquete": self.id,
            "descripcion": self.descripcion,
            "tipo": self.tipo,
            "peso_kg": self.peso_kg,
            "alto_cm": self.alto_cm,
            "ancho_cm": self.ancho_cm,
            "profundidad_cm": self.profundidad_cm,
            "volumen_m3": self.volumen_m3,
            "latitud": self.latitud,
            "longitud": self.longitud,
            "direccion": self.direccion,
            "barrio": self.barrio,
            "hora_salida": self.hora_salida,
            "hora_llegada": self.hora_llegada,
            "prioridad": self.prioridad,
            "vehiculo_asignado": self.vehiculo_asignado,
            "orden_entrega": self.orden_entrega
        }


@dataclass
class Vehicle:
    id: str                                  # Identificador único (ej: TRB-01, VAN-01, MOT-01)
    nombre: str                              # Nombre descriptivo (ej: Camión Turbo 1)
    tipo: str                                # 'turbo', 'van', 'moto'
    placa: str                               # Placa del vehículo
    capacidad_peso_kg: float                 # Límite máximo de carga en kg
    compartimiento_alto_cm: float            # Altura interior de carga en cm
    compartimiento_ancho_cm: float           # Ancho interior de carga en cm
    compartimiento_profundidad_cm: float     # Profundidad/Largo interior de carga en cm
    capacidad_volumen_m3: float              # Capacidad volumétrica máxima en m³
    peso_max_paquete_individual_kg: float    # Peso máximo admisible para 1 solo paquete
    tipos_permitidos: List[str]              # Lista de tipos de paquetes autorizados
    hora_salida: str = "08:00 AM"            # Hora de salida del depósito
    hora_retorno: str = ""                   # Hora de regreso estimada al depósito
    color_hex: str = "#3B82F6"               # Color distintivo para visualización
    paquetes_asignados: List[Package] = field(default_factory=list)
    peso_actual_kg: float = 0.0              # Peso acumulado cargado actualmente
    volumen_actual_m3: float = 0.0           # Volumen acumulado cargado actualmente
    distancia_total_km: float = 0.0          # Distancia total de la ruta en km
    tiempo_estimado_min: float = 0.0         # Tiempo total de viaje y servicio en minutos
    paradas: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def compartimiento_largo_cm(self) -> float:
        return self.compartimiento_profundidad_cm

    @compartimiento_largo_cm.setter
    def compartimiento_largo_cm(self, valor: float):
        self.compartimiento_profundidad_cm = valor

    @property
    def porcentaje_ocupacion_peso(self) -> float:
        if self.capacidad_peso_kg <= 0:
            return 0.0
        return round((self.peso_actual_kg / self.capacidad_peso_kg) * 100, 1)

    @property
    def porcentaje_ocupacion_volumen(self) -> float:
        if self.capacidad_volumen_m3 <= 0:
            return 0.0
        return round((self.volumen_actual_m3 / self.capacidad_volumen_m3) * 100, 1)

    def puede_recibir(self, pkg: Package) -> bool:
        """
        Valida rigurosamente todas las restricciones operacionales y físicas:
        1. Tipo de paquete permitido para este vehículo (ej: NUNCA una nevera en moto).
        2. Peso unitario y dimensiones 3D compatibles con el compartimiento.
        3. Capacidad remanente de peso en el vehículo.
        4. Capacidad remanente de volumen en el vehículo (considerando 90% factor estiba).
        """
        # Restricción 1: Tipo de mercancía admisible
        if pkg.tipo not in self.tipos_permitidos:
            return False

        # Restricción 2: Dimensiones 3D y peso individual
        if not pkg.puede_caber_en(
            self.compartimiento_profundidad_cm,
            self.compartimiento_ancho_cm,
            self.compartimiento_alto_cm,
            self.peso_max_paquete_individual_kg
        ):
            return False

        # Restricción 3: Límite de peso total
        if round(self.peso_actual_kg + pkg.peso_kg, 2) > self.capacidad_peso_kg:
            return False

        # Restricción 4: Límite de volumen total (factor de estiba 90%)
        if round(self.volumen_actual_m3 + pkg.volumen_m3, 4) > round(self.capacidad_volumen_m3 * 0.90, 4):
            return False

        return True

    def agregar_paquete(self, pkg: Package):
        """Asigna un paquete a este vehículo y actualiza sus totales."""
        self.paquetes_asignados.append(pkg)
        self.peso_actual_kg = round(self.peso_actual_kg + pkg.peso_kg, 2)
        self.volumen_actual_m3 = round(self.volumen_actual_m3 + pkg.volumen_m3, 4)
        pkg.vehiculo_asignado = self.id
        pkg.hora_salida = self.hora_salida

    def limpiar_asignaciones(self):
        """Reinicia la carga y ruta del vehículo."""
        self.paquetes_asignados.clear()
        self.peso_actual_kg = 0.0
        self.volumen_actual_m3 = 0.0
        self.distancia_total_km = 0.0
        self.tiempo_estimado_min = 0.0
        self.hora_retorno = ""
        self.paradas.clear()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "tipo": self.tipo,
            "placa": self.placa,
            "capacidad_peso_kg": self.capacidad_peso_kg,
            "capacidad_volumen_m3": self.capacidad_volumen_m3,
            "dimensiones_cm": {
                "alto": self.compartimiento_alto_cm,
                "ancho": self.compartimiento_ancho_cm,
                "profundidad": self.compartimiento_profundidad_cm
            },
            "peso_max_paquete_individual_kg": self.peso_max_paquete_individual_kg,
            "tipos_permitidos": self.tipos_permitidos,
            "hora_salida": self.hora_salida,
            "hora_retorno": self.hora_retorno,
            "total_paquetes": len(self.paquetes_asignados),
            "peso_actual_kg": self.peso_actual_kg,
            "volumen_actual_m3": self.volumen_actual_m3,
            "porcentaje_ocupacion_peso": self.porcentaje_ocupacion_peso,
            "porcentaje_ocupacion_volumen": self.porcentaje_ocupacion_volumen,
            "distancia_total_km": self.distancia_total_km,
            "tiempo_estimado_min": self.tiempo_estimado_min,
            "paquetes": [p.to_dict() for p in self.paquetes_asignados],
            "paradas": self.paradas
        }


@dataclass
class Depot:
    id: str = "DEPOT-00"
    nombre: str = "Centro de Distribución Principal (Hub Central Ibagué)"
    direccion: str = "Av. Mirolindo # 60-40, Zona Industrial El Papayo, Ibagué"
    latitud: float = 4.4250
    longitud: float = -75.2050

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "direccion": self.direccion,
            "latitud": self.latitud,
            "longitud": self.longitud
        }
