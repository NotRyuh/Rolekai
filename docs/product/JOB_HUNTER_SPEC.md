# Rolekai Hunter — Functional Specification v1.0

**Estado:** Diseño funcional; sin decisión de infraestructura  
**Fecha:** 2026-10-13

## 1. Propósito y límites

Rolekai Hunter descubre, importa y mantiene oportunidades. Su salida es un registro trazable y evaluable, no una candidatura ni una orden de postular. Opera mediante conectores independientes: agregar una fuente no debe cambiar el modelo principal ni la lógica de evaluación.

No hace scraping que contradiga las condiciones del proveedor. Cuando una URL no pertenece a una fuente autorizada o no contiene datos suficientes, se guarda como importación manual con evidencia disponible y se solicita revisión humana.

## 2. Estrategia de fuentes

El MVP usa un modelo híbrido: **Remotive** permite descubrir compañías y oportunidades a escala; tableros directos de **Greenhouse, Lever y Ashby** se usan para importar o enriquecer oportunidades cuando se conoce su URL o identificador. Esto evita limitarse a empresas precargadas sin prometer un rastreador universal de toda la web.

| Fuente | Acceso confirmado | Datos relevantes | Restricciones/incertidumbres | Conveniencia MVP |
| --- | --- | --- | --- | --- |
| Greenhouse Job Board API | GET público sin autenticación para un `board_token`; `content=true` incluye descripción, departamento y oficina. [Documentación](https://docs.greenhouse.io/job-board.html) | ID, título, ubicación, URL, actualización; contenido ampliado según tablero. | Requiere conocer/derivar el token del tablero; campos configurables pueden faltar. No usar el endpoint de postulación. | **P0:** conector directo inicial. |
| Lever Postings API | Postings publicados por `site`; JSON mediante `mode=json`/Accept. [Documentación](https://github.com/lever/postings-api/blob/master/README.md) | ID, título, categorías, país, descripción HTML/texto, URLs, modalidad. | Solo puestos publicados; se requiere el nombre del sitio de Lever; la API no ofrece búsqueda global. | **P1:** validar muestras reales antes de activar. |
| Ashby Public Job Postings API | GET público por `JOB_BOARD_NAME`, sin credencial indicada, con compensación opcional. [Documentación](https://developers.ashbyhq.com/docs/public-job-posting-api) | título, remoto/modalidad, ubicaciones, texto plano/HTML, fecha, tipo, URL y compensación si se pide. | Requiere conocer la parte final de `jobs.ashbyhq.com/{name}`; datos ausentes permanecen ausentes. Solo usar `isListed=true` para descubrimiento de lista. | **P1:** validar muestras reales antes de activar. |
| Remotive | API pública de empleos activos y filtros por categoría/búsqueda. [Documentación](https://github.com/remotive-com/remote-jobs-api/blob/main/README.md) | ID, título, empresa, URL, descripción, ubicación requerida, salario opcional, fecha y tipo. | Requiere atribución y enlace a Remotive; datos con retraso de 24 horas; recomienda máximo 4 consultas/día y bloquea exceso. No reutilizar para crear una bolsa pública sin autorización. | Alta: fuente agregada complementaria. |
| URL manual | El usuario proporciona una URL y, si corresponde, texto/descripción. | URL, contenido recuperable, fecha, nota del usuario. | La estructura y permiso dependen del sitio; no se asume extracción completa. | Crítica: captura universal y fallback. |

### Fuentes no incluidas en v0.1

APIs comerciales o con términos específicos (LinkedIn, Indeed, Glassdoor, bolsas locales y páginas de carrera no reconocidas) se evaluarán individualmente. No se incorpora una fuente solo porque sea técnicamente visible en el navegador.

## 3. Contrato funcional de conector

Cada conector debe implementar conceptualmente estas capacidades:

| Operación | Entrada | Salida |
| --- | --- | --- |
| Validar configuración | Identificador de tablero, URL o consulta | válida, inválida o no verificable; razón. |
| Descubrir | Consulta y cursor/ventana temporal opcional | lista de observaciones crudas y metadatos de ejecución. |
| Obtener detalle | Identificador/URL de fuente | una observación completa o fallo clasificado. |
| Normalizar | Observación cruda | propuesta de oportunidad normalizada + mapa de procedencia. |
| Verificar cambios | Registro de fuente previo | sin cambio, cambio o no disponible. |

Un conector no decide si el puesto encaja ni altera estados de candidatura. Debe reportar su versión/capacidad, límites conocidos y errores por fuente.

## 4. Perfil de búsqueda

### Criterios configurables

| Grupo | Campos | Uso |
| --- | --- | --- |
| Rol | títulos deseados, sinónimos y exclusiones | Descubrimiento, filtro y ranking. |
| Modalidad | remoto, híbrido, presencial | Regla obligatoria por defecto: remoto. |
| Elegibilidad geográfica | residencia: México; países permitidos; restricciones rechazadas; zonas horarias preferidas | Determina `eligible`, `ineligible` o `unknown`, nunca asume. |
| Experiencia | seniority objetivo, mínimo/máximo negociable | Filtro/relevancia. |
| Habilidades | tecnologías obligatorias, preferidas y exclusiones | Evaluación posterior y ranking. |
| Condiciones | idioma, contrato, salario mínimo/deseado, moneda | Filtro cuando haya evidencia. |
| Preferencias | industria, empresa, tamaño, palabras clave | Ranking solamente salvo marca obligatoria. |

### Política de elegibilidad México/remoto

1. **Confirmada:** el texto o campo estructurado permite explícitamente México, LATAM, global, worldwide o un conjunto que incluye México.
2. **Incompatible:** el texto/campo restringe a un país, estado, ciudad, zona de empleo o autorización no compatible y no enumera México.
3. **Incierta:** solo dice “remote” o no menciona ubicación/elegibilidad. Se puede mostrar pero no se etiqueta como compatible.
4. **Revisión humana:** la fuente presenta contradicción, por ejemplo `remote` y una restricción geográfica ambigua.

La clasificación conserva la cita o campo fuente. Palabras como “Americas” no se interpretan automáticamente como México hasta definir una política configurable y revisable.

## 5. Pipeline funcional

```text
Discovery → Extraction → Normalization → Deduplication → Filtering
     → Persistence → Evaluation Queue → Dashboard
```

| Etapa | Entrada | Validaciones/proceso | Salida |
| --- | --- | --- | --- |
| Discovery | Consulta configurada, tablero conocido o URL | Límite de fuente, formato, idempotencia de ejecución. | Observaciones crudas con ID/URL/fuente. |
| Extraction | Observación o URL | Preservar payload/texto original; detectar estructura/ATS sin inventar campos. | Atributos candidatos y evidencia. |
| Normalization | Atributos candidatos | Normalizar título, empresa, fechas, moneda, modalidad y país; registrar confianza. | Oportunidad propuesta + mapa de campos. |
| Deduplication | Propuesta + oportunidades existentes | Exacta primero; después candidatos por URL/ATS/empresa/título/ubicación. | crear, actualizar, fusionar o cola de revisión. |
| Filtering | Oportunidad normalizada + perfil | Reglas obligatorias antes de preferencias; elegibilidad explícita. | etiquetas y razones de inclusión/exclusión. |
| Persistence | Resultado de dedupe/filtro | Transacción lógica, historial y procedencia. | oportunidad consolidada y evento. |
| Evaluation Queue | Oportunidad elegible o revisable | No ejecutar sobre duplicado no resuelto ni dato incompleto crítico. | trabajo para Rolekai Evaluator. |
| Dashboard | Registros consolidados | Separar estados y ocultar ruido archivado por defecto. | ficha y vistas de usuario. |

### Reintentos y detección de cambios

- Errores transitorios (red, 429, 5xx) se reintentan con política acotada y respetando `Retry-After` cuando exista.
- Errores permanentes (tablero inexistente, formato incompatible, 401/403) no se reintentan automáticamente de forma agresiva; quedan visibles para configuración/revisión.
- Cada observación guarda `observed_at`, huella del contenido y, si existe, fecha de actualización de fuente.
- Una nueva huella produce un evento de cambio con campos afectados; una ausencia comprobable de la fuente cambia disponibilidad a `unavailable`, sin borrar datos.

## 6. Modelo conceptual de datos

### Job (registro consolidado)

| Campo | Descripción |
| --- | --- |
| `job_id` | Identificador interno estable. |
| `owner_id` | Propietario lógico, reservado para futura multiusuario. |
| `company_name` / `company_identity` | Nombre visual y, si se confirma, identidad canónica. |
| `title_raw` / `title_normalized` | Título fuente y título para búsqueda. |
| `description_original` | Contenido original conservado, con formato y fuente. |
| `description_normalized` | Texto normalizado para búsqueda/evaluación; no sustituye al original. |
| `canonical_url` / `apply_url` | Enlace principal y enlace de postulación si están disponibles. |
| `workplace_type` | `remote`, `hybrid`, `on_site` o `unknown`. |
| `locations` | Lista de ubicaciones fuente, cada una con nivel de confianza. |
| `remote_eligibility` | `eligible`, `ineligible`, `unknown`, `needs_review`; evidencia asociada. |
| `compensation` | Intervalos, moneda, periodo y texto original; todos opcionales. |
| `employment_type`, `seniority`, `language` | Valores normalizados o `unknown`. |
| `requirements` | Requisitos estructurados con texto fuente, categoría y confianza. |
| `posted_at` | Fecha publicada solo si la fuente la proporciona. |
| `discovered_at` / `last_verified_at` | Primera observación y última verificación. |
| `availability_status` | Disponible, no disponible o desconocida. |
| `discovery_status`, `decision_status` | Estados propios del Job; la evaluación y la postulación viven en entidades separadas. |

### SourceObservation (evidencia por fuente)

`observation_id`, `job_id`, `source_type`, `source_name`, `source_job_id`, `source_url`, `retrieved_at`, `raw_payload_or_snapshot`, `content_hash`, `source_updated_at`, `attribution`, `access_method`, `parser_version`, `field_provenance` y `error_reference` opcional.

### Límites de dominio

- **Job:** dato de la vacante, procedencia, disponibilidad y decisión del usuario.
- **Evaluation:** ejecución/versionado de compatibilidad y sus requisitos/evidencias; referencia al `job_id`, pero no cambia la vacante.
- **Application:** candidatura creada explícitamente por el usuario; referencia al `job_id`, pero su estado no se almacena en Job.
- **Activity:** bitácora inmutable que referencia al agregado afectado; no es fuente de verdad para los estados.

### ChangeEvent y ActivityEvent

- **ChangeEvent:** diferencia observada entre dos observaciones; tiene antes/después, campos, fuente, momento y confianza.
- **ActivityEvent:** acción de sistema o usuario; nunca se reescribe y puede referenciar una observación o cambio.

### Representación de desconocido

- Ausente de la fuente: `null` + procedencia “no proporcionado”.
- No aplicable: estado explícito `not_applicable`, no `null` ambiguo.
- Inferido: valor + `confidence` + regla/modelo + texto soporte.
- Conflicto: mantener todas las observaciones y marcar `needs_review`; no elegir silenciosamente una.

## 7. Deduplicación

### Secuencia

1. **Exacta:** mismo `source_type + source_job_id`, o URL canónica idéntica.
2. **Directa entre fuente:** mismo `apply_url`, URL hospedada del ATS o identificador externo conocido.
3. **Candidata:** empresa canónica similar + título normalizado similar + ubicación/modalidad compatibles + descripción/fecha cercanas.
4. **Resolución:** fusión automática solo sobre umbral conservador; el resto se muestra como candidata al usuario.

### Reglas de fusión

- No se descarta ninguna observación ni descripción original.
- La fuente directa del ATS se prefiere para campos de vacante, mientras Remotive conserva valor de descubrimiento y atribución.
- La preferencia de fuente no sobrescribe un valor conflictivo sin registrar ambos valores y el motivo.
- Una fusión nunca crea/actualiza una postulación.
- El usuario puede deshacer una fusión o marcar que dos registros son diferentes; esa decisión se conserva para futuras ejecuciones.

## 8. Filtrado y priorización

El filtro determina visibilidad/cola; el ranking ordena resultados. Un incumplimiento obligatorio no debe compensarse con preferencias.

| Resultado | Condición |
| --- | --- |
| `eligible` | Reglas obligatorias con evidencia suficiente; puede entrar a evaluación. |
| `ineligible` | Algún requisito obligatorio claramente incompatible. |
| `unknown` | Falta información relevante; visible con advertencia y revisable. |
| `preferred` | Elegible y satisface señales negociables; prioridad relativa mayor. |

La priorización inicial puede ser determinista: concordancia de títulos, modalidad, elegibilidad, tecnologías preferidas, seniority, idioma, salario conocido y frescura. Rolekai Evaluator añade la lectura semántica después; no debe borrar las razones deterministas.

## 9. Fallos y casos límite

| Situación | Comportamiento esperado |
| --- | --- |
| La API retorna una vacante sin salario, fecha o país | Persistir como desconocido; no excluir salvo regla configurada. |
| Remotive y un ATS muestran texto distinto | Conservar ambos; usar directo como preferente solo para campos confirmados; registrar conflicto. |
| “Remote — US only” | Marcar incompatible para residencia México, con cita fuente. |
| “Remote” sin restricciones | Marcar elegibilidad incierta, no compatible confirmada. |
| URL manual con paywall, JavaScript o error | Guardar URL, fecha y nota; pedir pegar descripción; no fingir extracción. |
| El puesto desaparece temporalmente | Marcar verificación fallida/transitoria primero; no `unavailable` hasta evidencia suficiente. |
| Dos puestos similares de la misma empresa | Mantener separados si ID, URL de aplicación, seniority o equipo prueban que son distintos. |
| La fuente devuelve contenido no esperado | Aislar ejecución, guardar diagnóstico seguro y requerir actualización del conector. |

## 10. Calidad y observabilidad del producto

Medir por fuente: éxito de ejecuciones, tiempo de respuesta, vacantes creadas/actualizadas, campos completos, errores por categoría, frescura, duplicados exactos, candidatos a fusión, correcciones humanas y tasa de elegibilidad confirmada/incierta/incompatible. Medir el ranking por decisiones del usuario (guardada, descartada, aplicada), sin convertir esos datos en una afirmación causal de contratación.

## 11. Alcance mínimo del primer flujo end-to-end

1. Perfil de búsqueda con residencia México, rol, modalidad y una o dos tecnologías preferidas.
2. Importación de una vacante desde Remotive y de una URL directa de **un** ATS (Greenhouse recomendado para el primer corte).
3. Registro normalizado con descripción original, fuente, elegibilidad y estado independiente.
4. Dedupe exacto por fuente/URL y detección de candidata a duplicado por reglas simples.
5. Evaluación inicial de requisitos contra perfil de evidencia.
6. Vista Discover → ficha → Save/Dismiss → registro manual de `applied`.

Lever y Ashby deben cumplir el mismo contrato antes de exponerse en P1. Remotive debe respetar estrictamente atribución, enlace y frecuencia acordada.
