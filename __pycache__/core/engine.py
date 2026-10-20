
import os
from typing import List, Dict, Any, Optional
from .models import Package, Vehicle, Depot
from .mochila import MochilaFleetOptimizer
from .route_optimizer import RouteOptimizer
from .fleet_manager import create_default_fleet
from .dataset_generator import (
    load_packages_from_csv,
    generate_package_dataset,
    save_packages_to_csv,
    export_route_results_to_csv
)


class LogisticsEngine:
    def __init__(self, num_turbos: int = 3, num_vans: int = 8, num_motos: int = 4):
        self.depot = Depot()
        self.vehicles: List[Vehicle] = create_default_fleet(
            num_turbos=num_turbos,
            num_vans=num_vans,
            num_motos=num_motos
        )
        self.packages: List[Package] = []
        self.unassigned_packages: List[Package] = []
        self.last_summary: Dict[str, Any] = {}
        self.is_optimized = False

        # Cargar dataset de 200 paquetes por defecto (Ibagué)
        csv_200 = os.path.join(os.path.dirname(__file__), "..", "data", "paquetes_ibague_200.csv")
        csv_fallback = os.path.join(os.path.dirname(__file__), "..", "data", "paquetes_bogota_200.csv")
        if os.path.exists(csv_200):
            self.load_from_csv(csv_200)
        elif os.path.exists(csv_fallback):
            self.load_from_csv(csv_fallback)
        else:
            # Si no existe, generarlo automáticamente con 200 paquetes en Ibagué
            self.packages = generate_package_dataset(200, seed=42)
            os.makedirs(os.path.dirname(csv_200), exist_ok=True)
            save_packages_to_csv(self.packages, csv_200)

    def configure_fleet(self, num_turbos: int, num_vans: int, num_motos: int):
        """
        Reconfigura la flota disponible (cantidad de turbos, vans y motos).
        """
        self.vehicles = create_default_fleet(num_turbos, num_vans, num_motos)
        self.is_optimized = False

    def load_from_csv(self, filepath: str):
        """
        Carga paquetes desde un archivo CSV con las columnas estándar.
        """
        self.packages = load_packages_from_csv(filepath)
        self.is_optimized = False

    def generate_and_load_dataset(self, count: int = 200, filepath: Optional[str] = None):
        """
        Genera un nuevo dataset de N paquetes y opcionalmente lo guarda en CSV.
        """
        self.packages = generate_package_dataset(count, seed=42)
        if filepath:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            save_packages_to_csv(self.packages, filepath)
        self.is_optimized = False

    def run_optimization(self) -> Dict[str, Any]:
        """
        Ejecuta el pipeline completo de optimización logística:
        - FASE 1: Algoritmo de la Mochila con RECURSIVIDAD (Asignación y Cubicaje 3D).
        - FASE 2: Modelado en Grafo Vial, Dijkstra y Secuenciación Óptima de Paradas (TSP / 2-Opt).
        - FASE 3: Cronograma de entrega (Hora de salida y Hora de llegada por parada).
        """
        if not self.packages:
            return {"error": "No hay paquetes cargados para optimizar."}

        # FASE 1: Algoritmo de la Mochila con Recursividad
        self.vehicles, self.unassigned_packages, packing_summary = MochilaFleetOptimizer.asignar_carga_flota(
            self.packages,
            self.vehicles,
            self.depot
        )

        # FASE 2: Ruteo con Grafo Vial, Dijkstra y TSP (2-Opt)
        self.vehicles = RouteOptimizer.optimize_all_routes(self.vehicles, self.depot)

        # Cálculo de métricas globales
        total_km = round(sum(v.distancia_total_km for v in self.vehicles), 2)
        total_tiempo_horas = round(sum(v.tiempo_estimado_min for v in self.vehicles) / 60.0, 1)
        vehiculos_activos = [v for v in self.vehicles if len(v.paquetes_asignados) > 0]

        # Estimación de ahorro comparado con ruteo sin optimización (~30% de ahorro)
        km_sin_opt = round(total_km * 1.34, 1)
        km_ahorrados = round(km_sin_opt - total_km, 1)
        ahorro_combustible_litros = round(km_ahorrados * 0.12, 1)
        co2_evitado_kg = round(ahorro_combustible_litros * 2.31, 1)

        self.last_summary = {
            "depot": self.depot.to_dict(),
            "metricas_generales": {
                "total_paquetes": len(self.packages),
                "paquetes_entregados": packing_summary["total_asignados"],
                "paquetes_pendientes": packing_summary["total_no_asignados"],
                "porcentaje_efectividad": round((packing_summary["total_asignados"] / len(self.packages)) * 100, 1),
                "vehiculos_totales": len(self.vehicles),
                "vehiculos_activos": len(vehiculos_activos),
                "distancia_total_flota_km": total_km,
                "tiempo_total_flota_horas": total_tiempo_horas,
                "km_ahorrados_estimados": km_ahorrados,
                "combustible_ahorrado_galones": round(ahorro_combustible_litros / 3.785, 1),
                "co2_evitado_kg": co2_evitado_kg
            },
            "packing_summary": packing_summary,
            "vehiculos": [v.to_dict() for v in self.vehicles],
            "paquetes_no_asignados": [p.to_dict() for p in self.unassigned_packages]
        }

        self.is_optimized = True
        return self.last_summary

    def export_results_to_csv(self, filepath: str):
        """
        Exporta las rutas optimizadas y cronograma de paradas a un archivo CSV.
        """
        export_route_results_to_csv(self.vehicles, self.unassigned_packages, filepath)
