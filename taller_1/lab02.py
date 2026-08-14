"""
Laboratorio 2 — Grafos RDF con rdflib
Web Semántica (ISIS4514) · 2026-20 · Universidad de los Andes

Esqueleto del laboratorio de la sesión 2. Cada bloque corresponde a una
sección de guia.pdf. Los puntos marcados con TODO son los que hay que
completar; el resto está resuelto y sirve de ejemplo.

Ejecución:
    pip install rdflib
    python lab02.py
"""

from rdflib import Graph, Namespace, Literal, BNode
from rdflib.collection import Collection
from rdflib.compare import isomorphic
from rdflib.namespace import RDF, RDFS, XSD

EX = Namespace("http://example.org/ws2026/")
DBO = Namespace("http://dbpedia.org/ontology/")
DBR = Namespace("http://dbpedia.org/resource/")


def enlazar(g: Graph) -> Graph:
    """Declara los prefijos para que las serializaciones salgan legibles."""
    g.bind("ex", EX)
    g.bind("dbo", DBO)
    g.bind("dbr", DBR)
    return g


def titulo(texto: str) -> None:
    print("\n" + "=" * 70)
    print(texto)
    print("=" * 70)


# ---------------------------------------------------------------------------
# 2. Construir un grafo a mano
# ---------------------------------------------------------------------------
def construir_grafo() -> Graph:
    g = enlazar(Graph())

    g.add((DBR.Pluto, RDFS.label, Literal("Plutón", lang="es")))
    g.add((DBR.Pluto, DBO.meanRadius, Literal(1161.0, datatype=XSD.double)))
    g.add((DBR.Pluto, DBO.discovered, Literal("1930-02-18", datatype=XSD.date)))
    g.add((DBR.Pluto, DBO.hasSatellite, DBR.Charon))
    g.add((DBR.Pluto, DBO.hasSatellite, DBR.Nix))
    g.add((DBR.Pluto, DBO.hasSatellite, DBR.Hydra))
    g.add((DBR.Charon, RDFS.label, Literal("Charon", lang="en")))
    g.add((DBR.Nix, RDFS.label, Literal("Nix", lang="en")))
    g.add((DBR.Hydra, RDFS.label, Literal("Hydra", lang="en")))

    # TODO 1: agregar la etiqueta en inglés y los tres satélites
    #         (dbr:Charon, dbr:Nix, dbr:Hydra) con dbo:hasSatellite.
    #         Antes de ejecutar, escriba aquí cuántas tripletas espera: _9__

    return g


# ---------------------------------------------------------------------------
# 3. Serializar en los cuatro formatos
# ---------------------------------------------------------------------------
def comparar_formatos(g: Graph) -> None:
    for formato in ["nt", "turtle", "xml", "json-ld"]:
        texto = g.serialize(format=formato)
        print(f"{formato:>8}  {len(texto):>7} bytes")

    # TODO 2: construir un grafo de 1000 tripletas sobre 20 sujetos y repetir
    #         la comparación. ¿Cambia el orden de los formatos por tamaño?


# ---------------------------------------------------------------------------
# 4. Isomorfismo, no diff
# ---------------------------------------------------------------------------
def comparar_grafos(g: Graph) -> None:
    xml = g.serialize(format="xml")
    ttl = g.serialize(format="turtle")

    g_xml = Graph().parse(data=xml, format="xml")
    g_ttl = Graph().parse(data=ttl, format="turtle")

    print(f"¿los textos son iguales?  {xml == ttl}")
    print(f"¿los grafos son iguales?  {isomorphic(g_xml, g_ttl)}")

    # TODO 3: construir un grafo con las mismas tripletas insertadas en orden
    #         inverso y comprobar que es isomorfo al original.


# ---------------------------------------------------------------------------
# 5. El tipo de dato olvidado
# ---------------------------------------------------------------------------
def literales() -> None:
    g = enlazar(Graph())
    g.add((EX.a, EX.valor, Literal("134340")))
    g.add((EX.b, EX.valor, Literal(134340)))

    for sujeto, _, objeto in g:
        print(f"{sujeto.n3():<40} {objeto.n3():<28} {type(objeto.toPython())}")

    print(f'Literal("134340") == Literal(134340)  ->  '
          f"{Literal('134340') == Literal(134340)}")

    # TODO 4: escriba la tripleta correcta para cada caso, con el tipo que
    #         corresponda: páginas de un libro, fecha de publicación, ISBN,
    #         título. Justifique en un comentario por qué el ISBN no es un
    #         número y por qué el título lleva etiqueta de idioma.


