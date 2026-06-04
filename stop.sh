#!/bin/bash
# Para Neo4j PoC (conserva los datos del volumen)
set -e

cd "$(dirname "$0")"

echo "[neo4j-poc] Parando Neo4j..."
docker stop neo4j-poc 2>/dev/null && echo "[neo4j-poc] Detenido." || echo "[neo4j-poc] Ya estaba parado."
