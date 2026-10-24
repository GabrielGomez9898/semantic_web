# Nexus — ontology and RDF instances

## Contents
- `data/`: the three source CSV files.
- `rdf/ontology.ttl`: OWL ontology.
- `rdf/instances.ttl`: RDF instances generated from the CSVs.
- `scripts/generate_instances.py`: repeatable CSV-to-RDF generator.
- `scripts/validate_rdf.py`: Turtle parsing and basic checks.
- `queries/`: example SPARQL queries.

## Generate again
From this directory, install dependencies and run:

```bash
python -m pip install -r requirements.txt
python scripts/generate_instances.py
python scripts/validate_rdf.py
```

## Namespace note
The namespace `https://w3id.org/nexus/` is provisional. Before publishing the ontology, replace it with a namespace/domain controlled by the Nexus project and update it consistently in Turtle files, scripts, and queries.

## Modeling decisions
- Every professor and article row becomes an RDF resource.
- Links are created only when both the professor and article IDs exist in their source CSVs.
- Exact duplicate rows in `profesores_articulos.csv` are deduplicated.
- Empty CSV values are omitted from RDF rather than represented as empty strings.
- Both `nex:hasArticle` and its inverse `nex:hasAuthor` are materialized in the graph for easier querying.
- `ACTIVE` is represented as an integer because the CSV encodes it as 0/1.
