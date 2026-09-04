"""Reconstruye datos/literatura-la.ttl a partir de Wikidata.

El archivo literatura-la.ttl ya está en el repositorio, de modo que este script
no hace falta para el taller. Está aquí por procedencia, para que se pueda
comprobar de dónde salió cada tripleta y para poder regenerar el volcado cuando
Wikidata cambie.

Es el mismo programa del laboratorio 4 con la lista de países ampliada de uno a
tres. Requiere red y unos minutos. Tres decisiones de diseño quedan explícitas
en el código.

1. Se piden obras literarias (P31 = Q7725634) y no ediciones. La primera
   versión de este script pedía cualquier obra escrita y el resultado estaba
   dominado por traducciones y reediciones de los mismos títulos.
2. Las etiquetas se piden en una consulta aparte, porque el servicio de
   etiquetas de Wikidata devuelve el propio QID en algunas filas cuando la
   consulta principal tiene muchos OPTIONAL.
3. La jerarquía territorial se recorre con tres pasadas de P131 en lugar de un
   camino con cierre, porque el camino con los dos extremos libres agota el
   tiempo del endpoint público.
"""
import json
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import OWL, RDF, RDFS, XSD

ENDPOINT = "https://query.wikidata.org/sparql"
UA = "WebSemanticaUniandes/1.0 (curso ISIS4514)"

BIB = Namespace("http://uniandes.edu.co/ws2026/vocab/lit#")
LIT = Namespace("http://uniandes.edu.co/ws2026/recurso/")

SALIDA = "literatura-la.ttl"

# Tres paises, para que el volcado sea el triple del laboratorio 4 y el orden
# de los patrones se note en el tiempo de respuesta. Con ocho, la extraccion
# tardaba mas de media hora contra el endpoint publico y acumulaba reintentos
# por limite de ritmo. Ampliar la lista es cambiar esta linea, y conviene
# hacerlo fuera de la semana de clase.
PAISES = "wd:Q739 wd:Q96 wd:Q414"   # Colombia, Mexico, Argentina


# ---------------------------------------------------------------------------
# Acceso al endpoint
# ---------------------------------------------------------------------------
def abrir(peticion, intentos=5):
    """
    Abre una petición reintentando cuando Wikidata limita el ritmo.
    """
    for intento in range(intentos):
        try:
            with urllib.request.urlopen(peticion, timeout=180) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code not in (429, 502, 503, 504) or intento == intentos - 1:
                raise
            espera = 10 * (intento + 1)
            print("   %d, esperando %d s" % (e.code, espera))
            time.sleep(espera)
    raise RuntimeError("no alcanzado")


def consultar(texto):
    datos = urllib.parse.urlencode({"query": texto, "format": "json"}).encode()
    peticion = urllib.request.Request(
        ENDPOINT, data=datos,
        headers={"User-Agent": UA,
                 "Accept": "application/sparql-results+json",
                 "Content-Type": "application/x-www-form-urlencoded"})
    time.sleep(1)
    return abrir(peticion)["results"]["bindings"]


def v(fila, clave):
    celda = fila.get(clave)
    return celda["value"] if celda else None


def qid(iri):
    return iri.rsplit("/", 1)[-1]


def valores(iris):
    return " ".join("wd:" + qid(x) for x in iris)


def slug(texto):
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "-", t).strip("-")[:60] or "sin-nombre"


def anio_de(fecha):
    """
    Devuelve (año, fecha completa o None).

    Wikidata almacena 1967-01-01 tanto para «publicada en 1967» como para
    «publicada el 1 de enero de 1967». Se conserva el año siempre y la fecha
    completa solo cuando el día no es el primero de enero, que es la
    convención con la que Wikidata marca la precisión de año.
    """
    if not fecha:
        return None, None
    m = re.match(r"(-?\d{4})-(\d{2})-(\d{2})", fecha)
    if not m:
        return None, None
    anio, mes, dia = m.groups()
    return anio, (fecha[:10] if (mes, dia) != ("01", "01") else None)


