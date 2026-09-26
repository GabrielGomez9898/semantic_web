from rdflib import Graph

archivo = "universidad-owl.ttl"

g = Graph()

try:
    g.parse(archivo, format="turtle")

    print("✅ El archivo Turtle es válido.")
    print(f"Triples cargados: {len(g)}")

except Exception as e:
    print("❌ Error al cargar el archivo:")
    print(e)