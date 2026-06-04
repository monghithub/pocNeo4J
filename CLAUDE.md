# Neo4j PoC — Exploración de capacidades

PoC de análisis de Neo4j usando un catálogo RPG como dominio de datos.
Corre en Docker (Neo4j community + GDS plugin). Python 3.

## Stack

- **Neo4j 5.x** community + plugin GDS (Graph Data Science)
- **Driver**: `neo4j` (oficial Python)
- **Puerto Bolt**: `bolt://localhost:7687`
- **Neo4j Browser**: `http://localhost:7474`
- **Credenciales**: ver `.env` (default: neo4j / titanpoc)

## Arrancar

```bash
# Levantar Neo4j
docker compose up -d

# Instalar deps Python (usar venv)
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Cargar datos RPG
python data/seed.py

# Abrir browser UI
xdg-open http://localhost:7474
```

## Ejemplos

| Fichero | Qué demuestra |
|---|---|
| `examples/01_basics.py` | CRUD, modelo nodos/relaciones, propiedades |
| `examples/02_cypher.py` | Queries: MATCH, WHERE, agregaciones, caminos |
| `examples/03_gds.py` | PageRank, comunidades, centralidad, similitud |
| `examples/04_patterns.py` | Recomendaciones, detección de patrones |

Ejecutar cualquiera: `python examples/01_basics.py`

## Dominio RPG

```
(Character)-[:KNOWS]->(Skill)
(Character)-[:BELONGS_TO]->(Class)
(Character)-[:VISITS]->(Zone)
(Zone)-[:CONTAINS]->(Enemy)
(Zone)-[:CONNECTS_TO]->(Zone)
(Enemy)-[:DROPS]->(Item)
(Character)-[:COMPLETES]->(Quest)
(Quest)-[:REWARDS]->(Item)
(Quest)-[:TAKES_PLACE_IN]->(Zone)
```

## Parar / limpiar

```bash
docker compose down          # para, conserva datos
docker compose down -v       # para + borra volumen
```
