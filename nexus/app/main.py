
import os
from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field


# ============================================================
# Configuration
# ============================================================

FUSEKI_QUERY_URL = os.getenv(
    "FUSEKI_QUERY_URL",
    "http://localhost:3031/nexus/query",
)

FUSEKI_USER = os.getenv("FUSEKI_USER", "admin")
FUSEKI_PASSWORD = os.getenv("FUSEKI_PASSWORD", "")
FUSEKI_TIMEOUT = float(os.getenv("FUSEKI_TIMEOUT", "20"))

PREFIXES = """
PREFIX nex: <https://w3id.org/nexus/ontology#>
"""


# ============================================================
# Models
# ============================================================

class ProfessorResult(BaseModel):
    id: str
    name: str
    username: str | None = None
    dependency: str | None = None


class ArticleCountResult(BaseModel):
    professor: str
    total_articles: int


class SparqlRequest(BaseModel):
    query: str = Field(min_length=1, max_length=10000)


# ============================================================
# HTTP client lifecycle
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http_client = httpx.AsyncClient(
        auth=(FUSEKI_USER, FUSEKI_PASSWORD),
        timeout=FUSEKI_TIMEOUT,
        headers={
            "Accept": "application/sparql-results+json"
        },
    )

    yield

    await app.state.http_client.aclose()


app = FastAPI(
    title="Nexus API",
    description=(
        "Backend for querying the Nexus scientific "
        "publications knowledge graph."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


# ============================================================
# Fuseki utilities
# ============================================================

def get_value(
    binding: dict[str, Any],
    key: str,
) -> str | None:
    value = binding.get(key)
    return value.get("value") if value else None


def sparql_string(value: str) -> str:
    """Escape a string before inserting it as a SPARQL literal."""
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
    )
    return f'"{escaped}"'


async def run_select(query: str) -> list[dict[str, Any]]:
    """Execute a SPARQL SELECT query against Fuseki."""
    try:
        response = await app.state.http_client.post(
            FUSEKI_QUERY_URL,
            data={"query": query},
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            },
        )

        response.raise_for_status()

        payload = response.json()
        return payload.get("results", {}).get("bindings", [])

    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=504,
            detail="Fuseki did not respond in time.",
        ) from exc

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "Fuseki returned HTTP "
                f"{exc.response.status_code}."
            ),
        ) from exc

    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail="Could not communicate with Fuseki.",
        ) from exc


# ============================================================
# Basic endpoints
# ============================================================

@app.get("/")
async def root():
    return {
        "service": "Nexus API",
        "version": app.version,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health():
    query = PREFIXES + """
    SELECT (COUNT(DISTINCT ?professor) AS ?total)
    WHERE {
        ?professor a nex:Professor .
    }
    """

    rows = await run_select(query)

    total = (
        int(get_value(rows[0], "total") or "0")
        if rows
        else 0
    )

    return {
        "status": "ok",
        "fuseki": "connected",
        "dataset": "nexus",
        "professors": total,
    }


@app.get("/stats")
async def stats():
    queries = {
        "professors": PREFIXES + """
            SELECT (COUNT(DISTINCT ?p) AS ?total)
            WHERE { ?p a nex:Professor . }
        """,
        "articles": PREFIXES + """
            SELECT (COUNT(DISTINCT ?a) AS ?total)
            WHERE { ?a a nex:JournalArticle . }
        """,
        "professor_article_links": PREFIXES + """
            SELECT (COUNT(*) AS ?total)
            WHERE { ?p nex:hasArticle ?a . }
        """,
    }

    result = {}

    for key, query in queries.items():
        rows = await run_select(query)
        result[key] = (
            int(get_value(rows[0], "total") or "0")
            if rows
            else 0
        )

    return result


# ============================================================
# Professor endpoints
# ============================================================

@app.get(
    "/professors",
    response_model=list[ProfessorResult],
)
async def search_professors(
    name: str = Query(
        min_length=1,
        max_length=150,
        description="Full or partial professor name",
    ),
    limit: int = Query(default=10, ge=1, le=100),
):
    query = PREFIXES + f"""
    SELECT ?id ?name ?username ?dependency
    WHERE {{
        ?professor a nex:Professor ;
                   nex:professorId ?id ;
                   nex:name ?name .

        OPTIONAL {{
            ?professor nex:username ?username .
        }}

        OPTIONAL {{
            ?professor nex:dependency ?dependency .
        }}

        FILTER(
            CONTAINS(
                LCASE(STR(?name)),
                LCASE({sparql_string(name)})
            )
        )
    }}
    ORDER BY ?name
    LIMIT {limit}
    """

    rows = await run_select(query)

    return [
        ProfessorResult(
            id=get_value(row, "id") or "",
            name=get_value(row, "name") or "",
            username=get_value(row, "username"),
            dependency=get_value(row, "dependency"),
        )
        for row in rows
    ]


@app.get(
    "/professors/{professor_id}/articles/count",
    response_model=ArticleCountResult,
)
async def count_professor_articles(professor_id: int):
    query = PREFIXES + f"""
    SELECT ?name (COUNT(DISTINCT ?article) AS ?total)
    WHERE {{
        ?professor a nex:Professor ;
                   nex:professorId {professor_id} ;
                   nex:name ?name .

        OPTIONAL {{
            ?professor nex:hasArticle ?article .
        }}
    }}
    GROUP BY ?name
    """

    rows = await run_select(query)

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"Professor with ID {professor_id} was not found.",
        )

    return ArticleCountResult(
        professor=get_value(rows[0], "name") or "",
        total_articles=int(
            get_value(rows[0], "total") or "0"
        ),
    )


# ============================================================
# SPARQL endpoint for development
# ============================================================

@app.post("/sparql/select")
async def custom_select(request: SparqlRequest):
    """
    Development endpoint for SELECT queries only.
    Do not expose this endpoint publicly without stronger
    query validation and authentication.
    """
    query = request.query.strip()

    # Remove PREFIX/BASE declarations before checking the operation.
    lines = [
        line for line in query.splitlines()
        if not line.strip().upper().startswith(("PREFIX ", "BASE "))
    ]
    operation = "\n".join(lines).lstrip().upper()

    if not operation.startswith("SELECT"):
        raise HTTPException(
            status_code=400,
            detail="Only SPARQL SELECT queries are allowed.",
        )

    forbidden = (
        "INSERT", "DELETE", "LOAD", "CLEAR",
        "DROP", "CREATE", "MOVE", "COPY", "ADD",
    )

    if any(word in operation for word in forbidden):
        raise HTTPException(
            status_code=400,
            detail="The query contains a forbidden operation.",
        )

    rows = await run_select(query)

    return {
        "count": len(rows),
        "results": rows,
    }
