"""Conexión compartida a Neo4j."""
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

URI  = os.getenv("NEO4J_URI",  "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASS = os.getenv("NEO4J_PASSWORD", "titanpoc")


def get_driver():
    return GraphDatabase.driver(URI, auth=(USER, PASS))


def run(query: str, params: dict = None):
    with get_driver() as driver:
        with driver.session() as session:
            return list(session.run(query, params or {}))
