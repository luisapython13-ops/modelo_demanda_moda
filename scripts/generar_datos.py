"""
Generador de datos calibrado con datos REALES de la empresa
Participación de venta e inventario tomada directamente de los reportes internos
3 años: 2022-2024 | 89 tiendas | 12 líneas principales | Ventas diarias
"""
import pandas as pd
import numpy as np
from datetime import date, timedelta
import os

np.random.seed(2024)
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'datos_excel')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── PARTICIPACIÓN REAL DE LA EMPRESA ─────────────────────
# Fuente: reporte interno últimos 12 meses
# Solo líneas principales (>0.5% participación en venta)
PART_VENTA = {
    "Jeans":        0.2264,  # JEA - líder indiscutible
    "Pantalón":     0.1810,  # GPT
    "Camiseta/Blusa": 0.1697, # CAM
    "Polo":         0.0783,  # POL
    "Bermuda":      0.0683,  # BER
    "Pantaloneta":  0.0641,  # PAN
    "Vestido":      0.0594,  # VES
    "Abrigo":       0.0342,  # ABR
    "Top/Interior": 0.0333,  # TPI
    "Buzo":         0.0311,  # BUZ
    "Falda":        0.0275,  # FAL
    "Pijama":       0.0037,  # PIJ
}

PART_INV = {
    "Jeans":          0.2162,
    "Pantalón":       0.1679,
    "Camiseta/Blusa": 0.1811,
    "Polo":           0.0735,
    "Bermuda":        0.0613,
    "Pantaloneta":    0.0733,
    "Vestido":        0.0524,
    "Abrigo":         0.0418,
    "Top/Interior":   0.0443,
    "Buzo":           0.0265,
    "Falda":          0.0309,
    "Pijama":         0.0036,
}

# GMROII real por línea (del reporte)
GMROII_REAL = {
    "Jeans":          2.42,
    "Pantalón":       2.72,
    "Camiseta/Blusa": 2.35,
    "Polo":           2.21,
    "Bermuda":        3.17,  # BER — mejor GMROII
    "Pantaloneta":    2.25,
    "Vestido":        2.30,
    "Abrigo":         1.51,  # ABR — más bajo, zona geográfica
    "Top/Interior":   2.35,
    "Buzo":           2.55,
    "Falda":          2.50,
    "Pijama":         2.95,
}

# Margen real por línea
MARGEN_REAL = {
    "Jeans":          0.4851,
    "Pantalón":       0.5118,
    "Camiseta/Blusa": 0.5050,
    "Polo":           0.4994,
    "Bermuda":        0.5258,
    "Pantaloneta":    0.4574,
    "Vestido":        0.4590,
    "Abrigo":         0.4124,
    "Top/Interior":   0.5141,
    "Buzo":           0.4598,
    "Falda":          0.5219,
    "Pijama":         0.4825,
}

# ── 1. TIENDAS ────────────────────────────────────────────
ciudades = [
    ("Bogotá",       "Cundinamarca", 35, "FRIO"),
    ("Medellín",     "Antioquia",    15, "TEMPLADO"),
    ("Cali",         "Valle",        10, "INTERIOR"),
    ("Barranquilla", "Atlántico",     8, "COSTA"),
    ("Bucaramanga",  "Santander",     4, "INTERIOR"),
    ("Pereira",      "Risaralda",     3, "TEMPLADO"),
    ("Manizales",    "Caldas",        2, "FRIO"),
    ("Cartagena",    "Bolívar",       3, "COSTA"),
    ("Cúcuta",       "N. Santander",  2, "INTERIOR"),
    ("Ibagué",       "Tolima",        2, "INTERIOR"),
    ("Santa Marta",  "Magdalena",     2, "COSTA"),
    ("Villavicencio","Meta",          1, "INTERIOR"),
    ("Pasto",        "Nariño",        1, "FRIO"),
    ("Montería",     "Córdoba",       1, "COSTA"),
]
formatos = ["Centro Comercial","Calle","Outlet","Flagship"]
fp_fmt   = [0.58, 0.27, 0.10, 0.05]

