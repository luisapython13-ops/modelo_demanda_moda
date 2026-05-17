-- ============================================================
-- MODELO PREDICTIVO DE DEMANDA - MANUFACTURA TEXTIL MODA
-- Base de datos: PostgreSQL (Supabase)
-- Ejecutar en orden: 01 → 02 → 03
-- ============================================================

-- ─────────────────────────────────────────────
-- DIMENSIÓN TIENDAS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dim_tiendas (
    tienda_id             SERIAL PRIMARY KEY,
    nombre_tienda         VARCHAR(100) NOT NULL,
    ciudad                VARCHAR(80)  NOT NULL,
    departamento          VARCHAR(80)  NOT NULL,
    formato               VARCHAR(50)  NOT NULL,  -- Centro Comercial | Calle | Outlet | Flagship
    metros_cuadrados      INT,
    capacidad_exhibicion  INT,
    segmento_cliente      VARCHAR(30),             -- Alto | Medio_Alto | Medio | Popular
    indice_rotacion       NUMERIC(5,2) DEFAULT 1.0,
    fecha_apertura        DATE,
    activa                BOOLEAN DEFAULT TRUE,
    cluster_tienda        INT,                     -- calculado por K-Means en Python
    created_at            TIMESTAMP DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- DIMENSIÓN TIPOS DE PRODUCTO
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dim_tipos_producto (
    tipo_producto         VARCHAR(60) PRIMARY KEY,
    familia               VARCHAR(30) NOT NULL,   -- Mujer | Hombre | Niño
    categoria             VARCHAR(50) NOT NULL,   -- Parte Superior | Inferior | Vestido | Abrigo
    precio_regular        INT         NOT NULL,
    costo_produccion      INT         NOT NULL,
    margen_objetivo_pct   NUMERIC(5,2),
    vida_semanas          INT         DEFAULT 12, -- semanas de vida esperada en tienda
    es_basico             BOOLEAN     DEFAULT FALSE,
    tallas_json           TEXT,                   -- JSON con distribución de tallas
    temporada_ciclo_sem   INT         DEFAULT 8,  -- cada cuántas semanas cambia la colección
    created_at            TIMESTAMP DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- DIMENSIÓN EVENTOS CALENDARIO
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dim_eventos (
    evento_id             SERIAL PRIMARY KEY,
    nombre_evento         VARCHAR(80) NOT NULL,
    fecha                 DATE        NOT NULL,
    alcance               VARCHAR(50) NOT NULL,   -- nacional | ciudad
    semanas_anticipacion  INT         DEFAULT 2,
    semanas_rebote        INT         DEFAULT 1,
    impacto_esperado_pct  NUMERIC(6,2),
    categorias_impactadas VARCHAR(50) DEFAULT 'TODAS',
    created_at            TIMESTAMP DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- FACT VENTAS DIARIAS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_ventas_diarias (
    venta_id          BIGSERIAL    PRIMARY KEY,
    fecha             DATE         NOT NULL,
    tienda_id         INT          NOT NULL REFERENCES dim_tiendas(tienda_id),
    tipo_producto     VARCHAR(60)  NOT NULL REFERENCES dim_tipos_producto(tipo_producto),
    familia           VARCHAR(30),
    unidades_vendidas INT          NOT NULL DEFAULT 0,
    precio_regular    INT,
    precio_venta      INT,
    descuento_pct     NUMERIC(5,2) DEFAULT 0,
    tipo_descuento    VARCHAR(20),                -- PRECIO_PLENO | PROMOCION_LEVE | PROMOCION_FUERTE | LIQUIDACION
    valor_venta       BIGINT,
    margen_bruto      BIGINT,
    es_precio_pleno   BOOLEAN      DEFAULT TRUE,
    created_at        TIMESTAMP DEFAULT NOW()
);

-- Índices para performance en queries del modelo
CREATE INDEX IF NOT EXISTS idx_ventas_fecha        ON fact_ventas_diarias(fecha);
CREATE INDEX IF NOT EXISTS idx_ventas_tienda       ON fact_ventas_diarias(tienda_id);
CREATE INDEX IF NOT EXISTS idx_ventas_tipo         ON fact_ventas_diarias(tipo_producto);
CREATE INDEX IF NOT EXISTS idx_ventas_fecha_tienda ON fact_ventas_diarias(fecha, tienda_id);

-- ─────────────────────────────────────────────
-- FACT INVENTARIO SEMANAL
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_inventario_semanal (
    inv_id                BIGSERIAL    PRIMARY KEY,
    fecha                 DATE         NOT NULL,  -- siempre lunes
    tienda_id             INT          NOT NULL REFERENCES dim_tiendas(tienda_id),
    tipo_producto         VARCHAR(60)  NOT NULL REFERENCES dim_tipos_producto(tipo_producto),
    familia               VARCHAR(30),
    unidades_disponibles  INT          DEFAULT 0,
    unidades_transito     INT          DEFAULT 0,
    costo_unitario        INT,
    valor_inventario      BIGINT,
    cobertura_semanas     NUMERIC(5,1),
    alerta_stock          VARCHAR(20), -- OK | QUIEBRE_RIESGO | EXCESO | CRITICO
    created_at            TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_inv_fecha       ON fact_inventario_semanal(fecha);
CREATE INDEX IF NOT EXISTS idx_inv_tienda      ON fact_inventario_semanal(tienda_id);
CREATE INDEX IF NOT EXISTS idx_inv_tipo        ON fact_inventario_semanal(tipo_producto);

-- ─────────────────────────────────────────────
-- TABLA DE OUTPUTS: FORECAST SEMANAL
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS output_forecast_semanal (
    forecast_id       BIGSERIAL    PRIMARY KEY,
    fecha_ejecucion   DATE         NOT NULL,  -- lunes en que corrió el modelo
    semana_objetivo   DATE         NOT NULL,  -- semana que se está prediciendo
    tienda_id         INT          NOT NULL REFERENCES dim_tiendas(tienda_id),
    tipo_producto     VARCHAR(60)  NOT NULL,
    familia           VARCHAR(30),
    forecast_bajo     NUMERIC(10,2),
    forecast_medio    NUMERIC(10,2),
    forecast_alto     NUMERIC(10,2),
    error_mape        NUMERIC(5,2),          -- error del modelo en validación
    created_at        TIMESTAMP DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- TABLA DE OUTPUTS: RECOMENDACIONES DESPACHO
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS output_despachos_recomendados (
    despacho_id         BIGSERIAL   PRIMARY KEY,
    fecha_ejecucion     DATE        NOT NULL,
    tienda_id           INT         NOT NULL REFERENCES dim_tiendas(tienda_id),
    tipo_producto       VARCHAR(60) NOT NULL,
    tipo_despacho       VARCHAR(20),          -- RESURTIDO | LANZAMIENTO | REDISTRIBUCION
    unidades_sugeridas  INT,
    semana_despacho     DATE,
    cobertura_actual    NUMERIC(5,1),
    cobertura_proyectada NUMERIC(5,1),
    gmroii_proyectado   NUMERIC(6,2),
    estado              VARCHAR(20) DEFAULT 'PENDIENTE', -- PENDIENTE | APROBADO | RECHAZADO
    created_at          TIMESTAMP DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- TABLA DE OUTPUTS: RECOMENDACIONES PRODUCCIÓN
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS output_produccion_recomendada (
    prod_id              BIGSERIAL   PRIMARY KEY,
    fecha_ejecucion      DATE        NOT NULL,
    tipo_producto        VARCHAR(60) NOT NULL,
    familia              VARCHAR(30),
    semana_inicio_prod   DATE,               -- cuándo debe arrancar la producción
    semana_llegada_cedi  DATE,               -- cuándo llega al CEDI
    unidades_totales     INT,
    distribucion_tallas  TEXT,               -- JSON con unidades por talla
    inversion_estimada   BIGINT,
    zona_pipeline        VARCHAR(10),        -- AZUL | AMARILLA | VERDE
    estado               VARCHAR(20) DEFAULT 'RECOMENDADO',
    created_at           TIMESTAMP DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- VISTA: SEMÁFORO SEMANAL DE INVENTARIO
-- ─────────────────────────────────────────────
CREATE OR REPLACE VIEW v_semaforo_inventario AS
SELECT
    i.fecha,
    t.nombre_tienda,
    t.ciudad,
    t.formato,
    i.tipo_producto,
    i.familia,
    i.unidades_disponibles,
    i.unidades_transito,
    i.cobertura_semanas,
    i.alerta_stock,
    i.valor_inventario,
    CASE
        WHEN i.alerta_stock = 'CRITICO'        THEN '🔴 CRÍTICO'
        WHEN i.alerta_stock = 'QUIEBRE_RIESGO' THEN '🟠 RIESGO'
        WHEN i.alerta_stock = 'EXCESO'         THEN '🟡 EXCESO'
        ELSE                                        '🟢 OK'
    END AS semaforo
FROM fact_inventario_semanal i
JOIN dim_tiendas t ON t.tienda_id = i.tienda_id
WHERE i.fecha = (SELECT MAX(fecha) FROM fact_inventario_semanal);

-- ─────────────────────────────────────────────
-- VISTA: KPIs GMROII POR TIENDA
-- ─────────────────────────────────────────────
CREATE OR REPLACE VIEW v_gmroii_tienda AS
SELECT
    v.tienda_id,
    t.nombre_tienda,
    t.ciudad,
    t.formato,
    v.tipo_producto,
    v.familia,
    DATE_TRUNC('month', v.fecha) AS mes,
    SUM(v.margen_bruto)                                          AS margen_total,
    SUM(v.valor_venta)                                           AS venta_total,
    SUM(v.unidades_vendidas)                                     AS unidades_total,
    AVG(i.valor_inventario)                                      AS inv_promedio,
    CASE
        WHEN AVG(i.valor_inventario) > 0
        THEN ROUND(SUM(v.margen_bruto) / AVG(i.valor_inventario), 2)
        ELSE NULL
    END                                                          AS gmroii,
    ROUND(AVG(v.descuento_pct), 1)                               AS descuento_promedio,
    ROUND(SUM(CASE WHEN v.es_precio_pleno THEN v.unidades_vendidas ELSE 0 END)::NUMERIC
          / NULLIF(SUM(v.unidades_vendidas),0) * 100, 1)         AS pct_precio_pleno
FROM fact_ventas_diarias v
JOIN dim_tiendas t ON t.tienda_id = v.tienda_id
LEFT JOIN fact_inventario_semanal i
       ON i.tienda_id = v.tienda_id
      AND i.tipo_producto = v.tipo_producto
      AND DATE_TRUNC('week', i.fecha) = DATE_TRUNC('week', v.fecha)
GROUP BY v.tienda_id, t.nombre_tienda, t.ciudad, t.formato,
         v.tipo_producto, v.familia, DATE_TRUNC('month', v.fecha);

COMMENT ON TABLE fact_ventas_diarias         IS 'Ventas diarias por tienda y tipo de producto';
COMMENT ON TABLE fact_inventario_semanal     IS 'Snapshot semanal de inventario por tienda';
COMMENT ON TABLE output_forecast_semanal     IS 'Forecast de ventas generado cada lunes por el modelo ML';
COMMENT ON TABLE output_despachos_recomendados IS 'Lista de despachos recomendados por el Motor 2';
COMMENT ON TABLE output_produccion_recomendada IS 'Recomendaciones de producción del Motor 3';
