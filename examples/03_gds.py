"""
03 — Graph Data Science (GDS): PageRank, comunidades, centralidad, similitud.
Requiere el plugin GDS (incluido en docker-compose.yml).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from data.db import get_driver
from rich.console import Console
from rich.table import Table

console = Console()

GRAPH_NAME = "rpg_graph"


def seccion(titulo):
    console.rule(f"[bold yellow]{titulo}[/]")


def tabla(titulo, columnas, filas):
    t = Table(title=titulo, show_lines=True)
    for c in columnas:
        t.add_column(c, style="cyan")
    for f in filas:
        t.add_row(*[str(round(v, 4) if isinstance(v, float) else v) for v in f])
    console.print(t)


def drop_graph_if_exists(s, name):
    exists = s.run("CALL gds.graph.exists($n) YIELD exists", n=name).single()["exists"]
    if exists:
        s.run("CALL gds.graph.drop($n)", n=name)


with get_driver() as driver:

    # ------------------------------------------------------------------
    seccion("0. Proyectar grafo en memoria GDS")
    # GDS trabaja sobre una proyección del grafo nativo almacenada en RAM.
    # Proyectamos Character + Zone + Enemy con sus relaciones.
    with driver.session() as s:
        drop_graph_if_exists(s, GRAPH_NAME)
        result = s.run("""
            CALL gds.graph.project(
              $name,
              ['Character','Zone','Enemy','Item','Quest','Class','Skill'],
              {
                CONNECTS_TO: {orientation:'UNDIRECTED'},
                BELONGS_TO:  {orientation:'NATURAL'},
                VISITS:      {orientation:'NATURAL'},
                CONTAINS:    {orientation:'NATURAL'},
                DROPS:       {orientation:'NATURAL'},
                COMPLETES:   {orientation:'NATURAL'},
                KNOWS:       {orientation:'NATURAL'},
                TEACHES:     {orientation:'NATURAL'},
                REWARDS:     {orientation:'NATURAL'},
                TAKES_PLACE_IN: {orientation:'NATURAL'}
              }
            )
            YIELD graphName, nodeCount, relationshipCount
        """, name=GRAPH_NAME).single()
    console.print(f"Grafo proyectado: [green]{result['nodeCount']}[/] nodos, "
                  f"[green]{result['relationshipCount']}[/] relaciones")

    # ------------------------------------------------------------------
    seccion("1. PageRank — nodos más influyentes/conectados")
    with driver.session() as s:
        rows = s.run("""
            CALL gds.pageRank.stream($name, {
                maxIterations: 20,
                dampingFactor: 0.85
            })
            YIELD nodeId, score
            RETURN gds.util.asNode(nodeId).name AS nodo,
                   labels(gds.util.asNode(nodeId))[0] AS tipo,
                   score
            ORDER BY score DESC
            LIMIT 12
        """, name=GRAPH_NAME).data()
    tabla("PageRank Top 12", ["Nodo","Tipo","Score"],
          [(r["nodo"],r["tipo"],r["score"]) for r in rows])

    # ------------------------------------------------------------------
    seccion("2. Betweenness Centrality — nodos 'puente'")
    with driver.session() as s:
        rows = s.run("""
            CALL gds.betweenness.stream($name)
            YIELD nodeId, score
            RETURN gds.util.asNode(nodeId).name AS nodo,
                   labels(gds.util.asNode(nodeId))[0] AS tipo,
                   score
            ORDER BY score DESC
            LIMIT 10
        """, name=GRAPH_NAME).data()
    tabla("Betweenness Centrality Top 10", ["Nodo","Tipo","Score"],
          [(r["nodo"],r["tipo"],r["score"]) for r in rows])

    # ------------------------------------------------------------------
    seccion("3. Degree Centrality — nodos con más conexiones")
    with driver.session() as s:
        rows = s.run("""
            CALL gds.degree.stream($name)
            YIELD nodeId, score
            RETURN gds.util.asNode(nodeId).name AS nodo,
                   labels(gds.util.asNode(nodeId))[0] AS tipo,
                   score
            ORDER BY score DESC
            LIMIT 10
        """, name=GRAPH_NAME).data()
    tabla("Degree Centrality Top 10", ["Nodo","Tipo","Grado"],
          [(r["nodo"],r["tipo"],int(r["score"])) for r in rows])

    # ------------------------------------------------------------------
    seccion("4. Louvain — detección de comunidades")
    with driver.session() as s:
        rows = s.run("""
            CALL gds.louvain.stream($name)
            YIELD nodeId, communityId
            WITH communityId,
                 collect(gds.util.asNode(nodeId).name) AS miembros,
                 count(*) AS tamaño
            ORDER BY tamaño DESC
            RETURN communityId, tamaño, miembros
        """, name=GRAPH_NAME).data()
    tabla("Comunidades Louvain", ["Comunidad","Tamaño","Miembros"],
          [(r["communityId"],r["tamaño"],", ".join(r["miembros"][:5])+
            (f"…+{len(r['miembros'])-5}" if len(r["miembros"])>5 else ""))
           for r in rows])

    # ------------------------------------------------------------------
    seccion("5. Label Propagation — comunidades (algoritmo alternativo)")
    with driver.session() as s:
        rows = s.run("""
            CALL gds.labelPropagation.stream($name)
            YIELD nodeId, communityId
            WITH communityId,
                 collect(gds.util.asNode(nodeId).name) AS miembros,
                 count(*) AS tamaño
            ORDER BY tamaño DESC
            LIMIT 6
            RETURN communityId, tamaño, miembros
        """, name=GRAPH_NAME).data()
    tabla("Label Propagation Top 6", ["Comunidad","Tamaño","Miembros"],
          [(r["communityId"],r["tamaño"],", ".join(r["miembros"][:5]))
           for r in rows])

    # ------------------------------------------------------------------
    seccion("6. Node Similarity — personajes similares (habilidades)")
    # Proyección específica solo Character→Skill para similitud
    SIMILARITY_GRAPH = "char_skill_graph"
    with driver.session() as s:
        drop_graph_if_exists(s, SIMILARITY_GRAPH)
        s.run("""
            CALL gds.graph.project($name,
              ['Character','Skill'],
              {KNOWS: {orientation:'NATURAL'}}
            )
        """, name=SIMILARITY_GRAPH)
        rows = s.run("""
            CALL gds.nodeSimilarity.stream($name, {
                topK: 3,
                similarityCutoff: 0.1
            })
            YIELD node1, node2, similarity
            RETURN gds.util.asNode(node1).name AS personaje1,
                   gds.util.asNode(node2).name AS personaje2,
                   similarity
            ORDER BY similarity DESC
            LIMIT 10
        """, name=SIMILARITY_GRAPH).data()
        drop_graph_if_exists(s, SIMILARITY_GRAPH)
    tabla("Similitud entre personajes (skills)", ["Personaje 1","Personaje 2","Similitud"],
          [(r["personaje1"],r["personaje2"],r["similarity"]) for r in rows])

    # ------------------------------------------------------------------
    seccion("7. Triangle Count / Clustering Coefficient")
    with driver.session() as s:
        rows = s.run("""
            CALL gds.triangleCount.stream($name)
            YIELD nodeId, triangleCount
            WHERE triangleCount > 0
            RETURN gds.util.asNode(nodeId).name AS nodo,
                   labels(gds.util.asNode(nodeId))[0] AS tipo,
                   triangleCount
            ORDER BY triangleCount DESC
            LIMIT 10
        """, name=GRAPH_NAME).data()
    if rows:
        tabla("Triangle Count (nodos en triángulos)", ["Nodo","Tipo","Triángulos"],
              [(r["nodo"],r["tipo"],r["triangleCount"]) for r in rows])
    else:
        console.print("[yellow]Sin triángulos en la proyección actual (grafo poco denso).[/]")

    # ------------------------------------------------------------------
    # Limpiar proyección principal
    with driver.session() as s:
        drop_graph_if_exists(s, GRAPH_NAME)
    console.print("\n[dim]Proyecciones GDS liberadas.[/]")

console.print("\n[bold green]03_gds completado.[/]")
