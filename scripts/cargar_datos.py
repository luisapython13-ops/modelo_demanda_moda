"""cargar_datos.py — Carga Excel a Supabase. Se salta si datos ya existen."""
import pandas as pd, os, sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / '.env')
from supabase import create_client

sb  = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))
DIR = Path(__file__).parent.parent / 'datos_excel'

def contar(tabla):
    try: return sb.table(tabla).select('*',count='exact').limit(1).execute().count or 0
    except: return 0

def cargar(df, tabla):
    registros = df.to_dict(orient='records')
    for i in range(0, len(registros), 500):
        lote = registros[i:i+500]
        for row in lote:
            for k,v in list(row.items()):
                if hasattr(v,'item'): row[k]=v.item()
                elif hasattr(v,'isoformat'): row[k]=v.isoformat()
                elif v!=v: row[k]=None
        sb.table(tabla).insert(lote).execute()
        print(f"  {min(i+500,len(registros))}/{len(registros)}", end='\r')
    print(f"  ✓ {len(registros):,} → {tabla}        ")

# Verificar si ya hay datos suficientes
n_v = contar('fact_ventas_diarias')
n_i = contar('fact_inventario_semanal')
n_t = contar('dim_tiendas')

if n_v > 100000 and n_i > 100000 and n_t >= 89:
    print(f"✅ Datos ya cargados: {n_v:,} ventas | {n_i:,} inventario | {n_t} tiendas")
    sys.exit(0)

print(f"📂 Cargando datos a Supabase...")

# Limpiar dimensiones
for t,col in [('dim_eventos','evento_id'),('dim_tipos_producto','tipo_producto'),('dim_tiendas','tienda_id')]:
    try: sb.table(t).delete().neq(col,0 if col=='evento_id' else '').execute()
    except: pass

df_t = pd.read_excel(DIR/'dim_tiendas.xlsx')
df_t['fecha_apertura'] = pd.to_datetime(df_t['fecha_apertura']).dt.date.astype(str)
df_t['activa'] = df_t['activa'].astype(bool)
df_t['tienda_id'] = df_t['tienda_id'].astype(int)
cargar(df_t, 'dim_tiendas')

cargar(pd.read_excel(DIR/'dim_tipos_producto.xlsx'), 'dim_tipos_producto')

df_ev = pd.read_excel(DIR/'dim_eventos.xlsx').drop(columns=['evento_id'],errors='ignore')
df_ev['fecha'] = pd.to_datetime(df_ev['fecha']).dt.date.astype(str)
cargar(df_ev, 'dim_eventos')
print("✓ Dimensiones cargadas")

try: sb.table('fact_ventas_diarias').delete().neq('venta_id',0).execute()
except: pass
for anio in [2022,2023,2024]:
    df_v = pd.read_excel(DIR/f'ventas_{anio}.xlsx')
    df_v['fecha'] = pd.to_datetime(df_v['fecha']).dt.date.astype(str)
    df_v = df_v[df_v['unidades_vendidas']>0].dropna(subset=['fecha','tienda_id','tipo_producto'])
    df_v['tienda_id'] = df_v['tienda_id'].astype(int)
    df_v['es_precio_pleno'] = (df_v['descuento_pct']==0).astype(bool)
    df_v = df_v.drop(columns=['venta_id'],errors='ignore')
    cargar(df_v, 'fact_ventas_diarias')
    print(f"✓ ventas_{anio}: {len(df_v):,}")

try: sb.table('fact_inventario_semanal').delete().neq('inv_id',0).execute()
except: pass
for parte in [1,2]:
    df_i = pd.read_excel(DIR/f'inventario_semanal_parte{parte}.xlsx')
    df_i['fecha'] = pd.to_datetime(df_i['fecha']).dt.date.astype(str)
    df_i['tienda_id'] = df_i['tienda_id'].astype(int)
    df_i = df_i.drop(columns=['inv_id'],errors='ignore')
    cargar(df_i, 'fact_inventario_semanal')
    print(f"✓ inventario parte {parte}: {len(df_i):,}")

print(f"\n✅ Carga completa: {contar('fact_ventas_diarias'):,} ventas | {contar('fact_inventario_semanal'):,} inventario")
