import pandas as pd, os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')
from supabase import create_client

sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))
print('Conectado OK')
DIR = Path(__file__).parent.parent / 'datos_excel'

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
        print(f'  {min(i+500,len(registros))}/{len(registros)} -> {tabla}')

# TIENDAS - conservar tienda_id original
df_t = pd.read_excel(DIR/'dim_tiendas.xlsx')
df_t['fecha_apertura'] = pd.to_datetime(df_t['fecha_apertura']).dt.date.astype(str)
df_t['activa'] = df_t['activa'].astype(bool)
df_t['tienda_id'] = df_t['tienda_id'].astype(int)
cargar(df_t, 'dim_tiendas')
print(f'OK dim_tiendas: {len(df_t)}')

cargar(pd.read_excel(DIR/'dim_tipos_producto.xlsx'), 'dim_tipos_producto')
print('OK dim_tipos_producto')

df_ev = pd.read_excel(DIR/'dim_eventos.xlsx').drop(columns=['evento_id'],errors='ignore')
df_ev['fecha'] = pd.to_datetime(df_ev['fecha']).dt.date.astype(str)
cargar(df_ev, 'dim_eventos')
print('OK dim_eventos')

for anio in [2022,2023,2024]:
    df_v = pd.read_excel(DIR/f'ventas_{anio}.xlsx')
    df_v['fecha'] = pd.to_datetime(df_v['fecha']).dt.date.astype(str)
    df_v = df_v[df_v['unidades_vendidas']>0].dropna(subset=['fecha','tienda_id','tipo_producto'])
    df_v['tienda_id'] = df_v['tienda_id'].astype(int)
    df_v['es_precio_pleno'] = (df_v['descuento_pct']==0).astype(bool)
    df_v = df_v.drop(columns=['venta_id'],errors='ignore')
    cargar(df_v, 'fact_ventas_diarias')
    print(f'OK ventas_{anio}: {len(df_v):,}')

for parte in [1,2]:
    df_i = pd.read_excel(DIR/f'inventario_semanal_parte{parte}.xlsx')
    df_i['fecha'] = pd.to_datetime(df_i['fecha']).dt.date.astype(str)
    df_i['tienda_id'] = df_i['tienda_id'].astype(int)
    df_i = df_i.drop(columns=['inv_id'],errors='ignore')
    cargar(df_i, 'fact_inventario_semanal')
    print(f'OK inventario parte {parte}: {len(df_i):,}')

print('\n=== VERIFICACION ===')
for t in ['dim_tiendas','dim_tipos_producto','dim_eventos','fact_ventas_diarias','fact_inventario_semanal']:
    r = sb.table(t).select('*',count='exact').limit(1).execute()
    print(f'  {t:<35} {r.count:>10,}')
print('\nLISTO - Supabase cargado')
