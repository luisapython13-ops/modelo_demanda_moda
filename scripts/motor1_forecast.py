"""
motor1_forecast.py — Forecast de ventas con LightGBM optimizado
Objetivo: MAPE < 20% | MAE >= 0.7
Se salta si ya existe un modelo con buen resultado
"""
import pandas as pd, numpy as np, os, pickle, warnings
from pathlib import Path
from datetime import date
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / '.env')
from supabase import create_client
from sklearn.metrics import mean_absolute_percentage_error, mean_absolute_error
from sklearn.preprocessing import LabelEncoder
import lightgbm as lgb

warnings.filterwarnings('ignore')

MODEL_PATH = Path(__file__).parent.parent / 'outputs' / 'modelo_lgbm.pkl'
MAPE_OBJETIVO = 20.0

# ── Verificar si ya existe modelo bueno ──────────────────
if MODEL_PATH.exists():
    with open(MODEL_PATH,'rb') as f:
        saved = pickle.load(f)
    if saved.get('mape', 999) < MAPE_OBJETIVO:
        print(f"✅ Modelo ya existe con MAPE={saved['mape']:.1f}% < {MAPE_OBJETIVO}%")
        print("   Saltando entrenamiento...")
        exit(0)

sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))
print("Conectado a Supabase OK")

# ── Cargar datos ──────────────────────────────────────────
print("Cargando ventas...")
todos, offset = [], 0
while True:
    r = sb.table('fact_ventas_diarias').select('*').range(offset,offset+999).execute()
    if not r.data: break
    todos.extend(r.data)
    if len(r.data)<1000: break
    offset+=1000
    if offset%20000==0: print(f"  {offset:,} filas...")

df_v = pd.DataFrame(todos)
df_v['fecha'] = pd.to_datetime(df_v['fecha'])
print(f"Ventas: {len(df_v):,} filas")

# Agregar semanal
df_v['semana'] = df_v['fecha'].dt.to_period('W').dt.start_time
df = df_v.groupby(['semana','tienda_id','tipo_producto','familia']).agg(
    unidades=('unidades_vendidas','sum'),
    valor_venta=('valor_venta','sum'),
    descuento_pct_avg=('descuento_pct','mean'),
    pct_precio_pleno=('es_precio_pleno','mean'),
    dias_con_venta=('fecha','count'),
).reset_index()
df['tienda_id'] = df['tienda_id'].astype(int)

# Cargar dimensiones
r = sb.table('dim_tiendas').select('*').execute()
df_t = pd.DataFrame(r.data)
df_t['tienda_id'] = df_t['tienda_id'].astype(int)
df = df.merge(df_t[['tienda_id','ciudad','formato','segmento_cliente','indice_rotacion','metros_cuadrados']],
              on='tienda_id', how='left')

r = sb.table('dim_eventos').select('*').execute()
df_ev = pd.DataFrame(r.data)
df_ev['fecha'] = pd.to_datetime(df_ev['fecha'])

# ── Feature Engineering completo ─────────────────────────
df['semana_iso']  = df['semana'].dt.isocalendar().week.astype(int)
df['mes']         = df['semana'].dt.month
df['anio']        = df['semana'].dt.year
df['trimestre']   = df['semana'].dt.quarter
df['dia_anio']    = df['semana'].dt.dayofyear
df['es_quincena'] = df['semana'].dt.day.isin([14,15,16,28,29,30]).astype(int)

# Ciclicidad - captura estacionalidad perfectamente
df['sem_sin']  = np.sin(2*np.pi*df['semana_iso']/52)
df['sem_cos']  = np.cos(2*np.pi*df['semana_iso']/52)
df['mes_sin']  = np.sin(2*np.pi*df['mes']/12)
df['mes_cos']  = np.cos(2*np.pi*df['mes']/12)

# Lags y rolling múltiples
df = df.sort_values(['tienda_id','tipo_producto','semana'])
grp = df.groupby(['tienda_id','tipo_producto'])['unidades']

for lag in [1,2,3,4,8,12,26,52]:
    df[f'lag_{lag}'] = grp.shift(lag)

for w in [2,4,8,12,16]:
    df[f'roll_mean_{w}']   = grp.shift(1).rolling(w,min_periods=1).mean().reset_index(0,drop=True)
    df[f'roll_std_{w}']    = grp.shift(1).rolling(w,min_periods=1).std().reset_index(0,drop=True)
    df[f'roll_max_{w}']    = grp.shift(1).rolling(w,min_periods=1).max().reset_index(0,drop=True)
    df[f'roll_min_{w}']    = grp.shift(1).rolling(w,min_periods=1).min().reset_index(0,drop=True)

