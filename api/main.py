"""
Intelligent Fashion Predictor v3.0
Dashboard claro por rol: Planeación / Comercial / Despachos
Lenguaje de negocio directo + semáforos + explicaciones
"""
import os, pickle
from pathlib import Path
from datetime import date
from typing import Optional
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / '.env')
from supabase import create_client

app = FastAPI(title="Intelligent Fashion Predictor", version="3.0")
sb  = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_ANON_KEY') or os.getenv('SUPABASE_SERVICE_KEY')
)

def q(tabla, filtros=None, limite=5000, order=None, desc=True):
    r = sb.table(tabla).select('*').limit(limite)
    if filtros:
        for k,v in filtros.items(): r = r.eq(k,v)
    if order: r = r.order(order, desc=desc)
    return r.execute().data

def count(tabla, filtros=None):
    r = sb.table(tabla).select('*', count='exact').limit(1)
    if filtros:
        for k,v in filtros.items(): r = r.eq(k,v)
    return r.execute().count or 0

HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Intelligent Fashion Predictor</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{
  --blue:#1565C0;--blue-dark:#0D47A1;--blue-light:#E3F2FD;--blue-mid:#1976D2;
  --gold:#F9A825;--white:#fff;--gray-50:#F8FAFC;--gray-100:#F1F5F9;
  --gray-200:#E2E8F0;--gray-400:#94A3B8;--gray-600:#475569;--gray-900:#0F172A;
  --green:#2E7D32;--green-bg:#E8F5E9;--red:#C62828;--red-bg:#FFEBEE;
  --amber:#E65100;--amber-bg:#FFF3E0;--shadow:0 2px 8px rgba(0,0,0,.08);
  --radius:12px;
}
*{box-sizing:border-box;margin:0;padding:0;font-family:'Inter',sans-serif}
body{background:var(--gray-50);color:var(--gray-900)}

.header{background:linear-gradient(135deg,var(--blue-dark),var(--blue));
  height:60px;padding:0 28px;display:flex;align-items:center;
  justify-content:space-between;position:sticky;top:0;z-index:100;
  box-shadow:0 2px 12px rgba(13,71,161,.3)}
.logo{display:flex;align-items:center;gap:10px}
.logo-badge{background:var(--gold);width:32px;height:32px;border-radius:8px;
  display:flex;align-items:center;justify-content:center;font-size:16px}
.logo-name{color:#fff;font-size:17px;font-weight:700;letter-spacing:-.2px}
.logo-sub{color:rgba(255,255,255,.7);font-size:11px;margin-top:1px}
.hdate{color:rgba(255,255,255,.8);font-size:12px;
  background:rgba(255,255,255,.12);padding:4px 12px;border-radius:20px}

.tabs{background:#fff;border-bottom:2px solid var(--gray-200);
  padding:0 28px;display:flex;gap:2px;position:sticky;top:60px;z-index:99;
  box-shadow:0 1px 4px rgba(0,0,0,.05)}
.tab{padding:14px 18px;font-size:13px;font-weight:500;color:var(--gray-600);
  border:none;background:transparent;cursor:pointer;
  border-bottom:3px solid transparent;margin-bottom:-2px;
  transition:all .2s;display:flex;align-items:center;gap:6px}
.tab:hover{color:var(--blue)}
.tab.on{color:var(--blue);border-bottom-color:var(--blue);font-weight:600}

.page{padding:24px 28px;max-width:1380px;margin:0 auto}
.view{display:none}.view.on{display:block}

/* KPI ROW */
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px;margin-bottom:22px}
.kpi{background:#fff;border-radius:var(--radius);padding:18px 20px;
  box-shadow:var(--shadow);border-left:4px solid var(--blue);transition:transform .15s}
.kpi:hover{transform:translateY(-2px)}
.kpi.g{border-left-color:var(--green)}
.kpi.a{border-left-color:var(--amber)}
.kpi.r{border-left-color:var(--red)}
.kpi-lbl{font-size:11px;color:var(--gray-400);font-weight:600;text-transform:uppercase;letter-spacing:.04em}
.kpi-val{font-size:26px;font-weight:700;color:var(--gray-900);margin:5px 0 3px;line-height:1}
.kpi-sub{font-size:11px;color:var(--gray-400)}
.kpi-explain{font-size:11px;color:var(--gray-600);margin-top:5px;
  background:var(--gray-100);padding:4px 8px;border-radius:6px;line-height:1.4}

/* INSIGHT BANNER */
.insight{background:var(--blue-light);border-left:4px solid var(--blue);
  border-radius:var(--radius);padding:14px 18px;margin-bottom:20px;
  font-size:13px;line-height:1.6;color:var(--blue-dark)}
.insight strong{font-weight:600}

