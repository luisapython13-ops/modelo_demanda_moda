import pandas as pd, numpy as np, os, ast
from pathlib import Path
from datetime import date, timedelta
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(Path(__file__).parent.parent / '.env')
sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))
print('Conectado OK')

COBERTURA_MIN=2.5; COBERTURA_OBJ=6.0; GMROII_MIN=1.8; SEMANAS_PROD=16; STOCK_SEG=0.15

def leer(tabla):
    todos, offset = [], 0
    while True:
        r = sb.table(tabla).select('*').range(offset,offset+999).execute()
        if not r.data: break
        todos.extend(r.data)
        if len(r.data)<1000: break
        offset+=1000
    return pd.DataFrame(todos)

def guardar(df, tabla):
    registros = df.to_dict(orient='records')
    for i in range(0,len(registros),500):
        lote = registros[i:i+500]
        for row in lote:
            for k,v in list(row.items()):
                if hasattr(v,'item'): row[k]=v.item()
                elif hasattr(v,'isoformat'): row[k]=v.isoformat()
                elif v!=v: row[k]=None
        sb.table(tabla).insert(lote).execute()
    print(f'OK {len(registros)} filas -> {tabla}')

print('Cargando datos...')
df_inv   = leer('fact_inventario_semanal')
df_tipos = leer('dim_tipos_producto')
df_tiend = leer('dim_tiendas')
df_fc    = leer('output_forecast_semanal')
print(f'Inventario:{len(df_inv):,} Tipos:{len(df_tipos)} Forecast:{len(df_fc):,}')

df_inv['tienda_id']   = df_inv['tienda_id'].astype(int)
df_tiend['tienda_id'] = df_tiend['tienda_id'].astype(int)
df_fc['tienda_id']    = df_fc['tienda_id'].astype(int)

# Ultimo inventario
fecha_max = df_inv['fecha'].max()
df_inv = df_inv[df_inv['fecha']==fecha_max].merge(
    df_tiend[['tienda_id','nombre_tienda','ciudad','formato']], on='tienda_id', how='left')

# Forecast 4 semanas
df_fc4 = df_fc.groupby(['tienda_id','tipo_producto','familia']).agg(
    forecast_4sem=('forecast_medio','sum')).reset_index()

precio_d = df_tipos.set_index('tipo_producto')['precio_regular'].to_dict()
costo_d  = df_tipos.set_index('tipo_producto')['costo_produccion'].to_dict()

def gmroii(tipo, u, fc4):
    if tipo not in precio_d or u<=0: return 0
    m = min(u,fc4)*precio_d[tipo]*((precio_d[tipo]-costo_d[tipo])/precio_d[tipo])
    c = u*costo_d[tipo]
    return round(m/c,2) if c>0 else 0

df_m = df_inv.merge(df_fc4[['tienda_id','tipo_producto','forecast_4sem']],
    on=['tienda_id','tipo_producto'],how='left').fillna({'forecast_4sem':0})
df_m['venta_sem']  = df_m['forecast_4sem']/4
df_m['cobertura']  = ((df_m['unidades_disponibles'].astype(float)+
    df_m['unidades_transito'].fillna(0).astype(float))/
    df_m['venta_sem'].replace(0,np.nan)).fillna(99).round(1)
df_m['u_sug'] = np.where(df_m['cobertura']<COBERTURA_MIN,
    (COBERTURA_OBJ*df_m['venta_sem']-df_m['unidades_disponibles'].astype(float)).clip(lower=0).round(0).astype(int),0)

desp = df_m[df_m['u_sug']>0].copy()
desp['gmroii']           = desp.apply(lambda r: gmroii(r['tipo_producto'],r['u_sug'],r['forecast_4sem']),axis=1)
desp['tipo_despacho']    = 'RESURTIDO'
desp['estado']           = np.where(desp['gmroii']>=GMROII_MIN,'APROBADO','REVISAR')
desp['fecha_ejecucion']  = str(date.today())
desp['semana_despacho']  = str(date.today()+timedelta(days=7))
print(f'Despachos:{len(desp):,} | Aprobados:{(desp.estado=="APROBADO").sum():,} | Revisar:{(desp.estado=="REVISAR").sum():,}')

cols_d = ['fecha_ejecucion','tienda_id','tipo_producto','tipo_despacho',
    'u_sug','semana_despacho','cobertura','gmroii','estado']
df_save = desp[cols_d].rename(columns={'u_sug':'unidades_sugeridas',
    'cobertura':'cobertura_actual','gmroii':'gmroii_proyectado'})
guardar(df_save, 'output_despachos_recomendados')

os.makedirs('outputs',exist_ok=True)
desp.to_excel('outputs/despachos_semana.xlsx',index=False)
print('Excel: outputs/despachos_semana.xlsx')

# MOTOR 3
dem = df_fc.groupby(['tipo_producto','familia']).agg(demanda_8sem=('forecast_medio','sum')).reset_index()
inv_red = df_m.groupby('tipo_producto').agg(inv_red=('unidades_disponibles','sum')).reset_index()
inv_red['inv_red'] = inv_red['inv_red'].astype(float)
plan = dem.merge(inv_red,on='tipo_producto',how='left').fillna({'inv_red':0})
plan = plan.merge(df_tipos[['tipo_producto','costo_produccion','tallas_json']],on='tipo_producto',how='left')
plan['stock_seg']    = (plan['demanda_8sem']*STOCK_SEG).round(0)
plan['u_producir']   = (plan['demanda_8sem']+plan['stock_seg']-plan['inv_red']).clip(lower=0).round(0).astype(int)

hoy = date.today()
prod_rows = []
for _,row in plan.iterrows():
    try: tallas=ast.literal_eval(str(row['tallas_json']))
    except: tallas={'S':0.25,'M':0.35,'L':0.25,'XL':0.15}
    total=row['u_producir']
    prod_rows.append({
        'fecha_ejecucion':     str(hoy),
        'tipo_producto':       row['tipo_producto'],
        'familia':             row['familia'],
        'semana_inicio_prod':  str(hoy+timedelta(weeks=1)),
        'semana_llegada_cedi': str(hoy+timedelta(weeks=SEMANAS_PROD)),
        'unidades_totales':    int(total),
        'distribucion_tallas': str({t:int(total*p) for t,p in tallas.items()}),
        'inversion_estimada':  int(total*row['costo_produccion']),
        'zona_pipeline':       'AZUL',
        'estado':              'RECOMENDADO'
    })

df_prod = pd.DataFrame(prod_rows)
guardar(df_prod, 'output_produccion_recomendada')
df_prod.to_excel('outputs/produccion_recomendada.xlsx',index=False)
print('Excel: outputs/produccion_recomendada.xlsx')

print('\n========== RESUMEN EJECUTIVO ==========')
print(f'Fecha: {hoy}')
print(f'Motor 1 - Forecast    : 10,680 predicciones (8 semanas)')
print(f'Motor 2 - Despachos   : {len(desp):,} | Aprobados: {(desp.estado=="APROBADO").sum():,}')
print(f'Motor 3 - Produccion  : {len(df_prod):,} tipos | ${df_prod.inversion_estimada.sum():,.0f} COP')
print(f'Llegada CEDI          : {hoy+timedelta(weeks=SEMANAS_PROD)}')
print('=======================================')
print('PROYECTO COMPLETO')
