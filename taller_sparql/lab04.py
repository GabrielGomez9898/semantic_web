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


# ===========================================================================
titulo(1, "Cargar y mirar qué hay")
# ===========================================================================
print("tripletas en el grafo:", len(g))

# TODO 1.1 — Cuente cuántas instancias tiene cada clase. Una sola consulta con
# GROUP BY, ordenada de mayor a menor.
#
# tabla(consultar(g, """
# SELECT ...
# """))
tabla(consultar(g, """
SELECT ?clase (COUNT(?instancia) AS ?cantidad)
WHERE {
    ?instancia rdf:type ?clase .
}
GROUP BY ?clase
ORDER BY DESC(?cantidad)
"""))

# TODO 1.2 — Liste el vocabulario, es decir los términos que son rdfs:Class o
# rdf:Property, con su rdfs:label. Es lo primero que se lee de un grafo ajeno.
tabla(consultar(g, """
SELECT ?sujeto ?etiqueta
WHERE {
    {?sujeto rdf:type rdfs:Class}
    UNION
    {?sujeto rdf:type rdf:Property}
    ?sujeto rdfs:label ?etiqueta .
}
"""))

# ===========================================================================
titulo(2, "El primer SELECT, y qué pasa con lo que falta")
# ===========================================================================

# TODO 2.1 — Las obras de Fernando Vallejo con su año de publicación,
# ordenadas por año. Busque al autor por su rdfs:label, que es
# "Fernando Vallejo"@es, y no por su IRI.
tabla(consultar(g, """
SELECT ?obra ?anio
WHERE {
    ?recurso rdfs:label "Fernando Vallejo"@es.
    ?obra bib:autor ?recurso ; rdfs:label ?etiqueta ; bib:publicadaEn ?anio .
}
"""))


# TODO 2.2 — La misma consulta con el año dentro de un OPTIONAL. Compare el
# número de filas con el de 2.1 y explique la diferencia en una línea de
# comentario.
tabla(consultar(g, """
SELECT ?obra ?anio
WHERE {
    ?recurso rdfs:label "Fernando Vallejo"@es.
    ?obra bib:autor ?recurso ; rdfs:label ?etiqueta .
    OPTIONAL {?obra bib:publicadaEn ?anio} .
}
"""))

# TODO 2.3 — El año se guardó como xsd:gYear. Ejecute la misma consulta con
# cada uno de estos seis filtros y anote cuántas filas devuelve cada uno.
# Dos de ellos devuelven cero, y no porque el grafo esté vacío.
#
#   ?y = "1927"^^xsd:gYear
#   ?y != "1927"^^xsd:gYear
#   ?y < "1900"^^xsd:gYear
#   !sameTerm(?y, "1927"^^xsd:gYear)
#   STR(?y) != "1927"
#   xsd:integer(STR(?y)) < 1900

print("--------- Ejercicio 2.3 --------")
print("--- (filtro: ?y = 1927^^xsd:gYear) ---")

tabla(consultar(g, """
SELECT ?obra ?anio
WHERE {
    ?recurso rdfs:label "Fernando Vallejo"@es.
    ?obra bib:autor ?recurso ; rdfs:label ?etiqueta ; bib:publicadaEn ?anio .
    FILTER (?anio = "1927"^^xsd:gYear) .
}
"""))

print("--- (filtro: ?y != 1927^^xsd:gYear) ---")

tabla(consultar(g, """
SELECT ?obra ?anio
WHERE {
    ?recurso rdfs:label "Fernando Vallejo"@es.
    ?obra bib:autor ?recurso ; rdfs:label ?etiqueta .
    ?obra bib:publicadaEn ?anio .
    FILTER (?anio != "1927"^^xsd:gYear)
}
"""))

print("--- (filtro: ?y < 1900^^xsd:gYear) ---")

tabla(consultar(g, """
SELECT ?obra ?anio
WHERE {
    ?recurso rdfs:label "Fernando Vallejo"@es.
    ?obra bib:autor ?recurso ; rdfs:label ?etiqueta ; bib:publicadaEn ?anio .
    FILTER (?anio < "1900"^^xsd:gYear) .
}
"""))

print("--- (filtro: !sameTerm(?y, 1927^^xsd:gYear)) ---")

tabla(consultar(g, """
SELECT ?obra ?anio
WHERE {
    ?recurso rdfs:label "Fernando Vallejo"@es.
    ?obra bib:autor ?recurso ; rdfs:label ?etiqueta ; bib:publicadaEn ?anio .
    FILTER (!sameTerm(?anio, "1927"^^xsd:gYear)) .
}
"""))


# ===========================================================================
titulo(3, "Contar bien")
# ===========================================================================

