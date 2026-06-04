"""
Carga el dataset RPG en Neo4j.
Idempotente: usa MERGE para no duplicar nodos.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from data.db import get_driver
from rich.console import Console
from rich.progress import track

console = Console()

CLASSES = ["Guerrero", "Mago", "Arquero", "Clérigo", "Pícaro"]

CHARACTERS = [
    {"name": "Aldric",   "level": 15, "class": "Guerrero", "hp": 320},
    {"name": "Seraphia", "level": 18, "class": "Mago",     "hp": 140},
    {"name": "Ryn",      "level": 12, "class": "Arquero",  "hp": 210},
    {"name": "Torvald",  "level": 20, "class": "Clérigo",  "hp": 260},
    {"name": "Nyx",      "level": 14, "class": "Pícaro",   "hp": 190},
    {"name": "Brynn",    "level": 11, "class": "Guerrero", "hp": 290},
    {"name": "Zara",     "level": 16, "class": "Mago",     "hp": 130},
    {"name": "Oryn",     "level": 13, "class": "Arquero",  "hp": 200},
    {"name": "Dael",     "level": 17, "class": "Clérigo",  "hp": 240},
    {"name": "Vesper",   "level": 10, "class": "Pícaro",   "hp": 180},
]

SKILLS = [
    {"name": "Golpe Devastador",  "class": "Guerrero", "damage": 80,  "cost": 20},
    {"name": "Torbellino",        "class": "Guerrero", "damage": 60,  "cost": 15},
    {"name": "Bola de Fuego",     "class": "Mago",     "damage": 120, "cost": 40},
    {"name": "Teletransporte",    "class": "Mago",     "damage": 0,   "cost": 30},
    {"name": "Lluvia de Flechas", "class": "Arquero",  "damage": 70,  "cost": 25},
    {"name": "Trampa Explosiva",  "class": "Arquero",  "damage": 90,  "cost": 35},
    {"name": "Curación Mayor",    "class": "Clérigo",  "damage": -150,"cost": 50},
    {"name": "Escudo Divino",     "class": "Clérigo",  "damage": 0,   "cost": 20},
    {"name": "Ataque Furtivo",    "class": "Pícaro",   "damage": 110, "cost": 30},
    {"name": "Veneno",            "class": "Pícaro",   "damage": 40,  "cost": 10},
    # Habilidades universales
    {"name": "Meditación",        "class": None,       "damage": 0,   "cost": 0},
    {"name": "Esquiva",           "class": None,       "damage": 0,   "cost": 5},
]

ZONES = [
    {"name": "Aldea Inicial",   "level": 1,  "type": "pueblo"},
    {"name": "Bosque Oscuro",   "level": 5,  "type": "exterior"},
    {"name": "Caverna de Hielo","level": 10, "type": "mazmorra"},
    {"name": "Ruinas Antiguas", "level": 15, "type": "exterior"},
    {"name": "Torre del Mago",  "level": 20, "type": "mazmorra"},
    {"name": "Llanos del Caos", "level": 25, "type": "exterior"},
    {"name": "Ciudad Capital",  "level": 1,  "type": "pueblo"},
]

ZONE_CONNECTIONS = [
    ("Aldea Inicial",   "Bosque Oscuro"),
    ("Aldea Inicial",   "Ciudad Capital"),
    ("Bosque Oscuro",   "Caverna de Hielo"),
    ("Bosque Oscuro",   "Ruinas Antiguas"),
    ("Ruinas Antiguas", "Torre del Mago"),
    ("Torre del Mago",  "Llanos del Caos"),
    ("Ciudad Capital",  "Ruinas Antiguas"),
]

ENEMIES = [
    {"name": "Lobo Oscuro",    "level": 5,  "hp": 80,  "zone": "Bosque Oscuro"},
    {"name": "Araña Gigante",  "level": 6,  "hp": 60,  "zone": "Bosque Oscuro"},
    {"name": "Golem de Hielo", "level": 12, "hp": 400, "zone": "Caverna de Hielo"},
    {"name": "Espectro",       "level": 16, "hp": 200, "zone": "Ruinas Antiguas"},
    {"name": "Archimago Rojo", "level": 22, "hp": 500, "zone": "Torre del Mago"},
    {"name": "Demonio Caído",  "level": 27, "hp": 600, "zone": "Llanos del Caos"},
]

ITEMS = [
    {"name": "Espada de Fuego",  "type": "arma",    "rarity": "raro",    "drops": "Archimago Rojo"},
    {"name": "Manto de Sombra",  "type": "armadura", "rarity": "épico",   "drops": "Demonio Caído"},
    {"name": "Colmillo de Lobo", "type": "material", "rarity": "común",   "drops": "Lobo Oscuro"},
    {"name": "Cristal de Hielo", "type": "material", "rarity": "raro",    "drops": "Golem de Hielo"},
    {"name": "Orbe Espectral",   "type": "accesorio","rarity": "épico",   "drops": "Espectro"},
    {"name": "Veneno de Araña",  "type": "material", "rarity": "común",   "drops": "Araña Gigante"},
    {"name": "Núcleo Demoníaco", "type": "material", "rarity": "legendario","drops": "Demonio Caído"},
]

QUESTS = [
    {"name": "El Primer Paso",      "zone": "Aldea Inicial",   "reward": "Colmillo de Lobo", "min_level": 1},
    {"name": "La Amenaza del Bosque","zone": "Bosque Oscuro",  "reward": "Cristal de Hielo", "min_level": 5},
    {"name": "Secretos Helados",    "zone": "Caverna de Hielo","reward": "Orbe Espectral",   "min_level": 10},
    {"name": "El Legado Perdido",   "zone": "Ruinas Antiguas", "reward": "Espada de Fuego",  "min_level": 15},
    {"name": "Ascenso al Poder",    "zone": "Torre del Mago",  "reward": "Manto de Sombra",  "min_level": 20},
]

# Qué personajes han completado qué quests
COMPLETIONS = [
    ("Aldric",   "El Primer Paso"),
    ("Aldric",   "La Amenaza del Bosque"),
    ("Seraphia", "El Primer Paso"),
    ("Seraphia", "La Amenaza del Bosque"),
    ("Seraphia", "Secretos Helados"),
    ("Seraphia", "El Legado Perdido"),
    ("Torvald",  "El Primer Paso"),
    ("Torvald",  "La Amenaza del Bosque"),
    ("Torvald",  "Secretos Helados"),
    ("Nyx",      "El Primer Paso"),
    ("Ryn",      "El Primer Paso"),
    ("Ryn",      "La Amenaza del Bosque"),
]


def seed(driver):
    with driver.session() as s:
        # Constraints e índices
        console.print("[bold cyan]Creando constraints...[/]")
        for label, prop in [("Character","name"),("Skill","name"),("Zone","name"),
                            ("Enemy","name"),("Item","name"),("Quest","name"),("Class","name")]:
            s.run(f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) REQUIRE n.{prop} IS UNIQUE")

        console.print("[bold cyan]Cargando clases...[/]")
        for c in CLASSES:
            s.run("MERGE (:Class {name: $n})", n=c)

        console.print("[bold cyan]Cargando personajes...[/]")
        for ch in track(CHARACTERS, description="Characters"):
            s.run("""
                MERGE (c:Character {name: $name})
                SET c.level = $level, c.hp = $hp
                WITH c
                MATCH (cl:Class {name: $class})
                MERGE (c)-[:BELONGS_TO]->(cl)
            """, **ch)

        console.print("[bold cyan]Cargando habilidades...[/]")
        for sk in track(SKILLS, description="Skills"):
            s.run("MERGE (:Skill {name: $name, damage: $damage, mana_cost: $cost})",
                  name=sk["name"], damage=sk["damage"], cost=sk["cost"])
            if sk["class"]:
                s.run("""
                    MATCH (cl:Class {name: $cls}), (sk:Skill {name: $sk})
                    MERGE (cl)-[:TEACHES]->(sk)
                """, cls=sk["class"], sk=sk["name"])

        # Personajes aprenden las habilidades de su clase + universales
        s.run("""
            MATCH (c:Character)-[:BELONGS_TO]->(cl:Class)-[:TEACHES]->(sk:Skill)
            MERGE (c)-[:KNOWS]->(sk)
        """)
        s.run("""
            MATCH (c:Character), (sk:Skill)
            WHERE NOT (sk)<-[:TEACHES]-(:Class)
            MERGE (c)-[:KNOWS]->(sk)
        """)

        console.print("[bold cyan]Cargando zonas...[/]")
        for z in track(ZONES, description="Zones"):
            s.run("MERGE (:Zone {name: $name, level: $level, type: $type})", **z)
        for a, b in ZONE_CONNECTIONS:
            s.run("""
                MATCH (a:Zone {name: $a}), (b:Zone {name: $b})
                MERGE (a)-[:CONNECTS_TO]->(b)
                MERGE (b)-[:CONNECTS_TO]->(a)
            """, a=a, b=b)

        console.print("[bold cyan]Cargando enemigos e items...[/]")
        for e in track(ENEMIES, description="Enemies"):
            s.run("""
                MERGE (en:Enemy {name: $name})
                SET en.level = $level, en.hp = $hp
                WITH en
                MATCH (z:Zone {name: $zone})
                MERGE (z)-[:CONTAINS]->(en)
            """, **e)
        for it in track(ITEMS, description="Items"):
            s.run("""
                MERGE (i:Item {name: $name, type: $type, rarity: $rarity})
                WITH i
                MATCH (en:Enemy {name: $drops})
                MERGE (en)-[:DROPS]->(i)
            """, **it)

        console.print("[bold cyan]Cargando quests...[/]")
        for q in track(QUESTS, description="Quests"):
            s.run("""
                MERGE (q:Quest {name: $name})
                SET q.min_level = $min_level
                WITH q
                MATCH (z:Zone {name: $zone}), (i:Item {name: $reward})
                MERGE (q)-[:TAKES_PLACE_IN]->(z)
                MERGE (q)-[:REWARDS]->(i)
            """, **q)
        for char, quest in COMPLETIONS:
            s.run("""
                MATCH (c:Character {name: $c}), (q:Quest {name: $q})
                MERGE (c)-[:COMPLETES]->(q)
            """, c=char, q=quest)

        # Visitas: personajes han visitado zonas de quests completadas
        s.run("""
            MATCH (c:Character)-[:COMPLETES]->(q:Quest)-[:TAKES_PLACE_IN]->(z:Zone)
            MERGE (c)-[:VISITS]->(z)
        """)

    console.print("\n[bold green]Dataset RPG cargado correctamente.[/]")
    with driver.session() as s:
        counts = s.run("""
            MATCH (n) RETURN labels(n)[0] AS label, count(n) AS total
            ORDER BY total DESC
        """)
        for r in counts:
            console.print(f"  {r['label']:15} {r['total']} nodos")


if __name__ == "__main__":
    with get_driver() as driver:
        seed(driver)