# ---------------------------------------------------------------------------
# Extracción
# ---------------------------------------------------------------------------
print("obras literarias de escritores latinoamericanos...")
OBRAS = consultar("""
SELECT ?a ?w ?nac ?fal ?pub ?genero ?generoLabel ?idiomaLabel WHERE {
  VALUES ?pais { %s }
  ?a wdt:P27 ?pais ; wdt:P106 wd:Q36180 .
  ?w wdt:P50 ?a ; wdt:P31 wd:Q7725634 .
  OPTIONAL { ?a wdt:P569 ?nac }
  OPTIONAL { ?a wdt:P570 ?fal }
  OPTIONAL { ?w wdt:P577 ?pub }
  OPTIONAL { ?w wdt:P136 ?genero }
  OPTIONAL { ?w wdt:P407 ?idioma }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "es,en". }
} LIMIT 20000""" % PAISES)
print("  ", len(OBRAS), "filas")

print("lugares de nacimiento...")
AUTOR_LUGAR = consultar("""
SELECT DISTINCT ?a ?lugar WHERE {
  VALUES ?pais { %s }
  ?a wdt:P27 ?pais ; wdt:P106 wd:Q36180 ; wdt:P19 ?lugar .
}""" % PAISES)
print("  ", len(AUTOR_LUGAR), "filas")

print("jerarquía territorial...")
# Se recorre P131 por niveles y en lotes. Un VALUES con miles de elementos
# hace que el endpoint devuelva 500, y un camino con cierre y los dos extremos
# libres agota el tiempo. Los lotes de trescientos funcionan.
PADRES = {}
frente = {v(f, "lugar") for f in AUTOR_LUGAR}
# Tres pasadas bastan para municipio, departamento y país. Con más, el número
# de lugares crece rápido sin aportar nada al taller.
for _ in range(3):
    if not frente:
        break
    nuevos = set()
    lote = sorted(frente)
    for i in range(0, len(lote), 300):
        filas = consultar("SELECT ?x ?p WHERE { VALUES ?x { %s } ?x wdt:P131 ?p }"
                          % valores(lote[i:i + 300]))
        for f in filas:
            PADRES.setdefault(v(f, "x"), set()).add(v(f, "p"))
            nuevos.add(v(f, "p"))
    frente = nuevos - set(PADRES)
    print("   nivel con %d lugares, %d aristas acumuladas"
          % (len(lote), sum(len(x) for x in PADRES.values())))
print("  ", sum(len(x) for x in PADRES.values()), "aristas")

print("premios...")
PREMIOS = consultar("""
SELECT DISTINCT ?a ?premio ?anio WHERE {
  VALUES ?pais { %s }
  ?a wdt:P27 ?pais ; wdt:P106 wd:Q36180 ; p:P166 ?st .
  ?st ps:P166 ?premio .
  OPTIONAL { ?st pq:P585 ?anio }
} LIMIT 8000""" % PAISES)
print("  ", len(PREMIOS), "filas")

# --- Etiquetas, en una consulta aparte -------------------------------------
entidades = set()
for f in OBRAS:
    entidades.update(x for x in (v(f, "a"), v(f, "w"), v(f, "genero")) if x)
for f in AUTOR_LUGAR:
    entidades.add(v(f, "lugar"))
for hijo, ps in PADRES.items():
    entidades.add(hijo)
    entidades.update(ps)
for f in PREMIOS:
    entidades.update(x for x in (v(f, "a"), v(f, "premio")) if x)
entidades = {e for e in entidades
             if e and e.startswith("http://www.wikidata.org/entity/Q")}

print("etiquetas de", len(entidades), "entidades...")
# Las etiquetas se piden a la API de entidades y no al servicio de consultas.
# El servicio devuelve el conjunto vacío para algunos elementos muy visitados,
# incluido Q5878, que es Gabriel García Márquez, y perderlo dejaría el grafo
# del curso sin el autor que todo el mundo va a buscar primero.
ETIQUETA = {}
API = "https://www.wikidata.org/w/api.php"
orden = sorted(entidades)
for i in range(0, len(orden), 50):
    trozo = [qid(x) for x in orden[i:i + 50]]
    url = API + "?" + urllib.parse.urlencode({
        "action": "wbgetentities", "format": "json", "props": "labels",
        "languages": "es|en", "languagefallback": "1", "ids": "|".join(trozo)})
    peticion = urllib.request.Request(url, headers={"User-Agent": UA})
    time.sleep(0.5)
    cuerpo = abrir(peticion)
    for clave, ent in cuerpo.get("entities", {}).items():
        etiquetas = ent.get("labels", {})
        for idioma in ("es", "en"):
            if idioma in etiquetas:
                ETIQUETA["http://www.wikidata.org/entity/" + clave] = \
                    etiquetas[idioma]["value"]
                break