# ---------------------------------------------------------------------------
# 6. Nodos en blanco y unión de grafos
# ---------------------------------------------------------------------------
def nodos_en_blanco() -> None:
    g1 = enlazar(Graph())
    m1 = BNode()
    g1.add((DBR.Pluto, DBO.spaceMission, m1))
    g1.add((m1, DBO.spaceShip, DBR.New_Horizons))
    g1.add((m1, DBO.visited, Literal("2015-07-14", datatype=XSD.date)))

    # TODO 5: construir g2 con la segunda misión, también con nodo en blanco.
    #         Unir con  union = g1 + g2  y contar las tripletas.
    #         Repetir usando un mismo IRI (EX["mision/NH"]) en ambos grafos.
    #         Comparar los dos conteos y explicar la diferencia.

    print(g1.serialize(format="turtle"))


def colecciones() -> None:
    g = enlazar(Graph())
    cabeza = BNode()
    Collection(g, cabeza, [EX.Azucar, EX.Agua, EX.Limon])
    g.add((EX.Limonada, EX.ingredientes, cabeza))

    print(f"tripletas de la colección: {len(g)}")
    print(g.serialize(format="turtle"))

    # TODO 6: escribir la misma información con tres tripletas del mismo
    #         predicado y comparar el conteo.


# ---------------------------------------------------------------------------
# 7. Un dato real
# ---------------------------------------------------------------------------
def dato_real(fuente: str = "http://dbpedia.org/data/Pluto.ttl") -> None:
    externo = Graph()
    try:
        externo.parse(fuente, format="turtle")
    except Exception as error:  # el endpoint público se cae con frecuencia
        print(f"no se pudo descargar ({error}); use la copia local pluto.ttl")
        return

    print(f"tripletas descargadas: {len(externo)}")
    predicados = {p for _, p, _ in externo}
    print(f"predicados distintos:  {len(predicados)}")

    # TODO 7: listar tres literales sin datatype que deberían tenerlo y tres
    #         literales con etiqueta de idioma.

# -------------------------METODOS AUXULIARES -------------------
def construir_grafo_1000() -> Graph:
    g = enlazar(Graph())
    for i in range(20):
        sujeto = EX[f"sujeto{i}"]
        for j in range(50):
            predicado = EX[f"predicado{j}"]
            objeto = Literal(f"objeto{i}_{j}")
            g.add((sujeto, predicado, objeto))
    return g

def grafo_inverso() -> Graph:
    
    g_inverso = enlazar(Graph())
    g_inverso.add((DBR.Hydra, RDFS.label, Literal("Hydra", lang="en")))      
    g_inverso.add((DBR.Nix, RDFS.label, Literal("Nix", lang="en")))           
    g_inverso.add((DBR.Charon, RDFS.label, Literal("Charon", lang="en")))     
    g_inverso.add((DBR.Pluto, DBO.hasSatellite, DBR.Hydra))                  
    g_inverso.add((DBR.Pluto, DBO.hasSatellite, DBR.Nix))                    
    g_inverso.add((DBR.Pluto, DBO.hasSatellite, DBR.Charon))                 
    g_inverso.add((DBR.Pluto, DBO.discovered, Literal("1930-02-18", datatype=XSD.date))) 
    g_inverso.add((DBR.Pluto, DBO.meanRadius, Literal(1161.0, datatype=XSD.double)))     
    g_inverso.add((DBR.Pluto, RDFS.label, Literal("Plutón", lang="es")))
    
    return g_inverso
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    titulo("2. Construir un grafo a mano")
    grafo = construir_grafo()
    print(f"tripletas: {len(grafo)}")
    print(grafo.serialize(format="turtle"))

    titulo("3. Serializar en los cuatro formatos")
    print("-- comparacion del grafo 1 --")
    comparar_formatos(grafo)
    
    print("-- comparacion del grafo 2 --")
    grafo_1000 = construir_grafo_1000()
    comparar_formatos(grafo_1000)
    

    titulo("4. Isomorfismo, no diff")
    print("-- comparacion del grafo original --")
    comparar_grafos(grafo)
    
    print("-- comparacion del grafo invertido --")
    grafo_invertido = grafo_inverso()
    comparar_grafos(grafo_invertido)

    titulo("5. El tipo de dato olvidado")
    literales()

    titulo("6. Nodos en blanco")
    nodos_en_blanco()

    titulo("6b. Colecciones")
    colecciones()

    titulo("7. Un dato real")
    dato_real()
