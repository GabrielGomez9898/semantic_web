"""
Laboratorio 2 — Solución de referencia
Web Semántica (ISIS4514) · 2026-20 · Universidad de los Andes

Versión completa de lab02.py. Conviene intentar el esqueleto antes de leer
esto. Los comentarios señalan el punto que cada bloque quiere dejar claro.

Ejecución:
    python solucion.py
"""

from rdflib import Graph, Namespace, Literal, BNode
from rdflib.collection import Collection
from rdflib.compare import isomorphic
from rdflib.namespace import RDFS, XSD

EX = Namespace("http://example.org/ws2026/")
DBO = Namespace("http://dbpedia.org/ontology/")
DBR = Namespace("http://dbpedia.org/resource/")


def enlazar(g: Graph) -> Graph:
    g.bind("ex", EX)
    g.bind("dbo", DBO)
    g.bind("dbr", DBR)
    return g


def titulo(texto: str) -> None:
    print("\n" + "=" * 70)
    print(texto)
    print("=" * 70)


# ---------------------------------------------------------------------------
# 2. Construir un grafo a mano — 7 tripletas
# ---------------------------------------------------------------------------
def construir_grafo() -> Graph:
    g = enlazar(Graph())

    g.add((DBR.Pluto, RDFS.label, Literal("Plutón", lang="es")))
    g.add((DBR.Pluto, RDFS.label, Literal("Pluto", lang="en")))
    g.add((DBR.Pluto, DBO.meanRadius, Literal(1161.0, datatype=XSD.double)))
    g.add((DBR.Pluto, DBO.discovered, Literal("1930-02-18", datatype=XSD.date)))

    for satelite in (DBR.Charon, DBR.Nix, DBR.Hydra):
        g.add((DBR.Pluto, DBO.hasSatellite, satelite))

    return g


# ---------------------------------------------------------------------------
# 3. Serializar
# ---------------------------------------------------------------------------
def comparar_formatos(g: Graph) -> None:
    for formato in ["nt", "turtle", "xml", "json-ld"]:
        texto = g.serialize(format=formato)
        print(f"{formato:>8}  {len(texto):>7} bytes")


def grafo_grande(sujetos: int = 20, props: int = 50) -> Graph:
    """Muchas tripletas sobre pocos sujetos, que es el caso donde Turtle gana.

    N-Triples repite el IRI del sujeto en cada línea, mientras que Turtle lo
    escribe una vez y usa punto y coma. La ventaja relativa de Turtle crece
    con el número de tripletas por sujeto.
    """
    g = enlazar(Graph())
    for i in range(sujetos):
        sujeto = EX[f"recurso{i}"]
        for j in range(props):
            g.add((sujeto, EX[f"prop{j}"], Literal(j)))
    return g


# ---------------------------------------------------------------------------
# 4. Isomorfismo
# ---------------------------------------------------------------------------
def comparar_grafos(g: Graph) -> None:
    xml = g.serialize(format="xml")
    ttl = g.serialize(format="turtle")

    g_xml = Graph().parse(data=xml, format="xml")
    g_ttl = Graph().parse(data=ttl, format="turtle")

    print(f"¿los textos son iguales?  {xml == ttl}")
    print(f"¿los grafos son iguales?  {isomorphic(g_xml, g_ttl)}")

    # El orden de inserción no importa porque un grafo es un conjunto. rdflib
    # lo almacena en un índice, no en una lista, de modo que la secuencia de
    # add() se pierde por construcción.
    invertido = enlazar(Graph())
    for tripleta in reversed(list(g)):
        invertido.add(tripleta)

    print(f"¿isomorfo al invertido?   {isomorphic(g, invertido)}")
    print(f"¿el Turtle es idéntico?   "
          f"{g.serialize(format='turtle') == invertido.serialize(format='turtle')}")


# ---------------------------------------------------------------------------
# 5. Literales
# ---------------------------------------------------------------------------
def literales() -> None:
    g = enlazar(Graph())
    g.add((EX.a, EX.valor, Literal("134340")))
    g.add((EX.b, EX.valor, Literal(134340)))

    for sujeto, _, objeto in g:
        print(f"{sujeto.n3():<40} {objeto.n3():<28} {type(objeto.toPython())}")

    print('Literal("134340") == Literal(134340)  ->  '
          f"{Literal('134340') == Literal(134340)}")

    # Las cuatro propiedades de un libro, cada una con el tipo que le
    # corresponde.
    libro = enlazar(Graph())
    libro.add((EX.libro1, EX.paginas, Literal(471, datatype=XSD.integer)))
    libro.add((EX.libro1, EX.publicado,
               Literal("1967-05-30", datatype=XSD.date)))
    # El ISBN es una cadena y no un número. Tiene ceros a la izquierda
    # significativos, un dígito de control que puede ser 'X', y nunca se suma
    # ni se compara por orden numérico.
    libro.add((EX.libro1, EX.isbn, Literal("9789587578621", datatype=XSD.string)))
    # El título lo va a leer un humano, de modo que lleva etiqueta de idioma.
    libro.add((EX.libro1, EX.titulo, Literal("Cien años de soledad", lang="es")))

    print(libro.serialize(format="turtle"))


