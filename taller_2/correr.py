import argparse
import base64
import json
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "http://localhost:3030/literatura"


def enviar(consulta, acepta, ruta="/sparql", campo="query"):
    credenciales = base64.b64encode(b"admin:taller2").decode("ascii")
    
    datos = urllib.parse.urlencode({campo: consulta}).encode()
    req = urllib.request.Request(
        BASE + ruta, data=datos,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": acepta,
            "Authorization": f"Basic {credenciales}"
        })
    
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.read()


def imprimir_tabla(bruto, maximo=15):
    datos = json.loads(bruto.decode("utf-8"))
    columnas = datos["head"]["vars"]
    filas = datos["results"]["bindings"]
    ancho = max(18, min(34, 100 // max(1, len(columnas))))
    plantilla = " | ".join("%%-%ds" % ancho for _ in columnas)
    print("  " + plantilla % tuple(c[:ancho] for c in columnas))
    print("  " + "-+-".join("-" * ancho for _ in columnas))
    for fila in filas[:maximo]:
        celdas = []
        for c in columnas:
            if c not in fila:
                celdas.append("SIN LIGAR")
            else:
                valor = fila[c]["value"]
                celdas.append(valor.rsplit("/", 1)[-1][:ancho])
        print("  " + plantilla % tuple(celdas))
    if len(filas) > maximo:
        print("  ... y %d filas más" % (len(filas) - maximo))
    print("  total: %d filas" % len(filas))
    return len(filas)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("archivo")
    ap.add_argument("-n", type=int, default=1, help="repeticiones para medir")
    ap.add_argument("--update", action="store_true",
                    help="envía al endpoint de actualización")
    ap.add_argument("--grafo", action="store_true",
                    help="la consulta es un CONSTRUCT o un DESCRIBE")
    args = ap.parse_args()

    with open(args.archivo, encoding="utf-8") as f:
        consulta = f.read()

    try:
        if args.update:
            enviar(consulta, "*/*", ruta="/update", campo="update")
            print("actualización aplicada")
            return

        acepta = ("text/turtle" if args.grafo
                  else "application/sparql-results+json")
        tiempos = []
        filas = None
        for i in range(args.n):
            inicio = time.perf_counter()
            bruto = enviar(consulta, acepta)
            tiempos.append(time.perf_counter() - inicio)
            if i == 0:
                if args.grafo:
                    texto = bruto.decode("utf-8")
                    print("\n".join("  " + l for l in texto.splitlines()[:20]))
                    filas = texto.count(" .")
                    print("  tripletas (aproximado por líneas): %d" % filas)
                else:
                    filas = imprimir_tabla(bruto)

        print()
        if args.n == 1:
            print("tiempo: %.0f ms  (una sola medición, no la reporte sola)"
                  % (tiempos[0] * 1000))
        else:
            print("%d ejecuciones: media %.0f ms, mediana %.0f ms, "
                  "mínimo %.0f ms, máximo %.0f ms"
                  % (args.n, 1000 * statistics.mean(tiempos),
                     1000 * statistics.median(tiempos),
                     1000 * min(tiempos), 1000 * max(tiempos)))
            print("primera ejecución: %.0f ms. Si es muy superior a la mediana,"
                  % (tiempos[0] * 1000))
            print("el motor estaba en frío y conviene descartarla.")
            print("filas devueltas: %s" % filas)
    except urllib.error.HTTPError as e:
        print("Fuseki devolvió %d:" % e.code)
        print(e.read().decode("utf-8", "replace")[:800])
        sys.exit(1)
    except urllib.error.URLError as e:
        print("No se pudo hablar con Fuseki en", BASE, "\nCausa:", e)
        print("Compruebe con  docker compose ps")
        sys.exit(1)


if __name__ == "__main__":
    main()
