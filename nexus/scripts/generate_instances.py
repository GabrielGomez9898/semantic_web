#!/usr/bin/env python3
"""Generate Nexus RDF instances from the three CSV files.

Usage from the project root:
    python scripts/generate_instances.py
"""
from pathlib import Path
import pandas as pd
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, XSD

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "rdf" / "instances.ttl"
NEX = Namespace("https://w3id.org/nexus/ontology#")
BASE = "https://w3id.org/nexus/resource/"

def clean(value):
    if pd.isna(value):
        return None
    value = str(value).strip()
    return value if value else None

def add_literal(g, subject, predicate, value, datatype=None):
    value = clean(value)
    if value is not None:
        g.add((subject, predicate, Literal(value, datatype=datatype)))

def main():
    articles = pd.read_csv(DATA / "articulos.csv")
    professors = pd.read_csv(DATA / "profesores.csv")
    links = pd.read_csv(DATA / "profesores_articulos.csv")

    g = Graph()
    g.bind("nex", NEX)
    g.bind("rdf", RDF)
    g.bind("xsd", XSD)

    article_ids = set()
    for _, row in articles.iterrows():
        article_id = int(row["ID"])
        article_ids.add(article_id)
        uri = URIRef(f"{BASE}article/{article_id}")
        g.add((uri, RDF.type, NEX.JournalArticle))
        add_literal(g, uri, NEX.articleId, article_id, XSD.integer)
        add_literal(g, uri, NEX.publicationYear, row["YEAR_"], XSD.integer)
        add_literal(g, uri, NEX.url, row["URL"], XSD.anyURI)
        add_literal(g, uri, NEX.productType, row["TYPE"])
        add_literal(g, uri, NEX.title, row["TITLE"])
        add_literal(g, uri, NEX.classification, row["CLASSIFICATION"])
        add_literal(g, uri, NEX.description, row["DESCRIPTION"])

    professor_ids = set()
    for _, row in professors.iterrows():
        professor_id = int(row["ID"])
        professor_ids.add(professor_id)
        uri = URIRef(f"{BASE}professor/{professor_id}")
        g.add((uri, RDF.type, NEX.Professor))
        add_literal(g, uri, NEX.professorId, professor_id, XSD.integer)
        add_literal(g, uri, NEX.active, row["ACTIVE"], XSD.integer)
        add_literal(g, uri, NEX.username, row["USERNAME"])
        add_literal(g, uri, NEX.dependency, row["DEPENDENCY"])
        add_literal(g, uri, NEX.name, row["NAME"])

    # Deduplicate exact mappings and only create links where both records exist.
    links = links.drop_duplicates(subset=["ARTICLE_ID", "PROFESOR_ID"])
    valid = links[
        links["ARTICLE_ID"].isin(article_ids) &
        links["PROFESOR_ID"].isin(professor_ids)
    ]
    for _, row in valid.iterrows():
        article = URIRef(f"{BASE}article/{int(row['ARTICLE_ID'])}")
        professor = URIRef(f"{BASE}professor/{int(row['PROFESOR_ID'])}")
        g.add((professor, NEX.hasArticle, article))
        g.add((article, NEX.hasAuthor, professor))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    g.serialize(destination=str(OUT), format="turtle")
    print(f"RDF escrito en: {OUT}")
    print(f"Triples: {len(g):,}")
    print(f"Artículos: {len(article_ids):,}")
    print(f"Profesores: {len(professor_ids):,}")
    print(f"Relaciones válidas únicas: {len(valid):,}")
    print(f"Relaciones sin profesor registrado: {len(links[~links['PROFESOR_ID'].isin(professor_ids)]):,}")
    print(f"Relaciones con artículo no registrado: {len(links[~links['ARTICLE_ID'].isin(article_ids)]):,}")

if __name__ == "__main__":
    main()
