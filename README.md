# 🧵 Modelo Predictivo de Demanda — Manufactura Textil Moda Colombia

> Proyecto universitario · Planeación de demanda y supply chain  
> Manufactura textil vestuario de moda · 89 tiendas nacionales · 3 años de historia

---

## ¿Qué hace este modelo?

Cada lunes el sistema responde tres preguntas críticas para la operación:

| Motor | Pregunta | Horizonte |
|-------|----------|-----------|
| **Motor 1** | ¿Cuánto se va a vender por tienda y tipo de producto? | 8 semanas |
| **Motor 2** | ¿Qué despachar a cada tienda y cuándo? | 1–4 semanas |
| **Motor 3** | ¿Qué producir y en qué cantidad por tallas? | 13–20 semanas |

---

## Estructura del proyecto

```
modelo_demanda_moda/
│
├── datos_excel/                       # Archivos Excel con los datos del negocio
│   ├── dim_tiendas.xlsx               # 89 tiendas: ciudad, formato, perfil
│   ├── dim_tipos_producto.xlsx        # 15 tipos de producto con jerarquía y costos
│   ├── dim_eventos.xlsx               # Calendario de eventos Colombia
│   ├── ventas_2022.xlsx               # Ventas diarias por tienda y tipo de producto
│   ├── ventas_2023.xlsx
│   ├── ventas_2024.xlsx
│   ├── inventario_semanal_parte1.xlsx # Stock semanal por tienda
│   └── inventario_semanal_parte2.xlsx
│
├── sql/
│   └── 01_crear_tablas.sql            # Tablas, índices y vistas en Supabase
│
├── notebooks/
│   ├── conexion.py                    # Módulo de conexión a Supabase (lee .env)
│   ├── 01_carga_datos.ipynb           # Carga Excel → Supabase
│   ├── 02_modelo_forecast.ipynb       # Feature engineering + LightGBM + forecast
│   └── 03_despachos_produccion.ipynb  # Motor 2 (despachos) + Motor 3 (producción)
│
├── docker/
│   └── requirements.txt
│
├── outputs/                           # Generado al correr los notebooks
│   ├── modelo_lgbm.pkl                # Modelo entrenado
│   ├── despachos_semana.xlsx          # Lista de despachos recomendados
│   └── produccion_recomendada.xlsx    # Plan de producción
│
├── Dockerfile
├── docker-compose.yml
├── .env.example                       # Plantilla de credenciales
├── .gitignore
└── README.md
```

---

## Requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Git
- Cuenta en [Supabase](https://supabase.com) *(ya configurada)*

---

## Cómo ejecutar el proyecto

### 1 · Clonar el repositorio

```bash
git clone https://github.com/luisapython13-ops/modelo_demanda_moda.git
cd modelo_demanda_moda
```

### 2 · Configurar credenciales

```bash
cp .env.example .env
# Editar .env con las credenciales reales de Supabase
```

### 3 · Crear las tablas en Supabase

1. Ir a [supabase.com](https://supabase.com) → tu proyecto
2. **SQL Editor** → pegar y ejecutar `sql/01_crear_tablas.sql`

### 4 · Levantar el entorno con Docker

```bash
docker-compose up --build
```

Abrir en el navegador: **http://localhost:8888**  
Token: `modelo2024`

### 5 · Ejecutar los notebooks en orden

| Notebook | Descripción | Tiempo |
|----------|-------------|--------|
| `01_carga_datos.ipynb` | Carga Excel → Supabase | ~5 min |
| `02_modelo_forecast.ipynb` | Entrena modelo + genera forecast | ~10 min |
| `03_despachos_produccion.ipynb` | Genera despachos y producción | ~3 min |

---

## Tablas en Supabase

| Tabla | Descripción |
|-------|-------------|
| `dim_tiendas` | 89 tiendas con perfil y ubicación |
| `dim_tipos_producto` | Jerarquía: familia → categoría → tipo |
| `dim_eventos` | Calendario: Días sin IVA, Navidad, Carnaval, etc. |
| `fact_ventas_diarias` | Ventas con precios, descuentos y márgenes |
| `fact_inventario_semanal` | Stock semanal con alertas de cobertura |
| `output_forecast_semanal` | Predicciones del Motor 1 |
| `output_despachos_recomendados` | Recomendaciones del Motor 2 con GMROII |
| `output_produccion_recomendada` | Plan de producción del Motor 3 |
| `v_semaforo_inventario` | Vista: semáforo verde/amarillo/rojo por tienda |
| `v_gmroii_tienda` | Vista: GMROII mensual por tienda y categoría |

---

## Parámetros del modelo (ajustables)

| Parámetro | Valor por defecto | Descripción |
|-----------|-------------------|-------------|
| `COBERTURA_MIN_SEM` | 2.5 semanas | Mínimo de stock antes de resurtir |
| `COBERTURA_OBJ_SEM` | 6.0 semanas | Objetivo de stock al resurtir |
| `COBERTURA_MAX_SEM` | 8.0 semanas | Máximo antes de alertar exceso |
| `GMROII_MINIMO` | 1.8 | Mínimo de retorno por despacho |
| `SEMANAS_PRODUCCION` | 16 semanas | Lead time de manufactura |

---

## Conceptos clave

**GMROII** — Gross Margin Return on Inventory Investment  
`GMROII = Margen Bruto Proyectado / Costo del Inventario`  
Indica cuántos pesos de margen genera cada peso invertido.

**Sell-through** — % del inventario inicial ya vendido.

**Cobertura de semanas** — `Stock disponible / Venta promedio semanal`

---

## Stack tecnológico

| Capa | Tecnología |
|------|------------|
| Lenguaje | Python 3.11 |
| Modelo ML | LightGBM + scikit-learn |
| Base de datos | PostgreSQL — Supabase |
| Visualización | Plotly |
| Notebooks | JupyterLab |
| Contenedores | Docker + Docker Compose |
| Versiones | Git + GitHub |

---

## Equipo

Proyecto universitario — Supply chain & demand planning  
Manufactura textil vestuario de moda — Colombia