print("  ", len(ETIQUETA), "con etiqueta;", len(entidades) - len(ETIQUETA), "sin ella")


# ---------------------------------------------------------------------------
# Construcción del grafo
# ---------------------------------------------------------------------------
g = Graph()
for pfx, ns in (("bib", BIB), ("lit", LIT), ("owl", OWL), ("xsd", XSD)):
    g.bind(pfx, ns)


def iri(carpeta, wd):
    """IRI local: el QID hace el identificador estable y el fragmento legible
    hace que el grafo se pueda leer a ojo. Se documenta en la guía."""
    nombre = ETIQUETA.get(wd)
    return LIT["%s/%s-%s" % (carpeta, qid(wd), slug(nombre))] if nombre else None


def etiquetar(sujeto, wd, clase):
    g.add((sujeto, RDF.type, clase))
    g.add((sujeto, RDFS.label, Literal(ETIQUETA[wd], lang="es")))
    g.add((sujeto, OWL.sameAs, URIRef(wd)))


# --- Vocabulario -----------------------------------------------------------
CLASES = [
    (BIB.Autor, "autor", "Persona que escribió al menos una obra literaria."),
    (BIB.Obra, "obra",
     "Obra literaria, entendida como creación y no como ejemplar ni edición."),
    (BIB.Lugar, "lugar", "Municipio, departamento o país."),
    (BIB.Genero, "género", "Género literario."),
    (BIB.Premio, "premio", "Distinción otorgada a una persona."),
    (BIB.Reconocimiento, "reconocimiento",
     "Hecho de que una persona recibió un premio, con su año cuando se conoce."),
]
PROPIEDADES = [
    (BIB.autor, "autor", "Persona que escribió la obra.", BIB.Obra, BIB.Autor),
    (BIB.fechaNacimiento, "fecha de nacimiento",
     "Fecha completa de nacimiento. Solo está cuando Wikidata la registra con "
     "precisión de día.", BIB.Autor, None),
    (BIB.anioNacimiento, "año de nacimiento",
     "Año de nacimiento.", BIB.Autor, None),
    (BIB.anioFallecimiento, "año de fallecimiento",
     "Año de fallecimiento. Su ausencia no significa que la persona esté viva.",
     BIB.Autor, None),
    (BIB.lugarNacimiento, "lugar de nacimiento",
     "Municipio de nacimiento.", BIB.Autor, BIB.Lugar),
    (BIB.ubicadoEn, "ubicado en",
     "Unidad territorial que contiene a esta.", BIB.Lugar, BIB.Lugar),
    (BIB.publicadaEn, "publicada en",
     "Año de primera publicación.", BIB.Obra, None),
    (BIB.genero, "género", "Género literario de la obra.", BIB.Obra, BIB.Genero),
    (BIB.idioma, "idioma", "Idioma en que se escribió la obra.", BIB.Obra, None),
    (BIB.reconocimiento, "reconocimiento",
     "Reconocimiento recibido por la persona.", BIB.Autor, BIB.Reconocimiento),
    (BIB.premio, "premio", "Premio del reconocimiento.",
     BIB.Reconocimiento, BIB.Premio),
    (BIB.anio, "año", "Año en que se otorgó el reconocimiento.",
     BIB.Reconocimiento, None),
]
for clase, etiqueta, comentario in CLASES:
    g.add((clase, RDF.type, RDFS.Class))
    g.add((clase, RDFS.label, Literal(etiqueta, lang="es")))
    g.add((clase, RDFS.comment, Literal(comentario, lang="es")))
for prop, etiqueta, comentario, dom, ran in PROPIEDADES:
    g.add((prop, RDF.type, RDF.Property))
    g.add((prop, RDFS.label, Literal(etiqueta, lang="es")))
    g.add((prop, RDFS.comment, Literal(comentario, lang="es")))
    if dom:
        g.add((prop, RDFS.domain, dom))
    if ran:
        g.add((prop, RDFS.range, ran))

