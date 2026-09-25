"""Laboratorio 4 — SPARQL sobre un grafo local y sobre Wikidata.

    python lab04.py

Ocho partes, cada una con al menos un TODO. La guía en guia.pdf explica qué se
busca en cada una y qué conviene mirar del resultado. La solución completa está
en solucion.py y conviene no abrirla antes de intentarlo.

Única dependencia:  pip install rdflib
La parte 8 usa urllib de la biblioteca estándar y necesita red.
"""
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from rdflib import Graph

DATOS = Path(__file__).parent / "datos" / "literatura.ttl"
WDQS = "https://query.wikidata.org/sparql"
UA = "WebSemanticaUniandes/1.0 (curso ISIS4514)"

PREFIJOS = """
PREFIX bib:  <http://uniandes.edu.co/ws2026/vocab/lit#>
PREFIX lit:  <http://uniandes.edu.co/ws2026/recurso/>
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl:  <http://www.w3.org/2002/07/owl#>
PREFIX dct:  <http://purl.org/dc/terms/>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>
"""

# El IRI del género «poesía». Lleva una barra en la parte local, de modo que no
# es un PNAME válido y hay que escribirlo entre ángulos.
POESIA = "<http://uniandes.edu.co/ws2026/recurso/genero/Q482-poesia>"


def titulo(n, texto):
    print()
    print("=" * 72)
    print("Parte %s. %s" % (n, texto))
    print("=" * 72)


def tabla(resultado, maximo=12):
    """Imprime un resultado de SELECT marcando las celdas sin ligar.

    Marcarlas importa. Una celda sin ligar impresa como cadena vacía esconde
    justamente lo que varias partes de este laboratorio quieren mostrar.
    """
    filas = list(resultado)
    nombres = [str(v) for v in resultado.vars]
    print("  " + " | ".join("%-34s" % n for n in nombres))
    print("  " + "-+-".join("-" * 34 for _ in nombres))
    for fila in filas[:maximo]:
        celdas = ["SIN LIGAR" if c is None else str(c).split("/")[-1] for c in fila]
        print("  " + " | ".join("%-34s" % c[:34] for c in celdas))
    if len(filas) > maximo:
        print("  ... y %d filas más" % (len(filas) - maximo))
    print("  total: %d filas" % len(filas))
    return filas


def consultar(g, consulta):
    return g.query(PREFIJOS + consulta)


g = Graph()
g.parse(DATOS, format="turtle")

# TODO 1.1 — Cuente cuántas instancias tiene cada clase. Una sola consulta con
# GROUP BY, ordenada de mayor a menor.
#
# tabla(consultar(g, """
# SELECT ...
# """))
tabla(consultar(g, """
SELECT ?anio (COUNT(?obra) AS ?num_obras)
WHERE {
    ?obra a bib:Obra .
    ?obra bib:publicadaEn ?anio .
}
GROUP BY ?anio

"""))