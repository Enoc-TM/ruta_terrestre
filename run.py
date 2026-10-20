
import sys
import os
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Asegurar importación de módulos core
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.engine import LogisticsEngine
from core.models import Package, Vehicle


def imprimir_encabezado(texto: str):
    print("\n" + "=" * 80)
    print(f"  {texto.upper()}")
    print("=" * 80)


def imprimir_subtitulo(texto: str):
    print("\n" + "-" * 80)
    print(f"  >>> {texto}")
    print("-" * 80)


def mostrar_flota_inicial(vehiculos):
    imprimir_subtitulo("1. CONFIGURACIÓN DE LA FLOTA TERRESTRE DISPONIBLE")
    print(f"{'VEHÍCULO':<22} | {'TIPO':<7} | {'PLACA':<8} | {'CAP. PESO':<10} | {'DIMENSIONES (Alt x Anc x Prof)':<30} | {'MÁX INDIV':<10}")
    print("-" * 105)
    for v in vehiculos:
        dims = f"{v.compartimiento_alto_cm:.0f} x {v.compartimiento_ancho_cm:.0f} x {v.compartimiento_profundidad_cm:.0f} cm"
        print(f"{v.nombre:<22} | {v.tipo.upper():<7} | {v.placa:<8} | {v.capacidad_peso_kg:>7.0f} kg | {dims:<30} | {v.peso_max_paquete_individual_kg:>7.0f} kg")


def mostrar_resumen_mochila(resultado):
    imprimir_subtitulo("2. RESULTADO DE ASIGNACIÓN (ALGORITMO DE LA MOCHILA CON RECURSIVIDAD)")
    metricas = resultado["metricas_generales"]
    packing = resultado["packing_summary"]

    print(f"  • Total de paquetes en inventario (CSV): {metricas['total_paquetes']}")
    print(f"  • Paquetes cargados en vehículos:       {metricas['paquetes_entregados']} ({metricas['porcentaje_efectividad']}%)")
    print(f"  • Paquetes pendientes:                   {metricas['paquetes_pendientes']}")
    print(f"  • Peso total cargado en la flota:       {packing['peso_total_cargado_kg']} kg")
    print(f"  • Volumen total cargado:                 {packing['volumen_total_cargado_m3']} m³")
    print(f"  • Vehículos activos utilizados:          {metricas['vehiculos_activos']} de {metricas['vehiculos_totales']}")


def mostrar_tabla_vehiculos(resultado):
    imprimir_subtitulo("3. ESTADO Y RUTAS POR VEHÍCULO (DIJKSTRA + 2-OPT TSP)")
    print(f"{'VEHÍCULO':<20} | {'TIPO':<6} | {'PLACA':<8} | {'PAQUETES':<8} | {'PESO (kg)':<15} | {'VOL (m³)':<14} | {'DISTANCIA':<10} | {'SALIDA':<9} | {'RETORNO':<9}")
    print("-" * 115)

    for v in resultado["vehiculos"]:
        if v["total_paquetes"] > 0:
            peso_str = f"{v['peso_actual_kg']:>6.1f} ({v['porcentaje_ocupacion_peso']}%)"
            vol_str = f"{v['volumen_actual_m3']:>5.3f} ({v['porcentaje_ocupacion_volumen']}%)"
            dist_str = f"{v['distancia_total_km']:>5.1f} km"
            print(f"{v['nombre']:<20} | {v['tipo'].upper():<6} | {v['placa']:<8} | {v['total_paquetes']:>8} | {peso_str:<15} | {vol_str:<14} | {dist_str:<10} | {v['hora_salida']:<9} | {v['hora_retorno']:<9}")