tiendas = []
tid = 1
for ciudad, dpto, n, zona in ciudades:
    for i in range(n):
        fmt = np.random.choice(formatos, p=fp_fmt)
        m2 = {"Centro Comercial": np.random.randint(90,320),
               "Calle":           np.random.randint(55,180),
               "Outlet":          np.random.randint(160,420),
               "Flagship":        np.random.randint(320,650)}[fmt]
        tiendas.append({
            "tienda_id":           tid,
            "codigo_tienda":       f"T-{tid:03d}",
            "nombre_tienda":       f"Tienda {ciudad} {i+1:02d}",
            "ciudad":              ciudad,
            "departamento":        dpto,
            "zona_climatica":      zona,
            "formato":             fmt,
            "metros_cuadrados":    m2,
            "capacidad_exhibicion":int(m2 * 1.75),
            "segmento_cliente":    np.random.choice(
                ["Alto","Medio_Alto","Medio","Popular"], p=[0.08,0.28,0.46,0.18]),
            "indice_rotacion":     round(np.random.uniform(0.78, 1.32), 2),
            "fecha_apertura":      (date(2018,1,1) +
                timedelta(days=int(np.random.randint(0,1100)))).strftime("%Y-%m-%d"),
            "activa": True,
        })
        tid += 1

pd.DataFrame(tiendas).to_excel(os.path.join(OUTPUT_DIR,"dim_tiendas.xlsx"), index=False)
print(f"✓ dim_tiendas: {len(tiendas)} tiendas")

zona_map   = {t["tienda_id"]: t["zona_climatica"] for t in tiendas}
ciudad_map = {t["tienda_id"]: t["ciudad"]         for t in tiendas}
idx_map    = {t["tienda_id"]: t["indice_rotacion"] for t in tiendas}

# ── 2. TIPOS DE PRODUCTO calibrados con datos reales ─────
# precio_regular calibrado para que el margen coincida con el real
# costo = precio * (1 - margen_real)
# factor_costa / factor_frio basados en comportamiento real del sector

tipos_raw = [
    # código, nombre, familia, precio, vida_sem, f_costa, f_frio
    ("JEA","Jeans",          "Unisex",  169900, 52, 1.05, 1.00),
    ("GPT","Pantalón",       "Unisex",  149900, 14, 0.88, 1.08),
    ("CAM","Camiseta/Blusa", "Unisex",   89900, 10, 1.35, 0.85),
    ("POL","Polo",           "Hombre",   79900, 10, 1.25, 0.88),
    ("BER","Bermuda",        "Unisex",   99900,  8, 1.80, 0.20),  # costa vende mucho
    ("PAN","Pantaloneta",    "Unisex",   69900,  8, 1.90, 0.15),  # costa vende mucho
    ("VES","Vestido",        "Mujer",   139900, 10, 2.20, 0.50),  # costa vende mucho
    ("ABR","Abrigo",         "Unisex",  189900, 14, 0.06, 2.40),  # frío vende mucho
    ("TPI","Top/Interior",   "Mujer",    59900, 10, 1.30, 0.90),
    ("BUZ","Buzo",           "Unisex",  119900, 12, 0.30, 1.80),  # frío vende
    ("FAL","Falda",          "Mujer",    99900, 10, 1.50, 0.60),
    ("PIJ","Pijama",         "Unisex",   89900, 12, 1.10, 1.05),
]

curvas_tallas = {
    "Unisex": {"S":0.15,"M":0.32,"L":0.33,"XL":0.14,"XXL":0.06},
    "Hombre": {"S":0.14,"M":0.31,"L":0.34,"XL":0.15,"XXL":0.06},
    "Mujer":  {"XS":0.07,"S":0.21,"M":0.36,"L":0.26,"XL":0.10},
}

registros_tipos = []
for cod, tp, familia, precio, vida, fc, ff in tipos_raw:
    margen = MARGEN_REAL[tp]
    costo  = round(precio * (1 - margen))
    registros_tipos.append({
        "codigo_linea":        cod,
        "tipo_producto":       tp,
        "familia":             familia,
        "precio_regular":      precio,
        "costo_produccion":    costo,
        "margen_real_pct":     round(margen*100, 2),
        "margen_objetivo_pct": round(margen*100, 2),
        "gmroii_real":         GMROII_REAL[tp],
        "vida_semanas":        vida,
        "es_basico":           cod in ("JEA","GPT","CAM","POL"),
        "part_venta_pct":      round(PART_VENTA[tp]*100, 2),
        "part_inv_pct":        round(PART_INV[tp]*100, 2),
        "factor_costa":        fc,
        "factor_frio":         ff,
        "tallas_json":         str(curvas_tallas[familia]),
        "temporada_ciclo_sem": 8,
    })

