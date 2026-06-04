"""
01 — Modelo de datos: nodos, relaciones, propiedades, CRUD.
Demuestra las primitivas fundamentales de Neo4j.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from data.db import get_driver
from rich.console import Console
from rich.table import Table

console = Console()


def seccion(titulo):
    console.rule(f"[bold yellow]{titulo}[/]")


def mostrar_tabla(titulo, columnas, filas):
    t = Table(title=titulo, show_lines=True)
    for c in columnas:
        t.add_column(c, style="cyan")
    for f in filas:
        t.add_row(*[str(v) for v in f])
    console.print(t)


with get_driver() as driver:

    # ------------------------------------------------------------------
    seccion("1. Contar nodos por tipo (esquema implícito)")
    # Neo4j no tiene esquema fijo: los labels son etiquetas opcionales.
    with driver.session() as s:
        rows = s.run("""
            CALL db.labels() YIELD label
            CALL apoc.cypher.run('MATCH (n:`' + label + '`) RETURN count(n) AS c', {}) YIELD value
            RETURN label, value.c AS total
            ORDER BY total DESC
        """).data()
        # Alternativa sin APOC (compatible siempre):
        rows = s.run("""
            MATCH (n)
            RETURN labels(n)[0] AS label, count(n) AS total
            ORDER BY total DESC
        """).data()
    mostrar_tabla("Nodos por label", ["Label", "Total"],
                  [(r["label"], r["total"]) for r in rows])

    # ------------------------------------------------------------------
    seccion("2. Contar relaciones por tipo")
    with driver.session() as s:
        rows = s.run("""
            MATCH ()-[r]->()
            RETURN type(r) AS tipo, count(r) AS total
            ORDER BY total DESC
        """).data()
    mostrar_tabla("Relaciones por tipo", ["Tipo", "Total"],
                  [(r["tipo"], r["total"]) for r in rows])

    # ------------------------------------------------------------------
    seccion("3. Leer propiedades de un nodo")
    with driver.session() as s:
        ch = s.run("MATCH (c:Character {name:'Seraphia'}) RETURN c").single()["c"]
    console.print(f"[green]Seraphia[/]: level={ch['level']}, hp={ch['hp']}")

    # ------------------------------------------------------------------
    seccion("4. Habilidades de un personaje (relación directa)")
    with driver.session() as s:
        rows = s.run("""
            MATCH (c:Character {name:'Seraphia'})-[:KNOWS]->(sk:Skill)
            RETURN sk.name AS skill, sk.damage AS damage, sk.mana_cost AS cost
            ORDER BY sk.damage DESC
        """).data()
    mostrar_tabla("Skills de Seraphia", ["Skill", "Daño", "Coste mana"],
                  [(r["skill"], r["damage"], r["cost"]) for r in rows])

    # ------------------------------------------------------------------
    seccion("5. CREATE → SET → DELETE (ciclo CRUD)")
    with driver.session() as s:
        # CREATE
        s.run("MERGE (x:Character {name:'TestChar'}) SET x.level=1, x.hp=100")
        n = s.run("MATCH (c:Character {name:'TestChar'}) RETURN c.level AS lv").single()
        console.print(f"[green]Creado[/] TestChar level={n['lv']}")

        # UPDATE
        s.run("MATCH (c:Character {name:'TestChar'}) SET c.level=5")
        n = s.run("MATCH (c:Character {name:'TestChar'}) RETURN c.level AS lv").single()
        console.print(f"[yellow]Actualizado[/] TestChar level={n['lv']}")

        # DELETE
        s.run("MATCH (c:Character {name:'TestChar'}) DETACH DELETE c")
        n = s.run("MATCH (c:Character {name:'TestChar'}) RETURN count(c) AS c").single()
        console.print(f"[red]Eliminado[/] — quedan {n['c']} nodos TestChar")

    # ------------------------------------------------------------------
    seccion("6. MERGE (upsert): idempotente")
    with driver.session() as s:
        for _ in range(3):
            s.run("MERGE (z:Zone {name:'Zona Demo'}) SET z.level=99")
        n = s.run("MATCH (z:Zone {name:'Zona Demo'}) RETURN count(z) AS c").single()
        console.print(f"Ejecutado 3×MERGE → {n['c']} nodo (idempotente OK)")
        s.run("MATCH (z:Zone {name:'Zona Demo'}) DETACH DELETE z")

    # ------------------------------------------------------------------
    seccion("7. Grafo de relaciones: personaje → clase → habilidades")
    with driver.session() as s:
        rows = s.run("""
            MATCH (c:Character)-[:BELONGS_TO]->(cl:Class)-[:TEACHES]->(sk:Skill)
            RETURN c.name AS personaje, cl.name AS clase, collect(sk.name) AS skills
            ORDER BY c.name
        """).data()
    mostrar_tabla("Personaje → Clase → Skills de clase",
                  ["Personaje", "Clase", "Skills"],
                  [(r["personaje"], r["clase"], ", ".join(r["skills"])) for r in rows])

console.print("\n[bold green]01_basics completado.[/]")
