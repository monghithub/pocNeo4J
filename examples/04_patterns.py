"""
04 — Patrones de uso real: recomendaciones, filtrado colaborativo,
     detección de patrones, búsqueda por grafos.
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
    seccion("1. Recomendación colaborativa: 'quests que han completado personajes similares a ti'")
    with driver.session() as s:
        rows = s.run("""
            MATCH (yo:Character {name: 'Aldric'})-[:COMPLETES]->(q:Quest)
                  <-[:COMPLETES]-(similar:Character)
            MATCH (similar)-[:COMPLETES]->(nueva:Quest)
            WHERE NOT (yo)-[:COMPLETES]->(nueva)
            RETURN nueva.name AS quest_recomendada,
                   nueva.min_level AS nivel_min,
                   count(DISTINCT similar) AS popularidad
            ORDER BY popularidad DESC
        """).data()
    tabla("Quests recomendadas para Aldric", ["Quest","Nivel mín.","Popularidad"],
          [(r["quest_recomendada"],r["nivel_min"],r["popularidad"]) for r in rows])

    # ------------------------------------------------------------------
    seccion("2. Ruta de progresión: zonas ordenadas por nivel desde inicio")
    with driver.session() as s:
        rows = s.run("""
            MATCH p = (inicio:Zone {name:'Aldea Inicial'})-[:CONNECTS_TO*1..5]->(destino:Zone)
            WHERE destino <> inicio
            RETURN DISTINCT destino.name AS zona,
                   destino.level AS nivel,
                   length(p) AS distancia
            ORDER BY destino.level, distancia
        """).data()
    tabla("Ruta de progresión desde Aldea", ["Zona","Nivel","Distancia"],
          [(r["zona"],r["nivel"],r["distancia"]) for r in rows])

    # ------------------------------------------------------------------
    seccion("3. Items que puede conseguir un personaje según zonas visitadas")
    with driver.session() as s:
        rows = s.run("""
            MATCH (c:Character {name:'Seraphia'})-[:VISITS]->(z:Zone)
                  -[:CONTAINS]->(e:Enemy)-[:DROPS]->(i:Item)
            RETURN DISTINCT i.name AS item,
                   i.rarity AS rareza,
                   i.type AS tipo,
                   e.name AS de_enemigo
            ORDER BY i.rarity
        """).data()
    tabla("Loot alcanzable por Seraphia", ["Item","Rareza","Tipo","Enemigo"],
          [(r["item"],r["rareza"],r["tipo"],r["de_enemigo"]) for r in rows])

    # ------------------------------------------------------------------
    seccion("4. Items AÚN no alcanzables (gap analysis)")
    with driver.session() as s:
        rows = s.run("""
            MATCH (i:Item)<-[:DROPS]-(:Enemy)<-[:CONTAINS]-(z:Zone)
            WHERE NOT EXISTS {
                MATCH (c:Character {name:'Seraphia'})-[:VISITS]->(z)
            }
            RETURN DISTINCT i.name AS item, i.rarity AS rareza, z.name AS en_zona
            ORDER BY i.rarity
        """).data()
    tabla("Loot NO alcanzable aún por Seraphia", ["Item","Rareza","Zona"],
          [(r["item"],r["rareza"],r["en_zona"]) for r in rows])

    # ------------------------------------------------------------------
    seccion("5. Detección de personajes 'hub': conocen muchas habilidades únicas")
    with driver.session() as s:
        rows = s.run("""
            MATCH (c:Character)-[:KNOWS]->(sk:Skill)
            WITH sk, collect(c.name) AS conocedores
            WHERE size(conocedores) = 1
            RETURN conocedores[0] AS personaje,
                   count(sk) AS skills_unicas,
                   collect(sk.name) AS skills
            ORDER BY skills_unicas DESC
        """).data()
    tabla("Personajes con habilidades únicas (solo ellos las conocen)",
          ["Personaje","Skills únicas","Skills"],
          [(r["personaje"],r["skills_unicas"],", ".join(r["skills"])) for r in rows])

    # ------------------------------------------------------------------
    seccion("6. Patrón 'clase más versátil': más skills enseñadas")
    with driver.session() as s:
        rows = s.run("""
            MATCH (cl:Class)-[:TEACHES]->(sk:Skill)
            WITH cl, count(sk) AS total_skills, collect(sk.name) AS skills,
                 sum(sk.damage) AS daño_total
            RETURN cl.name AS clase, total_skills, daño_total, skills
            ORDER BY daño_total DESC
        """).data()
    tabla("Clases por daño total", ["Clase","Nº Skills","Daño total","Skills"],
          [(r["clase"],r["total_skills"],r["daño_total"],", ".join(r["skills"])) for r in rows])

    # ------------------------------------------------------------------
    seccion("7. Cadena completa: personaje → quest → zona → enemigos → drops")
    with driver.session() as s:
        rows = s.run("""
            MATCH (c:Character)-[:COMPLETES]->(q:Quest)
                  -[:TAKES_PLACE_IN]->(z:Zone)
                  -[:CONTAINS]->(e:Enemy)
                  -[:DROPS]->(i:Item)
            RETURN c.name AS personaje,
                   q.name AS quest,
                   z.name AS zona,
                   e.name AS enemigo,
                   i.name AS item,
                   i.rarity AS rareza
            ORDER BY c.name, q.name
        """).data()
    tabla("Cadena completa personaje→quest→loot",
          ["Personaje","Quest","Zona","Enemigo","Item","Rareza"],
          [(r["personaje"],r["quest"],r["zona"],r["enemigo"],r["item"],r["rareza"])
           for r in rows])

    # ------------------------------------------------------------------
    seccion("8. Variable-length path: habilidad accesible en N pasos de relación")
    # ¿Qué habilidades puede aprender Nyx si tuviese multi-clase?
    with driver.session() as s:
        rows = s.run("""
            MATCH (c:Character {name:'Nyx'})-[:BELONGS_TO]->(cl:Class)
            MATCH (cl)-[:TEACHES]->(sk:Skill)
            RETURN 'Pícaro directo' AS origen, sk.name AS skill, sk.damage AS daño
            UNION
            MATCH (c:Character {name:'Nyx'})-[:KNOWS]->(sk:Skill)
            WHERE NOT EXISTS {
                MATCH (c)-[:BELONGS_TO]->(cl:Class)-[:TEACHES]->(sk)
            }
            RETURN 'Universal' AS origen, sk.name AS skill, sk.damage AS daño
            ORDER BY daño DESC
        """).data()
    tabla("Skills de Nyx (por origen)", ["Origen","Skill","Daño"],
          [(r["origen"],r["skill"],r["daño"]) for r in rows])

console.print("\n[bold green]04_patterns completado.[/]")
