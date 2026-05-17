"""
motores_2_3.py — Motor 2 (Despachos) + Motor 3 (Producción)
Se salta si ya existen resultados del día de hoy
"""
import pandas as pd, numpy as np, os, ast
from pathlib import Path
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / '.env')
from supabase import create_client

sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

COBERTURA_MIN  = 2.5
COBERTURA_OBJ  = 6.0
COBERTURA_MAX  = 8.0
GMROII_MIN     = 1.8
SEMANAS_PROD   = 16
STOCK_SEG      = 0.15
HOY            = str(date.today())

# ── Verificar si ya existen resultados de hoy ────────────
try:
    rd = sb.table('output_despachos_recomendados').select('*',count='exact').eq('fecha_ejecucion',HOY).limit(1).execute()
    rp = sb.table('output_produccion_recomendada').select('*',count='exact').eq('fecha_ejecucion',HOY).limit(1).execute()
    if (rd.count or 0) > 0 and (rp.count or 0) > 0:
        print(f"✅ Motores 2 y 3 ya ejecutados hoy ({HOY})")
        print(f"   Despachos: {rd.count} | Producción: {rp.count}")
        exit(0)
except: pass

print("Ejecutando Motor 2 y Motor 3...")

def leer(tabla, limite=300000):
    todos, offset = [], 0
    while offset < limite:
        r = sb.table(tabla).select('*').range(offset,offset+999).execute()
        if not r.data: break
        todos.extend(r.data)
        if len(r.data)<1000: break
        offset+=1000
    return pd.DataFrame(todos)

def guardar(df, tabla):
    registros = df.to_dict(orient='records')
    total = len(registros)
    for i in range(0,total,500):
        lote = registros[i:i+500]
        for row in lote:
            for k,v in list(row.items()):
                if hasattr(v,'item'): row[k]=v.item()
                elif hasattr(v,'isoformat'): row[k]=v.isoformat()
                elif v!=v: row[k]=None
        sb.table(tabla).insert(lote).execute()
    print(f"  ✓ {total:,} filas → {tabla}")

print("Cargando datos...")
df_inv   = leer('fact_inventario_semanal')
df_tipos = leer('dim_tipos_producto')
df_tiend = leer('dim_tiendas')
df_fc    = leer('output_forecast_semanal')

df_inv['tienda_id']   = df_inv['tienda_id'].astype(int)
df_tiend['tienda_id'] = df_tiend['tienda_id'].astype(int)
df_fc['tienda_id']    = df_fc['tienda_id'].astype(int)

# Último inventario
fecha_max = df_inv['fecha'].max()
df_inv = df_inv[df_inv['fecha']==fecha_max].merge(
    df_tiend[['tienda_id','nombre_tienda','ciudad','formato','departamento']],
    on='tienda_id', how='left')

# Forecast 4 semanas
df_fc4 = df_fc.groupby(['tienda_id','tipo_producto','familia']).agg(
    forecast_4sem=('forecast_medio','sum'),
    forecast_alto=('forecast_alto','sum')
).reset_index()

precio_d = df_tipos.set_index('tipo_producto')['precio_regular'].to_dict()
costo_d  = df_tipos.set_index('tipo_producto')['costo_produccion'].to_dict()

def calc_gmroii(tipo, u, fc4):
    if tipo not in precio_d or u<=0: return 0.0
    mg = (precio_d[tipo]-costo_d[tipo])/precio_d[tipo]
    margen = min(u,fc4)*precio_d[tipo]*mg
    costo  = u*costo_d[tipo]
    return round(margen/costo,2) if costo>0 else 0.0

# ── MOTOR 2 ───────────────────────────────────────────────
df_m = df_inv.merge(df_fc4[['tienda_id','tipo_producto','forecast_4sem','forecast_alto']],
    on=['tienda_id','tipo_producto'], how='left').fillna({'forecast_4sem':0,'forecast_alto':0})

df_m['unidades_disponibles'] = df_m['unidades_disponibles'].astype(float)
df_m['unidades_transito']    = df_m['unidades_transito'].fillna(0).astype(float)
df_m['venta_sem']   = df_m['forecast_4sem'] / 4
df_m['cobertura']   = ((df_m['unidades_disponibles']+df_m['unidades_transito']) /
                        df_m['venta_sem'].replace(0,np.nan)).fillna(99).round(1)