/* CHARTS */
.charts{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:22px}
.chart-box{background:#fff;border-radius:var(--radius);padding:18px;box-shadow:var(--shadow)}
.chart-box.full{grid-column:1/-1}
.chart-ttl{font-size:13px;font-weight:600;color:var(--gray-600);margin-bottom:4px}
.chart-sub{font-size:11px;color:var(--gray-400);margin-bottom:14px}
.chart-wrap{position:relative;height:240px}

/* SECTION */
.sec-ttl{font-size:15px;font-weight:700;color:var(--gray-900);
  margin-bottom:14px;display:flex;align-items:center;gap:8px}
.sec-ttl::after{content:'';flex:1;height:1px;background:var(--gray-200);margin-left:6px}

/* TABLE */
.tcard{background:#fff;border-radius:var(--radius);box-shadow:var(--shadow);overflow:hidden;margin-bottom:20px}
.thead{padding:14px 18px;border-bottom:1px solid var(--gray-200);
  display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px}
.ttitle{font-size:14px;font-weight:600}
.twrap{overflow-x:auto}
table{width:100%;border-collapse:collapse}
th{background:var(--gray-50);padding:9px 14px;text-align:left;
   font-size:11px;font-weight:600;color:var(--gray-400);
   text-transform:uppercase;letter-spacing:.04em;border-bottom:1px solid var(--gray-200)}
td{padding:10px 14px;font-size:12px;border-bottom:1px solid var(--gray-100);vertical-align:middle}
tr:hover td{background:var(--blue-light)}
tr:last-child td{border-bottom:none}
.reason{font-size:11px;color:var(--gray-600);margin-top:2px}
.consequence{font-size:11px;color:var(--red);margin-top:2px;font-style:italic}

/* BADGES */
.b{display:inline-flex;align-items:center;gap:3px;padding:3px 9px;
  border-radius:20px;font-size:11px;font-weight:600;white-space:nowrap}
.b-g{background:var(--green-bg);color:var(--green)}
.b-r{background:var(--red-bg);color:var(--red)}
.b-a{background:var(--amber-bg);color:var(--amber)}
.b-b{background:var(--blue-light);color:var(--blue)}

/* SEMÁFORO */
.sem{display:inline-flex;align-items:center;gap:5px;font-size:12px;font-weight:600}
.dot{width:9px;height:9px;border-radius:50%;flex-shrink:0}
.dot-g{background:#4CAF50}.dot-a{background:#FF9800}.dot-r{background:#F44336}.dot-gr{background:#9E9E9E}

/* ALERTA CARD */
.alerts{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:10px;margin-bottom:22px}
.alert-c{background:#fff;border-radius:var(--radius);padding:13px 15px;
  box-shadow:var(--shadow);border-left:4px solid;display:flex;gap:10px}
.alert-c.critico{border-left-color:var(--red)}
.alert-c.exceso{border-left-color:var(--amber)}
.alert-c.riesgo{border-left-color:#FF9800}
.alert-ico{width:34px;height:34px;border-radius:8px;
  display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0}
.alert-title{font-size:13px;font-weight:600}
.alert-sub{font-size:11px;color:var(--gray-600);margin-top:2px;line-height:1.4}
.alert-action{font-size:11px;font-weight:600;margin-top:4px}

/* PLAN PROD */
.prod-row{background:#fff;border-radius:var(--radius);padding:16px 18px;
  box-shadow:var(--shadow);margin-bottom:10px;border-left:4px solid var(--blue)}
.prod-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:8px}
.prod-name{font-size:14px;font-weight:700}
.prod-inv{font-size:11px;color:var(--gray-400)}
.prod-timeline{display:flex;gap:6px;margin-top:8px;flex-wrap:wrap}
.tl-item{background:var(--gray-100);border-radius:6px;padding:5px 10px;font-size:11px}
.tl-item strong{display:block;font-weight:600;font-size:12px}
.tl-item span{color:var(--gray-400)}
.tallas-row{display:flex;gap:6px;margin-top:8px;flex-wrap:wrap}
.talla-chip{background:var(--blue-light);color:var(--blue);
  padding:3px 9px;border-radius:12px;font-size:11px;font-weight:600}

/* FILTROS */
.filters{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px}
.filters select,.filters input{padding:7px 11px;border:1.5px solid var(--gray-200);
  border-radius:8px;font-size:12px;color:var(--gray-900);background:#fff}
.filters select:focus{outline:none;border-color:var(--blue)}
.btn{padding:7px 14px;border-radius:8px;font-size:12px;font-weight:600;
  cursor:pointer;border:none;font-family:inherit}
.btn-blue{background:var(--blue);color:#fff}
.btn-blue:hover{background:var(--blue-dark)}

.empty{text-align:center;padding:40px;color:var(--gray-400);font-size:13px}
.loading{text-align:center;padding:60px;color:var(--gray-400)}
.spin{width:36px;height:36px;border:3px solid var(--gray-200);
  border-top-color:var(--blue);border-radius:50%;animation:spin .7s linear infinite;margin:0 auto 12px}
@keyframes spin{to{transform:rotate(360deg)}}

.tag-why{display:inline-block;background:#EDE7F6;color:#4527A0;
  padding:2px 7px;border-radius:4px;font-size:10px;font-weight:600;margin-left:4px}
</style>
</head>
<body>

<header class="header">
  <div class="logo">
    <div class="logo-badge">👗</div>
    <div>
      <div class="logo-name">Intelligent Fashion Predictor</div>
      <div class="logo-sub">Sistema de predicción · Manufactura textil Colombia</div>
    </div>
  </div>
  <div class="hdate" id="hfecha"></div>
</header>

<div class="tabs">
  <button class="tab on" onclick="showTab('plan')">📊 Planeación</button>
  <button class="tab"    onclick="showTab('com')">🏪 Comercial</button>
  <button class="tab"    onclick="showTab('des')">📦 Despachos</button>
</div>

<div class="page">

<!-- ═══════ PLANEACIÓN ═══════ -->
<div id="v-plan" class="view on">
  <div id="plan-body"><div class="loading"><div class="spin"></div>Cargando datos de planeación...</div></div>
</div>

<!-- ═══════ COMERCIAL ═══════ -->
<div id="v-com" class="view">
  <div id="com-body"><div class="loading"><div class="spin"></div>Cargando datos comerciales...</div></div>
</div>

<!-- ═══════ DESPACHOS ═══════ -->
<div id="v-des" class="view">
  <div id="des-body"><div class="loading"><div class="spin"></div>Cargando lista de despachos...</div></div>
</div>

</div><!-- /page -->

<script>
const state = {loaded:{}};
const GMROII_MIN = 2.5;

document.getElementById('hfecha').textContent =
  new Date().toLocaleDateString('es-CO',{weekday:'short',day:'numeric',month:'long',year:'numeric'});

function showTab(t){
  document.querySelectorAll('.tab').forEach((b,i)=>b.classList.toggle('on',['plan','com','des'][i]===t));
  document.querySelectorAll('.view').forEach(v=>v.classList.remove('on'));
  document.getElementById('v-'+t).classList.add('on');
  if(!state.loaded[t]){loadView(t);state.loaded[t]=true;}
}

async function api(p){const r=await fetch(p);return r.json();}
const f=(n)=>Number(n||0).toLocaleString('es-CO');
const fp=(n)=>(+n||0).toFixed(1)+'%';
const fm=(n)=>'$'+(+n/1000000).toFixed(1)+'M';
const fg=(n)=>(+n||0).toFixed(2);
const BLUES=['#0D47A1','#1565C0','#1976D2','#1E88E5','#42A5F5','#90CAF9'];
const MULTI=['#1565C0','#2E7D32','#E65100','#6A1B9A','#00695C','#C62828','#F57F17'];

function semaforo(val, ok, warn, bad){
  if(val<=bad) return `<span class="sem"><span class="dot dot-r"></span>${val}</span>`;
  if(val<=warn) return `<span class="sem"><span class="dot dot-a"></span>${val}</span>`;
  return `<span class="sem"><span class="dot dot-g"></span>${val}</span>`;
}
function semaforoAlerta(tipo){
  const m={CRITICO:'<span class="sem"><span class="dot dot-r"></span>🔴 Sin stock</span>',
           QUIEBRE_RIESGO:'<span class="sem"><span class="dot dot-a"></span>🟠 Quiebre inminente</span>',
           EXCESO:'<span class="sem"><span class="dot dot-a"></span>🟡 Exceso de stock</span>',
           OK:'<span class="sem"><span class="dot dot-g"></span>🟢 OK</span>'};
  return m[tipo]||tipo;
}

// ════════════════════════════════════
// PLANEACIÓN
// ════════════════════════════════════
async function loadPlan(){
  const [res,fc,prod,alts]=await Promise.all([
    api('/api/resumen'), api('/api/forecast/top'), api('/api/produccion'), api('/api/alertas?limite=8')
  ]);

  // Calcular top producto y ciudad del forecast
  const topProd = fc.top_producto || 'Jean Hombre';
  const topCiudad = fc.top_ciudad || 'Bogotá';
  const uds4sem = f(res.unidades_forecast_4sem);

  document.getElementById('plan-body').innerHTML = `

  <!-- INSIGHT PRINCIPAL -->
  <div class="insight">
    📈 <strong>Resumen ejecutivo:</strong> En las próximas 4 semanas se proyecta vender
    <strong>${uds4sem} unidades</strong> en toda la red.
    El producto más demandado es <strong>${topProd}</strong> y la ciudad con mayor volumen es <strong>${topCiudad}</strong>.
    ${res.alertas_criticas>0
      ? `⚠️ <strong>Atención:</strong> hay <strong>${res.alertas_criticas} tiendas con stock crítico</strong> que requieren despacho urgente.`
      : '✅ El inventario en todas las tiendas está en niveles saludables.'}
  </div>

  <!-- KPIs -->
  <div class="kpis">
    <div class="kpi">
      <div class="kpi-lbl">Ventas proyectadas</div>
      <div class="kpi-val">${uds4sem}</div>
      <div class="kpi-sub">unidades · próximas 4 semanas</div>
      <div class="kpi-explain">¿Qué significa? Es cuánto debería vender toda la red si el inventario está disponible.</div>
    </div>
    <div class="kpi g">
      <div class="kpi-lbl">Producto estrella</div>
      <div class="kpi-val" style="font-size:16px;margin-top:6px">${topProd}</div>
      <div class="kpi-sub">${fp(fc.pct_top||32)} del volumen total</div>
      <div class="kpi-explain">El producto que más unidades mueve en la red. Priorizar en producción y despacho.</div>
    </div>
    <div class="kpi a">
      <div class="kpi-lbl">Inversión en producción</div>
      <div class="kpi-val">${fm(res.inversion_produccion)}</div>
      <div class="kpi-sub">plan período actual</div>
      <div class="kpi-explain">Capital a comprometer para la próxima colección. Llegada al CEDI en 16 semanas.</div>
    </div>
    <div class="kpi ${res.alertas_criticas>0?'r':'g'}">
      <div class="kpi-lbl">Alertas críticas</div>
      <div class="kpi-val">${res.alertas_criticas}</div>
      <div class="kpi-sub">tiendas sin stock</div>
      <div class="kpi-explain">${res.alertas_criticas>0?'¡Ojo! Estas tiendas están perdiendo ventas ahora mismo.':'Todo bajo control. Sin quiebres activos.'}</div>
    </div>
    <div class="kpi">
      <div class="kpi-lbl">Precisión del modelo</div>
      <div class="kpi-val">${fp(res.mape_modelo)}</div>
      <div class="kpi-sub">error promedio de predicción</div>
      <div class="kpi-explain">MAPE: cuánto se equivoca el modelo en promedio. Menor al 20% es excelente para moda.</div>
    </div>
  </div>

  <!-- ALERTAS -->
  ${(alts.data||[]).length>0?`
  <div class="sec-ttl">🚨 Alertas de inventario que requieren acción</div>
  <div class="alerts">
    ${(alts.data||[]).map(a=>{
      const esCrit = a.alerta_stock==='CRITICO';
      const esExc  = a.alerta_stock==='EXCESO';
      return `<div class="alert-c ${esCrit?'critico':esExc?'exceso':'riesgo'}">
        <div class="alert-ico" style="background:${esCrit?'#FFEBEE':esExc?'#FFF3E0':'#FFF8E1'}">
          ${esCrit?'🔴':esExc?'🟡':'🟠'}
        </div>
        <div>
          <div class="alert-title">${a.tipo_producto} · T-${String(a.tienda_id).padStart(3,'0')}</div>
          <div class="alert-sub">Cobertura: <strong>${(+a.cobertura_semanas||0).toFixed(1)} semanas</strong>
            ${esCrit?' — Sin unidades disponibles':esExc?' — Stock acumulado sin rotación':' — Stock por agotarse pronto'}</div>
          <div class="alert-action" style="color:${esCrit?'var(--red)':esExc?'var(--amber)':'#E65100'}">
            ${esCrit?'→ Despachar urgente esta semana':esExc?'→ Considerar redistribución o descuento':'→ Programar despacho en los próximos días'}
          </div>
        </div>
      </div>`;
    }).join('')}
  </div>`:''}

  <!-- GRÁFICAS -->
  <div class="charts">
    <div class="chart-box">
      <div class="chart-ttl">¿Qué se va a vender en las próximas 8 semanas?</div>
      <div class="chart-sub">Unidades proyectadas por tipo de producto · todas las tiendas</div>
      <div class="chart-wrap"><canvas id="c-fc-tipo"></canvas></div>
    </div>
    <div class="chart-box">
      <div class="chart-ttl">¿En qué ciudades se concentran las ventas?</div>
      <div class="chart-sub">Distribución del forecast por ciudad</div>
      <div class="chart-wrap"><canvas id="c-fc-ciudad"></canvas></div>
    </div>
  </div>

  <!-- PLAN DE PRODUCCIÓN -->
  <div class="sec-ttl">🏭 ¿Qué debemos producir? — Plan completo 16 semanas</div>
  <div class="insight" style="margin-bottom:16px">
    💡 <strong>¿Cómo leer este plan?</strong> Cada producto muestra cuándo debe <em>iniciar la producción</em>
    (compra de tela y corte) y cuándo llega al CEDI listo para distribuir.
    El lead time de manufactura es de <strong>16 semanas</strong>.
  </div>
  ${(prod.data||[]).filter(p=>p.unidades_totales>0).sort((a,b)=>b.unidades_totales-a.unidades_totales).map(p=>{
    let tallas = {};
    try{tallas=JSON.parse((p.distribucion_tallas||'{}').replace(/'/g,'"'));}catch(e){}
    const tallasStr = Object.entries(tallas).map(([t,u])=>`<span class="talla-chip">${t}: ${f(u)}</span>`).join('');
    return `<div class="prod-row">
      <div class="prod-header">
        <div>
          <div class="prod-name">${p.tipo_producto} <span class="b b-b">${p.familia}</span></div>
          <div class="prod-inv">Inversión estimada: <strong>${fm(p.inversion_estimada)}</strong></div>
        </div>
        <div style="text-align:right">
          <div style="font-size:22px;font-weight:700;color:var(--blue)">${f(p.unidades_totales)}</div>
          <div style="font-size:11px;color:var(--gray-400)">unidades a producir</div>
        </div>
      </div>
      <div class="prod-timeline">
        <div class="tl-item"><strong>Hoy</strong><span>Aprobar orden</span></div>
        <div class="tl-item" style="background:var(--amber-bg)"><strong>${p.semana_inicio_prod}</strong><span>Inicio corte</span></div>
        <div class="tl-item" style="background:var(--green-bg)"><strong>${p.semana_llegada_cedi}</strong><span>Llegada CEDI</span></div>
      </div>
      ${tallasStr?`<div class="tallas-row">${tallasStr}</div>`:''}
    </div>`;
  }).join('')}`;

  // Charts
  const tipoData={}, ciudadData={};
  (fc.data||[]).forEach(r=>{
    tipoData[r.tipo_producto]=(tipoData[r.tipo_producto]||0)+(+r.forecast_total||0);
    ciudadData[r.ciudad]=(ciudadData[r.ciudad]||0)+(+r.forecast_total||0);
  });
  const tipos=Object.keys(tipoData).sort((a,b)=>tipoData[b]-tipoData[a]).slice(0,10);
  new Chart(document.getElementById('c-fc-tipo'),{
    type:'bar',
    data:{labels:tipos,datasets:[{label:'Unidades',data:tipos.map(t=>Math.round(tipoData[t])),
      backgroundColor:tipos.map((_,i)=>BLUES[Math.min(i,BLUES.length-1)]),borderRadius:5}]},
    options:{responsive:true,maintainAspectRatio:false,indexAxis:'y',
      plugins:{legend:{display:false}},
      scales:{x:{ticks:{font:{size:10}}},y:{ticks:{font:{size:10}}}}}
  });
  const ciudades=Object.keys(ciudadData).sort((a,b)=>ciudadData[b]-ciudadData[a]).slice(0,8);
  new Chart(document.getElementById('c-fc-ciudad'),{
    type:'doughnut',
    data:{labels:ciudades,datasets:[{data:ciudades.map(c=>Math.round(ciudadData[c])),
      backgroundColor:BLUES,borderWidth:2,borderColor:'#fff'}]},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{position:'right',labels:{font:{size:10},boxWidth:10}}}}
  });
}

// ════════════════════════════════════
// COMERCIAL
// ════════════════════════════════════
async function loadCom(){
  const [gm,fc]=await Promise.all([api('/api/gmroii?limite=100'),api('/api/forecast/top')]);

  const sobre = (gm.data||[]).filter(d=>(+d.gmroii_proyectado||0)>=GMROII_MIN);
  const bajo  = (gm.data||[]).filter(d=>(+d.gmroii_proyectado||0)<GMROII_MIN);

  document.getElementById('com-body').innerHTML=`

  <div class="insight">
    💰 <strong>Estado del GMROII en la red:</strong>
    <strong>${sobre.length} tiendas/productos</strong> superan el objetivo de ${GMROII_MIN}
    (generan $${GMROII_MIN} o más de margen por cada $1 invertido en inventario).
    ${bajo.length>0
      ?`⚠️ <strong>${bajo.length} combinaciones</strong> están por debajo del objetivo — revisar política de precios o redistribución.`
      :'✅ Toda la red cumple el objetivo de rentabilidad.'}
    <br><small style="color:var(--blue-dark)">
      GMROII = Margen bruto ÷ Costo del inventario. Objetivo mínimo: ${GMROII_MIN}
    </small>
  </div>

  <div class="kpis">
    <div class="kpi g">
      <div class="kpi-lbl">GMROII promedio red</div>
      <div class="kpi-val">${fg(gm.gmroii_promedio)}</div>
      <div class="kpi-sub">objetivo mínimo: ${GMROII_MIN}</div>
      <div class="kpi-explain">Por cada $1 invertido en inventario, la red genera $${fg(gm.gmroii_promedio)} de margen.</div>
    </div>
    <div class="kpi g">
      <div class="kpi-lbl">Sobre objetivo</div>
      <div class="kpi-val">${sobre.length}</div>
      <div class="kpi-sub">combinaciones tienda×producto</div>
      <div class="kpi-explain">Estas tiendas y productos están siendo rentables para el capital invertido.</div>
    </div>
    <div class="kpi ${bajo.length>0?'r':'g'}">
      <div class="kpi-lbl">Bajo objetivo</div>
      <div class="kpi-val">${bajo.length}</div>
      <div class="kpi-sub">requieren revisión</div>
      <div class="kpi-explain">${bajo.length>0?'Posibles causas: exceso de inventario, descuentos excesivos o baja rotación.':'¡Excelente! Todo cumple el objetivo.'}</div>
    </div>
    <div class="kpi">
      <div class="kpi-lbl">Mejor producto red</div>
      <div class="kpi-val" style="font-size:15px;margin-top:6px">${gm.mejor_producto||'Jean Hombre'}</div>
      <div class="kpi-sub">mayor GMROII promedio</div>
      <div class="kpi-explain">El producto que mejor retorno genera por peso invertido en inventario.</div>
    </div>
  </div>

  <div class="charts">
    <div class="chart-box">
      <div class="chart-ttl">GMROII por tipo de producto</div>
      <div class="chart-sub">La línea roja es el objetivo mínimo (${GMROII_MIN}). Verde = cumple · Rojo = revisar</div>
      <div class="chart-wrap"><canvas id="c-gm-prod"></canvas></div>
    </div>
    <div class="chart-box">
      <div class="chart-ttl">Distribución de GMROII en la red</div>
      <div class="chart-sub">¿Cuántas combinaciones tienda×producto caen en cada rango?</div>
      <div class="chart-wrap"><canvas id="c-gm-dist"></canvas></div>
    </div>
  </div>

  <div class="sec-ttl">📋 Detalle GMROII por tienda y producto</div>
  <div class="filters">
    <select id="f-estado" onchange="filtrarGmroii()">
      <option value="">Todos los estados</option>
      <option value="APROBADO">✅ Sobre objetivo</option>
      <option value="REVISAR">⚠️ Bajo objetivo</option>
    </select>
    <span style="font-size:12px;color:var(--gray-400);align-self:center">
      Mostrando ${Math.min((gm.data||[]).length,100)} registros
    </span>
  </div>
  <div class="tcard">
    <div class="twrap">
      <table id="t-gmroii">
        <tr><th>Tienda</th><th>Producto</th><th>GMROII</th><th>Estado</th><th>¿Qué significa?</th></tr>
        ${(gm.data||[]).slice(0,50).map(d=>{
          const g=+d.gmroii_proyectado||0;
          const ok=g>=GMROII_MIN;
          return `<tr>
            <td><strong>T-${String(d.tienda_id).padStart(3,'0')}</strong></td>
            <td>${d.tipo_producto}</td>
            <td><strong style="color:${ok?'var(--green)':'var(--red)'}">${fg(g)}</strong></td>
            <td><span class="b ${ok?'b-g':'b-r'}">${ok?'✅ Rentable':'⚠️ Revisar'}</span></td>
            <td style="font-size:11px;color:var(--gray-600)">
              ${ok
                ?`Genera $${fg(g)} por cada $1 invertido. Buena rotación.`
                :`Por debajo del objetivo ${GMROII_MIN}. ${g<1.5?'Considerar redistribución o liquidación.':'Ajustar nivel de descuentos.'}`}
            </td>
          </tr>`;
        }).join('')}
      </table>
    </div>
  </div>`;

  // Charts GMROII
  const prodGm={};
  (gm.data||[]).forEach(d=>{
    if(!prodGm[d.tipo_producto]) prodGm[d.tipo_producto]=[];
    prodGm[d.tipo_producto].push(+d.gmroii_proyectado||0);
  });
  const prods=Object.keys(prodGm);
  const gmVals=prods.map(p=>+(prodGm[p].reduce((a,b)=>a+b,0)/prodGm[p].length).toFixed(2));
  new Chart(document.getElementById('c-gm-prod'),{
    type:'bar',
    data:{labels:prods,
      datasets:[{label:'GMROII',data:gmVals,
        backgroundColor:gmVals.map(v=>v>=GMROII_MIN?'#2E7D32':'#C62828'),borderRadius:5}]},
    options:{responsive:true,maintainAspectRatio:false,indexAxis:'y',
      plugins:{legend:{display:false},
        annotation:{annotations:{line:{type:'line',xMin:GMROII_MIN,xMax:GMROII_MIN,
          borderColor:'#F44336',borderWidth:2,borderDash:[5,5]}}}},
      scales:{x:{ticks:{font:{size:10}},suggestedMin:0},y:{ticks:{font:{size:9}}}}}
  });
  const bins={'< 1.5':0,'1.5 – 2.0':0,'2.0 – 2.5':0,'2.5 – 3.0':0,'> 3.0':0};
  (gm.data||[]).forEach(d=>{
    const g=+d.gmroii_proyectado||0;
    if(g<1.5) bins['< 1.5']++;
    else if(g<2.0) bins['1.5 – 2.0']++;
    else if(g<2.5) bins['2.0 – 2.5']++;
    else if(g<3.0) bins['2.5 – 3.0']++;
    else bins['> 3.0']++;
  });
  new Chart(document.getElementById('c-gm-dist'),{
    type:'bar',
    data:{labels:Object.keys(bins),
      datasets:[{label:'Combinaciones',data:Object.values(bins),
        backgroundColor:['#C62828','#E65100','#F57C00','#2E7D32','#1B5E20'],borderRadius:5}]},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false}},
      scales:{x:{ticks:{font:{size:10}}},y:{ticks:{font:{size:10}}}}}
  });
}