# --- Autores y obras -------------------------------------------------------
# Solo se conservan los autores con al menos una obra con etiqueta. Un autor
# suelto sería ruido en todas las consultas del laboratorio.
autores_ok = set()
for f in OBRAS:
    if iri("autor", v(f, "a")) and iri("obra", v(f, "w")):
        autores_ok.add(v(f, "a"))

for f in OBRAS:
    wa, ww = v(f, "a"), v(f, "w")
    if wa not in autores_ok:
        continue
    a, o = iri("autor", wa), iri("obra", ww)
    if not o:
        continue
    etiquetar(a, wa, BIB.Autor)
    etiquetar(o, ww, BIB.Obra)
    g.add((o, BIB.autor, a))

    anio, completa = anio_de(v(f, "nac"))
    if anio:
        g.add((a, BIB.anioNacimiento, Literal(anio, datatype=XSD.gYear)))
        if completa:
            g.add((a, BIB.fechaNacimiento, Literal(completa, datatype=XSD.date)))
    muerte, _ = anio_de(v(f, "fal"))
    if muerte:
        g.add((a, BIB.anioFallecimiento, Literal(muerte, datatype=XSD.gYear)))

    pub, _ = anio_de(v(f, "pub"))
    if pub:
        g.add((o, BIB.publicadaEn, Literal(pub, datatype=XSD.gYear)))

    wg = v(f, "genero")
    if wg and iri("genero", wg):
        gi = iri("genero", wg)
        etiquetar(gi, wg, BIB.Genero)
        g.add((o, BIB.genero, gi))

    idioma = v(f, "idiomaLabel")
    if idioma:
        g.add((o, BIB.idioma, Literal(idioma, lang="es")))

# --- Lugares ---------------------------------------------------------------
for f in AUTOR_LUGAR:
    wa, wl = v(f, "a"), v(f, "lugar")
    if wa not in autores_ok:
        continue
    li = iri("lugar", wl)
    if not li:
        continue
    etiquetar(li, wl, BIB.Lugar)
    g.add((iri("autor", wa), BIB.lugarNacimiento, li))

# La jerarquía se agrega solo para los lugares que quedaron en el grafo, y
# después se cierra hacia arriba para que no queden aristas colgando.
pendientes = {wl for wl in PADRES if iri("lugar", wl) in set(g.subjects(RDF.type, BIB.Lugar))}
while pendientes:
    wl = pendientes.pop()
    for wp in PADRES.get(wl, ()):
        pi = iri("lugar", wp)
        if not pi:
            continue
        if (pi, RDF.type, BIB.Lugar) not in g:
            etiquetar(pi, wp, BIB.Lugar)
            pendientes.add(wp)
        g.add((iri("lugar", wl), BIB.ubicadoEn, pi))

# --- Reconocimientos, como relación n-aria --------------------------------
for f in PREMIOS:
    wa, wp = v(f, "a"), v(f, "premio")
    if wa not in autores_ok or not iri("premio", wp):
        continue
    pi = iri("premio", wp)
    etiquetar(pi, wp, BIB.Premio)
    nodo = BNode()
    g.add((iri("autor", wa), BIB.reconocimiento, nodo))
    g.add((nodo, RDF.type, BIB.Reconocimiento))
    g.add((nodo, BIB.premio, pi))
    anio, _ = anio_de(v(f, "anio"))
    if anio:
        g.add((nodo, BIB.anio, Literal(anio, datatype=XSD.gYear)))

# ---------------------------------------------------------------------------
g.serialize(destination=SALIDA, format="turtle")
print()
print("escrito", SALIDA, "con", len(g), "tripletas")
for clase, nombre in ((BIB.Autor, "autores"), (BIB.Obra, "obras"),
                      (BIB.Lugar, "lugares"), (BIB.Genero, "géneros"),
                      (BIB.Premio, "premios"),
                      (BIB.Reconocimiento, "reconocimientos")):
    print("  %-16s %4d" % (nombre, len(set(g.subjects(RDF.type, clase)))))
