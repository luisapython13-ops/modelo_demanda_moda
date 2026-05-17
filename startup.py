#!/usr/bin/env python3
"""
startup.py — Orquestador de inicio automático
Verifica qué pasos ya están hechos y solo ejecuta los pendientes
"""
import os, sys, subprocess, time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / '.env')

SCRIPTS = Path(__file__).parent / 'scripts'
OUTPUTS = Path(__file__).parent / 'outputs'
OUTPUTS.mkdir(exist_ok=True)

def run(script, desc):
    print(f"\n{'─'*50}")
    print(f"▶  {desc}")
    print(f"{'─'*50}")
    result = subprocess.run([sys.executable, str(SCRIPTS/script)],
                            capture_output=False, text=True)
    if result.returncode != 0:
        print(f"⚠️  {script} terminó con código {result.returncode}")
    return result.returncode

print("╔══════════════════════════════════════════════╗")
print("║   Intelligent Fashion Predictor v2.0        ║")
print("║   Inicializando sistema...                   ║")
print("╚══════════════════════════════════════════════╝")

# 1. Verificar credenciales
if not os.getenv('SUPABASE_URL') or not os.getenv('SUPABASE_SERVICE_KEY'):
    print("❌ ERROR: Faltan credenciales en .env")
    print("   Crea el archivo .env con:")
    print("   SUPABASE_URL=...")
    print("   SUPABASE_ANON_KEY=...")
    print("   SUPABASE_SERVICE_KEY=...")
    sys.exit(1)

# 2. Verificar datos Excel
datos_dir = Path(__file__).parent / 'datos_excel'
archivos_requeridos = ['dim_tiendas.xlsx','dim_tipos_producto.xlsx','dim_eventos.xlsx',
                       'ventas_2022.xlsx','ventas_2023.xlsx','ventas_2024.xlsx',
                       'inventario_semanal_parte1.xlsx','inventario_semanal_parte2.xlsx']

faltantes = [f for f in archivos_requeridos if not (datos_dir/f).exists()]
if faltantes:
    print(f"\n⚠️  Generando datos simulados (faltan: {len(faltantes)} archivos)...")
    run('generar_datos.py', 'Generando datos simulados')
else:
    print(f"\n✅ Datos Excel encontrados ({len(archivos_requeridos)} archivos)")

# 3. Cargar datos a Supabase (se salta si ya están)
run('cargar_datos.py', 'Verificando/Cargando datos a Supabase')

# 4. Motor 1 - Forecast (se salta si modelo ya es bueno)
run('motor1_forecast.py', 'Motor 1: Entrenando modelo y generando forecast')

# 5. Motores 2 y 3 (se salta si ya corrieron hoy)
run('motores_2_3.py', 'Motor 2 y 3: Despachos y producción')

print("\n╔══════════════════════════════════════════════╗")
print("║   ✅ Sistema inicializado correctamente       ║")
print("║   🌐 API disponible en el puerto 8000        ║")
print("║   📊 Dashboard: /                            ║")
print("║   📖 API Docs:  /docs                        ║")
print("╚══════════════════════════════════════════════╝\n")
