#!/usr/bin/env python3
"""Basic checks for generated Nexus Turtle files."""
from pathlib import Path
from rdflib import Graph, Namespace
from rdflib.namespace import RDF

ROOT = Path(__file__).resolve().parents[1]
NEX = Namespace("https://w3id.org/nexus/ontology#")

def main():
    ontology = Graph()
    ontology.parse(ROOT / "rdf" / "ontology.ttl", format="turtle")
    instances = Graph()
    instances.parse(ROOT / "rdf" / "instances.ttl", format="turtle")

    print(f"Ontology triples: {len(ontology):,}")
    print(f"Instance triples: {len(instances):,}")
    print(f"Professor instances: {len(set(instances.subjects(RDF.type, NEX.Professor))):,}")
    print(f"Article instances: {len(set(instances.subjects(RDF.type, NEX.JournalArticle))):,}")
    print(f"hasArticle links: {len(set(instances.triples((None, NEX.hasArticle, None)))):,}")
    print(f"hasAuthor links: {len(set(instances.triples((None, NEX.hasAuthor, None)))):,}")
    assert len(set(instances.subjects(RDF.type, NEX.Professor))) > 0
    assert len(set(instances.subjects(RDF.type, NEX.JournalArticle))) > 0
    print("Turtle parse and basic checks: OK")

if __name__ == "__main__":
    main()
