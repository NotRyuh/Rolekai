# Rolekai — Technology Decisions v1.0

## Decisiones

| Área | Elección | Justificación |
| --- | --- | --- |
| Web | Next.js + TypeScript | interfaz React tipada y consistente; Next.js incorpora soporte TypeScript. [Docs](https://nextjs.org/docs/app/api-reference/config/typescript) |
| API/dominio | Python + FastAPI + Pydantic | ecosistema de conectores/IA en Python, validación tipada y OpenAPI. [FastAPI/OpenAPI](https://fastapi.tiangolo.com/reference/openapi/models/) |
| Orquestación AI | LangGraph, alcance acotado | grafo explícito, checkpoints e interrupciones humanas para Evaluator/Tailor futuro, no para CRUD. [Persistencia](https://langchain-ai.github.io/langgraph/concepts/durable_execution/) |
| Persistencia | PostgreSQL | transacciones y esquema relacional para dominio/auditoría; `jsonb` para payloads variables con índices cuando sean necesarios. [Tipos JSON](https://www.postgresql.org/docs/current/datatype-json.html) |
| Trabajo asíncrono | tabla de trabajos PostgreSQL + worker único | menos infraestructura que Celery/Redis/Temporal; suficiente hasta que métricas demuestren lo contrario. |
| Observabilidad | OpenTelemetry obligatorio; LangSmith opcional | OTel conserva trazas/métricas/logs portables; LangSmith añade trazas y evaluaciones específicas de LLM. [OTel Python](https://opentelemetry.io/docs/languages/python/), [LangSmith evals](https://docs.langchain.com/langsmith/evaluation-types) |
| Pruebas | pytest, fixtures, integración Postgres, contratos OpenAPI y datasets de evaluación | cubre reglas deterministas y comportamiento no determinista por separado. |

## Alternativas evaluadas

| Decisión | Alternativa | Motivo de no elegirla ahora |
| --- | --- | --- |
| Backend | API routes de Next.js únicamente | duplicaría el ecosistema Python necesario para conectores/evaluación y mezcla UI con dominio. |
| Orquestación | funciones de servicio solamente | suficiente para Hunter P0, pero no cubre bien evaluación con pausa/reanudación; LangGraph se adopta solo ahí. |
| Orquestación | Temporal/Celery/cola distribuida | útiles con alto volumen o workflows distribuidos; añaden operación y complejidad sin evidencia de necesidad. |
| Base | SQLite | adecuada para prototipo local, pero peor encaje para worker concurrente, auditoría y evolución multiusuario. |
| Búsqueda | vector DB desde inicio | no hay caso de uso medido que la justifique; FTS/índices se añaden antes si hacen falta. |
| Observabilidad | LangSmith solamente | expone dependencia de proveedor; OTel sigue siendo la capa transversal portable. |

## Estrategia de pruebas y evaluación

1. **Unitarias:** elegibilidad México/remoto, normalización, dedupe exacto, transiciones y autorización.
2. **Fixtures de conectores:** respuestas anonimizadas/versionadas de Remotive y Greenhouse; contrato que valida transformación y atribución.
3. **Integración:** PostgreSQL real efímero para transacciones, restricciones, idempotencia y worker.
4. **API:** OpenAPI y pruebas de contrato entre Next.js/FastAPI, incluyendo `202`, cursores y errores.
5. **Evaluación de agente:** dataset pequeño de vacantes + perfil con requisitos/citas esperadas; métricas de citas válidas, abstención correcta, clasificación de requisitos y regresión por versión de prompt/modelo. Las decisiones de usuario no son ground truth de contratación.
6. **Seguridad:** tests de aislamiento por `owner_id`, sanitización HTML, redacción de logs y bloqueo SSRF.

## Hitos técnicos recomendados

1. **Hito 1 — vertical slice P0:** esquema y migraciones, perfil/evidencia, Job/observación/Activity, URL manual + Remotive + Greenhouse, dedupe exacto, Discover/Save/Application manual. Sin LangGraph todavía si la evaluación no está lista.
2. **Hito 2 — Evaluator confiable:** snapshots, graph acotado, validación Pydantic, dataset de evaluación, trazas OTel y LangSmith opcional.
3. **Hito 3 — robustez:** worker/reintentos, candidatos a fusión, cambios por reimportación, Lever/Ashby P1 y Overview/Activity.

## Riesgos técnicos a vigilar

- Límites y cambios de fuentes: fixtures, capacidades por conector y kill switch.
- Datos de terceros/SSRF/HTML: validación de URL, sanitización y retención.
- Costos y alucinación de LLM: snapshots mínimos, schema/citas obligatorias, budget y abstención.
- Worker en PostgreSQL: monitorizar espera, trabajos fallidos y duración antes de sumar infraestructura.
- Evolución multiusuario: aplicar `owner_id` y autorización desde el primer endpoint/migración, pero posponer proveedor de identidad, RBAC y equipos.
