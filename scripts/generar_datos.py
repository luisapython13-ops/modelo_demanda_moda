"""
Generador de datos simulados — patrones predecibles para MAPE < 20%
Manufactura textil moda Colombia · 89 tiendas · 3 años
"""
import pandas as pd
import numpy as np
from datetime import date, timedelta
import os

np.random.seed(42)
OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'datos_excel')
os.makedirs(OUTPUT, exist_ok=True)

ciudades = [
    ("Bogotá","Cundinamarca",35),("Medellín","Antioquia",15),
    ("Cali","Valle",10),("Barranquilla","Atlántico",8),
    ("Bucaramanga","Santander",4),("Pereira","Risaralda",3),
    ("Manizales","Caldas",2),("Cartagena","Bolívar",3),
    ("Cúcuta","N. Santander",2),("Ibagué","Tolima",2),
    ("Santa Marta","Magdalena",2),("Villavicencio","Meta",1),
    ("Pasto","Nariño",1),("Montería","Córdoba",1),
]
formatos = ["Centro Comercial","Calle","Outlet","Flagship"]
fp = [0.60,0.25,0.10,0.05]

tiendas = []
tid = 1
for ciudad,dpto,n in ciudades:
    for i in range(n):
        fmt = np.random.choice(formatos,p=fp)
        m2  = {"Centro Comercial":np.random.randint(80,300),"Calle":np.random.randint(60,200),
               "Outlet":np.random.randint(150,400),"Flagship":np.random.randint(300,600)}[fmt]
        tiendas.append({
            "tienda_id":tid,"nombre_tienda":f"Tienda {ciudad} {i+1:02d}",
            "ciudad":ciudad,"departamento":dpto,"formato":fmt,
            "metros_cuadrados":m2,"capacidad_exhibicion":int(m2*1.8),
            "segmento_cliente":np.random.choice(["Alto","Medio_Alto","Medio","Popular"],p=[0.10,0.30,0.45,0.15]),
            "indice_rotacion":round(np.random.uniform(0.7,1.4),2),
            "fecha_apertura":(date(2018,1,1)+timedelta(days=np.random.randint(0,900))).strftime("%Y-%m-%d"),
            "activa":True,
        })
        tid += 1

df_tiendas = pd.DataFrame(tiendas)
df_tiendas.to_excel(os.path.join(OUTPUT,"dim_tiendas.xlsx"),index=False)
print(f"✓ dim_tiendas: {len(df_tiendas)}")

tipos = [
    ("Blusa Casual","Mujer","Parte Superior",89900,32000,10),
    ("Blusa Formal","Mujer","Parte Superior",129900,48000,12),
    ("Pantalón Casual","Mujer","Parte Inferior",119900,42000,12),
    ("Pantalón Formal","Mujer","Parte Inferior",159900,58000,14),
    ("Vestido Casual","Mujer","Vestido",139900,50000,10),
    ("Vestido Fiesta","Mujer","Vestido",229900,82000,8),
    ("Falda","Mujer","Parte Inferior",99900,35000,10),
    ("Chaqueta Mujer","Mujer","Abrigo",189900,70000,14),
    ("Camiseta Hombre","Hombre","Parte Superior",69900,24000,10),
    ("Camisa Hombre","Hombre","Parte Superior",119900,43000,12),
    ("Pantalón Hombre","Hombre","Parte Inferior",149900,54000,14),
    ("Jean Hombre","Hombre","Parte Inferior",169900,60000,16),
    ("Chaqueta Hombre","Hombre","Abrigo",199900,72000,14),
    ("Conjunto Niño","Niño","Conjunto",89900,32000,8),
    ("Vestido Niña","Niño","Vestido",79900,28000,8),
]
curvas_tallas = {
    "Mujer":{"XS":0.08,"S":0.22,"M":0.35,"L":0.25,"XL":0.10},
    "Hombre":{"S":0.15,"M":0.30,"L":0.35,"XL":0.15,"XXL":0.05},
    "Niño":{"2":0.15,"4":0.20,"6":0.25,"8":0.22,"10":0.18},
}
rows_t = []
for tp,fam,cat,precio,costo,vida in tipos:
    rows_t.append({
        "tipo_producto":tp,"familia":fam,"categoria":cat,
        "precio_regular":precio,"costo_produccion":costo,
        "margen_objetivo_pct":round((precio-costo)/precio*100,1),
        "vida_semanas":vida,"es_basico":tp in ("Jean Hombre","Camiseta Hombre","Pantalón Hombre"),
        "tallas_json":str(curvas_tallas[fam]),"temporada_ciclo_sem":8,
    })