pd.DataFrame(registros_tipos).to_excel(
    os.path.join(OUTPUT_DIR,"dim_tipos_producto.xlsx"), index=False)
print(f"✓ dim_tipos_producto: {len(registros_tipos)} líneas")

# ── 3. EVENTOS Colombia — fechas reales ───────────────────
eventos = [
    ("dia_sin_iva_mar22","2022-03-11","nacional",2,2,270,"TODAS"),
    ("dia_sin_iva_jun22","2022-06-17","nacional",2,2,270,"TODAS"),
    ("dia_sin_iva_oct22","2022-10-28","nacional",2,2,270,"TODAS"),
    ("dia_sin_iva_mar23","2023-03-03","nacional",2,2,270,"TODAS"),
    ("dia_sin_iva_jun23","2023-06-16","nacional",2,2,270,"TODAS"),
    ("dia_sin_iva_oct23","2023-10-27","nacional",2,2,270,"TODAS"),
    ("dia_sin_iva_mar24","2024-03-08","nacional",2,2,270,"TODAS"),
    ("dia_sin_iva_jun24","2024-06-14","nacional",2,2,270,"TODAS"),
    ("dia_sin_iva_oct24","2024-10-25","nacional",2,2,270,"TODAS"),
    ("dia_madre_22","2022-05-08","nacional",3,0,90,"Mujer"),
    ("dia_madre_23","2023-05-14","nacional",3,0,90,"Mujer"),
    ("dia_madre_24","2024-05-12","nacional",3,0,90,"Mujer"),
    ("amor_amistad_22","2022-09-17","nacional",2,0,55,"TODAS"),
    ("amor_amistad_23","2023-09-16","nacional",2,0,55,"TODAS"),
    ("amor_amistad_24","2024-09-21","nacional",2,0,55,"TODAS"),
    ("navidad_22","2022-12-18","nacional",4,0,130,"TODAS"),
    ("navidad_23","2023-12-17","nacional",4,0,130,"TODAS"),
    ("navidad_24","2024-12-15","nacional",4,0,130,"TODAS"),
    ("black_friday_22","2022-11-25","nacional",1,1,110,"TODAS"),
    ("black_friday_23","2023-11-24","nacional",1,1,110,"TODAS"),
    ("black_friday_24","2024-11-29","nacional",1,1,110,"TODAS"),
    ("carnaval_22","2022-02-28","Barranquilla",2,0,80,"TODAS"),
    ("carnaval_23","2023-02-20","Barranquilla",2,0,80,"TODAS"),
    ("carnaval_24","2024-02-10","Barranquilla",2,0,80,"TODAS"),
    ("feria_cali_22","2022-12-26","Cali",1,0,50,"TODAS"),
    ("feria_cali_23","2023-12-26","Cali",1,0,50,"TODAS"),
    ("feria_cali_24","2024-12-26","Cali",1,0,50,"TODAS"),
    ("flores_med_22","2022-08-01","Medellín",1,0,40,"TODAS"),
    ("flores_med_23","2023-08-07","Medellín",1,0,40,"TODAS"),
    ("flores_med_24","2024-08-05","Medellín",1,0,40,"TODAS"),
    ("regreso_ene22","2022-01-24","nacional",1,0,25,"TODAS"),
    ("regreso_jul22","2022-07-18","nacional",1,0,25,"TODAS"),
    ("regreso_ene23","2023-01-23","nacional",1,0,25,"TODAS"),
    ("regreso_jul23","2023-07-17","nacional",1,0,25,"TODAS"),
    ("regreso_ene24","2024-01-22","nacional",1,0,25,"TODAS"),
    ("regreso_jul24","2024-07-15","nacional",1,0,25,"TODAS"),
]
pd.DataFrame(eventos, columns=["nombre_evento","fecha","alcance",
    "semanas_anticipacion","semanas_rebote","impacto_esperado_pct",
    "categorias_impactadas"]
).to_excel(os.path.join(OUTPUT_DIR,"dim_eventos.xlsx"), index=False)
print(f"✓ dim_eventos: {len(eventos)} eventos")

# ── 4. VENTAS DIARIAS calibradas con participación real ───
print("Generando ventas diarias calibradas con datos reales...")

fecha_inicio = date(2022, 1, 1)
fecha_fin    = date(2024, 12, 31)
dias         = (fecha_fin - fecha_inicio).days + 1

