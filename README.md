# 👗 Intelligent Fashion Predictor

> Sistema de predicción de demanda para manufactura textil de moda  
> 89 tiendas · Colombia · Planeación mensual con horizonte de 20 semanas

---

## ¿Qué hace?

| Motor | Pregunta | Horizonte |
|-------|----------|-----------|
| **Motor 1** | ¿Cuánto se va a vender? | 8 semanas |
| **Motor 2** | ¿Qué despachar a cada tienda? | 1–4 semanas |
| **Motor 3** | ¿Qué producir y en qué cantidad? | 13–20 semanas |

---

## Inicio rápido

### Con Docker (recomendado)

```bash
# 1. Clonar
git clone https://github.com/luisapython13-ops/modelo_demanda_moda.git
cd modelo_demanda_moda

# 2. Crear .env con credenciales
cp .env.example .env
# Editar .env con tus credenciales de Supabase

# 3. Levantar
docker-compose up --build
```

Abrir: **http://localhost:8000**

### En Codespaces

```bash
# 1. Crear .env
python3 -c "
open('.env','w').write('''SUPABASE_URL=https://imtigjfydbtzhpaiovmr.supabase.co
SUPABASE_ANON_KEY=TU_ANON_KEY
SUPABASE_SERVICE_KEY=TU_SERVICE_KEY
''')
"

# 2. Instalar dependencias
pip install -r docker/requirements.txt

# 3. Inicializar pipeline completo
python startup.py

# 4. Levantar API
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

---

## Estructura

```
├── api/
│   └── main.py                # FastAPI + Dashboard HTML
├── scripts/
│   ├── generar_datos.py       # Genera datos simulados
│   ├── cargar_datos.py        # Carga Excel → Supabase
│   ├── motor1_forecast.py     # LightGBM forecast
│   └── motores_2_3.py         # Despachos + Producción
├── datos_excel/               # Archivos Excel
├── outputs/                   # Modelo entrenado + Excel resultados
├── sql/                       # DDL Supabase
├── startup.py                 # Orquestador automático
├── Dockerfile
└── docker-compose.yml
```

---

## Dashboard

Tres vistas por rol:

- **📊 Planeación** — Forecast, alertas de inventario, plan de producción
- **🏪 Comercial** — GMROII por tienda, sell-through, tendencias
- **📦 Despachos** — Lista de despachos aprobados, alertas de quiebre

---

## Stack

| Capa | Tecnología |
|------|-----------|
| ML | LightGBM · MAPE < 20% |
| API | FastAPI + Python |
| Base de datos | PostgreSQL — Supabase |
| Frontend | HTML/CSS/JS + Chart.js |
| Contenedores | Docker + Docker Compose |