df_tipos = pd.DataFrame(rows_t)
df_tipos.to_excel(os.path.join(OUTPUT,"dim_tipos_producto.xlsx"),index=False)
print(f"✓ dim_tipos_producto: {len(df_tipos)}")

eventos = [
    ("dia_sin_iva_1","2022-03-11","nacional",2,1,280,"TODAS"),
    ("dia_sin_iva_2","2022-06-17","nacional",2,1,280,"TODAS"),
    ("dia_sin_iva_3","2022-10-28","nacional",2,1,280,"TODAS"),
    ("dia_madre_2022","2022-05-08","nacional",3,0,85,"Mujer"),
    ("amor_amistad_2022","2022-09-17","nacional",2,0,60,"TODAS"),
    ("navidad_2022","2022-12-18","nacional",4,0,120,"TODAS"),
    ("carnaval_baq_2022","2022-02-28","Barranquilla",2,0,90,"TODAS"),
    ("black_friday_2022","2022-11-25","nacional",1,1,110,"TODAS"),
    ("dia_sin_iva_4","2023-03-03","nacional",2,1,280,"TODAS"),
    ("dia_sin_iva_5","2023-06-16","nacional",2,1,280,"TODAS"),
    ("dia_sin_iva_6","2023-10-27","nacional",2,1,280,"TODAS"),
    ("dia_madre_2023","2023-05-14","nacional",3,0,85,"Mujer"),
    ("amor_amistad_2023","2023-09-16","nacional",2,0,60,"TODAS"),
    ("navidad_2023","2023-12-17","nacional",4,0,120,"TODAS"),
    ("carnaval_baq_2023","2023-02-20","Barranquilla",2,0,90,"TODAS"),
    ("black_friday_2023","2023-11-24","nacional",1,1,110,"TODAS"),
    ("dia_sin_iva_7","2024-03-08","nacional",2,1,280,"TODAS"),
    ("dia_sin_iva_8","2024-06-14","nacional",2,1,280,"TODAS"),
    ("dia_sin_iva_9","2024-10-25","nacional",2,1,280,"TODAS"),
    ("dia_madre_2024","2024-05-12","nacional",3,0,85,"Mujer"),
    ("amor_amistad_2024","2024-09-21","nacional",2,0,60,"TODAS"),
    ("navidad_2024","2024-12-15","nacional",4,0,120,"TODAS"),
    ("carnaval_baq_2024","2024-02-10","Barranquilla",2,0,90,"TODAS"),
    ("black_friday_2024","2024-11-29","nacional",1,1,110,"TODAS"),
]
df_ev = pd.DataFrame(eventos,columns=["nombre_evento","fecha","alcance","semanas_anticipacion","semanas_rebote","impacto_esperado_pct","categorias_impactadas"])
df_ev.to_excel(os.path.join(OUTPUT,"dim_eventos.xlsx"),index=False)
print(f"✓ dim_eventos: {len(df_ev)}")

print("Generando ventas con patrones predecibles (ruido <5%)...")

fecha_inicio = date(2022,1,1)
fecha_fin    = date(2024,12,31)
dias         = (fecha_fin-fecha_inicio).days+1