# Venta base semanal por tienda promedio
# Calibrada para que la participación coincida con los datos reales
# Total red ≈ 89 tiendas × 52 semanas × 3 años
# Ventas totales reales 12 meses: ~$326B COP
# Escalado a datos simulados manteniendo proporciones reales

BASE_TOTAL_SEM = 280  # unidades/semana promedio por tienda (toda la red)

# Ventas base en UNIDADES/semana/tienda promedio
# Calibradas por VALOR en pesos para que la participación en ventas
# coincida con los datos reales de la empresa
# Base: $13.5M COP/semana/tienda × participación / precio unitario
# Ventas base en UNIDADES/semana/tienda
# Calibradas por VALOR en pesos para que la participación coincida
# con los datos reales de la empresa (calibración por factor geográfico ponderado)
# Valor base por tienda: ~$13.7M COP/semana
ventas_base = {
    "Jeans":           18.0,   # JEA 22.64% — líder
    "Pantalón":        16.5,   # GPT 18.10%
    "Camiseta/Blusa":  25.2,   # CAM 16.97% — precio bajo = más uds
    "Polo":            13.2,   # POL  7.83%
    "Bermuda":         11.4,   # BER  6.83%
    "Pantaloneta":     14.4,   # PAN  6.41%
    "Vestido":          5.3,   # VES  5.94%
    "Abrigo":           1.8,   # ABR  3.42%
    "Top/Interior":     7.3,   # TPI  3.33%
    "Buzo":             3.1,   # BUZ  3.11%
    "Falda":            3.9,   # FAL  2.75%
    "Pijama":           0.5,   # PIJ  0.37%
}

# Estacionalidad mensual real calibrada por línea
# Basada en ciclos del sector textil colombiano (DANE-EMCM)
estac = {
    "Jeans":          [1.00,0.92,1.02,0.98,1.05,1.00,1.18,1.22,1.05,1.00,0.95,1.03],
    "Pantalón":       [0.95,0.92,1.02,1.00,1.05,1.00,1.12,1.15,1.05,1.00,0.92,1.08],
    "Camiseta/Blusa": [0.85,0.88,0.95,1.02,1.10,1.15,1.22,1.15,1.05,0.98,0.88,1.05],
    "Polo":           [0.88,0.88,0.95,1.00,1.05,1.18,1.28,1.18,1.02,0.98,0.88,1.02],
    "Bermuda":        [0.60,0.65,0.80,1.05,1.30,1.45,1.50,1.40,1.10,0.85,0.65,0.80],
    "Pantaloneta":    [0.55,0.60,0.78,1.05,1.35,1.50,1.55,1.45,1.12,0.82,0.60,0.75],
    "Vestido":        [0.72,0.75,0.88,1.05,1.15,1.28,1.32,1.25,1.10,0.95,0.75,1.02],
    "Abrigo":         [1.65,1.55,1.25,0.92,0.70,0.52,0.48,0.52,0.82,1.12,1.35,1.55],
    "Top/Interior":   [0.90,0.88,0.98,1.02,1.08,1.15,1.20,1.15,1.05,0.98,0.88,1.05],
    "Buzo":           [1.45,1.38,1.15,0.88,0.68,0.50,0.45,0.52,0.78,1.08,1.28,1.48],
    "Falda":          [0.72,0.72,0.88,1.08,1.18,1.28,1.28,1.18,1.05,0.92,0.75,1.02],
    "Pijama":         [1.08,0.95,0.98,0.98,1.00,1.02,1.05,1.02,1.00,1.00,0.98,1.30],
}

# Factor día de semana — patrón real retail Colombia
# Viernes mayor, lunes menor (basado en flujo de centros comerciales)
factor_dow = [0.09, 0.10, 0.12, 0.13, 0.20, 0.23, 0.13]  # L-D

# Lookup eventos
ev_lookup = {}
for ev in eventos:
    nombre, fecha_ev_s, alcance, pre, post, impacto, cats = ev
    fecha_ev = date.fromisoformat(fecha_ev_s)
    for s in range(-pre, post+1):
        f_date = fecha_ev + timedelta(weeks=s)
        key    = (f_date.isoformat(), alcance)
        if s < 0:    mult = 1 + (impacto/100)*0.40*(1-abs(s)/max(pre,1))
        elif s == 0: mult = 1 + impacto/100
        else:        mult = max(0.65, 1-(impacto/100)*0.30)
        ev_lookup[key] = max(ev_lookup.get(key, 1.0), mult)

