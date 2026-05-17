"""
Intelligent Fashion Predictor — API Principal
Dashboard para Planeación, Comercial y Despachos
"""
import os, json
from pathlib import Path
from datetime import date
from typing import Optional
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / '.env')
from supabase import create_client

app = FastAPI(title="Intelligent Fashion Predictor", version="2.0")

sb_url = os.getenv('SUPABASE_URL')
sb_key = os.getenv('SUPABASE_ANON_KEY') or os.getenv('SUPABASE_SERVICE_KEY')
sb = create_client(sb_url, sb_key)

def leer(tabla, filtros=None, limite=5000, order=None):
    q = sb.table(tabla).select('*').limit(limite)
    if filtros:
        for k,v in filtros.items():
            q = q.eq(k,v)
    if order:
        q = q.order(order, desc=True)
    return q.execute().data

# ── DASHBOARD HTML ────────────────────────────────────────
DASHBOARD_HTML = '''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Intelligent Fashion Predictor</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Serif+Display&display=swap" rel="stylesheet">
<style>
:root {
  --blue-900:#0B2447; --blue-700:#19376D; --blue-500:#1565C0;
  --blue-400:#1976D2; --blue-200:#90CAF9; --blue-100:#E3F2FD;
  --gold:#C9A84C; --white:#FFFFFF; --gray-50:#F8FAFC;
  --gray-100:#F1F5F9; --gray-200:#E2E8F0; --gray-500:#64748B;
  --gray-700:#334155; --gray-900:#0F172A;
  --green:#2E7D32; --green-light:#E8F5E9;
  --red:#C62828; --red-light:#FFEBEE;
  --amber:#E65100; --amber-light:#FFF3E0;
  --shadow:0 2px 8px rgba(11,36,71,.10);
  --shadow-lg:0 8px 32px rgba(11,36,71,.16);
  --radius:12px; --radius-lg:20px;
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'DM Sans',sans-serif;background:var(--gray-50);color:var(--gray-900);min-height:100vh}

/* HEADER */
.header{background:linear-gradient(135deg,var(--blue-900) 0%,var(--blue-700) 100%);
  padding:0 32px;height:64px;display:flex;align-items:center;justify-content:space-between;
  box-shadow:0 2px 16px rgba(0,0,0,.25);position:sticky;top:0;z-index:100}
.logo{display:flex;align-items:center;gap:12px}
.logo-icon{width:36px;height:36px;background:var(--gold);border-radius:8px;
  display:flex;align-items:center;justify-content:center;font-size:18px}
.logo-text{font-family:'DM Serif Display',serif;color:var(--white);font-size:20px;letter-spacing:.3px}
.logo-sub{color:var(--blue-200);font-size:11px;font-weight:400;margin-top:-2px}
.header-right{display:flex;align-items:center;gap:16px}
.badge-date{background:rgba(255,255,255,.12);color:var(--white);font-size:12px;
  padding:4px 12px;border-radius:20px;border:1px solid rgba(255,255,255,.2)}

/* TABS */
.tabs-bar{background:var(--white);border-bottom:1.5px solid var(--gray-200);
  padding:0 32px;display:flex;gap:4px;position:sticky;top:64px;z-index:99;
  box-shadow:0 1px 4px rgba(0,0,0,.06)}
.tab-btn{padding:16px 20px;font-size:13px;font-weight:500;color:var(--gray-500);
  border:none;background:transparent;cursor:pointer;border-bottom:3px solid transparent;
  transition:all .2s;display:flex;align-items:center;gap:7px;margin-bottom:-1.5px}
.tab-btn:hover{color:var(--blue-500)}
.tab-btn.active{color:var(--blue-500);border-bottom-color:var(--blue-500);font-weight:600}
.tab-icon{font-size:16px}

/* CONTENT */
.content{padding:28px 32px;max-width:1400px;margin:0 auto}
.view{display:none}.view.active{display:block}

/* KPI CARDS */
.kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-bottom:24px}
.kpi-card{background:var(--white);border-radius:var(--radius);padding:20px 22px;
  box-shadow:var(--shadow);border-left:4px solid var(--blue-400);transition:transform .2s}
.kpi-card:hover{transform:translateY(-2px)}
.kpi-card.green{border-left-color:var(--green)}
.kpi-card.amber{border-left-color:var(--amber)}
.kpi-card.red{border-left-color:var(--red)}
.kpi-label{font-size:12px;color:var(--gray-500);font-weight:500;text-transform:uppercase;letter-spacing:.05em}
.kpi-value{font-size:28px;font-weight:700;color:var(--blue-900);margin:4px 0;line-height:1}
.kpi-sub{font-size:12px;color:var(--gray-500)}
.kpi-trend{font-size:12px;font-weight:600;margin-top:4px}
.kpi-trend.up{color:var(--green)}.kpi-trend.down{color:var(--red)}

/* CHARTS ROW */
.charts-row{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:24px}
.chart-card{background:var(--white);border-radius:var(--radius);padding:20px;box-shadow:var(--shadow)}
.chart-card.full{grid-column:1/-1}
.chart-title{font-size:14px;font-weight:600;color:var(--gray-700);margin-bottom:16px;
  display:flex;align-items:center;justify-content:space-between}
.chart-wrap{position:relative;height:260px}

/* TABLE */
.table-card{background:var(--white);border-radius:var(--radius);box-shadow:var(--shadow);overflow:hidden;margin-bottom:20px}
.table-header{padding:16px 20px;border-bottom:1px solid var(--gray-200);
  display:flex;align-items:center;justify-content:space-between}
.table-title{font-size:14px;font-weight:600;color:var(--gray-700)}
.table-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse}
th{background:var(--gray-50);padding:10px 14px;text-align:left;font-size:11px;
   font-weight:600;color:var(--gray-500);text-transform:uppercase;letter-spacing:.04em;
   border-bottom:1px solid var(--gray-200)}
td{padding:11px 14px;font-size:13px;border-bottom:1px solid var(--gray-100);vertical-align:middle}
tr:hover td{background:var(--blue-100)}
tr:last-child td{border-bottom:none}

/* BADGES */
.badge{display:inline-flex;align-items:center;gap:4px;padding:3px 10px;border-radius:20px;
  font-size:11px;font-weight:600;white-space:nowrap}
.badge-green{background:var(--green-light);color:var(--green)}
.badge-red{background:var(--red-light);color:var(--red)}
.badge-amber{background:var(--amber-light);color:var(--amber)}
.badge-blue{background:var(--blue-100);color:var(--blue-700)}

/* ALERTS */
.alerts-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px;margin-bottom:24px}
.alert-item{background:var(--white);border-radius:var(--radius);padding:14px 16px;
  box-shadow:var(--shadow);display:flex;align-items:center;gap:12px;border-left:4px solid}
.alert-item.critico{border-left-color:var(--red)}
.alert-item.exceso{border-left-color:var(--amber)}
.alert-item.riesgo{border-left-color:#F57C00}
.alert-icon{width:36px;height:36px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0}
.alert-info .title{font-size:13px;font-weight:600;color:var(--gray-900)}
.alert-info .sub{font-size:12px;color:var(--gray-500);margin-top:2px}

/* LOADING */
.loading{text-align:center;padding:60px;color:var(--gray-500)}
.spinner{width:40px;height:40px;border:3px solid var(--gray-200);
  border-top-color:var(--blue-400);border-radius:50%;animation:spin .8s linear infinite;margin:0 auto 12px}
@keyframes spin{to{transform:rotate(360deg)}}

/* SECTION TITLE */
.section-title{font-size:16px;font-weight:700;color:var(--gray-900);margin-bottom:16px;
  display:flex;align-items:center;gap:8px}
.section-title::after{content:'';flex:1;height:1px;background:var(--gray-200);margin-left:8px}

/* FILTER BAR */
.filter-bar{display:flex;gap:10px;margin-bottom:20px;flex-wrap:wrap;align-items:center}
.filter-bar select,.filter-bar input{padding:8px 12px;border:1.5px solid var(--gray-200);
  border-radius:8px;font-size:13px;font-family:inherit;color:var(--gray-700);background:var(--white)}
.filter-bar select:focus,.filter-bar input:focus{outline:none;border-color:var(--blue-400)}
.btn{padding:8px 16px;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;
  border:none;transition:all .2s;font-family:inherit}
.btn-primary{background:var(--blue-500);color:var(--white)}
.btn-primary:hover{background:var(--blue-700)}

/* EMPTY */
.empty{text-align:center;padding:40px;color:var(--gray-500);font-size:14px}
</style>
</head>
<body>

<!-- HEADER -->
<header class="header">
  <div class="logo">
    <div class="logo-icon">👗</div>
    <div>
      <div class="logo-text">Intelligent Fashion Predictor</div>
      <div class="logo-sub">Sistema de predicción de demanda · Manufactura textil</div>
    </div>
  </div>
  <div class="header-right">
    <div class="badge-date" id="fechaHoy"></div>
  </div>
</header>

<!-- TABS -->
<div class="tabs-bar">
  <button class="tab-btn active" onclick="showTab('planeacion')">
    <span class="tab-icon">📊</span>Planeación
  </button>
  <button class="tab-btn" onclick="showTab('comercial')">
    <span class="tab-icon">🏪</span>Comercial
  </button>
  <button class="tab-btn" onclick="showTab('despachos')">
    <span class="tab-icon">📦</span>Despachos
  </button>
</div>

<!-- ══════════ PLANEACIÓN ══════════ -->
<div class="content">
<div id="view-planeacion" class="view active">
  <div id="plan-content"><div class="loading"><div class="spinner"></div>Cargando datos de planeación...</div></div>
</div>

<!-- ══════════ COMERCIAL ══════════ -->
<div id="view-comercial" class="view">
  <div id="com-content"><div class="loading"><div class="spinner"></div>Cargando datos comerciales...</div></div>
</div>

<!-- ══════════ DESPACHOS ══════════ -->
<div id="view-despachos" class="view">
  <div id="des-content"><div class="loading"><div class="spinner"></div>Cargando datos de despachos...</div></div>
</div>
</div>

<script>
// ── Estado de la app ─────────────────────────────────────
const state = { loaded: {} };

// Fecha hoy
document.getElementById('fechaHoy').textContent =
  new Date().toLocaleDateString('es-CO',{weekday:'long',year:'numeric',month:'long',day:'numeric'});

// ── Cambio de tab ────────────────────────────────────────
function showTab(tab) {
  document.querySelectorAll('.tab-btn').forEach((b,i) => {
    b.classList.toggle('active', ['planeacion','comercial','despachos'][i]===tab);
  });
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.getElementById('view-'+tab).classList.add('active');
  if (!state.loaded[tab]) { loadView(tab); state.loaded[tab]=true; }
}

// ── Fetch helper ─────────────────────────────────────────
async function api(path) {
  const r = await fetch(path);
  return r.json();
}

function fmt(n) { return Number(n).toLocaleString('es-CO'); }
function fmtM(n) { return '$' + (n/1000000).toFixed(1) + 'M'; }
function fmtPct(n) { return Number(n).toFixed(1) + '%'; }

// ── COLORES CHART ────────────────────────────────────────
const BLUES = ['#0B2447','#19376D','#1565C0','#1976D2','#42A5F5','#90CAF9','#BBDEFB'];
const MULTI = ['#1565C0','#2E7D32','#E65100','#C62828','#6A1B9A','#00695C','#F57F17'];

// ════════════════════════════════════════════════════════
// VISTA PLANEACIÓN
// ════════════════════════════════════════════════════════
async function loadPlaneacion() {
  const [resumen, forecast, produccion, alertas] = await Promise.all([
    api('/api/resumen'),
    api('/api/forecast/agregado'),
    api('/api/produccion'),
    api('/api/alertas?limite=6'),
  ]);

  const html = `
  <!-- KPIs -->
  <div class="kpi-grid">
    <div class="kpi-card">
      <div class="kpi-label">Predicciones generadas</div>
      <div class="kpi-value">${fmt(resumen.forecast_predicciones)}</div>
      <div class="kpi-sub">8 semanas · todas las tiendas</div>
    </div>
    <div class="kpi-card green">
      <div class="kpi-label">Unidades forecast 4 sem.</div>
      <div class="kpi-value">${fmt(resumen.unidades_forecast_4sem)}</div>
      <div class="kpi-sub">Próximas 4 semanas</div>
    </div>
    <div class="kpi-card amber">
      <div class="kpi-label">Inversión producción</div>
      <div class="kpi-value">${fmtM(resumen.inversion_produccion)}</div>
      <div class="kpi-sub">Plan período actual</div>
    </div>
    <div class="kpi-card ${resumen.alertas_criticas>0?'red':'green'}">
      <div class="kpi-label">Alertas críticas</div>
      <div class="kpi-value">${resumen.alertas_criticas}</div>
      <div class="kpi-sub">Quiebres de stock activos</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Precisión del modelo</div>
      <div class="kpi-value">${fmtPct(resumen.mape_modelo)}</div>
      <div class="kpi-sub">MAPE · error de predicción</div>
    </div>
  </div>

  <!-- Alertas de inventario -->
  ${alertas.data && alertas.data.length > 0 ? `
  <div class="section-title">🚨 Alertas de inventario</div>
  <div class="alerts-grid">
    ${alertas.data.slice(0,6).map(a => `
    <div class="alert-item ${a.alerta_stock==='CRITICO'?'critico':a.alerta_stock==='EXCESO'?'exceso':'riesgo'}">
      <div class="alert-icon" style="background:${a.alerta_stock==='CRITICO'?'#FFEBEE':a.alerta_stock==='EXCESO'?'#FFF3E0':'#FFF8E1'}">
        ${a.alerta_stock==='CRITICO'?'🔴':a.alerta_stock==='EXCESO'?'🟡':'🟠'}
      </div>
      <div class="alert-info">
        <div class="title">${a.tipo_producto}</div>
        <div class="sub">Cobertura: ${a.cobertura_semanas} sem · ${a.alerta_stock}</div>
      </div>
    </div>`).join('')}
  </div>` : ''}

  <!-- Gráficas -->
  <div class="charts-row">
    <div class="chart-card">
      <div class="chart-title">Forecast por tipo de producto (8 sem.)</div>
      <div class="chart-wrap"><canvas id="chart-forecast-tipo"></canvas></div>
    </div>
    <div class="chart-card">
      <div class="chart-title">Distribución forecast por familia</div>
      <div class="chart-wrap"><canvas id="chart-forecast-familia"></canvas></div>
    </div>
  </div>

  <!-- Producción recomendada -->
  <div class="section-title">🏭 Plan de producción recomendado</div>
  <div class="table-card">
    <div class="table-wrap">
      <table>
        <tr><th>Tipo de producto</th><th>Familia</th><th>Unidades</th><th>Inversión</th><th>Inicio producción</th><th>Llegada CEDI</th><th>Estado</th></tr>
        ${produccion.data.map(p=>`
        <tr>
          <td><strong>${p.tipo_producto}</strong></td>
          <td>${p.familia}</td>
          <td>${fmt(p.unidades_totales)}</td>
          <td>${fmtM(p.inversion_estimada)}</td>
          <td>${p.semana_inicio_prod}</td>
          <td>${p.semana_llegada_cedi}</td>
          <td><span class="badge badge-blue">${p.estado}</span></td>
        </tr>`).join('')}
      </table>
    </div>
  </div>`;

  document.getElementById('plan-content').innerHTML = html;

  // Chart forecast por tipo
  const tiposData = {};
  (forecast.data||[]).forEach(r => {
    tiposData[r.tipo_producto] = (tiposData[r.tipo_producto]||0) + (r.forecast_total||0);
  });
  const tipos = Object.keys(tiposData).sort((a,b)=>tiposData[b]-tiposData[a]).slice(0,10);
  new Chart(document.getElementById('chart-forecast-tipo'), {
    type:'bar',
    data:{
      labels: tipos,
      datasets:[{label:'Unidades forecast',data:tipos.map(t=>Math.round(tiposData[t])),
        backgroundColor:BLUES[2],borderRadius:6}]
    },
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false}},
      scales:{x:{ticks:{font:{size:10}}},y:{ticks:{font:{size:10}}}}}
  });

  // Chart por familia
  const famData = {};
  (forecast.data||[]).forEach(r => {
    famData[r.familia] = (famData[r.familia]||0) + (r.forecast_total||0);
  });
  new Chart(document.getElementById('chart-forecast-familia'), {
    type:'doughnut',
    data:{
      labels:Object.keys(famData),
      datasets:[{data:Object.values(famData).map(Math.round),
        backgroundColor:BLUES,borderWidth:2,borderColor:'#fff'}]
    },
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{position:'right',labels:{font:{size:11}}}}}
  });
}

// ════════════════════════════════════════════════════════
// VISTA COMERCIAL
// ════════════════════════════════════════════════════════
async function loadComercial() {
  const [gmroii, sellthrough, forecast] = await Promise.all([
    api('/api/gmroii?limite=20'),
    api('/api/sellthrough'),
    api('/api/forecast/agregado'),
  ]);

  const html = `
  <!-- KPIs -->
  <div class="kpi-grid">
    <div class="kpi-card green">
      <div class="kpi-label">GMROII promedio red</div>
      <div class="kpi-value">${(gmroii.gmroii_promedio||0).toFixed(2)}</div>
      <div class="kpi-sub">Retorno por peso invertido</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Tiendas sobre objetivo</div>
      <div class="kpi-value">${gmroii.tiendas_sobre_objetivo||0}</div>
      <div class="kpi-sub">GMROII ≥ 1.8</div>
    </div>
    <div class="kpi-card amber">
      <div class="kpi-label">Tiendas bajo objetivo</div>
      <div class="kpi-value">${gmroii.tiendas_bajo_objetivo||0}</div>
      <div class="kpi-sub">Requieren atención</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Sell-through promedio</div>
      <div class="kpi-value">${fmtPct(sellthrough.promedio||0)}</div>
      <div class="kpi-sub">% inventario vendido</div>
    </div>
  </div>

  <!-- Gráficas -->
  <div class="charts-row">
    <div class="chart-card">
      <div class="chart-title">GMROII por tipo de producto</div>
      <div class="chart-wrap"><canvas id="chart-gmroii-tipo"></canvas></div>
    </div>
    <div class="chart-card">
      <div class="chart-title">Forecast próximas 8 semanas por familia</div>
      <div class="chart-wrap"><canvas id="chart-trend-familia"></canvas></div>
    </div>
  </div>

  <!-- Ranking tiendas -->
  <div class="section-title">🏆 Ranking de tiendas por GMROII</div>
  <div class="table-card">
    <div class="table-wrap">
      <table>
        <tr><th>#</th><th>Tienda</th><th>Ciudad</th><th>Formato</th><th>GMROII</th><th>Estado</th></tr>
        ${(gmroii.data||[]).slice(0,15).map((t,i)=>`
        <tr>
          <td><strong>${i+1}</strong></td>
          <td>${t.nombre_tienda||'Tienda '+t.tienda_id}</td>
          <td>${t.ciudad||'-'}</td>
          <td>${t.formato||'-'}</td>
          <td><strong>${(t.gmroii_proyectado||0).toFixed(2)}</strong></td>
          <td><span class="badge ${(t.gmroii_proyectado||0)>=1.8?'badge-green':'badge-red'}">
            ${(t.gmroii_proyectado||0)>=1.8?'✅ OK':'⚠️ Bajo'}</span></td>
        </tr>`).join('')}
      </table>
    </div>
  </div>`;

  document.getElementById('com-content').innerHTML = html;

  // Chart GMROII por tipo
  const gData = {};
  (gmroii.data||[]).forEach(r => {
    if (r.tipo_producto) {
      if (!gData[r.tipo_producto]) gData[r.tipo_producto] = [];
      gData[r.tipo_producto].push(r.gmroii_proyectado||0);
    }
  });
  const gTipos = Object.keys(gData);
  const gVals  = gTipos.map(t => gData[t].reduce((a,b)=>a+b,0)/gData[t].length);
  new Chart(document.getElementById('chart-gmroii-tipo'), {
    type:'bar',
    data:{
      labels:gTipos,
      datasets:[{label:'GMROII',data:gVals.map(v=>+v.toFixed(2)),
        backgroundColor:gVals.map(v=>v>=1.8?'#2E7D32':'#C62828'),borderRadius:6}]
    },
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false}},
      scales:{x:{ticks:{font:{size:9}}},y:{beginAtZero:true,
        ticks:{font:{size:10}},
        annotations:{line1:{type:'line',yMin:1.8,yMax:1.8,borderColor:'#C62828',borderDash:[5,5]}}}}}
  });

  // Chart tendencia forecast
  const semanas = [...new Set((forecast.data||[]).map(r=>r.semana_objetivo))].sort().slice(0,8);
  const familias = [...new Set((forecast.data||[]).map(r=>r.familia))];
  const datasets = familias.map((f,i)=>({
    label:f,
    data:semanas.map(s=>{
      const rows = (forecast.data||[]).filter(r=>r.familia===f && r.semana_objetivo===s);
      return Math.round(rows.reduce((a,r)=>a+(r.forecast_total||0),0));
    }),
    borderColor:MULTI[i%MULTI.length],
    backgroundColor:MULTI[i%MULTI.length]+'22',
    fill:true,tension:.4,pointRadius:3
  }));
  new Chart(document.getElementById('chart-trend-familia'), {
    type:'line',
    data:{labels:semanas,datasets},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{position:'bottom',labels:{font:{size:10},boxWidth:12}}},
      scales:{x:{ticks:{font:{size:9}}},y:{ticks:{font:{size:10}}}}}
  });
}

// ════════════════════════════════════════════════════════
// VISTA DESPACHOS
// ════════════════════════════════════════════════════════
async function loadDespachos() {
  const [despachos, inventario] = await Promise.all([
    api('/api/despachos?limite=200'),
    api('/api/inventario/cobertura'),
  ]);

  const aprobados = (despachos.data||[]).filter(d=>d.estado==='APROBADO');
  const revisar   = (despachos.data||[]).filter(d=>d.estado==='REVISAR');

  const html = `
  <!-- KPIs -->
  <div class="kpi-grid">
    <div class="kpi-card green">
      <div class="kpi-label">Despachos aprobados</div>
      <div class="kpi-value">${aprobados.length}</div>
      <div class="kpi-sub">GMROII ≥ 1.8 · listos para ejecutar</div>
    </div>
    <div class="kpi-card amber">
      <div class="kpi-label">Despachos a revisar</div>
      <div class="kpi-value">${revisar.length}</div>
      <div class="kpi-sub">GMROII bajo · requieren aprobación</div>
    </div>
    <div class="kpi-card red">
      <div class="kpi-label">Tiendas con quiebre</div>
      <div class="kpi-value">${inventario.criticos||0}</div>
      <div class="kpi-sub">Stock en cero</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Tiendas con exceso</div>
      <div class="kpi-value">${inventario.excesos||0}</div>
      <div class="kpi-sub">Cobertura > 8 semanas</div>
    </div>
  </div>

  <!-- Gráfica cobertura -->
  <div class="charts-row">
    <div class="chart-card">
      <div class="chart-title">Distribución de alertas de inventario</div>
      <div class="chart-wrap"><canvas id="chart-alertas-dist"></canvas></div>
    </div>
    <div class="chart-card">
      <div class="chart-title">GMROII de despachos recomendados</div>
      <div class="chart-wrap"><canvas id="chart-gmroii-desp"></canvas></div>
    </div>
  </div>

  <!-- Tabla despachos aprobados -->
  <div class="section-title">✅ Despachos aprobados — listos para ejecutar</div>
  <div class="table-card">
    <div class="table-wrap">
      <table>
        <tr><th>Tienda ID</th><th>Tipo producto</th><th>Unidades</th><th>Semana despacho</th><th>Cobertura actual</th><th>GMROII</th><th>Estado</th></tr>
        ${aprobados.length>0 ? aprobados.map(d=>`
        <tr>
          <td><strong>${d.tienda_id}</strong></td>
          <td>${d.tipo_producto}</td>
          <td><strong>${fmt(d.unidades_sugeridas)}</strong></td>
          <td>${d.semana_despacho}</td>
          <td>${(d.cobertura_actual||0).toFixed(1)} sem</td>
          <td><strong style="color:var(--green)">${(d.gmroii_proyectado||0).toFixed(2)}</strong></td>
          <td><span class="badge badge-green">✅ APROBADO</span></td>
        </tr>`).join('') : '<tr><td colspan="7" class="empty">No hay despachos aprobados hoy</td></tr>'}
      </table>
    </div>
  </div>

  <!-- Tabla revisar -->
  ${revisar.length>0?`
  <div class="section-title">⚠️ Despachos a revisar</div>
  <div class="table-card">
    <div class="table-wrap">
      <table>
        <tr><th>Tienda ID</th><th>Tipo producto</th><th>Unidades</th><th>Cobertura actual</th><th>GMROII</th><th>Estado</th></tr>
        ${revisar.slice(0,20).map(d=>`
        <tr>
          <td>${d.tienda_id}</td>
          <td>${d.tipo_producto}</td>
          <td>${fmt(d.unidades_sugeridas)}</td>
          <td>${(d.cobertura_actual||0).toFixed(1)} sem</td>
          <td style="color:var(--amber)"><strong>${(d.gmroii_proyectado||0).toFixed(2)}</strong></td>
          <td><span class="badge badge-amber">⚠️ REVISAR</span></td>
        </tr>`).join('')}
      </table>
    </div>
  </div>`:''}`;

  document.getElementById('des-content').innerHTML = html;

  // Chart alertas
  new Chart(document.getElementById('chart-alertas-dist'), {
    type:'doughnut',
    data:{
      labels:['OK','Quiebre Riesgo','Exceso','Crítico'],
      datasets:[{data:[inventario.ok||0,inventario.riesgo||0,inventario.excesos||0,inventario.criticos||0],
        backgroundColor:['#2E7D32','#F57C00','#E65100','#C62828'],borderWidth:2,borderColor:'#fff'}]
    },
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{position:'right',labels:{font:{size:11}}}}}
  });

  // Chart GMROII despachos
  const gmroiiBins = {'<1.0':0,'1.0-1.5':0,'1.5-1.8':0,'1.8-2.5':0,'>2.5':0};
  (despachos.data||[]).forEach(d=>{
    const g=d.gmroii_proyectado||0;
    if(g<1) gmroiiBins['<1.0']++;
    else if(g<1.5) gmroiiBins['1.0-1.5']++;
    else if(g<1.8) gmroiiBins['1.5-1.8']++;
    else if(g<2.5) gmroiiBins['1.8-2.5']++;
    else gmroiiBins['>2.5']++;
  });
  new Chart(document.getElementById('chart-gmroii-desp'), {
    type:'bar',
    data:{
      labels:Object.keys(gmroiiBins),
      datasets:[{label:'Despachos',data:Object.values(gmroiiBins),
        backgroundColor:['#C62828','#E65100','#F57C00','#2E7D32','#1B5E20'],borderRadius:6}]
    },
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false}},
      scales:{x:{ticks:{font:{size:11}}},y:{ticks:{font:{size:10}}}}}
  });
}

// ── Cargar vista según tab ────────────────────────────────
function loadView(tab) {
  if (tab==='planeacion') loadPlaneacion();
  else if (tab==='comercial') loadComercial();
  else if (tab==='despachos') loadDespachos();
}

// Cargar primera vista
loadPlaneacion();
state.loaded['planeacion'] = true;
</script>
</body>
</html>'''

