

import math
from typing import List, Tuple, Dict, Any
from .models import Package, Vehicle, Depot
from .dijkstra import haversine_distance_km


def calcular_utilidad_paquete(pkg: Package) -> float:
    """
    Función de valor/utilidad para la función objetivo de la mochila.
    Prioriza paquetes urgentes y optimiza la densidad de aprovechamiento de carga.
    """
    bonus_prioridad = 15.0 if pkg.prioridad == "urgente" else (8.0 if pkg.prioridad == "alta" else 2.0)
    # El valor combina el peso útil transportado, el volumen aprovechado y la prioridad de despacho
    return pkg.peso_kg + (pkg.volumen_m3 * 80.0) + bonus_prioridad


def mochila_recursiva(
    indice: int,
    peso_disponible: float,
    volumen_disponible: float,
    candidatos: List[Package],
    memo: Dict[Tuple[int, int, int], Tuple[float, List[int]]]
) -> Tuple[float, List[int]]:


    if indice < 0 or peso_disponible <= 0.05 or volumen_disponible <= 0.0001:
        return (0.0, [])

    # Clave de estado discretizada para la tabla dinámica (memoización)
    # Discretización: bloques de 1 kg y 0.01 m³ para garantizar solapamiento de subproblemas
    clave_estado = (indice, int(peso_disponible), int(volumen_disponible * 100))
    if clave_estado in memo:
        return memo[clave_estado]

    pkg_actual = candidatos[indice]

   
    # 2. CASO DE NO FACTIBILIDAD (PODA DE CAPACIDAD):
    #    Si el paquete actual supera el peso o volumen disponible en la mochila,
    #    NO puede ser incluido. Avanzamos recursivamente con el paquete anterior.
   
    if pkg_actual.peso_kg > peso_disponible or pkg_actual.volumen_m3 > volumen_disponible:
        resultado = mochila_recursiva(
            indice - 1,
            peso_disponible,
            volumen_disponible,
            candidatos,
            memo
        )
        memo[clave_estado] = resultado
        return resultado


    # 3. PASO RECURSIVO: RAMIFICACIÓN DE DECISIÓN (Incluir vs. No incluir)
   
    # RAMA A: NO incluir el paquete actual en el vehículo
    valor_sin, seleccion_sin = mochila_recursiva(
        indice - 1,
        peso_disponible,
        volumen_disponible,
        candidatos,
        memo
    )

    # RAMA B: SÍ incluir el paquete actual en el vehículo
    # Se descuenta su peso y volumen de la capacidad restante, y se suma su utilidad
    utilidad_item = calcular_utilidad_paquete(pkg_actual)
    valor_con, seleccion_con = mochila_recursiva(
        indice - 1,
        peso_disponible - pkg_actual.peso_kg,
        volumen_disponible - pkg_actual.volumen_m3,
        candidatos,
        memo
    )
    valor_con += utilidad_item

    # 4. DECISIÓN ÓPTIMA:
    #    Elegir la rama que produzca el mayor valor acumulado.
    
    if valor_con > valor_sin:
        mejor_opcion = (valor_con, seleccion_con + [indice])
    else:
        mejor_opcion = (valor_sin, seleccion_sin)

    # Guardar en memo para reutilizar en subárboles recursivos idénticos
    memo[clave_estado] = mejor_opcion
    return mejor_opcion


