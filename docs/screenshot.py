"""
Genera capturas de pantalla del Neo4j Browser para el manual.
Usa el parámetro URL ?cmd=play&arg= de Neo4j Browser para auto-ejecutar queries.
Uso: python3 docs/screenshot.py
"""
import os
import time
import urllib.parse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from rich.console import Console

console = Console()
OUT = os.path.join(os.path.dirname(__file__), "screenshots")
os.makedirs(OUT, exist_ok=True)

NEO4J_URL = "http://localhost:7474/browser/"
USER = "neo4j"
PASS = "titanpoc"

QUERIES = [
    {
        "id": "02-schema",
        "title": "Esquema del grafo",
        "query": "CALL db.schema.visualization()",
        "wait": 6,
    },
    {
        "id": "03-full-graph",
        "title": "Grafo RPG completo",
        "query": "MATCH (n)-[r]->(m) RETURN n,r,m LIMIT 80",
        "wait": 6,
    },
    {
        "id": "04-seraphia",
        "title": "Personaje y sus conexiones — Seraphia",
        "query": "MATCH (c:Character {name:'Seraphia'})-[r]-(n) RETURN c,r,n",
        "wait": 5,
    },
    {
        "id": "05-zone-network",
        "title": "Red de zonas del mundo",
        "query": "MATCH (a:Zone)-[r:CONNECTS_TO]->(b:Zone) RETURN a,r,b",
        "wait": 5,
    },
    {
        "id": "06-shortest-path",
        "title": "Camino más corto: Aldea Inicial → Torre del Mago",
        "query": (
            "MATCH (a:Zone {name:'Aldea Inicial'}),(b:Zone {name:'Torre del Mago'}) "
            "MATCH p=shortestPath((a)-[:CONNECTS_TO*]-(b)) RETURN p"
        ),
        "wait": 5,
    },
    {
        "id": "07-character-table",
        "title": "Ranking de personajes por nivel",
        "query": (
            "MATCH (c:Character)-[:BELONGS_TO]->(cl:Class) "
            "RETURN c.name AS Nombre, c.level AS Nivel, c.hp AS HP, cl.name AS Clase "
            "ORDER BY c.level DESC"
        ),
        "wait": 4,
    },
    {
        "id": "08-loot-chain",
        "title": "Cadena zona → enemigo → item",
        "query": (
            "MATCH (z:Zone)-[:CONTAINS]->(e:Enemy)-[:DROPS]->(i:Item) "
            "RETURN z.name AS Zona, e.name AS Enemigo, "
            "i.name AS Item, i.rarity AS Rareza ORDER BY i.rarity"
        ),
        "wait": 4,
    },
    {
        "id": "09-collab-filter",
        "title": "Recomendación colaborativa — quests para Aldric",
        "query": (
            "MATCH (yo:Character {name:'Aldric'})-[:COMPLETES]->(q:Quest)"
            "<-[:COMPLETES]-(similar:Character)-[:COMPLETES]->(nueva:Quest) "
            "WHERE NOT (yo)-[:COMPLETES]->(nueva) "
            "RETURN nueva.name AS Quest, count(DISTINCT similar) AS Popularidad "
            "ORDER BY Popularidad DESC"
        ),
        "wait": 4,
    },
    {
        "id": "10-pagerank",
        "title": "GDS PageRank — nodos más influyentes",
        "query": (
            "CALL gds.graph.project('pr_shot',"
            "['Character','Zone','Enemy','Item','Quest','Class','Skill'],"
            "{CONNECTS_TO:{orientation:'UNDIRECTED'},"
            "BELONGS_TO:{orientation:'NATURAL'},"
            "VISITS:{orientation:'NATURAL'},"
            "CONTAINS:{orientation:'NATURAL'},"
            "DROPS:{orientation:'NATURAL'},"
            "COMPLETES:{orientation:'NATURAL'},"
            "KNOWS:{orientation:'NATURAL'},"
            "TEACHES:{orientation:'NATURAL'},"
            "REWARDS:{orientation:'NATURAL'},"
            "TAKES_PLACE_IN:{orientation:'NATURAL'}})"
            " YIELD graphName "
            "CALL gds.pageRank.stream('pr_shot',{maxIterations:20,dampingFactor:0.85})"
            " YIELD nodeId, score "
            "RETURN gds.util.asNode(nodeId).name AS Nodo,"
            "labels(gds.util.asNode(nodeId))[0] AS Tipo,"
            "round(score,4) AS Score "
            "ORDER BY Score DESC LIMIT 10"
        ),
        "wait": 8,
    },
]