// ════════════════════════════════════
// DESPACHOS
// ════════════════════════════════════
async function loadDes(){
  const [dep,inv]=await Promise.all([api('/api/despachos?limite=300'),api('/api/inventario/cobertura')]);

  const aprobados=(dep.data||[]).filter(d=>d.estado==='APROBADO');
  const revisar  =(dep.data||[]).filter(d=>d.estado==='REVISAR');

  document.getElementById('des-body').innerHTML=`

  <div class="insight">
    📦 <strong>Lista de despachos de esta semana:</strong>
    <strong>${aprobados.length} despachos aprobados</strong> listos para ejecutar (GMROII ≥ ${GMROII_MIN}).
    ${revisar.length>0?`<strong>${revisar.length} despachos</strong> requieren revisión antes de ejecutar — el retorno proyectado está bajo el mínimo.`:''}
    ${inv.criticos>0
      ?`🔴 <strong>¡Urgente!</strong> ${inv.criticos} tiendas sin stock están perdiendo ventas ahora.`
      :'✅ Sin tiendas en quiebre crítico.'}
  </div>

  <div class="kpis">
    <div class="kpi g">
      <div class="kpi-lbl">Despachos aprobados</div>
      <div class="kpi-val">${aprobados.length}</div>
      <div class="kpi-sub">GMROII ≥ ${GMROII_MIN} · ejecutar esta semana</div>
      <div class="kpi-explain">Estos despachos tienen el retorno suficiente para justificar el movimiento de mercancía.</div>
    </div>
    <div class="kpi ${revisar.length>0?'a':'g'}">
      <div class="kpi-lbl">A revisar</div>
      <div class="kpi-val">${revisar.length}</div>
      <div class="kpi-sub">GMROII bajo el mínimo</div>
      <div class="kpi-explain">Esperar o ajustar cobertura objetivo. Despachar podría no ser rentable.</div>
    </div>
    <div class="kpi ${inv.criticos>0?'r':'g'}">
      <div class="kpi-lbl">Tiendas sin stock</div>
      <div class="kpi-val">${inv.criticos}</div>
      <div class="kpi-sub">cobertura = 0 semanas</div>
      <div class="kpi-explain">${inv.criticos>0?'¡Ojo! Estas tiendas no pueden vender. Despachar hoy sin falta.':'Sin quiebres activos en la red.'}</div>
    </div>
    <div class="kpi a">
      <div class="kpi-lbl">Tiendas con exceso</div>
      <div class="kpi-val">${inv.excesos}</div>
      <div class="kpi-sub">cobertura > 10 semanas</div>
      <div class="kpi-explain">Demasiado stock inmovilizado. Evaluar redistribución hacia tiendas con quiebre.</div>
    </div>
  </div>

  <div class="charts">
    <div class="chart-box">
      <div class="chart-ttl">Estado del inventario en la red</div>
      <div class="chart-sub">¿Cuántas combinaciones tienda×producto están en cada estado?</div>
      <div class="chart-wrap"><canvas id="c-inv-est"></canvas></div>
    </div>
    <div class="chart-box">
      <div class="chart-ttl">GMROII de los despachos recomendados</div>
      <div class="chart-sub">La línea roja es el mínimo (${GMROII_MIN}). Solo despachar los verdes.</div>
      <div class="chart-wrap"><canvas id="c-dep-gm"></canvas></div>
    </div>
  </div>

  <!-- APROBADOS -->
  <div class="sec-ttl">✅ Despachos aprobados — ejecutar esta semana</div>
  ${aprobados.length>0?`
  <div class="insight" style="margin-bottom:14px">
    💡 <strong>¿Cómo leer esta tabla?</strong>
    "Cobertura actual" = cuántas semanas de stock le quedan a la tienda HOY.
    "Si no se despacha" = cuándo se quedaría sin stock.
    "GMROII" = rentabilidad del despacho (mínimo ${GMROII_MIN}).
  </div>
  <div class="tcard">
    <div class="twrap">
      <table>
        <tr>
          <th>Tienda</th><th>Producto</th><th>Unidades</th>
          <th>Cobertura actual</th><th>Sin despacho...</th>
          <th>GMROII</th><th>Semana despacho</th><th>Estado</th>
        </tr>
        ${aprobados.map(d=>{
          const cob=+d.cobertura_actual||0;
          const diasSinStock=Math.round(cob*7);
          const fechaQuiebre=new Date(Date.now()+diasSinStock*86400000)
            .toLocaleDateString('es-CO',{day:'numeric',month:'short'});
          return `<tr>
            <td><strong>T-${String(d.tienda_id).padStart(3,'0')}</strong></td>
            <td>${d.tipo_producto}</td>
            <td><strong>${f(d.unidades_sugeridas)} uds</strong></td>
            <td>${semaforo(cob.toFixed(1),4,2,0)} sem</td>
            <td class="consequence">Se queda sin stock ~${fechaQuiebre}</td>
            <td><strong style="color:var(--green)">${fg(d.gmroii_proyectado)}</strong></td>
            <td>${d.semana_despacho||'-'}</td>
            <td><span class="b b-g">✅ Aprobar</span></td>
          </tr>`;
        }).join('')}
      </table>
    </div>
  </div>`:`<div class="empty">No hay despachos aprobados para esta semana.</div>`}

  <!-- REVISAR -->
  ${revisar.length>0?`
  <div class="sec-ttl">⚠️ Despachos a revisar — GMROII bajo el mínimo</div>
  <div class="tcard">
    <div class="twrap">
      <table>
        <tr><th>Tienda</th><th>Producto</th><th>Unidades</th><th>Cobertura</th><th>GMROII</th><th>¿Por qué está bajo?</th></tr>
        ${revisar.slice(0,20).map(d=>{
          const g=+d.gmroii_proyectado||0;
          const razon=g<1.0?'Stock muy alto, poca demanda proyectada — evaluar liquidación'
            :g<1.5?'Rotación lenta — esperar o reducir cantidad a despachar'
            :'Cerca del objetivo — puede aprobar si hay urgencia operativa';
          return `<tr>
            <td>T-${String(d.tienda_id).padStart(3,'0')}</td>
            <td>${d.tipo_producto}</td>
            <td>${f(d.unidades_sugeridas)} uds</td>
            <td>${(+d.cobertura_actual||0).toFixed(1)} sem</td>
            <td style="color:var(--amber)"><strong>${fg(g)}</strong></td>
            <td style="font-size:11px;color:var(--gray-600)">${razon}</td>
          </tr>`;
        }).join('')}
      </table>
    </div>
  </div>`:''}`;

  // Charts inventario
  new Chart(document.getElementById('c-inv-est'),{
    type:'doughnut',
    data:{labels:['✅ OK','🟠 Quiebre riesgo','🟡 Exceso','🔴 Crítico'],
      datasets:[{data:[inv.ok,inv.riesgo,inv.excesos,inv.criticos],
        backgroundColor:['#2E7D32','#FF9800','#E65100','#C62828'],borderWidth:2,borderColor:'#fff'}]},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{position:'right',labels:{font:{size:11},boxWidth:10}}}}
  });
  const bins2={'< 1.5':0,'1.5–2.0':0,'2.0–2.5':0,'2.5–3.0':0,'> 3.0':0};
  (dep.data||[]).forEach(d=>{
    const g=+d.gmroii_proyectado||0;
    if(g<1.5) bins2['< 1.5']++;
    else if(g<2.0) bins2['1.5–2.0']++;
    else if(g<2.5) bins2['2.0–2.5']++;
    else if(g<3.0) bins2['2.5–3.0']++;
    else bins2['> 3.0']++;
  });
  new Chart(document.getElementById('c-dep-gm'),{
    type:'bar',
    data:{labels:Object.keys(bins2),
      datasets:[{label:'Despachos',data:Object.values(bins2),
        backgroundColor:['#C62828','#E65100','#F57C00','#2E7D32','#1B5E20'],borderRadius:5}]},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false}},
      scales:{x:{ticks:{font:{size:10}}},y:{ticks:{font:{size:10}}}}}
  });
}

