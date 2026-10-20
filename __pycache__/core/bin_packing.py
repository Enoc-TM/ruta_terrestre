
from typing import List, Tuple, Dict, Any
from .models import Package, Vehicle, Depot
from .mochila import MochilaFleetOptimizer, mochila_recursiva


class PackingOptimizer:
    """
    Optimizador de empaquetamiento que conecta la lógica de asignación con el
    Algoritmo de la Mochila 0/1 Multidimensional Recursivo.
    """

    @classmethod
    def assign_packages_to_fleet(
        cls,
        packages: List[Package],
        vehicles: List[Vehicle],
        depot: Depot
    ) -> Tuple[List[Vehicle], List[Package], Dict[str, Any]]:
        """
        Asigna paquetes a la flota mediante Mochila Recursiva respetando:
        1. Dimensiones físicas 3D (Alto, Ancho, Profundidad)
        2. Tipo de carga admisible (Neveras exclusivamente en Turbos, nunca en motos)
        3. Capacidad de peso máximo (kg)
        4. Capacidad de volumen máximo (m³) con 90% factor estiba
        """
        return MochilaFleetOptimizer.asignar_carga_flota(packages, vehicles, depot)