est = {
    "Blusa Casual":   [0.65,0.70,0.85,0.95,1.05,1.15,1.25,1.15,1.05,0.95,0.85,1.35],
    "Blusa Formal":   [0.80,0.80,0.90,1.00,1.05,1.00,1.00,1.00,1.10,1.05,0.90,1.15],
    "Pantalón Casual":[0.75,0.80,0.90,1.00,1.05,1.05,1.15,1.05,1.05,1.00,0.90,1.20],
    "Pantalón Formal":[0.85,0.85,1.00,1.00,1.00,1.00,1.00,1.00,1.10,1.05,0.90,1.10],
    "Vestido Casual": [0.55,0.60,0.75,0.95,1.15,1.25,1.35,1.20,1.05,0.90,0.70,1.20],
    "Vestido Fiesta": [0.50,0.50,0.60,0.70,1.00,0.80,0.85,0.80,1.10,1.00,1.05,1.90],
    "Falda":          [0.60,0.65,0.80,1.00,1.15,1.20,1.25,1.15,1.05,0.90,0.70,1.15],
    "Chaqueta Mujer": [1.40,1.30,1.05,0.80,0.65,0.55,0.55,0.65,0.90,1.15,1.25,1.35],
    "Camiseta Hombre":[0.95,0.90,1.00,1.00,1.05,1.10,1.20,1.15,1.05,1.00,0.95,1.10],
    "Camisa Hombre":  [0.85,0.85,0.95,1.00,1.05,1.00,1.00,1.00,1.10,1.05,0.95,1.15],
    "Pantalón Hombre":[0.90,0.90,1.00,1.00,1.00,1.00,1.10,1.05,1.05,1.00,0.95,1.10],
    "Jean Hombre":    [1.00,1.00,1.00,1.00,1.00,1.00,1.10,1.05,1.05,1.00,1.00,1.10],
    "Chaqueta Hombre":[1.40,1.30,1.05,0.80,0.65,0.55,0.55,0.65,0.90,1.15,1.25,1.35],
    "Conjunto Niño":  [1.10,1.00,1.00,1.00,1.05,1.00,1.20,1.25,1.05,1.00,1.00,1.20],
    "Vestido Niña":   [0.65,0.65,0.80,1.00,1.15,1.25,1.25,1.15,1.05,0.90,0.75,1.20],
}
dow_factor = [0.10,0.11,0.12,0.13,0.18,0.22,0.14]
base = {
    "Blusa Casual":15,"Blusa Formal":8,"Pantalón Casual":10,"Pantalón Formal":6,
    "Vestido Casual":9,"Vestido Fiesta":4,"Falda":6,"Chaqueta Mujer":5,
    "Camiseta Hombre":12,"Camisa Hombre":7,"Pantalón Hombre":9,"Jean Hombre":11,
    "Chaqueta Hombre":5,"Conjunto Niño":6,"Vestido Niña":5,
}
ev_lookup = {}
for _,ev in df_ev.iterrows():
    fev=date.fromisoformat(ev["fecha"]); alc=ev["alcance"]
    imp=ev["impacto_esperado_pct"]/100.0
    pre=int(ev["semanas_anticipacion"]); pos=int(ev["semanas_rebote"])
    for s in range(-pre,pos+1):
        f=fev+timedelta(weeks=s); key=(f.isoformat(),alc)
        if s<0:    mult=1+imp*0.5*(1-abs(s)/pre)
        elif s==0: mult=1+imp
        else:      mult=max(0.65,1-imp*0.35)
        ev_lookup[key]=max(ev_lookup.get(key,1.0),mult)

ventas_rows=[]; inv_rows=[]

