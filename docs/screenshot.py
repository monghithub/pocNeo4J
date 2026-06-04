"""
Genera capturas para el manual: pyvis para grafos + HTML para tablas.
Uso: python3 docs/screenshot.py
"""
import os, sys, time, textwrap
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from data.db import get_driver
from pyvis.network import Network
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from rich.console import Console

console = Console()
OUT  = os.path.join(os.path.dirname(__file__), "screenshots")
TMP  = os.path.join(os.path.dirname(__file__), "_tmp")
os.makedirs(OUT, exist_ok=True)
os.makedirs(TMP, exist_ok=True)

# ── colores por label ──────────────────────────────────────────
COLORS = {
    "Character": "#79c0ff",
    "Class":     "#ffa657",
    "Skill":     "#39d0d8",
    "Zone":      "#56d364",
    "Enemy":     "#ff7b72",
    "Item":      "#d2a8ff",
    "Quest":     "#f0883e",
}
DEFAULT_COLOR = "#8b949e"

# ── opciones comunes de pyvis ──────────────────────────────────
PYVIS_OPTS = """
{
  "nodes": {
    "font": {"color": "#e6edf3", "size": 13},
    "borderWidth": 2,
    "shadow": true
  },
  "edges": {
    "font": {"color": "#8b949e", "size": 10, "align": "middle"},
    "color": {"color": "#30363d", "highlight": "#018BFF"},
    "arrows": {"to": {"enabled": true, "scaleFactor": 0.7}},
    "smooth": {"type": "dynamic"}
  },
  "physics": {
    "barnesHut": {
      "gravitationalConstant": -8000,
      "springLength": 120,
      "avoidOverlap": 0.3
    },
    "stabilization": {"iterations": 200}
  },
  "interaction": {"hover": true},
  "background": "#161b22"
}
"""


def make_net(height="580px", width="100%"):
    net = Network(height=height, width=width, bgcolor="#161b22",
                  font_color="#e6edf3", directed=True)
    net.set_options(PYVIS_OPTS)
    return net


def node_color(label):
    return COLORS.get(label, DEFAULT_COLOR)


def add_neo4j_node(net, node, seen):
    nid = node.element_id
    if nid in seen:
        return
    seen.add(nid)
    label = list(node.labels)[0] if node.labels else "Node"
    name  = node.get("name", nid[-6:])
    title = "\n".join(f"{k}: {v}" for k, v in dict(node).items())
    net.add_node(nid, label=name, title=title,
                 color=node_color(label),
                 shape="dot", size=18)


def graph_screenshot(driver, html_file, out_file):
    driver.get(f"file://{os.path.abspath(html_file)}")
    time.sleep(4)          # deja que vis.js stabilize
    driver.save_screenshot(out_file)
    console.print(f"[green]{os.path.basename(out_file)}[/]")


# ── Selenium headless ──────────────────────────────────────────
def make_driver():
    opts = Options()
    opts.add_argument("--headless")
    opts.binary_location = "/snap/firefox/current/usr/lib/firefox/firefox"
    svc = Service("/snap/bin/geckodriver", log_output=os.devnull)
    drv = webdriver.Firefox(service=svc, options=opts)
    drv.set_window_size(1280, 820)
    return drv


# ══════════════════════════════════════════════════════════════
# GENERADORES DE VISUALIZACIONES
# ══════════════════════════════════════════════════════════════

def gen_schema(driver, db):
    """02 — Esquema del grafo"""
    net = make_net()
    seen_n, seen_e = set(), set()
    with db.session() as s:
        for record in s.run("CALL db.schema.visualization()"):
            for n in record["nodes"]:
                nid = n.element_id
                if nid not in seen_n:
                    seen_n.add(nid)
                    label = list(n.labels)[0]
                    net.add_node(nid, label=label, color=node_color(label),
                                 shape="dot", size=28,
                                 font={"size": 15, "color": "#e6edf3"})
            for r in record["relationships"]:
                eid = r.element_id
                if eid not in seen_e:
                    seen_e.add(eid)
                    net.add_edge(r.start_node.element_id,
                                 r.end_node.element_id, label=r.type,
                                 color="#018BFF", width=2)

    html = os.path.join(TMP, "02-schema.html")
    net.save_graph(html)
    graph_screenshot(driver, html, os.path.join(OUT, "02-schema.png"))