class MochilaFleetOptimizer:
    """
    Optimizador de carga para la flota completa usando el Algoritmo de la Mochila Recursivo.
    """

    @classmethod
    def asignar_carga_flota(
        cls,
        paquetes: List[Package],
        vehiculos: List[Vehicle],
        depot: Depot
    ) -> Tuple[List[Vehicle], List[Package], Dict[str, Any]]:
        """
        Asigna los N paquetes a los vehículos de la flota mediante la Mochila Recursiva.
        Asegura que:
        - Las neveras y electrodomésticos solo se asignen a Turbos.
        - Las motos solo lleven sobres y paquetes menores a 8 kg.
        - Ningún vehículo exceda su peso ni su volumen máximo (factor estiba 90%).
        """
        # 1. Reiniciar asignaciones
        for v in vehiculos:
            v.limpiar_asignaciones()

        pendientes = list(paquetes)

        # 2. Orden estratégico de asignación logística:
        # A) Primero las MOTOS toman sobres y paquetería ultraligera (< 8 kg)
        # B) Luego los TURBOS toman electrodomésticos y carga pesada (> 20 kg o voluminosa)
        # C) Luego las VANS toman paquetería mediana y estándar
        # D) Finalmente cualquier vehículo con espacio remanente absorbe paquetes restantes
        turbos = [v for v in vehiculos if v.tipo == "turbo"]
        vans = [v for v in vehiculos if v.tipo == "van"]
        motos = [v for v in vehiculos if v.tipo == "moto"]

        # Pasada 1: Carga por especialidad
        secuencia_especializada = [
            (motos, ["sobre", "caja_pequena"]),
            (turbos, ["electrodomestico", "caja_grande"]),
            (vans, ["caja_mediana", "caja_pequena", "caja_grande"]),
            (turbos + vans + motos, None)  # Remanentes
        ]

        for grupo_vehiculos, tipos_preferidos in secuencia_especializada:
            for v in grupo_vehiculos:
                if not pendientes:
                    break

                hubo_asignacion = True
                while hubo_asignacion and pendientes:
                    hubo_asignacion = False

                    peso_disp = v.capacidad_peso_kg - v.peso_actual_kg
                    vol_disp = (v.capacidad_volumen_m3 * 0.90) - v.volumen_actual_m3

                    if peso_disp <= 0.1 or vol_disp <= 0.001:
                        break

                    # Filtrar candidatos físicamente aptos y acordes a la preferencia
                    if tipos_preferidos is not None:
                        candidatos = [p for p in pendientes if v.puede_recibir(p) and p.tipo in tipos_preferidos]
                    else:
                        candidatos = [p for p in pendientes if v.puede_recibir(p)]

                    if not candidatos:
                        break

                    # Ordenar por cercanía
                    if v.paquetes_asignados:
                        ultimo_pkg = v.paquetes_asignados[-1]
                        ref_lat, ref_lng = ultimo_pkg.latitud, ultimo_pkg.longitud
                    else:
                        ref_lat, ref_lng = depot.latitud, depot.longitud

                    candidatos.sort(
                        key=lambda p: (
                            haversine_distance_km(ref_lat, ref_lng, p.latitud, p.longitud),
                            -p.peso_kg
                        )
                    )

                    lote = candidatos[:12]
                    memo: Dict[Tuple[int, int, int], Tuple[float, List[int]]] = {}
                    _, indices_seleccionados = mochila_recursiva(
                        indice=len(lote) - 1,
                        peso_disponible=peso_disp,
                        volumen_disponible=vol_disp,
                        candidatos=lote,
                        memo=memo
                    )

                    if indices_seleccionados:
                        hubo_asignacion = True
                        paquetes_elegidos = [lote[i] for i in indices_seleccionados]
                        for p in paquetes_elegidos:
                            v.agregar_paquete(p)
                            if p in pendientes:
                                pendientes.remove(p)

        unassigned = pendientes

        # Estadísticas del empaquetamiento
        total_asignados = sum(len(v.paquetes_asignados) for v in vehiculos)
        peso_total = sum(v.peso_actual_kg for v in vehiculos)
        volumen_total = sum(v.volumen_actual_m3 for v in vehiculos)

        resumen = {
            "total_paquetes": len(paquetes),
            "total_asignados": total_asignados,
            "total_no_asignados": len(unassigned),
            "peso_total_cargado_kg": round(peso_total, 2),
            "volumen_total_cargado_m3": round(volumen_total, 4),
            "vehiculos_utilizados": sum(1 for v in vehiculos if len(v.paquetes_asignados) > 0),
            "vehiculos_totales": len(vehiculos)
        }

        return vehiculos, unassigned, resumen