def make_driver():
    opts = Options()
    opts.add_argument("--headless")
    opts.binary_location = "/snap/firefox/current/usr/lib/firefox/firefox"
    svc = Service("/snap/bin/geckodriver", log_output=os.devnull)
    driver = webdriver.Firefox(service=svc, options=opts)
    driver.set_window_size(1280, 900)
    return driver


def login(driver):
    """Login inicial en Neo4j Browser."""
    driver.get(NEO4J_URL)
    time.sleep(3)
    driver.save_screenshot(os.path.join(OUT, "01-login.png"))
    console.print("[cyan]01-login.png[/]")

    wait = WebDriverWait(driver, 10)

    for sel in ["input[data-testid='username']", "input#username", "input[type='text']"]:
        try:
            el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
            el.clear(); el.send_keys(USER); break
        except Exception:
            continue

    for sel in ["input[data-testid='password']", "input#password", "input[type='password']"]:
        try:
            el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
            el.clear(); el.send_keys(PASS); break
        except Exception:
            continue

    connected = False
    for sel in ["button[data-testid='connect']", "button[type='submit']"]:
        try:
            btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
            btn.click(); connected = True; break
        except Exception:
            continue
    if not connected:
        driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys(Keys.RETURN)

    time.sleep(5)
    console.print("[green]Login OK[/]")


def wait_for_result(driver, timeout=10):
    """Espera a que aparezca un frame de resultado en Neo4j Browser."""
    wait = WebDriverWait(driver, timeout)
    for sel in [
        "[data-testid='frame-loaded-contents']",
        "[class*='frame-contents']",
        ".stream-wrapper .frame",
        "section.stream",
        "article[class*='frame']",
        "div[class*='result']",
    ]:
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
            return True
        except Exception:
            continue
    return False


def capture_query(driver, entry):
    qid = entry["id"]
    query = entry["query"]
    wait_secs = entry["wait"]

    # Navegar con cmd=play — Neo4j Browser auto-ejecuta la query
    encoded = urllib.parse.quote(query)
    url = f"{NEO4J_URL}?cmd=play&arg={encoded}"
    driver.get(url)

    # Esperar a que la app cargue y ejecute
    time.sleep(wait_secs)
    wait_for_result(driver, timeout=8)
    time.sleep(1)  # margen extra para renderizado D3/SVG

    path = os.path.join(OUT, f"{qid}.png")
    driver.save_screenshot(path)
    console.print(f"[green]{qid}.png[/] — {entry['title']}")


def main():
    console.rule("[bold cyan]Neo4j Browser — generando capturas[/]")
    driver = make_driver()

    try:
        login(driver)

        for entry in QUERIES:
            try:
                capture_query(driver, entry)
            except Exception as e:
                console.print(f"[red]Error {entry['id']}:[/] {e}")
                driver.save_screenshot(os.path.join(OUT, f"{entry['id']}-error.png"))

    finally:
        # Limpiar GDS graph si quedó
        try:
            encoded = urllib.parse.quote(
                "CALL gds.graph.exists('pr_shot') YIELD exists "
                "WITH exists WHERE exists = true "
                "CALL gds.graph.drop('pr_shot') YIELD graphName RETURN graphName"
            )
            driver.get(f"{NEO4J_URL}?cmd=play&arg={encoded}")
            time.sleep(3)
        except Exception:
            pass
        driver.quit()

    console.rule("[bold green]Capturas completadas[/]")
    shots = sorted(f for f in os.listdir(OUT) if f.endswith(".png") and "error" not in f)
    for f in shots:
        kb = os.path.getsize(os.path.join(OUT, f)) // 1024
        console.print(f"  {f}  ({kb} KB)")


if __name__ == "__main__":
    main()