def gen_full_graph(driver, db):
    """03 — Grafo RPG completo"""
    net = make_net()
    seen_n, seen_e = set(), set()
    with db.session() as s:
        for record in s.run("MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 80"):
            add_neo4j_node(net, record["n"], seen_n)
            add_neo4j_node(net, record["m"], seen_n)
            r = record["r"]
            if r.element_id not in seen_e:
                seen_e.add(r.element_id)
                net.add_edge(r.start_node.element_id, r.end_node.element_id,
                             label=r.type, width=1.5)

    html = os.path.join(TMP, "03-full-graph.html")
    net.save_graph(html)
    graph_screenshot(driver, html, os.path.join(OUT, "03-full-graph.png"))


def gen_character(driver, db, char_name, shot_id):
    """04 — Personaje y sus conexiones"""
    net = make_net()
    seen_n, seen_e = set(), set()
    main_id = None
    with db.session() as s:
        for record in s.run(
                "MATCH (c:Character {name:$n})-[r]-(x) RETURN c, r, x",
                n=char_name):
            c, x, r = record["c"], record["x"], record["r"]
            add_neo4j_node(net, c, seen_n)
            add_neo4j_node(net, x, seen_n)
            if main_id is None:
                main_id = c.element_id
            if r.element_id not in seen_e:
                seen_e.add(r.element_id)
                net.add_edge(r.start_node.element_id, r.end_node.element_id,
                             label=r.type, width=2, color="#018BFF")

    if main_id:
        net.get_node(main_id)["size"] = 35
        net.get_node(main_id)["color"] = "#018BFF"

    html = os.path.join(TMP, f"{shot_id}.html")
    net.save_graph(html)
    graph_screenshot(driver, html, os.path.join(OUT, f"{shot_id}.png"))


def gen_zones(driver, db):
    """05 — Red de zonas"""
    net = make_net()
    seen_n, seen_e = set(), set()
    with db.session() as s:
        for row in s.run(
                "MATCH (a:Zone)-[r:CONNECTS_TO]->(b:Zone) RETURN a, r, b"):
            for key in ("a", "b"):
                n = row[key]
                nid = n.element_id
                if nid not in seen_n:
                    seen_n.add(nid)
                    name  = n.get("name", "?")
                    level = n.get("level", "")
                    ntype = n.get("type", "")
                    net.add_node(nid, label=f"{name}\nlv{level}",
                                 title=f"{name} | Nivel {level} | {ntype}",
                                 color="#56d364", shape="dot", size=24,
                                 font={"size": 13})
            r = row["r"]
            if r.element_id not in seen_e:
                seen_e.add(r.element_id)
                net.add_edge(r.start_node.element_id, r.end_node.element_id,
                             color="#ffa657", width=2)

    html = os.path.join(TMP, "05-zone-network.html")
    net.save_graph(html)
    graph_screenshot(driver, html, os.path.join(OUT, "05-zone-network.png"))


def gen_shortest_path(driver, db):
    """06 — Camino más corto"""
    with db.session() as s:
        result = s.run(
            "MATCH (a:Zone {name:'Aldea Inicial'}),(b:Zone {name:'Torre del Mago'}) "
            "MATCH p=shortestPath((a)-[:CONNECTS_TO*]-(b)) "
            "RETURN [z IN nodes(p) | z.name] AS ruta, "
            "relationships(p) AS rels, nodes(p) AS nodos"
        ).single()

    net = make_net(height="400px")
    path_nodes = result["nodos"]
    path_rels  = result["rels"]
    ruta = result["ruta"]

    seen_n = set()
    for i, n in enumerate(path_nodes):
        nid = n.element_id
        seen_n.add(nid)
        is_start = (i == 0)
        is_end   = (i == len(path_nodes) - 1)
        color = "#018BFF" if is_start else ("#d29922" if is_end else "#56d364")
        size  = 30 if (is_start or is_end) else 22
        net.add_node(nid, label=f"{n['name']}\nlv{n.get('level','')}",
                     color=color, size=size,
                     font={"size":14, "color":"#e6edf3"})

    for r in path_rels:
        net.add_edge(r.start_node.element_id, r.end_node.element_id,
                     color="#018BFF", width=4,
                     label="CONNECTS_TO")

    html = os.path.join(TMP, "06-shortest-path.html")
    net.save_graph(html)

    # añadir título de ruta
    with open(html, "r") as f:
        content = f.read()
    banner = (f'<div style="position:fixed;top:10px;left:50%;transform:translateX(-50%);'
              f'background:#21262d;border:1px solid #018BFF;border-radius:8px;'
              f'padding:8px 20px;color:#e6edf3;font-family:monospace;font-size:13px;z-index:999">'
              f'Ruta: {" → ".join(ruta)}</div>')
    content = content.replace("<body>", f"<body>{banner}")
    with open(html, "w") as f:
        f.write(content)

    graph_screenshot(driver, html, os.path.join(OUT, "06-shortest-path.png"))


