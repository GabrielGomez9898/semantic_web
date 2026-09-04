import argparse
import glob
import base64
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "http://localhost:3030/literatura"


def peticion(url, datos=None, metodo="GET", tipo=None, acepta=None):
    cabeceras = {}
    
    credenciales = base64.b64encode(b"admin:taller2").decode("ascii")
    cabeceras["Authorization"] = f"Basic {credenciales}"
        
    if tipo:
        cabeceras["Content-Type"] = tipo
    if acepta:
        cabeceras["Accept"] = acepta
    req = urllib.request.Request(url, data=datos, headers=cabeceras, method=metodo)
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.status, r.read()


def contar():
    """Cuenta las tripletas del grafo por omisión con una consulta."""
    url = BASE + "/sparql?" + urllib.parse.urlencode(
        {"query": "SELECT (COUNT(*) AS ?n) WHERE { ?s ?p ?o }"})
    _, cuerpo = peticion(url, acepta="text/csv")
    return int(cuerpo.decode("utf-8").strip().splitlines()[-1])


def contar_todo():
    """Cuenta incluyendo los grafos con nombre."""
    url = BASE + "/sparql?" + urllib.parse.urlencode(
        {"query": "SELECT (COUNT(*) AS ?n) WHERE { { ?s ?p ?o } UNION "
                  "{ GRAPH ?g { ?s ?p ?o } } }"})
    _, cuerpo = peticion(url, acepta="text/csv")
    return int(cuerpo.decode("utf-8").strip().splitlines()[-1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("archivos", nargs="*", help="por omisión, datos/*.ttl")
    ap.add_argument("--grafo", default=None,
                    help="IRI del grafo con nombre; sin esto va al grafo por omisión")
    ap.add_argument("--limpiar", action="store_true",
                    help="borra el grafo de destino antes de cargar")
    args = ap.parse_args()

    # archivos = args.archivos or sorted(glob.glob(os.path.join("datos", "*.ttl")))
    archivos = args.archivos or [os.path.join("datos", "literatura-la.ttl")]
    if not archivos:
        sys.exit("no hay nada que cargar; se esperaba datos/*.ttl")

    destino = BASE + "/data"
    if args.grafo:
        destino += "?" + urllib.parse.urlencode({"graph": args.grafo})
    else:
        destino += "?default"

    try:
        if args.limpiar:
            print("borrando el grafo de destino")
            peticion(destino, metodo="DELETE")

        for ruta in archivos:
            tam = os.path.getsize(ruta)
            print("cargando %s (%.1f MB)" % (ruta, tam / 1e6), end="", flush=True)
            with open(ruta, "rb") as f:
                cuerpo = f.read()
            inicio = time.perf_counter()
            # POST agrega al grafo. PUT lo reemplazaría.
            estado, _ = peticion(destino, datos=cuerpo, metodo="POST",
                                 tipo="text/turtle; charset=utf-8")
            print("  -> %d en %.1f s" % (estado, time.perf_counter() - inicio))

        print()
        print("tripletas en el grafo por omisión:", contar())
        print("tripletas en total, con los grafos con nombre:", contar_todo())
    except urllib.error.URLError as e:
        print()
        print("No se pudo hablar con Fuseki en", BASE)
        print("Causa:", e)
        print()
        print("Compruebe que el contenedor está arriba:")
        print("  docker compose ps")
        print("  docker compose logs --tail 30 fuseki")
        sys.exit(1)


if __name__ == "__main__":
    main()
