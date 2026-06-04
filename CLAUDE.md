# Neo4j PoC — Contexto para Claude

PoC de análisis de Neo4j usando un catálogo de juego RPG. Vive en titan como repo
independiente: `git@github.com:monghithub/pocNeo4J.git`, excluido del git de titan.

## Estado actual (2026-06-04)

- Neo4j 5.26 Community + GDS 2.13 corriendo en Docker
- Dataset RPG cargado: 60 nodos, ~150 relaciones
- Manual completo con 10 casos de uso: `docs/manual.md`
- Presentación HTML con capturas reales: `docs/presentacion.html`
- Scripts de arranque/parada registrados en titanctl (grupo dev)

## Arrancar Neo4j

```bash
# On-demand desde titanctl / titan.monghit.com (grupo Desarrollo)
# O con los scripts directamente:
./start.sh                            # arranca + espera a que Neo4j esté listo
./stop.sh                             # para (conserva datos del volumen)
# Borrar datos completamente:
docker compose down -v
```

Neo4j Browser: `http://localhost:7474` · LAN: `http://192.168.1.135:7474`
Credenciales: `neo4j` / `titanpoc` · Bolt: `bolt://localhost:7687`

## Entorno Python

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt       # neo4j, python-dotenv, rich, pyvis, selenium
python data/seed.py                   # carga dataset RPG (idempotente)
```

## Ejecutar ejemplos

```bash
python examples/01_basics.py          # CRUD, modelo, constraints
python examples/02_cypher.py          # Cypher avanzado: paths, aggregations, UNWIND
python examples/03_gds.py             # GDS: PageRank, Louvain, Node Similarity
python examples/04_patterns.py        # Recomendaciones, gap analysis, multi-hop
```

## Regenerar capturas y presentación

```bash
source .venv/bin/activate
python3 docs/screenshot.py            # genera docs/screenshots/*.png
# Abre la presentación:
xdg-open docs/presentacion.html
```

Las capturas usan **pyvis** (grafos) + HTML dark-theme (tablas). Selenium + Firefox
headless para el renderizado. Si modificas queries o datos, regenera con el script.

## Estructura

```
neoj4/
├── CLAUDE.md                   # este fichero
├── docker-compose.yml          # Neo4j 5 + GDS
├── .env                        # credenciales locales (no versionado)
├── requirements.txt
├── data/
│   ├── db.py                   # driver singleton
│   └── seed.py                 # carga RPG idempotente
├── examples/
│   ├── 01_basics.py            # CRUD y modelo
│   ├── 02_cypher.py            # Cypher avanzado
│   ├── 03_gds.py               # algoritmos GDS
│   └── 04_patterns.py          # patrones reales
└── docs/
    ├── manual.md               # manual con capturas embebidas
    ├── presentacion.html       # presentación 15 slides dark-theme
    ├── screenshot.py           # generador de capturas (pyvis + Selenium)
    └── screenshots/            # 10 PNGs únicos (01-login … 10-pagerank)
```

## Dominio RPG

```
(Character)-[:BELONGS_TO]->(Class)-[:TEACHES]->(Skill)
(Character)-[:KNOWS]->(Skill)
(Character)-[:VISITS]->(Zone)
(Character)-[:COMPLETES]->(Quest)
(Zone)-[:CONNECTS_TO]->(Zone)
(Zone)-[:CONTAINS]->(Enemy)
(Enemy)-[:DROPS]->(Item)
(Quest)-[:TAKES_PLACE_IN]->(Zone)
(Quest)-[:REWARDS]->(Item)
```

## Queries útiles en el Browser

```cypher
CALL db.schema.visualization()                           -- esquema visual
MATCH (n)-[r]->(m) RETURN n,r,m LIMIT 80               -- grafo completo
CALL gds.list() YIELD name RETURN count(name)           -- nº algoritmos GDS
:sysinfo                                                 -- estado del servidor
```
