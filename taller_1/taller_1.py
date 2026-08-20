import csv
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD
import owlrl
g = Graph()
# ... construir el vocabulario y las instancias ...
antes = len(g)
owlrl.RDFSClosure.RDFS_Semantics(g, False, False, False).closure()
print(f"asertadas {antes}, tras la clausura {len(g)}")