# TODO 3.1 — Cuántas obras hay de cada género, con COUNT(?o) y GROUP BY.

tabla(consultar(g, """
SELECT (COUNT(?obra) AS ?cantidad_obras) ?genero
WHERE {
    ?obra bib:genero ?genero .
}
GROUP BY ?genero
"""))

# TODO 3.2 — Encuentre las obras que declaran más de un género. Use HAVING.
tabla(consultar(g, """
SELECT ?obra (COUNT(?genero) AS ?cantidad_generos)
WHERE {
    ?obra bib:genero ?genero .
}
GROUP BY ?obra
HAVING (COUNT(?genero) > 1)
"""))

# TODO 3.3 — En una sola consulta, devuelva COUNT(?o) y COUNT(DISTINCT ?o)
# sobre las obras con género. Explique la diferencia usando el resultado
# de 3.2.

tabla(consultar(g, """
SELECT ?obra (COUNT(?genero) AS ?cantidad_generos) (COUNT(DISTINCT ?genero) AS ?cantidad_generos_distintos)
WHERE {
    ?obra bib:genero ?genero .
}
GROUP BY ?obra
HAVING (COUNT(?genero) > 1)
"""))


# ===========================================================================
titulo(4, "Caminos de propiedad")
# ===========================================================================

# TODO 4.1 — Los municipios y la unidad territorial que los contiene, con un
# solo paso de bib:ubicadoEn.
tabla(consultar(g, """
SELECT ?recurso ?lugar
WHERE {
    ?recurso bib:ubicadoEn ?lugar .
}

"""))

# TODO 4.2 — Cuántos autores nacieron en cada unidad territorial, siguiendo
# bib:ubicadoEn con cierre transitivo. Use COUNT(DISTINCT ?a).
# Mire la primera fila y explique por qué está ahí.
tabla(consultar(g, """
SELECT  ?unidad_territorial (COUNT(distinct ?autor) AS ?cantidad_autores)
WHERE {
    ?obra bib:autor ?autor .
    ?autor bib:lugarNacimiento ?lugar .
    ?lugar bib:ubicadoEn+ ?unidad_territorial .
}
GROUP BY ?unidad_territorial
"""))

# TODO 4.3 — Repita 4.2 excluyendo a Colombia. El IRI es
# <http://uniandes.edu.co/ws2026/recurso/lugar/Q739-Colombia>.
# Revise después la lista y diga qué sigue estando mal, y por qué eso no se
# arregla con una consulta mejor.

# TODO 4.4 — Cuente las parejas de ?x bib:ubicadoEn+ ?y y las de
# ?x bib:ubicadoEn* ?y. Explique la diferencia con un número, no con una
# palabra.


# ===========================================================================
titulo(5, "Negación")
# ===========================================================================

# --- Primera pregunta: autores sin año de nacimiento registrado -----------
# TODO 5.1 — Escríbala de tres maneras y compruebe que las tres coinciden.
#   (a) OPTIONAL con FILTER(!BOUND(?y))
#   (b) FILTER NOT EXISTS
#   (c) MINUS

print("--------- Ejercicio 5.1 --------")
print("--- (a) OPTIONAL con FILTER(!BOUND(?y)) ---")
tabla(consultar(g, """
SELECT DISTINCT ?autor ?anio
WHERE {
    ?obra bib:autor ?autor .
    OPTIONAL {?autor bib:fechaNacimiento ?anio}
    FILTER (!BOUND(?anio))
}
"""))

print("--- (b) FILTER NOT EXISTS ---")
tabla(consultar(g, """
SELECT DISTINCT ?autor ?anio
WHERE {
    ?obra bib:autor ?autor .
    FILTER NOT EXISTS { ?autor bib:fechaNacimiento ?anio}
    
}
"""))

print("--- (c) MINUS ---")
tabla(consultar(g, """
SELECT DISTINCT ?autor ?anio
WHERE {
    ?obra bib:autor ?autor .
    MINUS { ?autor bib:fechaNacimiento ?anio}
    
}
"""))


# TODO 5.2 — Repita el MINUS cambiando la variable del bloque interno por una
# que no aparezca afuera. Cuente las filas y explique el resultado en términos
# de asignaciones compatibles.
print("--- Ejercicio 5.2 — MINUS con variable interna distinta ---")
tabla(consultar(g, """
SELECT DISTINCT ?autor ?anio
WHERE {
    ?obra bib:autor ?autor .
    MINUS { ?autor bib:fechaNacimiento ?fecha}
    
}
"""))

