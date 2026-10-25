# Nexus Backend — primera etapa

API en FastAPI para consultar Nexus en Apache Jena Fuseki. Esta versión aún no incluye LLM.

## Requisitos
- Python 3.10 o superior
- Fuseki activo en `http://localhost:3031`
- Dataset `nexus` cargado

## Ejecutar en macOS/Linux
Desde la carpeta `nexus_backend`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Configura la contraseña de Fuseki. Puedes exportar variables en la terminal antes de arrancar:

```bash
export FUSEKI_QUERY_URL=http://localhost:3031/nexus/query
export FUSEKI_USER=admin
export FUSEKI_PASSWORD='TU_PASSWORD_REAL'
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Documentación: `http://127.0.0.1:8000/docs`

## Endpoints
- `GET /` estado general del servicio
- `GET /health` comprueba conexión con Fuseki
- `GET /stats` cuenta profesores, artículos y relaciones
- `GET /professors?name=ruben` busca profesores por nombre
- `GET /professors/{id}/articles/count` cuenta artículos por ID de profesor
- `POST /sparql/select` permite consultas SELECT para depuración

No subas la contraseña real a Git. El endpoint genérico de SPARQL es para desarrollo; protégelo o elimínalo antes de producción.