# ---------------------------------------------------------------------------
# 6. Nodos en blanco y unión
# ---------------------------------------------------------------------------
def mision_con_blanco(nave, fecha: str) -> Graph:
    g = enlazar(Graph())
    m = BNode()
    g.add((DBR.Pluto, DBO.spaceMission, m))
    g.add((m, DBO.spaceShip, nave))
    g.add((m, DBO.visited, Literal(fecha, datatype=XSD.date)))
    return g


def mision_con_iri(iri, nave, fecha: str) -> Graph:
    g = enlazar(Graph())
    g.add((DBR.Pluto, DBO.spaceMission, iri))
    g.add((iri, DBO.spaceShip, nave))
    g.add((iri, DBO.visited, Literal(fecha, datatype=XSD.date)))
    return g


def nodos_en_blanco() -> None:
    # Caso 1: la misma misión descrita dos veces con nodos en blanco.
    a = mision_con_blanco(DBR.New_Horizons, "2015-07-14")
    b = mision_con_blanco(DBR.New_Horizons, "2015-07-14")
    print(f"con nodos en blanco, la unión tiene {len(a + b)} tripletas")

    # Caso 2: la misma misión con un IRI compartido.
    iri = EX["mision/NH-Pluto"]
    c = mision_con_iri(iri, DBR.New_Horizons, "2015-07-14")
    d = mision_con_iri(iri, DBR.New_Horizons, "2015-07-14")
    print(f"con un IRI compartido,  la unión tiene {len(c + d)} tripletas")

    # Seis contra tres. Los nodos en blanco no se identifican entre documentos,
    # de modo que la unión describe dos misiones donde había una sola. Esta es
    # la razón por la que la integración de datos entre fuentes independientes
    # exige identificadores compartidos.


def colecciones() -> None:
    cerrada = enlazar(Graph())
    cabeza = BNode()
    Collection(cerrada, cabeza, [EX.Azucar, EX.Agua, EX.Limon])
    cerrada.add((EX.Limonada, EX.ingredientes, cabeza))
    print(f"colección cerrada:        {len(cerrada)} tripletas")

    plana = enlazar(Graph())
    for ingrediente in (EX.Azucar, EX.Agua, EX.Limon):
        plana.add((EX.Limonada, EX.ingrediente, ingrediente))
    print(f"tripletas repetidas:      {len(plana)} tripletas")

    # Siete contra tres, por conservar un orden que en este dominio no importa.
    print(cerrada.serialize(format="turtle"))


# ---------------------------------------------------------------------------
# 7. Un dato real
# ---------------------------------------------------------------------------
def dato_real(fuente: str = "http://dbpedia.org/data/Pluto.ttl") -> None:
    externo = Graph()
    try:
        externo.parse(fuente, format="turtle")
    except Exception as error:
        print(f"no se pudo descargar ({error}); use la copia local pluto.ttl")
        return

    print(f"tripletas descargadas: {len(externo)}")
    print(f"predicados distintos:  {len({p for _, p, _ in externo})}")

    sin_tipo, con_idioma = [], []
    for _, p, o in externo:
        if isinstance(o, Literal):
            if o.language:
                con_idioma.append((p, o))
            elif o.datatype is None:
                sin_tipo.append((p, o))

    print(f"literales sin datatype: {len(sin_tipo)}")
    for p, o in sin_tipo[:3]:
        print(f"   {p.n3(externo.namespace_manager)}  {o.n3()[:60]}")
    print(f"literales con idioma:   {len(con_idioma)}")
    for p, o in con_idioma[:3]:
        print(f"   {p.n3(externo.namespace_manager)}  {o.n3()[:60]}")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    titulo("2. Construir un grafo a mano")
    grafo = construir_grafo()
    print(f"tripletas: {len(grafo)}")
    print(grafo.serialize(format="turtle"))

    titulo("3. Serializar en los cuatro formatos")
    comparar_formatos(grafo)
    print("\nMil tripletas sobre veinte sujetos:")
    comparar_formatos(grafo_grande())

    titulo("4. Isomorfismo, no diff")
    comparar_grafos(grafo)

    titulo("5. El tipo de dato olvidado")
    literales()

    titulo("6. Nodos en blanco y unión")
    nodos_en_blanco()

    titulo("6b. Colecciones")
    colecciones()

    titulo("7. Un dato real")
    dato_real()