function filtrarGmroii(){
  // Reservado para implementación futura
}

function loadView(t){
  if(t==='plan') loadPlan();
  else if(t==='com') loadCom();
  else if(t==='des') loadDes();
}
loadPlan();
state.loaded['plan']=true;
</script>
</body></html>"""

# ── ENDPOINTS ─────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def dashboard(): return HTML

@app.get("/api/resumen")
async def resumen():
    try:
        fc   = sb.table('output_forecast_semanal').select('forecast_medio,tipo_producto,semana_objetivo').limit(10000).execute().data
        dep  = count('output_despachos_recomendados')
        prod = sb.table('output_produccion_recomendada').select('inversion_estimada,unidades_totales').execute().data
        inv  = count('fact_inventario_semanal', {'alerta_stock':'CRITICO'})

        uds_4 = sum(r.get('forecast_medio',0) or 0 for r in fc
                    if r.get('semana_objetivo','') <= str(date.today()))
        if uds_4 == 0:
            uds_4 = sum(r.get('forecast_medio',0) or 0 for r in fc) / 2

        inv_prod = sum(r.get('inversion_estimada',0) or 0 for r in prod)
        mape = 0
        mp = Path(__file__).parent.parent / 'outputs' / 'modelo_lgbm.pkl'
        if mp.exists():
            with open(mp,'rb') as f: mape = pickle.load(f).get('mape',0)

        return {"forecast_predicciones": len(fc), "despachos_total": dep,
                "alertas_criticas": inv, "unidades_forecast_4sem": round(uds_4),
                "inversion_produccion": inv_prod, "mape_modelo": round(mape,1)}
    except Exception as e:
        return {"error":str(e),"forecast_predicciones":0,"despachos_total":0,
                "alertas_criticas":0,"unidades_forecast_4sem":0,
                "inversion_produccion":0,"mape_modelo":0}

@app.get("/api/forecast/top")
async def forecast_top():
    try:
        data = sb.table('output_forecast_semanal').select('*').limit(10000).execute().data
        from supabase import create_client as _cc
        tiendas_data = sb.table('dim_tiendas').select('tienda_id,ciudad').execute().data
        ciudad_map = {t['tienda_id']:t['ciudad'] for t in tiendas_data}

        agg, ciudad_agg, tipo_agg = {}, {}, {}
        for r in data:
            tp = r.get('tipo_producto','')
            tid = r.get('tienda_id')
            sem = r.get('semana_objetivo','')
            ciudad = ciudad_map.get(tid,'')
            val = r.get('forecast_medio',0) or 0
            key = (tp, ciudad, sem)
            if key not in agg: agg[key]={'tipo_producto':tp,'ciudad':ciudad,'semana_objetivo':sem,'forecast_total':0}
            agg[key]['forecast_total'] += val
            ciudad_agg[ciudad] = ciudad_agg.get(ciudad,0) + val
            tipo_agg[tp] = tipo_agg.get(tp,0) + val

        top_tipo   = max(tipo_agg,   key=tipo_agg.get)   if tipo_agg   else 'Jean Hombre'
        top_ciudad = max(ciudad_agg, key=ciudad_agg.get) if ciudad_agg else 'Bogotá'
        total      = sum(tipo_agg.values()) or 1
        pct_top    = round(tipo_agg.get(top_tipo,0)/total*100,1)

        return {"top_producto":top_tipo,"top_ciudad":top_ciudad,"pct_top":pct_top,
                "total":len(agg),"data":list(agg.values())}
    except Exception as e:
        return {"error":str(e),"data":[],"top_producto":"Jean Hombre","top_ciudad":"Bogotá","pct_top":32}

@app.get("/api/produccion")
async def produccion():
    try:
        data = sb.table('output_produccion_recomendada').select('*').order('fecha_ejecucion',desc=True).limit(100).execute().data
        return {"total":len(data),"data":data}
    except Exception as e: return {"error":str(e),"data":[]}

@app.get("/api/alertas")
async def alertas(limite:int=20):
    try:
        fm = sb.table('fact_inventario_semanal').select('fecha').order('fecha',desc=True).limit(1).execute().data
        if not fm: return {"data":[]}
        data = sb.table('fact_inventario_semanal').select('*').eq('fecha',fm[0]['fecha']).neq('alerta_stock','OK').limit(limite).execute().data
        return {"total":len(data),"data":data}
    except Exception as e: return {"error":str(e),"data":[]}

@app.get("/api/gmroii")
async def gmroii(limite:int=100):
    try:
        data = sb.table('output_despachos_recomendados').select('*').order('gmroii_proyectado',desc=True).limit(limite).execute().data
        if not data: return {"data":[],"gmroii_promedio":0,"mejor_producto":""}
        vals = [+r.get('gmroii_proyectado',0) for r in data]
        prom = sum(vals)/len(vals) if vals else 0
        prod_gm = {}
        for r in data:
            p = r.get('tipo_producto','')
            g = +r.get('gmroii_proyectado',0)
            if p not in prod_gm: prod_gm[p]=[]
            prod_gm[p].append(g)
        mejor = max(prod_gm, key=lambda p: sum(prod_gm[p])/len(prod_gm[p])) if prod_gm else ''
        return {"gmroii_promedio":round(prom,2),"mejor_producto":mejor,
                "tiendas_sobre_objetivo":sum(1 for v in vals if v>=2.5),
                "tiendas_bajo_objetivo":sum(1 for v in vals if v<2.5),"data":data}
    except Exception as e: return {"error":str(e),"data":[],"gmroii_promedio":0,"mejor_producto":""}

@app.get("/api/despachos")
async def despachos(estado:Optional[str]=None, limite:int=300):
    try:
        r = sb.table('output_despachos_recomendados').select('*').order('gmroii_proyectado',desc=True).limit(limite)
        if estado: r = r.eq('estado',estado)
        data = r.execute().data
        return {"total":len(data),"data":data}
    except Exception as e: return {"error":str(e),"data":[]}

@app.get("/api/inventario/cobertura")
async def cobertura():
    try:
        fm = sb.table('fact_inventario_semanal').select('fecha').order('fecha',desc=True).limit(1).execute().data
        if not fm: return {"ok":0,"riesgo":0,"excesos":0,"criticos":0}
        data = sb.table('fact_inventario_semanal').select('alerta_stock').eq('fecha',fm[0]['fecha']).limit(50000).execute().data
        c={"OK":0,"QUIEBRE_RIESGO":0,"EXCESO":0,"CRITICO":0}
        for r in data: c[r.get('alerta_stock','OK')]=c.get(r.get('alerta_stock','OK'),0)+1
        return {"ok":c["OK"],"riesgo":c["QUIEBRE_RIESGO"],"excesos":c["EXCESO"],"criticos":c["CRITICO"]}
    except Exception as e: return {"error":str(e),"ok":0,"riesgo":0,"excesos":0,"criticos":0}

@app.get("/health")
async def health(): return {"status":"ok","app":"Intelligent Fashion Predictor v3.0"}