df_m['exceso']      = df_m['cobertura'] > COBERTURA_MAX
df_m['u_sugeridas'] = np.where(
    df_m['cobertura'] < COBERTURA_MIN,
    (COBERTURA_OBJ*df_m['venta_sem']-df_m['unidades_disponibles']).clip(lower=0).round(0).astype(int),
    0
)

desp = df_m[df_m['u_sugeridas']>0].copy()
desp['gmroii']          = desp.apply(lambda r: calc_gmroii(r['tipo_producto'],r['u_sugeridas'],r['forecast_4sem']),axis=1)
desp['tipo_despacho']   = 'RESURTIDO'
desp['estado']          = np.where(desp['gmroii']>=GMROII_MIN,'APROBADO','REVISAR')
desp['fecha_ejecucion'] = HOY
desp['semana_despacho'] = str(date.today()+timedelta(days=7))
desp['cobertura_proy']  = (desp['cobertura']+COBERTURA_OBJ).round(1)

print(f"Motor 2: {len(desp):,} despachos | Aprobados:{(desp.estado=='APROBADO').sum()} | Revisar:{(desp.estado=='REVISAR').sum()}")

try: sb.table('output_despachos_recomendados').delete().eq('fecha_ejecucion',HOY).execute()
except: pass

cols_d = ['fecha_ejecucion','tienda_id','tipo_producto','tipo_despacho',
          'u_sugeridas','semana_despacho','cobertura','cobertura_proy','gmroii','estado']
df_save = desp[cols_d].rename(columns={
    'u_sugeridas':'unidades_sugeridas','cobertura':'cobertura_actual',
    'cobertura_proy':'cobertura_proyectada','gmroii':'gmroii_proyectado'})
guardar(df_save, 'output_despachos_recomendados')

os.makedirs(Path(__file__).parent.parent/'outputs', exist_ok=True)
desp.to_excel(Path(__file__).parent.parent/'outputs'/'despachos_semana.xlsx', index=False)

# ── MOTOR 3 ───────────────────────────────────────────────
dem = df_fc.groupby(['tipo_producto','familia']).agg(
    demanda_8sem=('forecast_medio','sum')).reset_index()
inv_red = df_m.groupby('tipo_producto').agg(
    inv_red=('unidades_disponibles','sum')).reset_index()
inv_red['inv_red'] = inv_red['inv_red'].astype(float)

plan = dem.merge(inv_red,on='tipo_producto',how='left').fillna({'inv_red':0})
plan = plan.merge(df_tipos[['tipo_producto','costo_produccion','tallas_json']],on='tipo_producto',how='left')
plan['stock_seg']  = (plan['demanda_8sem']*STOCK_SEG).round(0)
plan['u_producir'] = (plan['demanda_8sem']+plan['stock_seg']-plan['inv_red']).clip(lower=0).round(0).astype(int)

hoy = date.today()
prod_rows = []
for _,row in plan.iterrows():
    try: tallas=ast.literal_eval(str(row['tallas_json']))
    except: tallas={'S':0.25,'M':0.35,'L':0.25,'XL':0.15}
    total = row['u_producir']
    prod_rows.append({
        'fecha_ejecucion':     HOY,
        'tipo_producto':       row['tipo_producto'],
        'familia':             row['familia'],
        'semana_inicio_prod':  str(hoy+timedelta(weeks=1)),
        'semana_llegada_cedi': str(hoy+timedelta(weeks=SEMANAS_PROD)),
        'unidades_totales':    int(total),
        'distribucion_tallas': str({t:int(total*p) for t,p in tallas.items()}),
        'inversion_estimada':  int(total*row['costo_produccion']),
        'zona_pipeline':       'AZUL',
        'estado':              'RECOMENDADO',
    })

df_prod = pd.DataFrame(prod_rows)
try: sb.table('output_produccion_recomendada').delete().eq('fecha_ejecucion',HOY).execute()
except: pass
guardar(df_prod, 'output_produccion_recomendada')
df_prod.to_excel(Path(__file__).parent.parent/'outputs'/'produccion_recomendada.xlsx', index=False)

print(f"\n{'='*50}")
print(f"RESUMEN EJECUTIVO — {HOY}")
print(f"{'='*50}")
print(f"Motor 2 · Despachos    : {len(desp):,} | Aprobados:{(desp.estado=='APROBADO').sum()}")
print(f"Motor 3 · Producción   : {len(df_prod)} tipos | ${df_prod.inversion_estimada.sum():,.0f} COP")
print(f"         Llegada CEDI  : {hoy+timedelta(weeks=SEMANAS_PROD)}")
print(f"{'='*50}")
