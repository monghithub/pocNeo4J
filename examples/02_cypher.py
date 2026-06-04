"""
02 — Cypher avanzado: filtros, agregaciones, caminos, subconsultas.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from data.db import get_driver
from rich.console import Console
from rich.table import Table

console = Console()


def seccion(titulo):
    console.rule(f"[bold yellow]{titulo}[/]")


def tabla(titulo, columnas, filas):
    t = Table(title=titulo, show_lines=True)
    for c in columnas:
        t.add_column(c, style="cyan")
    for f in filas:
        t.add_row(*[str(v) for v in f])
    console.print(t)


with get_driver() as driver:

    # ------------------------------------------------------------------
    seccion("1. Filtros compuestos: personajes de nivel alto con mucho HP")
    with driver.session() as s:
        rows = s.run("""
            MATCH (c:Character)-[:BELONGS_TO]->(cl:Class)
            WHERE c.level >= 14 AND c.hp > 150
            RETURN c.name AS nombre, c.level AS nivel, c.hp AS hp, cl.name AS clase
            ORDER BY c.level DESC
        """).data()
    tabla("Personajes nivel≥14 y hp>150", ["Nombre","Nivel","HP","Clase"],
          [(r["nombre"],r["nivel"],r["hp"],r["clase"]) for r in rows])

    # ------------------------------------------------------------------
    seccion("2. Agregaciones: quests completadas por personaje")
    with driver.session() as s:
        rows = s.run("""
            MATCH (c:Character)
            OPTIONAL MATCH (c)-[:COMPLETES]->(q:Quest)
            RETURN c.name AS personaje, count(q) AS quests_completadas
            ORDER BY quests_completadas DESC
        """).data()
    tabla("Quests por personaje", ["Personaje","Quests completadas"],
          [(r["personaje"],r["quests_completadas"]) for r in rows])

    # ------------------------------------------------------------------
    seccion("3. COLLECT y listas: zonas visitadas por personaje")
    with driver.session() as s:
        rows = s.run("""
            MATCH (c:Character)-[:VISITS]->(z:Zone)
            RETURN c.name AS personaje,
                   count(z) AS zonas,
                   collect(z.name) AS lista
            ORDER BY zonas DESC
        """).data()
    tabla("Zonas visitadas", ["Personaje","N","Zonas"],
          [(r["personaje"],r["zonas"],", ".join(r["lista"])) for r in rows])

    # ------------------------------------------------------------------
    seccion("4. Camino más corto entre zonas (shortestPath)")
    with driver.session() as s:
        result = s.run("""
            MATCH (a:Zone {name:'Aldea Inicial'}), (b:Zone {name:'Torre del Mago'})
            MATCH p = shortestPath((a)-[:CONNECTS_TO*]-(b))
            RETURN [z IN nodes(p) | z.name] AS ruta, length(p) AS pasos
        """).single()
    if result:
        console.print(f"Ruta más corta: [green]{' → '.join(result['ruta'])}[/] ({result['pasos']} pasos)")

    # ------------------------------------------------------------------
    seccion("5. Todos los caminos (allShortestPaths)")
    with driver.session() as s:
        rows = s.run("""
            MATCH (a:Zone {name:'Bosque Oscuro'}), (b:Zone {name:'Llanos del Caos'})
            MATCH p = allShortestPaths((a)-[:CONNECTS_TO*]-(b))
            RETURN [z IN nodes(p) | z.name] AS ruta, length(p) AS pasos
        """).data()
    tabla("Todos los caminos más cortos Bosque→Llanos",
          ["Ruta","Pasos"],
          [(" → ".join(r["ruta"]), r["pasos"]) for r in rows])

    # ------------------------------------------------------------------
    seccion("6. Enemigos accesibles para un personaje nivel X (camino + nivel)")
    with driver.session() as s:
        rows = s.run("""
            MATCH (start:Zone {name:'Aldea Inicial'})-[:CONNECTS_TO*1..3]-(z:Zone)
               -[:CONTAINS]->(e:Enemy)
            WHERE e.level <= 15
            RETURN DISTINCT e.name AS enemigo, e.level AS nivel, z.name AS zona
            ORDER BY e.level
        """).data()
    tabla("Enemigos alcanzables desde Aldea (nivel≤15, dist≤3)",
          ["Enemigo","Nivel","Zona"],
          [(r["enemigo"],r["nivel"],r["zona"]) for r in rows])

    # ------------------------------------------------------------------
    seccion("7. WITH y subconsultas encadenadas")
    with driver.session() as s:
        rows = s.run("""
            MATCH (c:Character)-[:COMPLETES]->(q:Quest)-[:REWARDS]->(i:Item)
            WITH c, collect(i.name) AS recompensas, count(i) AS total
            WHERE total > 1
            RETURN c.name AS personaje, total, recompensas
            ORDER BY total DESC
        """).data()
    tabla("Personajes con >1 recompensa", ["Personaje","Total","Items"],
          [(r["personaje"],r["total"],", ".join(r["recompensas"])) for r in rows])

    # ------------------------------------------------------------------
    seccion("8. UNWIND: aplanar listas")
    with driver.session() as s:
        rows = s.run("""
            MATCH (e:Enemy)-[:DROPS]->(i:Item)
            WITH e, collect(i) AS drops
            UNWIND drops AS item
            RETURN e.name AS enemigo, item.name AS item, item.rarity AS rareza
            ORDER BY e.name
        """).data()
    tabla("Drops por enemigo (UNWIND)", ["Enemigo","Item","Rareza"],
          [(r["enemigo"],r["item"],r["rareza"]) for r in rows])

    # ------------------------------------------------------------------
    seccion("9. CASE: categorizar personajes por nivel")
    with driver.session() as s:
        rows = s.run("""
            MATCH (c:Character)
            RETURN c.name AS nombre, c.level AS nivel,
                   CASE
                     WHEN c.level < 13 THEN 'Novato'
                     WHEN c.level < 17 THEN 'Veterano'
                     ELSE 'Maestro'
                   END AS categoria
            ORDER BY c.level DESC
        """).data()
    tabla("Categorías de personaje", ["Nombre","Nivel","Categoría"],
          [(r["nombre"],r["nivel"],r["categoria"]) for r in rows])

    # ------------------------------------------------------------------
    seccion("10. EXISTS / NOT EXISTS: personajes sin quests")
    with driver.session() as s:
        rows = s.run("""
            MATCH (c:Character)
            WHERE NOT EXISTS { MATCH (c)-[:COMPLETES]->(:Quest) }
            RETURN c.name AS personaje, c.level AS nivel
        """).data()
    tabla("Personajes sin quests completadas", ["Personaje","Nivel"],
          [(r["personaje"],r["nivel"]) for r in rows])

console.print("\n[bold green]02_cypher completado.[/]")