# --- Segunda pregunta: autores que no escribieron poesía ------------------
# TODO 5.3 — Cuántos autores tienen al menos una obra con género POESIA.
print("--- Ejercicio 5.3 — autores con al menos una obra de poesía ---")
tabla(consultar(g, """
SELECT (COUNT(?autor) AS ?cantidad_autores)
WHERE {
    ?obra bib:autor ?autor .
    ?recurso_genero rdfs:label "poesía"@es .
    ?obra bib:genero ?recurso_genero .
    
}
"""))

# TODO 5.4 — Escriba la versión con FILTER ( ?gx != POESIA ) y la versión con
# FILTER NOT EXISTS. Dan números muy distintos.

# TODO 5.5 — De los que devuelve la versión con desigualdad, encuentre los que
# sí escribieron poesía. Son los que demuestran que esa consulta responde otra
# pregunta.

# TODO 5.6 — La versión con NOT EXISTS devuelve muchos más autores de los que
# uno esperaría. Averigüe cuántos autores no tienen ningún género declarado y
# explique, en dos líneas de comentario, qué tiene que ver eso con la
# hipótesis de mundo abierto.


# ===========================================================================
titulo(6, "CONSTRUCT")
# ===========================================================================

# TODO 6.1 — Escriba un CONSTRUCT que traduzca el grafo al vocabulario de
# Dublin Core, con dct:title, dct:creator y dct:issued. El año va dentro de un
# OPTIONAL. Cuente las tripletas generadas y las obras cubiertas, e imprima
# las primeras líneas del resultado en Turtle.
#
#   resultado = g.query(PREFIJOS + "CONSTRUCT { ... } WHERE { ... }")
#   salida = Graph()
#   for t in resultado:
#       salida.add(t)
#   print(salida.serialize(format="turtle"))


# ===========================================================================
titulo(7, "El orden de los patrones")
# ===========================================================================

LENTA = """
SELECT ?autor ?obra
WHERE {
  ?o a bib:Obra .
  ?a a bib:Autor .
  ?o bib:autor ?a .
  ?a rdfs:label ?autor .
  ?o rdfs:label ?obra .
  ?a bib:anioNacimiento "1927"^^xsd:gYear .
}
"""

# TODO 7.1 — Escriba RAPIDA, equivalente a LENTA, poniendo primero el patrón
# más selectivo. No cambie qué devuelve, solo el orden.

# TODO 7.2 — Mida las dos. Ejecute cada una varias veces y promedie, porque
# una sola medición sobre un grafo pequeño no dice nada.
#
# def medir(consulta, repeticiones=20):
#     inicio = time.perf_counter()
#     for _ in range(repeticiones):
#         n = len(list(consultar(g, consulta)))
#     return n, (time.perf_counter() - inicio) / repeticiones

# TODO 7.3 — Compruebe que las dos devuelven el mismo número de filas. Si no,
# no son equivalentes y la comparación de tiempos no significa nada.


# ===========================================================================
titulo(8, "El endpoint remoto")
# ===========================================================================


def wdqs(consulta, intentos=4):
    """Envía una consulta a Wikidata por POST, con reintentos.

    Un endpoint público responde 429 cuando se le pide demasiado seguido.
    Reintentar con espera creciente es lo que se espera de un cliente educado.
    """
    datos = urllib.parse.urlencode({"query": consulta, "format": "json"}).encode()
    peticion = urllib.request.Request(
        WDQS, data=datos,
        headers={"User-Agent": UA,
                 "Accept": "application/sparql-results+json",
                 "Content-Type": "application/x-www-form-urlencoded"})
    for intento in range(intentos):
        try:
            with urllib.request.urlopen(peticion, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))["results"]["bindings"]
        except urllib.error.HTTPError as e:
            if e.code not in (429, 503) or intento == intentos - 1:
                raise
            time.sleep(8 * (intento + 1))
    raise RuntimeError("no alcanzado")


# TODO 8.1 — Saque del grafo local unos seis autores que tengan owl:sameAs y
# al menos un bib:reconocimiento. Los enlaces owl:sameAs son la puerta hacia
# Wikidata.

# TODO 8.2 — Pregunte a Wikidata los premios de cada uno, con una petición por
# autor, y mida el tiempo total. La propiedad de premio es wdt:P166.
#
#   SELECT ?premioLabel WHERE {
#     wd:Q12345 wdt:P166 ?premio .
#     SERVICE wikibase:label { bd:serviceParam wikibase:language "es,en". }
#   }

# TODO 8.3 — Haga lo mismo en una sola petición, con VALUES. Mida y compare.
# Anote cuántas veces menos tiempo tomó, y verifique que los datos son los
# mismos.

# TODO 8.4 — Compare los premios que devuelve Wikidata con los que tiene el
# grafo local. Si sobran o faltan, explique por qué, sabiendo que el grafo
# local se generó de Wikidata en agosto de 2026.

print()
print("Fin. Compare con solucion.py cuando haya intentado todo.")