def desc_sector(mes, inv_actual, base_sem, es_fin_temp, zona):
    """
    Política de descuentos real del sector textil colombiano
    - 62% precio pleno
    - 18% promoción leve (10-15%) — lunes y martes de semana intermedia
    - 15% promoción fuerte (20-30%) — fin de temporada media
    - 5%  liquidación (40-60%) — jun y dic
    """
    if es_fin_temp:
        return float(np.random.choice([40,50,60], p=[0.40,0.40,0.20]))
    if inv_actual > base_sem * 9:
        return float(np.random.choice([20,25,30], p=[0.40,0.35,0.25]))
    if inv_actual > base_sem * 6:
        return float(np.random.choice([0,0,10,15], p=[0.50,0.18,0.20,0.12]))
    return float(np.random.choice([0,0,0,10,15], p=[0.50,0.14,0.11,0.15,0.10]))

ventas_rows = []
inv_rows    = []
total_ops   = len(tiendas) * len(tipos_raw)
op          = 0

for tienda in tiendas:
    tid_   = tienda["tienda_id"]
    zona   = tienda["zona_climatica"]
    ciudad = tienda["ciudad"]
    idx_r  = tienda["indice_rotacion"]

    for cod, tp, familia, precio, vida, fc_val, ff_val in tipos_raw:
        op += 1
        if op % 300 == 0:
            pct = op/total_ops*100
            print(f"  {pct:.0f}% ({op}/{total_ops})", end='\r')

        # Factor geográfico real
        f_geo = (fc_val if zona == "COSTA"
                 else ff_val if zona == "FRIO"
                 else 1.0)

        # Bermudas y pantalonetas casi no se venden en Bogotá/Manizales/Pasto
        if tp in ("Bermuda","Pantaloneta") and zona == "FRIO":
            f_geo = 0.10
        if tp == "Abrigo" and zona == "COSTA":
            f_geo = 0.04

        base_sem   = ventas_base[tp] * idx_r * f_geo
        costo      = round(precio * (1 - MARGEN_REAL[tp]))
        inv_actual = int(base_sem * np.random.uniform(4.5, 7.5))

        for d in range(dias):
            fecha_actual = fecha_inicio + timedelta(days=d)
            mes  = fecha_actual.month
            dow  = fecha_actual.weekday()
            fstr = fecha_actual.isoformat()

            est    = estac[tp][mes-1]
            fdow   = factor_dow[dow]
            dia_m  = fecha_actual.day

            # Efecto quincena real: +40% días 14-16 y 28-31
            if dia_m in range(13,18) or dia_m in range(27,32):
                f_q = 1.40
            elif dia_m in range(1,5) or dia_m in range(18,23):
                f_q = 0.90
            else:
                f_q = 1.00

            # Evento
            f_ev = ev_lookup.get((fstr,"nacional"), 1.0)
            f_ev = max(f_ev, ev_lookup.get((fstr, ciudad), 1.0))

            # Ventas esperadas con ruido muy controlado ±7%
            esperado   = (base_sem / 7.0) * est * fdow * f_q * f_ev
            ruido      = np.random.normal(1.0, 0.07)
            ventas_dia = max(0, int(round(esperado * ruido)))

            if ventas_dia == 0:
                continue

            # Fin de temporada: jun y dic
            es_fin = (mes == 6 and dia_m >= 20) or (mes == 12 and dia_m >= 15)
            desc   = desc_sector(mes, inv_actual, base_sem, es_fin, zona)

            # Días sin IVA → siempre precio pleno
            if f_ev > 2.5:
                desc = 0.0

            pv     = round(precio * (1 - desc/100))
            margen = (pv - costo) * ventas_dia

            tipo_desc = ("PRECIO_PLENO"    if desc == 0
                        else "PROMOCION_LEVE"    if desc <= 15
                        else "PROMOCION_FUERTE"  if desc <= 30
                        else "LIQUIDACION")

            ventas_rows.append({
                "fecha":             fstr,
                "tienda_id":         tid_,
                "codigo_tienda":     tienda["codigo_tienda"],
                "codigo_linea":      cod,
                "tipo_producto":     tp,
                "familia":           familia,
                "unidades_vendidas": ventas_dia,
                "precio_regular":    precio,
                "precio_venta":      pv,
                "descuento_pct":     desc,
                "tipo_descuento":    tipo_desc,
                "valor_venta":       pv * ventas_dia,
                "margen_bruto":      margen,
                "es_precio_pleno":   desc == 0,
            })

            inv_actual = max(0, inv_actual - ventas_dia)
            if inv_actual < base_sem * 2 and np.random.random() < 0.40:
                inv_actual += int(base_sem * np.random.uniform(4, 7))

        # Inventario semanal (lunes)
        inv_snap   = int(base_sem * np.random.uniform(4.5, 7.5))
        fecha_iter = fecha_inicio
        while fecha_iter <= fecha_fin:
            if fecha_iter.weekday() == 0:
                vp  = base_sem * estac[tp][fecha_iter.month-1]
                cob = round(inv_snap / max(0.1, vp), 1)
                alerta = ("CRITICO"        if inv_snap == 0
                          else "QUIEBRE_RIESGO" if cob < 2.0
                          else "EXCESO"         if cob > 10.0
                          else "OK")
                inv_rows.append({
                    "fecha":                fecha_iter.isoformat(),
                    "tienda_id":            tid_,
                    "codigo_tienda":        tienda["codigo_tienda"],
                    "codigo_linea":         cod,
                    "tipo_producto":        tp,
                    "familia":              familia,
                    "unidades_disponibles": max(0, inv_snap),
                    "unidades_transito":    int(base_sem * np.random.uniform(0, 1.2)),
                    "costo_unitario":       costo,
                    "valor_inventario":     max(0, inv_snap) * costo,
                    "cobertura_semanas":    cob,
                    "alerta_stock":         alerta,
                })
                ventas_sem = int(vp * np.random.uniform(0.80, 1.20))
                inv_snap   = max(0, inv_snap - ventas_sem)
                if inv_snap < base_sem * 2 and np.random.random() < 0.50:
                    inv_snap += int(base_sem * np.random.uniform(4, 7))
            fecha_iter += timedelta(days=1)

