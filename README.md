# PoC Neo4j — Exploración de capacidades con dominio RPG

Proof of concept completo de **Neo4j** (base de datos orientada a grafos) usando un catálogo de juego RPG como dominio de datos. El objetivo es analizar las capacidades de Neo4j: modelo de datos, lenguaje de consulta Cypher, algoritmos de grafos (GDS) e integración Python.

## Stack

| Componente | Versión / detalle |
|---|---|
| Neo4j Community | 5.26 |
| Plugin GDS | Graph Data Science (incluido en imagen Docker) |
| Driver Python | `neo4j` 5.28 oficial |
| Python | 3.x (venv) |
| Despliegue | Docker / docker-compose |

## Arranque rápido

```bash
# 1. Levantar Neo4j (esperar ~30s hasta "Started")
docker compose up -d
docker compose logs -f neo4j

# 2. Entorno Python
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. Cargar dataset RPG
python data/seed.py

# 4. Ejecutar ejemplos (en orden)
python examples/01_basics.py
python examples/02_cypher.py
python examples/03_gds.py
python examples/04_patterns.py
```

**Neo4j Browser**: `http://localhost:7474` — usuario `neo4j`, contraseña `titanpoc`  
**Bolt**: `bolt://localhost:7687`

## Estructura del proyecto

```
neoj4/
├── docker-compose.yml      # Neo4j 5 + GDS plugin
├── .env                    # Credenciales locales (no versionado)
├── .env.example            # Plantilla de variables
├── requirements.txt        # neo4j + python-dotenv + rich
├── data/
│   ├── db.py               # Conexión compartida (driver singleton)
│   └── seed.py             # Carga idempotente del dataset RPG
└── examples/
    ├── 01_basics.py        # CRUD, modelo de datos
    ├── 02_cypher.py        # Cypher avanzado
    ├── 03_gds.py           # Algoritmos de grafos (GDS)
    └── 04_patterns.py      # Patrones de uso real
```

## Dominio de datos: catálogo RPG

El dataset modela un mundo RPG con las siguientes entidades y relaciones:

```
(Character)-[:BELONGS_TO]->(Class)
(Character)-[:KNOWS]->(Skill)
(Character)-[:VISITS]->(Zone)
(Character)-[:COMPLETES]->(Quest)
(Class)-[:TEACHES]->(Skill)
(Zone)-[:CONNECTS_TO]->(Zone)
(Zone)-[:CONTAINS]->(Enemy)
(Enemy)-[:DROPS]->(Item)
(Quest)-[:TAKES_PLACE_IN]->(Zone)
(Quest)-[:REWARDS]->(Item)
```

**Volumen aproximado:** ~60 nodos, ~150 relaciones tras el seed.

### Entidades

- **5 clases**: Guerrero, Mago, Arquero, Clérigo, Pícaro
- **10 personajes** (nivel 10–20, HP variable por clase)
- **12 habilidades** (2 por clase + 2 universales)
- **7 zonas** (interconectadas, nivel 1–25, tipo pueblo/exterior/mazmorra)
- **6 enemigos** (nivel 5–27, distribuidos por zona)
- **7 items** (rareza común/raro/épico/legendario)
- **5 quests** (con nivel mínimo, zona y recompensa)

## Capacidades demostradas

### 01 — Modelo de datos y CRUD (`01_basics.py`)

- Esquema implícito: labels, propiedades, constraints únicos
- `CREATE`, `SET`, `MATCH`, `DETACH DELETE`
- `MERGE` como upsert idempotente
- Traversal básico: `(a)-[:REL]->(b)`
- Conteo de nodos y relaciones por tipo

### 02 — Cypher avanzado (`02_cypher.py`)

| Construcción | Qué demuestra |
|---|---|
| `WHERE` compuesto | Filtros multi-condición sobre propiedades |
| `OPTIONAL MATCH` | LEFT JOIN equivalente |
| `collect()` | Agregar resultados en listas |
| `shortestPath()` | Camino más corto entre nodos |
| `allShortestPaths()` | Todos los caminos óptimos |
| Path variable-length `[:REL*1..N]` | Traversal a profundidad variable |
| `WITH` + subconsultas | Encadenamiento de operaciones |
| `UNWIND` | Aplanar listas a filas |
| `CASE` | Expresiones condicionales |
| `EXISTS {}` / `NOT EXISTS {}` | Filtrado por existencia de subpatrones |