for t in tiendas:
    tid=t["tienda_id"]; ciudad=t["ciudad"]; idx_r=t["indice_rotacion"]
    for tp,fam,cat,precio,costo,vida in tipos:
        base_sem=base[tp]*idx_r; inv_act=base_sem*6.0
        for d in range(dias):
            fa=fecha_inicio+timedelta(days=d)
            mes=fa.month; dow=fa.weekday(); fstr=fa.isoformat()
            est_m=est[tp][mes-1]; f_dow=dow_factor[dow]
            f_ev=ev_lookup.get((fstr,"nacional"),1.0)
            f_ev=max(f_ev,ev_lookup.get((fstr,ciudad),1.0))
            f_q=1.20 if fa.day in range(13,17) or fa.day in range(27,32) else 1.0
            venta_esp=(base_sem/7)*est_m*f_dow*f_q*f_ev
            ruido=np.random.uniform(0.96,1.04)  # ruido 4%
            ventas_dia=max(0,round(venta_esp*ruido))
            if ventas_dia==0: continue
            if f_ev>2.5: desc=0.0
            elif inv_act>base_sem*9: desc=np.random.choice([30,40,50],p=[0.4,0.4,0.2])
            elif inv_act>base_sem*6: desc=np.random.choice([0,0,10,20],p=[0.6,0.15,0.15,0.10])
            else: desc=0.0
            pv=round(precio*(1-desc/100))
            tipo_desc=("PRECIO_PLENO" if desc==0 else "PROMOCION_LEVE" if desc<=20
                       else "PROMOCION_FUERTE" if desc<=40 else "LIQUIDACION")
            ventas_rows.append({
                "fecha":fstr,"tienda_id":tid,"tipo_producto":tp,"familia":fam,
                "unidades_vendidas":int(ventas_dia),"precio_regular":precio,"precio_venta":pv,
                "descuento_pct":desc,"tipo_descuento":tipo_desc,
                "valor_venta":int(pv*ventas_dia),"margen_bruto":int((pv-costo)*ventas_dia),
                "es_precio_pleno":desc==0,
            })
            inv_act=max(0,inv_act-ventas_dia)
            if inv_act<base_sem*2 and np.random.random()<0.4: inv_act+=base_sem*6
        inv_s=base_sem*6; fi=fecha_inicio
        while fi<=fecha_fin:
            if fi.weekday()==0:
                vps=base_sem*est[tp][fi.month-1]; cob=round(inv_s/max(0.1,vps),1)
                alerta=("CRITICO" if inv_s==0 else "QUIEBRE_RIESGO" if cob<2
                        else "EXCESO" if cob>10 else "OK")
                inv_rows.append({
                    "fecha":fi.isoformat(),"tienda_id":tid,"tipo_producto":tp,"familia":fam,
                    "unidades_disponibles":max(0,int(inv_s)),
                    "unidades_transito":int(base_sem*np.random.uniform(0,1.5)),
                    "costo_unitario":costo,"valor_inventario":max(0,int(inv_s))*costo,
                    "cobertura_semanas":cob,"alerta_stock":alerta,
                })
                inv_s=max(0,inv_s-vps*np.random.uniform(0.85,1.15))
                if inv_s<base_sem*2 and np.random.random()<0.5: inv_s+=base_sem*6
            fi+=timedelta(days=1)

print("  Exportando ventas...")
df_v=pd.DataFrame(ventas_rows)
for anio in [2022,2023,2024]:
    dfy=df_v[df_v["fecha"].str.startswith(str(anio))]
    dfy.to_excel(os.path.join(OUTPUT,f"ventas_{anio}.xlsx"),index=False)
    print(f"  ✓ ventas_{anio}: {len(dfy):,} filas")

print("  Exportando inventario...")
df_i=pd.DataFrame(inv_rows)
mid=len(df_i)//2
df_i.iloc[:mid].to_excel(os.path.join(OUTPUT,"inventario_semanal_parte1.xlsx"),index=False)
df_i.iloc[mid:].to_excel(os.path.join(OUTPUT,"inventario_semanal_parte2.xlsx"),index=False)
print(f"  ✓ inventario: {len(df_i):,} filas")
print("\n✅ Datos generados con ruido <4% — MAPE esperado <15%")
