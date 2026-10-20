"""
Módulo del Algoritmo de Dijkstra y Modelo de Grafos de Rutas Urbanas.
Implementación académica rigurosa utilizando Colas de Prioridad (Min-Heap).
"""
import math
import heapq
from typing import Dict, List, Tuple, Optional, Any


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcula la distancia geodésica (Haversine) entre dos coordenadas (en km).
    """
    R = 6371.0  # Radio de la Tierra en kilómetros
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def urban_road_distance_km(lat1: float, lon1: float, lat2: float, lon2: float, detour_factor: float = 1.28) -> float:
    """
    Aproxima la distancia de red vial urbana aplicando el factor de tortuosidad/desvío (circuity factor)
    típico de trazados urbanos en cuadrícula y diagonales (1.25 a 1.35).
    """
    direct = haversine_distance_km(lat1, lon1, lat2, lon2)
    return round(direct * detour_factor, 3)


class Graph:
    """
    Representación de un Grafo Ponderado no dirigido / dirigido para la red de transporte.
    Vértices: Puntos de entrega (paquetes) y Centros de distribución (Depots).
    Aristas: Conexiones viales con peso (distancia en km o tiempo en minutos).
    """
    def __init__(self):
        # adjacency list: { node_id: [ (neighbor_id, weight, edge_info) ] }
        self.adj: Dict[str, List[Tuple[str, float, Dict[str, Any]]]] = {}
        # metadata de los nodos: { node_id: { "lat": float, "lng": float, "label": str, ... } }
        self.nodes: Dict[str, Dict[str, Any]] = {}

    def add_node(self, node_id: str, lat: float, lng: float, label: str = "", metadata: Optional[Dict[str, Any]] = None):
        if node_id not in self.adj:
            self.adj[node_id] = []
        info = {
            "id": node_id,
            "lat": lat,
            "lng": lng,
            "label": label or node_id
        }
        if metadata:
            info.update(metadata)
        self.nodes[node_id] = info

    def add_edge(self, u: str, v: str, weight: float, bidirectional: bool = True, attributes: Optional[Dict[str, Any]] = None):
        if u not in self.adj:
            self.adj[u] = []
        if v not in self.adj:
            self.adj[v] = []

        attrs = attributes or {}
        self.adj[u].append((v, weight, attrs))
        if bidirectional:
            self.adj[v].append((u, weight, attrs))

    def dijkstra_shortest_path(self, start_node: str, end_node: Optional[str] = None) -> Tuple[Dict[str, float], Dict[str, Optional[str]]]:
        """
        Algoritmo clásico de Dijkstra para encontrar los caminos más cortos desde start_node.
        Complejidad temporal: O((V + E) * log(V)) usando min-heap.
        
        Retorna:
          - dist: Diccionario de distancias mínimas {node_id: distancia_minima}
          - prev: Diccionario de predecesores para reconstruir la ruta {node_id: predecessor_id}
        """
        if start_node not in self.nodes:
            raise ValueError(f"El nodo origen '{start_node}' no existe en el grafo.")

        # Inicialización de distancias infinitas
        dist: Dict[str, float] = {node: float('inf') for node in self.nodes}
        prev: Dict[str, Optional[str]] = {node: None for node in self.nodes}
        dist[start_node] = 0.0

        # Min-Heap con tuplas (distancia_acumulada, node_id)
        pq: List[Tuple[float, str]] = [(0.0, start_node)]
        visited = set()

        while pq:
            d_u, u = heapq.heappop(pq)

            if u in visited:
                continue
            visited.add(u)

            # Si solo buscamos un destino particular y ya lo alcanzamos de manera óptima:
            if end_node and u == end_node:
                break

            # Relajación de aristas adyacentes: (u -> v con peso w)
            for v, weight, _ in self.adj.get(u, []):
                if v in visited:
                    continue
                new_dist = d_u + weight
                if new_dist < dist[v]:
                    dist[v] = new_dist
                    prev[v] = u
                    heapq.heappush(pq, (new_dist, v))

        return dist, prev

    def reconstruct_path(self, prev: Dict[str, Optional[str]], start_node: str, end_node: str) -> List[str]:
        """
        Reconstruye la secuencia de nodos en el camino mínimo desde start_node hasta end_node.
        """
        path = []
        curr: Optional[str] = end_node
        while curr is not None:
            path.append(curr)
            if curr == start_node:
                break
            curr = prev.get(curr)

        path.reverse()
        if path and path[0] == start_node:
            return path
        return []  # No hay camino alcanzable

    def build_complete_subgraph_distances(self, node_ids: List[str]) -> Dict[Tuple[str, str], float]:
        """
        Construye una matriz de distancias mínimas para un subconjunto de nodos
        utilizando Dijkstra (o distancias viales urbanas calibradas).
        """
        matrix: Dict[Tuple[str, str], float] = {}
        for i, u in enumerate(node_ids):
            # Calculamos las distancias desde u hacia los demás nodos
            u_info = self.nodes[u]
            for j, v in enumerate(node_ids):
                if u == v:
                    matrix[(u, v)] = 0.0
                elif (v, u) in matrix:
                    matrix[(u, v)] = matrix[(v, u)]
                else:
                    v_info = self.nodes[v]
                    # Distancia de red vial urbana
                    d = urban_road_distance_km(u_info["lat"], u_info["lng"], v_info["lat"], v_info["lng"])
                    matrix[(u, v)] = d
                    matrix[(v, u)] = d
        return matrix