def html_table(title, columns, rows_data, footer=""):
    """Genera HTML con tabla dark-theme."""
    header_html = "".join(f"<th>{c}</th>" for c in columns)
    rows_html = ""
    for row in rows_data:
        cells = "".join(f"<td>{v}</td>" for v in row)
        rows_html += f"<tr>{cells}</tr>"

    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
  body{{margin:0;background:#0d1117;font-family:'Segoe UI',system-ui,sans-serif;
       display:flex;flex-direction:column;align-items:center;
       justify-content:center;min-height:100vh;padding:32px;}}
  h2{{color:#018BFF;font-size:1.2rem;margin-bottom:20px;
      letter-spacing:1px;text-transform:uppercase;}}
  table{{border-collapse:collapse;width:960px;max-width:100%;}}
  th{{background:#21262d;color:#018BFF;padding:12px 18px;text-align:left;
      border-bottom:2px solid #018BFF;font-size:.8rem;
      letter-spacing:1px;text-transform:uppercase;}}
  td{{padding:11px 18px;border-bottom:1px solid #30363d;
      color:#8b949e;font-size:.9rem;}}
  tr:hover td{{background:#161b22;}}
  td:first-child{{color:#e6edf3;font-weight:600;}}
  .footer{{color:#8b949e;font-size:.75rem;margin-top:14px;}}
  .badge{{display:inline-block;padding:2px 10px;border-radius:10px;
          font-size:.75rem;font-weight:600;}}
  .legendario{{background:rgba(210,168,255,.2);color:#d2a8ff;}}
  .epico    {{background:rgba(255,166,87,.2); color:#ffa657;}}
  .raro     {{background:rgba(1,139,255,.2);  color:#79c0ff;}}
  .comun    {{background:rgba(139,148,158,.2);color:#8b949e;}}
</style></head><body>
<h2>{title}</h2>
<table><thead><tr>{header_html}</tr></thead>
<tbody>{rows_html}</tbody></table>
<div class="footer">{footer}</div>
</body></html>"""


def rarity_badge(val):
    cls = {"legendario":"legendario","épico":"epico",
           "raro":"raro","común":"comun"}.get(str(val).lower(), "")
    return f'<span class="badge {cls}">{val}</span>' if cls else val


def gen_table_character(driver, db):
    with db.session() as s:
        rows = s.run(
            "MATCH (c:Character)-[:BELONGS_TO]->(cl:Class) "
            "RETURN c.name AS Nombre, c.level AS Nivel, c.hp AS HP, cl.name AS Clase "
            "ORDER BY c.level DESC").data()
    data = [(r["Nombre"], r["Nivel"], r["HP"], r["Clase"]) for r in rows]
    html_str = html_table("Ranking de personajes",
                          ["Nombre","Nivel","HP","Clase"], data,
                          f"{len(data)} personajes")
    _table_shot(driver, html_str, "07-character-table")


def gen_table_loot(driver, db):
    with db.session() as s:
        rows = s.run(
            "MATCH (z:Zone)-[:CONTAINS]->(e:Enemy)-[:DROPS]->(i:Item) "
            "RETURN z.name AS Zona, e.name AS Enemigo, "
            "i.name AS Item, i.rarity AS Rareza ORDER BY i.rarity").data()
    data = [(r["Zona"], r["Enemigo"], r["Item"], rarity_badge(r["Rareza"]))
            for r in rows]
    html_str = html_table("Cadena zona → enemigo → loot",
                          ["Zona","Enemigo","Item","Rareza"], data)
    _table_shot(driver, html_str, "08-loot-chain")


def gen_table_collab(driver, db):
    with db.session() as s:
        rows = s.run(
            "MATCH (yo:Character {name:'Aldric'})-[:COMPLETES]->(q:Quest)"
            "<-[:COMPLETES]-(similar:Character)-[:COMPLETES]->(nueva:Quest) "
            "WHERE NOT (yo)-[:COMPLETES]->(nueva) "
            "RETURN nueva.name AS Quest, nueva.min_level AS Nivel, "
            "count(DISTINCT similar) AS Popularidad "
            "ORDER BY Popularidad DESC").data()
    data = [(r["Quest"], r["Nivel"], "★" * r["Popularidad"]) for r in rows]
    html_str = html_table("Recomendación colaborativa — quests para Aldric",
                          ["Quest recomendada","Nivel mín.","Popularidad"], data,
                          "Personajes similares a Aldric también completaron estas quests")
    _table_shot(driver, html_str, "09-collab-filter")


def gen_table_pagerank(driver, db):
    # drop grafo si existe
    with db.session() as s:
        ex = s.run("CALL gds.graph.exists('pr_pres') YIELD exists").single()["exists"]
        if ex:
            s.run("CALL gds.graph.drop('pr_pres')")
        s.run("""
            CALL gds.graph.project('pr_pres',
              ['Character','Zone','Enemy','Item','Quest','Class','Skill'],
              {CONNECTS_TO:{orientation:'UNDIRECTED'},
               BELONGS_TO:{orientation:'NATURAL'},
               VISITS:{orientation:'NATURAL'},
               CONTAINS:{orientation:'NATURAL'},
               DROPS:{orientation:'NATURAL'},
               COMPLETES:{orientation:'NATURAL'},
               KNOWS:{orientation:'NATURAL'},
               TEACHES:{orientation:'NATURAL'},
               REWARDS:{orientation:'NATURAL'},
               TAKES_PLACE_IN:{orientation:'NATURAL'}})
        """)
        rows = s.run("""
            CALL gds.pageRank.stream('pr_pres',
              {maxIterations:20, dampingFactor:0.85})
            YIELD nodeId, score
            RETURN gds.util.asNode(nodeId).name AS Nodo,
                   labels(gds.util.asNode(nodeId))[0] AS Tipo,
                   round(score, 4) AS Score
            ORDER BY Score DESC LIMIT 12
        """).data()
        s.run("CALL gds.graph.drop('pr_pres')")

    # barra visual
    max_score = rows[0]["Score"] if rows else 1
    data = []
    for r in rows:
        pct = int((r["Score"] / max_score) * 120)
        bar = (f'<span style="display:inline-block;height:10px;width:{pct}px;'
               f'background:#018BFF;border-radius:3px;vertical-align:middle;'
               f'margin-right:8px"></span>{r["Score"]}')
        data.append((r["Nodo"], r["Tipo"], bar))

    html_str = html_table("GDS PageRank — nodos más influyentes",
                          ["Nodo","Tipo","Score"], data,
                          "Algoritmo PageRank (dampingFactor=0.85, 20 iteraciones) — "
                          "plugin Graph Data Science 2.13")
    _table_shot(driver, html_str, "10-pagerank")


def _table_shot(driver, html_str, shot_id):
    html_file = os.path.join(TMP, f"{shot_id}.html")
    with open(html_file, "w") as f:
        f.write(html_str)
    driver.get(f"file://{os.path.abspath(html_file)}")
    time.sleep(1)
    out = os.path.join(OUT, f"{shot_id}.png")
    driver.save_screenshot(out)
    console.print(f"[green]{shot_id}.png[/]")


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════
def main():
    console.rule("[bold cyan]Generando capturas[/]")
    driver = make_driver()
    db     = get_driver()

    try:
        gen_schema(driver, db)
        gen_full_graph(driver, db)
        gen_character(driver, db, "Seraphia", "04-seraphia")
        gen_zones(driver, db)
        gen_shortest_path(driver, db)
        gen_table_character(driver, db)
        gen_table_loot(driver, db)
        gen_table_collab(driver, db)
        gen_table_pagerank(driver, db)
    finally:
        driver.quit()
        db.close()

    import shutil; shutil.rmtree(TMP, ignore_errors=True)
    console.rule("[bold green]Listo[/]")
    for f in sorted(f for f in os.listdir(OUT) if f.endswith(".png")):
        kb = os.path.getsize(os.path.join(OUT, f)) // 1024
        console.print(f"  {f}  ({kb} KB)")


if __name__ == "__main__":
    main()