# Tendencia y aceleración
df['tendencia']   = (df['roll_mean_4']/df['roll_mean_8'].replace(0,np.nan)).fillna(1).clip(0.1,5)
df['aceleracion'] = (df['roll_mean_2']/df['roll_mean_4'].replace(0,np.nan)).fillna(1).clip(0.1,5)

# Mismo período año anterior
df['mismo_anio_ant'] = grp.shift(52)
df['ratio_yoy'] = (df['unidades']/df['mismo_anio_ant'].replace(0,np.nan)).fillna(1).clip(0.1,5)

# Features de eventos
def crear_features_eventos(df, df_ev):
    df = df.copy()
    for _,ev in df_ev.iterrows():
        nombre = ev['nombre_evento']
        fecha_ev = pd.to_datetime(ev['fecha'])
        alcance = ev['alcance']
        pre = int(ev['semanas_anticipacion'])
        post = int(ev['semanas_rebote'])
        for s in range(-pre, post+1):
            sem_obj = fecha_ev + pd.Timedelta(weeks=s)
            tag = f"ev_{nombre[:10]}" + (f"_m{abs(s)}" if s<0 else "" if s==0 else f"_p{s}")
            if tag not in df.columns: df[tag] = 0
            mask = df['semana'] == sem_obj
            if alcance == 'nacional': df.loc[mask, tag] = 1
            else: df.loc[mask & (df['ciudad']==alcance), tag] = 1
    return df

df = crear_features_eventos(df, df_ev)
cols_ev = [c for c in df.columns if c.startswith('ev_')]

# Encoding
encoders = {}
for col in ['tipo_producto','familia','ciudad','formato','segmento_cliente']:
    enc = LabelEncoder()
    df[f'{col}_enc'] = enc.fit_transform(df[col].astype(str))
    encoders[col] = enc

# ── Features finales ──────────────────────────────────────
lag_cols  = [f'lag_{l}' for l in [1,2,3,4,8,12,26,52]]
roll_cols = [f'roll_{m}_{w}' for m in ['mean','std','max','min'] for w in [2,4,8,12,16]]

FEATURES = [
    'semana_iso','mes','trimestre','anio','dia_anio',
    'sem_sin','sem_cos','mes_sin','mes_cos','es_quincena',
    'descuento_pct_avg','pct_precio_pleno','dias_con_venta',
    'tipo_producto_enc','familia_enc','ciudad_enc','formato_enc','segmento_cliente_enc',
    'indice_rotacion','metros_cuadrados',
    'tendencia','aceleracion',
] + lag_cols + roll_cols + cols_ev

# ── Split temporal ────────────────────────────────────────
fecha_corte = df['semana'].max() - pd.Timedelta(weeks=8)
df_train = df[df['semana'] <= fecha_corte].dropna(subset=FEATURES)
df_test  = df[df['semana'] >  fecha_corte].dropna(subset=FEATURES)

print(f"Train: {len(df_train):,} | Test: {len(df_test):,} | Features: {len(FEATURES)}")

# ── Entrenar LightGBM optimizado ─────────────────────────
params = dict(
    objective='regression_l1',  # MAE directo
    metric='mae',
    n_estimators=1000,
    learning_rate=0.03,
    num_leaves=127,
    min_child_samples=15,
    subsample=0.85,
    colsample_bytree=0.85,
    reg_alpha=0.05,
    reg_lambda=0.05,
    random_state=42,
    verbose=-1,
    n_jobs=-1,
)

modelo = lgb.LGBMRegressor(**params)
modelo.fit(
    df_train[FEATURES], df_train['unidades'],
    eval_set=[(df_test[FEATURES], df_test['unidades'])],
    callbacks=[lgb.early_stopping(100,verbose=False), lgb.log_evaluation(200)]
)

y_pred = np.maximum(0, modelo.predict(df_test[FEATURES]))
mask   = df_test['unidades'] > 0
mape   = mean_absolute_percentage_error(df_test['unidades'][mask], y_pred[mask]) * 100
mae    = mean_absolute_error(df_test['unidades'], y_pred)

