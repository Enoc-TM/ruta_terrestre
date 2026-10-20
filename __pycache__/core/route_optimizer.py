"""
Módulo de Optimización de Rutas de Entrega utilizando Grafos, Dijkstra y 2-Opt (TSP).
Genera la secuencia óptima de paradas minimizando la distancia y el tiempo total.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from .models import Vehicle, Package, Depot
from .dijkstra import Graph, urban_road_distance_km


def two_opt_swap(route: List[str], i: int, k: int) -> List[str]:
    """
    Invierte la sub-ruta entre los índices i y k para eliminar cruces.
    """
    new_route = route[:i] + route[i:k + 1][::-1] + route[k + 1:]
    return new_route


def calculate_tour_distance(route: List[str], dist_matrix: Dict[Tuple[str, str], float]) -> float:
    """
    Calcula la distancia total de una ruta circular (depot -> paradas -> depot).
    """
    total = 0.0
    for idx in range(len(route) - 1):
        u, v = route[idx], route[idx + 1]
        total += dist_matrix.get((u, v), 0.0)
    return total


class RouteOptimizer:
    """
    Optimizador de rutas urbanas para cada vehículo de la flota.
    """

    @classmethod
    def optimize_vehicle_route(
        cls,
        vehicle: Vehicle,
        depot: Depot,
        urban_speed_kmh: float = 28.0
    ) -> Vehicle:
        """
        Optimiza la secuencia de paradas de un vehículo:
        1. Construye el grafo vial entre el Depósito y los paquetes asignados.
        2. Aplica Dijkstra para generar la matriz de distancias mínimas.
        3. Construye un circuito inicial con Nearest Neighbor (Vecino más cercano).
        4. Mejora el circuito aplicando 2-Opt local search hasta convergencia.
        5. Calcula tiempos estimados de llegada (ETA) y distancia total.
        """
        packages = vehicle.paquetes_asignados
        if not packages:
            vehicle.distancia_total_km = 0.0
            vehicle.tiempo_estimado_min = 0.0
            vehicle.paradas = []
            return vehicle

        # 1. Construir el Grafo
        graph = Graph()
        # Nodo depósito
        graph.add_node(
            depot.id,
            lat=depot.latitud,
            lng=depot.longitud,
            label=depot.nombre,
            metadata={"tipo": "deposito"}
        )

        # Nodos de paquetes
        pkg_map: Dict[str, Package] = {}
        for p in packages:
            pkg_map[p.id] = p
            graph.add_node(
                p.id,
                lat=p.latitud,
                lng=p.longitud,
                label=f"{p.id} - {p.barrio}",
                metadata={"tipo": "entrega", "paquete": p.to_dict()}
            )

        all_nodes = [depot.id] + [p.id for p in packages]

        # 2. Matriz de distancias viales usando la red urbana y Dijkstra
        dist_matrix = graph.build_complete_subgraph_distances(all_nodes)

        # 3. Construcción de ruta inicial mediante Heurística del Vecino Más Cercano (Nearest Neighbor)
        unvisited = set(p.id for p in packages)
        current = depot.id
        ordered_route = [depot.id]

        while unvisited:
            next_node = min(unvisited, key=lambda node: dist_matrix.get((current, node), float('inf')))
            ordered_route.append(next_node)
            unvisited.remove(next_node)
            current = next_node

        # Retorno al depósito (circuito cerrado)
        ordered_route.append(depot.id)

        # 4. Optimización con 2-Opt para desenredar cualquier cruce en el plano vial
        improved = True
        best_distance = calculate_tour_distance(ordered_route, dist_matrix)

        max_iterations = 50
        iteration = 0
        while improved and iteration < max_iterations:
            improved = False
            iteration += 1
            for i in range(1, len(ordered_route) - 2):
                for k in range(i + 1, len(ordered_route) - 1):
                    new_route = two_opt_swap(ordered_route, i, k)
                    new_dist = calculate_tour_distance(new_route, dist_matrix)
                    if new_dist < (best_distance - 0.001):
                        ordered_route = new_route
                        best_distance = new_dist
                        improved = True
                        break
                if improved:
                    break

        # 5. Generación de paradas detalladas y cronograma con tiempos de entrega (ETA)
        vehicle.distancia_total_km = round(best_distance, 2)

        # Ajuste de velocidad según tipo de vehículo en la ciudad
        speed_factor = 1.0
        if vehicle.tipo == "moto":
            speed_factor = 1.15  # Las motos circulan más rápido en tráfico urbano
        elif vehicle.tipo == "turbo":
            speed_factor = 0.85  # Los camiones turbos tienen menor velocidad media y maniobrabilidad

        effective_speed = urban_speed_kmh * speed_factor

        # Parsear hora de salida del vehículo (e.g. "08:00 AM")
        try:
            current_time = datetime.strptime(vehicle.hora_salida, "%I:%M %p")
        except Exception:
            current_time = datetime.strptime("08:00 AM", "%I:%M %p")

        paradas_info = []
        cumulative_dist = 0.0

        for idx, node_id in enumerate(ordered_route):
            node_data = graph.nodes[node_id]

            # Calcular tiempo de traslado desde la parada anterior
            if idx > 0:
                prev_node_id = ordered_route[idx - 1]
                leg_dist = dist_matrix.get((prev_node_id, node_id), 0.0)
                cumulative_dist += leg_dist
                # Tiempo de viaje en minutos: (distancia / velocidad) * 60
                travel_minutes = (leg_dist / effective_speed) * 60.0
                current_time += timedelta(minutes=travel_minutes)
            else:
                leg_dist = 0.0

            if node_id == depot.id:
                if idx == 0:
                    paradas_info.append({
                        "orden": 0,
                        "tipo": "deposito_salida",
                        "nodo_id": node_id,
                        "nombre": depot.nombre,
                        "direccion": depot.direccion,
                        "latitud": depot.latitud,
                        "longitud": depot.longitud,
                        "hora_estimada": current_time.strftime("%I:%M %p"),
                        "distancia_tramo_km": 0.0,
                        "distancia_acumulada_km": 0.0,
                        "paquete": None
                    })
                else:
                    paradas_info.append({
                        "orden": idx,
                        "tipo": "deposito_retorno",
                        "nodo_id": node_id,
                        "nombre": f"Retorno a {depot.nombre}",
                        "direccion": depot.direccion,
                        "latitud": depot.latitud,
                        "longitud": depot.longitud,
                        "hora_estimada": current_time.strftime("%I:%M %p"),
                        "distancia_tramo_km": round(leg_dist, 2),
                        "distancia_acumulada_km": round(cumulative_dist, 2),
                        "paquete": None
                    })
            else:
                # Es un paquete de entrega
                pkg = pkg_map[node_id]
                pkg.orden_entrega = idx
                pkg.hora_estimada_entrega = current_time.strftime("%I:%M %p")

                # Tiempo de servicio en la entrega (descarga, firma de guía)
                service_time_min = 4.0 if pkg.tipo in ["sobre", "caja_pequena"] else (10.0 if pkg.tipo == "electrodomestico" else 7.0)

                paradas_info.append({
                    "orden": idx,
                    "tipo": "entrega",
                    "nodo_id": node_id,
                    "nombre": f"Entrega #{idx}: {pkg.descripcion}",
                    "direccion": pkg.direccion,
                    "barrio": pkg.barrio,
                    "latitud": pkg.latitud,
                    "longitud": pkg.longitud,
                    "hora_estimada": current_time.strftime("%I:%M %p"),
                    "tiempo_servicio_min": service_time_min,
                    "distancia_tramo_km": round(leg_dist, 2),
                    "distancia_acumulada_km": round(cumulative_dist, 2),
                    "paquete": pkg.to_dict()
                })

                # Añadimos el tiempo de atención en el sitio
                current_time += timedelta(minutes=service_time_min)

        vehicle.paradas = paradas_info

        # Calcular tiempo total en minutos entre salida y retorno
        salida_time = datetime.strptime(vehicle.hora_salida, "%I:%M %p")
        duracion_total = (current_time - salida_time).total_seconds() / 60.0
        vehicle.tiempo_estimado_min = round(duracion_total, 1)
        vehicle.hora_retorno = current_time.strftime("%I:%M %p")

        return vehicle

    @classmethod
    def optimize_all_routes(cls, vehicles: List[Vehicle], depot: Depot) -> List[Vehicle]:
        """
        Optimiza las rutas para todos los vehículos con paquetes asignados.
        """
        for v in vehicles:
            if v.paquetes_asignados:
                cls.optimize_vehicle_route(v, depot)
            else:
                v.distancia_total_km = 0.0
                v.tiempo_estimado_min = 0.0
                v.paradas = []
        return vehicles
