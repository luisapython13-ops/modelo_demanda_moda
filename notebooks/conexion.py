"""
conexion.py — Conexión a Supabase via API REST
Funciona en Codespaces sin conexión TCP directa
"""
import os
from pathlib import Path
from dotenv import load_dotenv

def get_supabase_client():
    from supabase import create_client
    root = Path(__file__).resolve().parent.parent
    load_dotenv(root / '.env')
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_ANON_KEY')
    if not url or not key:
        raise ValueError("Faltan SUPABASE_URL o SUPABASE_ANON_KEY en .env\nEncontralas en: Supabase -> Project Settings -> API")
    client = create_client(url, key)
    print(f"Conectado a Supabase: {url}")
    return client

def get_datos_dir():
    for p in [Path(__file__).resolve().parent.parent/'datos_excel',
              Path('../datos_excel'), Path('datos_excel')]:
        if p.exists(): return p
    raise FileNotFoundError("No se encontro la carpeta datos_excel")

def supabase_to_df(client, tabla, columnas='*', limite=200000):
    import pandas as pd
    todos, offset, batch = [], 0, 1000
    while offset < limite:
        r = client.table(tabla).select(columnas).range(offset, offset+batch-1).execute()
        if not r.data: break
        todos.extend(r.data)
        if len(r.data) < batch: break
        offset += batch
    return pd.DataFrame(todos)

def df_to_supabase(client, df, tabla, limpiar_hoy=False):
    from datetime import date
    if limpiar_hoy:
        try: client.table(tabla).delete().eq('fecha_ejecucion', str(date.today())).execute()
        except: pass
    registros = df.to_dict(orient='records')
    total = len(registros)
    for i in range(0, total, 500):
        lote = registros[i:i+500]
        for row in lote:
            for k,v in row.items():
                if hasattr(v,'item'): row[k]=v.item()
                elif hasattr(v,'isoformat'): row[k]=v.isoformat()
                elif v!=v: row[k]=None
        client.table(tabla).insert(lote).execute()
        print(f"  {min(i+500,total)}/{total} filas -> {tabla}")
    print(f"OK {total} filas en {tabla}")
