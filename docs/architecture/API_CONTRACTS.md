# Rolekai — API Contracts v1.0

## 1. Convenciones

- Prefijo: `/api/v1`; JSON UTF-8; fechas RFC 3339 UTC; IDs UUID.
- Los DTOs de request/response son modelos Pydantic compartidos por módulos; FastAPI publica OpenAPI como contrato para el frontend tipado.
- Errores: `{ "error": { "code", "message", "details", "request_id" } }`. No filtrar payloads, secretos ni PII de proveedor.
- Listas: `limit` (máx. 100), cursor opaco, `next_cursor`; filtros explícitos.
- Mutaciones asíncronas aceptan `Idempotency-Key`; devolverán el mismo `job_run_id` para la misma intención.

## 2. Recursos y endpoints P0

| Método y ruta | Propósito | Respuesta |
| --- | --- | --- |
| `GET/PUT /profile/search` | leer/editar preferencias de búsqueda. | `SearchProfile`. |
| `GET/POST /profile/evidence` | listar/agregar evidencia profesional. | `ProfileEvidence`. |
| `GET /jobs` | Discover/Saved con filtros por decisión, fuente, elegibilidad y fecha. | `JobListPage`. |
| `GET /jobs/{job_id}` | ficha consolidada, observaciones, procedencia, evaluaciones y aplicación relacionada. | `JobDetail`. |
| `PATCH /jobs/{job_id}/decision` | `inbox|saved|dismissed`, con motivo opcional. | `Job`. |
| `POST /imports/remotive` | iniciar importación filtrada, asíncrona. | `202 ImportAccepted`. |
| `POST /imports/greenhouse` | importar tablero/URL Greenhouse, asíncrona. | `202 ImportAccepted`. |
| `POST /imports/url` | importar URL manual y texto opcional, asíncrona. | `202 ImportAccepted`. |
| `GET /import-runs/{run_id}` | resultado agregado y errores por observación. | `ImportRun`. |
| `POST /jobs/{job_id}/evaluations` | solicitar evaluación de snapshot actual. | `202 EvaluationAccepted`. |
| `GET /evaluations/{evaluation_id}` | resultado, requisitos, evidencia y estado. | `Evaluation`. |
| `POST /jobs/{job_id}/applications` | crear candidatura manual desde Job `saved`. | `201 Application`. |
| `PATCH /applications/{id}` | transición válida, notas o fecha/canal. | `Application`. |
| `GET /activity` | timeline filtrable por sujeto y tipo. | `ActivityPage`. |

## 3. DTOs conceptuales

`JobSummary` contiene identidad, título, empresa, fuente preferida, modalidad, elegibilidad, decisión, disponibilidad, fechas y evaluación más reciente resumida. `JobDetail` añade descripciones, observaciones, procedencia por campo y candidatos a fusión.

`ImportAccepted` = `run_id`, `status=queued`, `source`, `submitted_at`. `ImportRun` = conteos `created|updated|duplicate|needs_review|failed`, errores seguros y vínculos a Jobs.

`Evaluation` contiene versión, snapshot hashes, `fit_score_relative` opcional, `requirements[]`, `evidence[]`, `unknowns[]`, `status` y trazabilidad. No expone chain-of-thought ni prompts secretos.

## 4. Semántica de estados y códigos

- `201`: recurso creado de forma síncrona (evidencia, Application).
- `202`: trabajo aceptado, todavía no se afirma éxito de importación/evaluación.
- `400`: contrato inválido; `401/403`: identidad/propiedad; `404`: no existe o no pertenece al usuario.
- `409`: transición de dominio inválida, duplicado de Application activa o versión obsoleta.
- `422`: datos semánticamente no válidos (p. ej., URL privada/no permitida).
- `429`: límite local o de fuente; `502/503`: dependencia externa indisponible, con `request_id`.

## 5. Contratos internos

`Connector.discover(request) -> list[RawObservation]`; `Connector.fetch_detail(ref) -> RawObservation`; `Normalizer.normalize(raw) -> NormalizedJobCandidate`; `DeduplicationService.resolve(candidate) -> Create|Update|MergeCandidate`; `EvaluationWorkflow.run(job_snapshot, profile_snapshot) -> EvaluationResult`.

Los contratos internos se validan con Pydantic y fixtures. Ningún conector recibe un repositorio de Applications ni un cliente LLM.