def mostrar_detalle_vehiculo_especifico(engine: LogisticsEngine, vehiculo_id: str):
    """
    Muestra el detalle parada por parada de un vehículo seleccionado,
    cumpliendo con la petición del profesor en la transcripción:
    'Por ejemplo yo selecciono camión 1, me salgan los paquetes que van dentro de ese camión,
     la hora de salida y la ruta de entrega'.
    """
    vehiculo = next((v for v in engine.vehicles if v.id == vehiculo_id or v.nombre == vehiculo_id), None)
    if not vehiculo:
        return

    imprimir_subtitulo(f"DETALLE DE HOJA DE RUTA: {vehiculo.nombre} ({vehiculo.tipo.upper()} | {vehiculo.placa})")
    print(f"  • Hora de salida del Hub:   {vehiculo.hora_salida}")
    print(f"  • Hora estimada de retorno: {vehiculo.hora_retorno}")
    print(f"  • Carga transportada:       {vehiculo.peso_actual_kg} kg / {vehiculo.capacidad_peso_kg} kg ({vehiculo.porcentaje_ocupacion_peso}%)")
    print(f"  • Volumen ocupado:          {vehiculo.volumen_actual_m3} m³ / {vehiculo.capacidad_volumen_m3} m³")
    print(f"  • Recorrido total vial:     {vehiculo.distancia_total_km} km (Tiempo total: {vehiculo.tiempo_estimado_min:.0f} min)")
    print("\n  SECUENCIA ÓPTIMA DE PARADAS (DIJKSTRA):")
    print(f"  {'#':<3} | {'HORA':<9} | {'TIPO PARADA':<16} | {'DESCRIPCIÓN / DESTINO':<35} | {'PESO':<8} | {'DIMENSIONES':<18} | {'DIRECCIÓN / BARRIO'}")
    print("  " + "-" * 125)

    for parada in vehiculo.paradas:
        orden = parada["orden"]
        hora = parada["hora_estimada"]
        tipo = parada["tipo"]

        if tipo == "deposito_salida":
            print(f"  {orden:<3} | {hora:<9} | {'SALIDA HUB':<16} | {parada['nombre']:<35} | {'---':<8} | {'---':<18} | {parada['direccion']}")
        elif tipo == "deposito_retorno":
            print(f"  {orden:<3} | {hora:<9} | {'RETORNO HUB':<16} | {parada['nombre']:<35} | {'---':<8} | {'---':<18} | {parada['direccion']}")
        else:
            pkg = parada["paquete"]
            desc = pkg["descripcion"][:35]
            peso = f"{pkg['peso_kg']:.1f} kg"
            dims = f"{pkg['alto_cm']:.0f}x{pkg['ancho_cm']:.0f}x{pkg['profundidad_cm']:.0f}cm"
            ubicacion = f"{pkg['direccion']} ({pkg['barrio']})"
            print(f"  {orden:<3} | {hora:<9} | {'ENTREGA CLIENTE':<16} | {desc:<35} | {peso:<8} | {dims:<18} | {ubicacion}")


def main():
    imprimir_encabezado("TransLogística Express Ibagué — Enrutador y Cubicaje Terrestre")
    print("  Proyecto de Optimización Logística Urbana en Ibagué (Consola / Terminal)")
    print("  Algoritmo de la Mochila (Knapsack) Recursivo + Algoritmo de Dijkstra + TSP")

    # 1. Instanciar motor de logística
    engine = LogisticsEngine(num_turbos=3, num_vans=8, num_motos=4)

    # 2. Mostrar Flota
    mostrar_flota_inicial(engine.vehicles)

    # 3. Mostrar Dataset
    csv_input = os.path.join(os.path.dirname(__file__), "data", "paquetes_ibague_200.csv")
    if not os.path.exists(csv_input):
        csv_input = os.path.join(os.path.dirname(__file__), "data", "paquetes_bogota_200.csv")
    imprimir_subtitulo("CARGA DE PAQUETES DESDE ARCHIVO CSV (IBAGUÉ)")
    print(f"  • Archivo CSV cargado: {csv_input}")
    print(f"  • Cantidad de paquetes: {len(engine.packages)}")
    print(f"  • Columnas validadas: id_paquete, tipo, peso_kg, alto_cm, ancho_cm, profundidad_cm,")
    print(f"                        volumen_m3, latitud, longitud, direccion, barrio, hora_salida, hora_llegada")

    # 4. Ejecutar Pipeline de Optimización
    imprimir_subtitulo("EJECUTANDO OPTIMIZACIÓN...")
    print("  [1/2] Ejecutando Algoritmo de la Mochila Multidimensional con RECURSIVIDAD...")
    print("  [2/2] Calculando Caminos Mínimos en Grafo con Algoritmo de Dijkstra y TSP (2-Opt)...")

    resultado = engine.run_optimization()

    # 5. Mostrar Resultados Consolidados
    mostrar_resumen_mochila(resultado)
    mostrar_tabla_vehiculos(resultado)

    # 6. Demostración para el profesor: Inspeccionar un Camión Turbo (con electrodomésticos)
    mostrar_detalle_vehiculo_especifico(engine, "TRB-01")

    # 7. Demostración para el profesor: Inspeccionar una Moto (solo sobres y paquetes < 8 kg)
    # Demuestra que la regla física se cumplió: Jamás una nevera en moto
    mostrar_detalle_vehiculo_especifico(engine, "MOT-01")

    # 8. Exportar archivo CSV con los resultados de las rutas y horarios
    csv_output = os.path.join(os.path.dirname(__file__), "data", "rutas_optimizadas_200.csv")
    engine.export_results_to_csv(csv_output)
    imprimir_subtitulo("4. EXPORTACIÓN DE RESULTADOS COMPLETADA")
    print(f"  • Se ha generado exitosamente el archivo CSV con las rutas:")
    print(f"    --> {csv_output}")
    print("  • Cada fila contiene: Vehículo, Placa, Parada #, Paquete, Peso, Dimensiones,")
    print("                        Hora de Salida del Hub y Hora Exacta de Llegada/Entrega.")

    imprimir_encabezado("OPTIMIZACIÓN COMPLETADA CON ÉXITO")


if __name__ == "__main__":
    main()
