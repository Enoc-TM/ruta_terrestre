
import sys
import os

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.engine import LogisticsEngine


def test_sistema():
    print("Iniciando verificación del sistema en Ibagué...")
    engine = LogisticsEngine(num_turbos=3, num_vans=8, num_motos=4)

    # 1. Verificar carga de datos
    assert len(engine.packages) == 200, f"Error: esperados 200 paquetes, encontrados {len(engine.packages)}"
    print(f"[OK] Carga de 200 paquetes en CSV validada (Ibagué).")

    # 2. Ejecutar optimización
    res = engine.run_optimization()
    assert res["metricas_generales"]["paquetes_entregados"] > 0, "Error: no se asignaron paquetes"
    print(f"[OK] Optimización ejecutada: {res['metricas_generales']['paquetes_entregados']} paquetes asignados.")

    # 3. Validar Regla de Oro Física: Jamás una nevera o electrodoméstico en una moto
    for v in engine.vehicles:
        if v.tipo == "moto":
            for p in v.paquetes_asignados:
                assert p.tipo in ["sobre", "caja_pequena"], f"Violación física: moto {v.id} lleva {p.tipo}"
                assert p.peso_kg <= 8.0, f"Violación de peso: moto {v.id} lleva paquete de {p.peso_kg} kg"
                assert p.alto_cm <= 40.0 and p.ancho_cm <= 40.0 and p.profundidad_cm <= 40.0, "Dimensiones excedidas en moto"
    print("[OK] Regla física garantizada: Ninguna moto transporta electrodomésticos ni paquetes > 8 kg.")

    # 4. Validar que las paradas tengan hora de salida y hora de llegada
    for v in engine.vehicles:
        if v.paquetes_asignados:
            assert v.hora_salida != "", "Falta hora de salida en vehículo"
            assert v.hora_retorno != "", "Falta hora de retorno en vehículo"
            for p in v.paquetes_asignados:
                assert p.hora_llegada != "Pendiente", f"Paquete {p.id} no tiene hora de llegada calculada"
    print("[OK] Cronograma validado: Cada parada y paquete cuenta con hora de salida y llegada exacta.")

    print("\nTODAS LAS PRUEBAS PASARON EXITOSAMENTE EN IBAGUÉ!")


if __name__ == "__main__":
    test_sistema()
