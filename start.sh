#!/bin/bash
# Arranca Neo4j PoC (docker compose)
set -e

cd "$(dirname "$0")"

echo "[neo4j-poc] Arrancando Neo4j..."
docker compose up -d

echo "[neo4j-poc] Esperando que Neo4j esté listo..."
for i in $(seq 1 30); do
    if docker exec neo4j-poc neo4j status 2>/dev/null | grep -q "running"; then
        echo "[neo4j-poc] Listo — Browser: http://localhost:7474 (neo4j/titanpoc)"
        exit 0
    fi
    sleep 2
done

echo "[neo4j-poc] Advertencia: timeout esperando Neo4j, puede seguir arrancando"