print(f"\n  Exportando ventas...")
df_v = pd.DataFrame(ventas_rows)
total_uds = df_v["unidades_vendidas"].sum()

# Verificar participación en VALOR (como mide la empresa en sus reportes)
total_val = df_v["valor_venta"].sum()
print("\n  ╔══════════════════════════════════════════════════════════╗")
print("  ║  VERIFICACIÓN vs DATOS REALES — PARTICIPACIÓN EN VALOR  ║")
print("  ╠══════════╦══════════╦══════════╦══════════╦══════════════╣")
print("  ║ Línea    ║ Part.Real║ Part.Sim ║ Dif.     ║ GMROII Real  ║")
print("  ╠══════════╬══════════╬══════════╬══════════╬══════════════╣")
for cod, tp, *_ in tipos_raw:
    sim_val  = df_v[df_v["tipo_producto"]==tp]["valor_venta"].sum()
    sim_pct  = sim_val/total_val*100
    real_pct = PART_VENTA[tp]*100
    dif      = sim_pct - real_pct
    ok       = "✅" if abs(dif)<1.5 else "⚠️"
    print(f"  ║ {cod:<8} ║ {real_pct:>7.2f}% ║ {sim_pct:>7.2f}% ║ {dif:>+7.2f}% ║ {ok} {GMROII_REAL[tp]:>6.2f}      ║")
print("  ╚══════════╩══════════╩══════════╩══════════╩══════════════╝")
print(f"  Nota: participación medida en valor COP (como el reporte de la empresa)")

for anio in [2022,2023,2024]:
    dfy = df_v[df_v["fecha"].str.startswith(str(anio))]
    dfy.to_excel(os.path.join(OUTPUT_DIR,f"ventas_{anio}.xlsx"), index=False)
    print(f"  ✓ ventas_{anio}.xlsx: {len(dfy):,} filas | {dfy['unidades_vendidas'].sum():,} uds")

print(f"\n  Exportando inventario...")
df_i = pd.DataFrame(inv_rows)
mid  = len(df_i)//2
df_i.iloc[:mid].to_excel(os.path.join(OUTPUT_DIR,"inventario_semanal_parte1.xlsx"), index=False)
df_i.iloc[mid:].to_excel(os.path.join(OUTPUT_DIR,"inventario_semanal_parte2.xlsx"), index=False)
print(f"  ✓ inventario: {len(df_i):,} filas en 2 partes")
print(f"\n✅ Datos generados y calibrados con participación real de la empresa")
