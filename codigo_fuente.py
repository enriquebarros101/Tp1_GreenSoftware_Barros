from codecarbon import EmissionsTracker
import time
from typing import Dict, Any
import argparse


def reglaDeTres(valor1: float, valor2: float, valor3: float) -> float:
    if valor1 == 0:
        return 0.0
    return (valor2 * valor3) / valor1


class TrackerCarbono:

    def __init__(self, nombre_proyecto: str = "Código_prueba"):
        self.nombre_proyecto = nombre_proyecto
        self.tracker = None
        self.resultados: Dict[str, Any] = {}

    def iniciar_tracking(self):
        self.tracker = EmissionsTracker(
            project_name=self.nombre_proyecto,
            measure_power_secs=1,
            save_to_file=False,
            log_level="CRITICAL"
        )

        print()
        self.tracker.start()

    def detener_tracking(self) -> Dict[str, Any]:
        if not self.tracker:
            print("⚠️ No hay tracking activo")
            return {}

        emisiones_kg = self.tracker.stop()

        # Intentar leer energía (kWh)
        energia_kwh = None
        try:
            total_energy = getattr(self.tracker, "_total_energy", None)
            if total_energy is not None:
                energia_kwh = getattr(total_energy, "kWh", None)
        except Exception:
            energia_kwh = None

        self.resultados = {
            'emisiones_kg': float(emisiones_kg),
            'emisiones_g': float(emisiones_kg) * 1000.0,
            'energia_kwh': energia_kwh
        }
        
        return self.resultados

    def trackear_funcion(self, func, *args, **kwargs):
        self.iniciar_tracking()
        tiempo_inicio = time.time()
        try:
            resultado = func(*args, **kwargs)
            tiempo_ejecucion = time.time() - tiempo_inicio
            metricas = self.detener_tracking()
            metricas['tiempo_ejecucion'] = tiempo_ejecucion
            return resultado, metricas
        finally:
            try:
                self.detener_tracking()
            except Exception:
                pass

    @staticmethod
    def calcular_compensacion_arboles(emisiones_kg: float, tiempo_ejecucion_segundos: float) -> Dict[str, float]:
        tiempo_horas = tiempo_ejecucion_segundos / 3600.0
        ARBOL_JOVEN_ANUAL_KG = 30.0
        ARBOL_ADULTO_ANUAL_KG = 300.0

        
        horas_joven = reglaDeTres(emisiones_kg, tiempo_horas, ARBOL_JOVEN_ANUAL_KG)
        horas_adulto = reglaDeTres(emisiones_kg, tiempo_horas, ARBOL_ADULTO_ANUAL_KG)

        tasa_emision_kg_por_hora = (emisiones_kg / tiempo_horas) if tiempo_horas > 0 else 0.0

        return {
            'tasa_emision_kg_por_hora': tasa_emision_kg_por_hora,
            'tiempo_ejecucion_horas': tiempo_horas,
            'horas_para_compensar_arbol_joven': horas_joven,
            'horas_para_compensar_arbol_adulto': horas_adulto,
        }

    def imprimir_resultados(self, datos_compensacion: Dict[str, float] = None):
        if not self.resultados:
            print("⚠️ No hay resultados disponibles")
            return

        print("\n" + "=" * 60)
        print("📊 RESUMEN DE TRACKING (CodeCarbon)")
        print("=" * 60)
        print(f"🏷️  Proyecto: {self.nombre_proyecto}")
        print(f"⚡ Emisiones (CO2eq): {self.resultados['emisiones_kg']:.10f} kg ")

        if self.resultados.get('energia_kwh') is not None:
            print(f"🔋 Energía consumida: {self.resultados['energia_kwh']:.10f} kWh")
        else:
            print("🔋 Energía consumida: (no disponible desde CodeCarbon)")

        if 'tiempo_ejecucion' in self.resultados:
            print(f"⏱️  Tiempo de ejecución medido: {self.resultados['tiempo_ejecucion']:.2f} s")

        if datos_compensacion:
            print("\n🌳 HORAS DE PROCESAMIENTO NECESARIAS PARA COMPENSARSE X 1 ÁRBOL:")
            print("-" * 60)
            print(f"🌱 Árbol joven (30 kg CO2/año): {datos_compensacion['horas_para_compensar_arbol_joven']:.2f} horas ")
            print(f"🌲 Árbol adulto (300 kg CO2/año): {datos_compensacion['horas_para_compensar_arbol_adulto']:.2f} horas ")
            
        print("=" * 60)


# === FUNCIÓN DE PRUEBA ===
def codigo_prueba_timed(target_seconds: float = 15.0):
    print(f"🔄 Ejecutando prueba...")
    print()
    inicio = time.time()
    total = 0
    iteraciones = 0
    chunk_size = 50000  # fijo

    while True:
        for i in range(chunk_size):
            total += i * i

        iteraciones += 1
        if (time.time() - inicio) >= target_seconds:
            break

    tiempo_total = time.time() - inicio
    print(f"✅ Prueba completada.")
    return {'total_acumulado': int(total), 'iteraciones': iteraciones, 'tiempo_ejecucion_segundos': tiempo_total}


# === MAIN ===
def main(target_seconds: float = 15.0):
    print("=" * 60)
    print("🚀 INICIANDO...")
    print("=" * 60)

    tracker = TrackerCarbono("código_prueba")

    resultado_prueba, metricas = tracker.trackear_funcion(
        codigo_prueba_timed,
        target_seconds
    )

    emisiones_kg = metricas.get('emisiones_kg', 0.0)
    tiempo_ejecucion = metricas.get('tiempo_ejecucion', resultado_prueba.get('tiempo_ejecucion_segundos'))

    compensacion = TrackerCarbono.calcular_compensacion_arboles(emisiones_kg, tiempo_ejecucion)

    tracker.resultados['tiempo_ejecucion'] = tiempo_ejecucion
    tracker.imprimir_resultados(compensacion)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test timed para medir CO2/energía con CodeCarbon")
    parser.add_argument("--seconds", "-s", type=float, default=10, help="Tiempo objetivo de ejecución (s)")
    args = parser.parse_args()

    main(target_seconds=args.seconds)