# ── ENDPOINTS API ─────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return DASHBOARD_HTML

@app.get("/api/resumen")
async def resumen():
    try:
        fc   = sb.table('output_forecast_semanal').select('*',count='exact').limit(1).execute()
        dep  = sb.table('output_despachos_recomendados').select('*',count='exact').limit(1).execute()
        prod = sb.table('output_produccion_recomendada').select('*').execute()
        inv  = sb.table('fact_inventario_semanal').select('*',count='exact').eq('alerta_stock','CRITICO').limit(1).execute()
        fc4  = sb.table('output_forecast_semanal').select('forecast_medio').limit(5000).execute()
        total_fc4 = sum(r.get('forecast_medio',0) or 0 for r in fc4.data)
        inv_prod  = sum(r.get('inversion_estimada',0) or 0 for r in prod.data)

        import pickle
        mape = 0
        model_path = Path(__file__).parent.parent / 'outputs' / 'modelo_lgbm.pkl'
        if model_path.exists():
            with open(model_path,'rb') as f:
                saved = pickle.load(f)
            mape = saved.get('mape', 0)

        return {
            "forecast_predicciones":  fc.count or 0,
            "despachos_total":        dep.count or 0,
            "tipos_produccion":       len(prod.data),
            "alertas_criticas":       inv.count or 0,
            "unidades_forecast_4sem": round(total_fc4),
            "inversion_produccion":   inv_prod,
            "mape_modelo":            round(mape, 1),
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/forecast/agregado")
async def forecast_agregado():
    try:
        data = sb.table('output_forecast_semanal').select('*').limit(10000).execute().data
        agg = {}
        for r in data:
            key = (r.get('tipo_producto'), r.get('familia'), r.get('semana_objetivo'))
            if key not in agg:
                agg[key] = {'tipo_producto':r.get('tipo_producto'),
                            'familia':r.get('familia'),
                            'semana_objetivo':r.get('semana_objetivo'),
                            'forecast_total':0}
            agg[key]['forecast_total'] += r.get('forecast_medio') or 0
        return {"total": len(agg), "data": list(agg.values())}
    except Exception as e:
        return {"error": str(e), "data": []}

@app.get("/api/produccion")
async def produccion():
    try:
        data = sb.table('output_produccion_recomendada').select('*').order('fecha_ejecucion',desc=True).limit(100).execute().data
        return {"total": len(data), "data": data}
    except Exception as e:
        return {"error": str(e), "data": []}

@app.get("/api/alertas")
async def alertas(limite: int = 20):
    try:
        fecha_max = sb.table('fact_inventario_semanal').select('fecha').order('fecha',desc=True).limit(1).execute().data
        if not fecha_max: return {"data": []}
        fmax = fecha_max[0]['fecha']
        data = sb.table('fact_inventario_semanal').select('*').eq('fecha',fmax).neq('alerta_stock','OK').limit(limite).execute().data
        return {"total": len(data), "data": data}
    except Exception as e:
        return {"error": str(e), "data": []}

@app.get("/api/gmroii")
async def gmroii(limite: int = 50):
    try:
        data = sb.table('output_despachos_recomendados').select('*').order('gmroii_proyectado',desc=True).limit(limite).execute().data
        if not data: return {"data":[],"gmroii_promedio":0,"tiendas_sobre_objetivo":0,"tiendas_bajo_objetivo":0}
        vals = [r.get('gmroii_proyectado') or 0 for r in data]
        prom = sum(vals)/len(vals) if vals else 0
        return {
            "gmroii_promedio":        round(prom, 2),
            "tiendas_sobre_objetivo": sum(1 for v in vals if v >= 1.8),
            "tiendas_bajo_objetivo":  sum(1 for v in vals if v < 1.8),
            "data": data
        }
    except Exception as e:
        return {"error": str(e), "data": []}

@app.get("/api/sellthrough")
async def sellthrough():
    try:
        fecha_max = sb.table('fact_inventario_semanal').select('fecha').order('fecha',desc=True).limit(1).execute().data
        if not fecha_max: return {"promedio": 0, "data": []}
        fmax = fecha_max[0]['fecha']
        data = sb.table('fact_inventario_semanal').select('cobertura_semanas,tipo_producto,familia').eq('fecha',fmax).limit(2000).execute().data
        vals = [r.get('cobertura_semanas') or 0 for r in data if r.get('cobertura_semanas')]
        # Sell-through estimado de cobertura
        st = max(0, min(100, 100 - (sum(vals)/len(vals) if vals else 0) * 8))
        return {"promedio": round(st, 1), "data": data[:50]}
    except Exception as e:
        return {"error": str(e), "promedio": 0}

@app.get("/api/despachos")
async def despachos(estado: Optional[str] = None, limite: int = 200):
    try:
        q = sb.table('output_despachos_recomendados').select('*').order('gmroii_proyectado',desc=True).limit(limite)
        if estado: q = q.eq('estado', estado)
        data = q.execute().data
        return {"total": len(data), "data": data}
    except Exception as e:
        return {"error": str(e), "data": []}

@app.get("/api/inventario/cobertura")
async def inventario_cobertura():
    try:
        fecha_max = sb.table('fact_inventario_semanal').select('fecha').order('fecha',desc=True).limit(1).execute().data
        if not fecha_max: return {"ok":0,"riesgo":0,"excesos":0,"criticos":0}
        fmax = fecha_max[0]['fecha']
        conteos = {"OK":0,"QUIEBRE_RIESGO":0,"EXCESO":0,"CRITICO":0}
        data = sb.table('fact_inventario_semanal').select('alerta_stock').eq('fecha',fmax).limit(50000).execute().data
        for r in data:
            k = r.get('alerta_stock','OK')
            conteos[k] = conteos.get(k,0)+1
        return {
            "ok":      conteos.get('OK',0),
            "riesgo":  conteos.get('QUIEBRE_RIESGO',0),
            "excesos": conteos.get('EXCESO',0),
            "criticos":conteos.get('CRITICO',0),
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/health")
async def health():
    return {"status": "ok", "app": "Intelligent Fashion Predictor"}