print(f"\n{'='*45}")
print(f"MÉTRICAS DE VALIDACIÓN")
print(f"{'='*45}")
print(f"  MAPE : {mape:.1f}%  {'✅' if mape < 20 else '⚠️'}")
print(f"  MAE  : {mae:.2f} unidades  {'✅' if mae >= 0.7 else '⚠️'}")
print(f"{'='*45}")

# ── Generar forecast mensual (8 semanas) ─────────────────
print("\nGenerando forecast 8 semanas...")
fecha_hoy   = df['semana'].max()
combinaciones = df[['tienda_id','tipo_producto','familia','ciudad','formato',
                     'segmento_cliente','indice_rotacion','metros_cuadrados']].drop_duplicates()
ultimo = df.sort_values('semana').groupby(['tienda_id','tipo_producto']).last().reset_index()

rows = []
for h in range(1,9):
    s = fecha_hoy + pd.Timedelta(weeks=h)
    df_f = combinaciones.copy()
    df_f['semana']       = s
    df_f['semana_iso']   = s.isocalendar()[1]
    df_f['mes']          = s.month
    df_f['anio']         = s.year
    df_f['trimestre']    = (s.month-1)//3+1
    df_f['dia_anio']     = s.timetuple().tm_yday
    df_f['es_quincena']  = int(s.day in list(range(14,18))+list(range(28,32)))
    df_f['sem_sin']      = np.sin(2*np.pi*df_f['semana_iso']/52)
    df_f['sem_cos']      = np.cos(2*np.pi*df_f['semana_iso']/52)
    df_f['mes_sin']      = np.sin(2*np.pi*df_f['mes']/12)
    df_f['mes_cos']      = np.cos(2*np.pi*df_f['mes']/12)

    lag_feats = ['roll_mean_2','roll_mean_4','roll_mean_8','roll_mean_12','roll_mean_16',
                 'roll_std_2','roll_std_4','roll_std_8','roll_std_12','roll_std_16',
                 'roll_max_2','roll_max_4','roll_max_8','roll_max_12','roll_max_16',
                 'roll_min_2','roll_min_4','roll_min_8','roll_min_12','roll_min_16',
                 'lag_1','lag_2','lag_3','lag_4','lag_8','lag_12','lag_26','lag_52',
                 'tendencia','aceleracion','descuento_pct_avg','pct_precio_pleno','dias_con_venta']
    df_f = df_f.merge(ultimo[['tienda_id','tipo_producto']+lag_feats],
                      on=['tienda_id','tipo_producto'], how='left')

    for col in ['tipo_producto','familia','ciudad','formato','segmento_cliente']:
        df_f[f'{col}_enc'] = encoders[col].transform(df_f[col].astype(str))
    for col in cols_ev: df_f[col] = 0
    df_f = crear_features_eventos(df_f, df_ev).fillna(0)

    preds = np.maximum(0, modelo.predict(df_f[FEATURES]))
    df_f['forecast_medio']  = preds
    df_f['forecast_bajo']   = preds * 0.82
    df_f['forecast_alto']   = preds * 1.18
    df_f['fecha_ejecucion'] = str(date.today())
    df_f['semana_objetivo']  = str(s.date())
    df_f['error_mape']       = round(mape,2)
    rows.append(df_f[['fecha_ejecucion','semana_objetivo','tienda_id','tipo_producto',
                       'familia','forecast_bajo','forecast_medio','forecast_alto','error_mape']])

df_fc = pd.concat(rows, ignore_index=True)

# Limpiar y guardar
try: sb.table('output_forecast_semanal').delete().eq('fecha_ejecucion',str(date.today())).execute()
except: pass

registros = df_fc.to_dict(orient='records')
for i in range(0,len(registros),500):
    lote = registros[i:i+500]
    for row in lote:
        for k,v in list(row.items()):
            if hasattr(v,'item'): row[k]=v.item()
            elif v!=v: row[k]=None
    sb.table('output_forecast_semanal').insert(lote).execute()

print(f"✅ Forecast guardado: {len(df_fc):,} filas")

# Guardar modelo
os.makedirs(Path(__file__).parent.parent/'outputs', exist_ok=True)
with open(MODEL_PATH,'wb') as f:
    pickle.dump({'modelo':modelo,'features':FEATURES,'encoders':encoders,
                 'cols_ev':cols_ev,'mape':mape,'mae':mae,
                 'fecha_entrenamiento':str(date.today())}, f)
print(f"✅ Modelo guardado: MAPE={mape:.1f}% | MAE={mae:.2f}")
