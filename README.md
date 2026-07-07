# NYC Taxi Data Platform

Proyecto de análisis e ingeniería de datos orientado a construir una plataforma analítica para registros históricos de viajes de taxi en Nueva York.

## Objetivo

Diseñar un pipeline de datos que permita ingerir, transformar, validar y analizar datos de movilidad urbana, aplicando buenas prácticas de ingeniería de datos y análisis de negocio.

## Caso de negocio

El proyecto busca responder preguntas relacionadas con demanda de viajes, ingresos, horarios pico, comportamiento por zona, métodos de pago y eficiencia operativa.

## Arquitectura inicial

El proyecto seguirá una arquitectura tipo medallón:

- Raw: archivos originales descargados desde la fuente.
- Bronze: datos almacenados en formato estructurado sin reglas complejas.
- Silver: datos limpios, estandarizados y validados.
- Gold: tablas analíticas listas para SQL, dashboard y KPIs.

## Tecnologías

- Python
- pandas
- PyArrow
- DuckDB
- PostgreSQL
- SQL
- Power BI
- Git y GitHub
- VS Code

## Estado del proyecto

Proyecto en fase inicial de configuración.