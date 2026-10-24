# Informe de validación de datos de Nexus

## Volumen
- Artículos en `articulos.csv`: 24,162
- Profesores en `profesores.csv`: 7,968
- Filas de relación originales en `profesores_articulos.csv`: 35,666
- Relaciones únicas tras eliminar duplicados exactos: 35,664
- Relaciones válidas usadas para enlazar instancias: 35,015

## Calidad y decisiones
- IDs de artículo duplicados: 0
- IDs de profesor duplicados: 0
- Filas de relación duplicadas: 2
- Relaciones cuyo profesor no aparece en `profesores.csv`: 649 (IDs de profesor únicos: 148)
- Relaciones cuyo artículo no aparece en `articulos.csv`: 0
- Valores vacíos en artículos: {'ID': 0, 'YEAR_': 0, 'URL': 10895, 'TYPE': 0, 'TITLE': 0, 'CLASSIFICATION': 7479, 'DESCRIPTION': 20273}
- Valores vacíos en profesores: {'ID': 0, 'ACTIVE': 0, 'USERNAME': 1, 'DEPENDENCY': 0, 'NAME': 0}

## Criterios de generación
- No se crean profesores adicionales para los 148 IDs ausentes del CSV de profesores.
- Se omiten valores nulos/vacíos en lugar de crear literales vacíos.
- Se deduplican las relaciones exactas.
- Se materializan ambas direcciones de la relación: `nex:hasArticle` y `nex:hasAuthor`.
- El namespace `https://w3id.org/nexus/` queda como provisional; reemplazarlo por uno controlado por el proyecto antes de publicar la ontología.