### 03 — Graph Data Science (`03_gds.py`)

Todos los algoritmos usan una **proyección en memoria** (`gds.graph.project`) que carga el subgrafo relevante en RAM de Neo4j para operaciones vectorizadas.

| Algoritmo | Para qué sirve |
|---|---|
| **PageRank** | Importancia relativa de nodos (influencia, autoridad) |
| **Betweenness Centrality** | Nodos "puente": críticos para la conectividad |
| **Degree Centrality** | Nodos con más conexiones directas |
| **Louvain** | Detección de comunidades (maximiza modularidad) |
| **Label Propagation** | Detección de comunidades (propagación iterativa, más rápido) |
| **Node Similarity** | Similitud entre nodos por vecinos compartidos (Jaccard) |
| **Triangle Count** | Densidad local del grafo (coeficiente de clustering) |

### 04 — Patrones de uso real (`04_patterns.py`)

| Patrón | Descripción |
|---|---|
| Filtrado colaborativo | "Quests que han completado personajes similares a ti" |
| Ruta de progresión | Zonas ordenadas por nivel/distancia desde el inicio |
| Loot alcanzable | Items conseguibles según zonas visitadas |
| Gap analysis | Items AÚN no alcanzables (qué zonas faltan) |
| Hub detection | Personajes con habilidades únicas (solo ellos las conocen) |
| Clase versátil | Ranking de clases por daño total de sus skills |
| Cadena multi-hop | `character → quest → zone → enemy → item` en una sola query |

## Comparativa: Neo4j vs alternativas

| Aspecto | Neo4j | PostgreSQL (relacional) | MongoDB (documental) |
|---|---|---|---|
| Modelo | Grafo (nodos + aristas + props) | Tablas + JOINs | Documentos JSON anidados |
| Consulta | Cypher (declarativo, orientado a patrones) | SQL | MQL / aggregation pipeline |
| Traversal profundo | Nativo, O(camino) | JOINs en cascada, costoso | `$lookup` anidado, limitado |
| Camino más corto | `shortestPath()` built-in | Requiere extensión (pgRouting) | No nativo |
| Algoritmos de grafos | GDS plugin (PageRank, comunidades…) | pgvector para similitud | No nativo |
| Esquema | Opcional (labels + constraints selectivos) | Rígido | Flexible |
| Mejor para | Redes, recomendaciones, dependencias, fraude | Datos tabulares relacionales | Datos semiestructurados |

## Cuándo usar Neo4j

✅ **Ideal para:**
- Redes sociales / grafos de relaciones
- Sistemas de recomendación (filtrado colaborativo)
- Detección de fraude (patrones en transacciones)
- Grafos de conocimiento (knowledge graphs)
- Análisis de dependencias (infraestructura, software)
- Cadenas de suministro y logística

❌ **No óptimo para:**
- Datos puramente tabulares sin relaciones complejas
- Agregaciones masivas tipo OLAP/data warehouse
- Búsqueda full-text (usar Elasticsearch o el módulo `db.index.fulltext` de Neo4j como complemento)
- Volúmenes extremos sin sharding (Community Edition es single-node)

## Comandos útiles en Neo4j Browser

```cypher
-- Ver todo el grafo (cuidado con grafos grandes)
MATCH (n)-[r]->(m) RETURN n,r,m LIMIT 100

-- Ver solo personajes y sus clases
MATCH (c:Character)-[:BELONGS_TO]->(cl:Class) RETURN c,cl

-- Explorar el esquema
CALL db.schema.visualization()

-- Ver todos los labels e índices
CALL db.labels()
CALL db.indexes()
```

## Parar / limpiar

```bash
docker compose down          # para Neo4j, conserva volumen de datos
docker compose down -v       # para + borra datos (reset completo)
```
