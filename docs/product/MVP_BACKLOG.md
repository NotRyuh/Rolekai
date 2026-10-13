# Rolekai — MVP Backlog v0.1

**Principio:** entregar primero un flujo completo y auditable, no cuatro agentes autónomos ni una colección de conectores incompletos.

## Priorización

- **P0:** imprescindible para el primer flujo end-to-end.
- **P1:** completa el MVP público/portafolio tras validar P0.
- **P2:** siguiente iteración; fuera del MVP inicial.

## Épica E1 — Perfil y reglas de búsqueda

| ID | Prioridad | Historia | Dependencias | Criterio de aceptación |
| --- | --- | --- | --- | --- |
| E1-01 | P0 | Como candidato, quiero definir roles, residencia México y modalidad para filtrar oportunidades irrelevantes. | — | Se guardan y aplican al menos título, México y remoto; cada regla indica si es obligatoria o preferida. |
| E1-02 | P0 | Como candidato, quiero registrar mi evidencia profesional para recibir evaluaciones explicables. | E1-01 | La evidencia tiene fuente/fecha y puede diferenciarse de una inferencia. |
| E1-03 | P0 | Como candidato, quiero configurar una o más tecnologías preferidas para priorizar la primera evaluación. | E1-01 | Las tecnologías se guardan como preferencias y aparecen como criterio explicable de ranking/evaluación. |
| E1-04 | P1 | Como candidato, quiero configurar idioma, seniority, contrato, salario y exclusiones. | E1-01 | Cada campo puede estar ausente sin romper filtros ni mostrar valor inventado. |

## Épica E2 — Dominio de oportunidades y trazabilidad

| ID | Prioridad | Historia | Dependencias | Criterio de aceptación |
| --- | --- | --- | --- | --- |
| E2-01 | P0 | Como candidato, quiero una ficha de oportunidad que conserve descripción original y campos normalizados. | — | La ficha tiene título, empresa, URL, fuente, descripción original, fechas y campos desconocidos explícitos. |
| E2-02 | P0 | Como candidato, quiero saber de dónde proviene cada dato. | E2-01 | Cada importación conserva fuente, URL, momento y observación; una edición humana es distinguible. |
| E2-03 | P1 | Como candidato, quiero ver cambios observados sin perder la historia. | E2-02 | Cambios de disponibilidad, contenido o atributo clave crean eventos antes/después. |

## Épica E3 — Conectores e importación

| ID | Prioridad | Historia | Dependencias | Criterio de aceptación |
| --- | --- | --- | --- | --- |
| E3-01 | P0 | Como candidato, quiero descubrir vacantes remotas desde Remotive respetando sus condiciones. | E1-01, E2-01 | Los resultados incluyen atribución/enlace, respetan la frecuencia configurada y registran errores de fuente. |
| E3-02 | P0 | Como candidato, quiero importar una URL manual para no perder una oportunidad encontrada fuera de las fuentes. | E2-01 | Se guarda URL, contenido recuperable o texto pegado, fuente manual y resultado de extracción. |
| E3-03 | P0 | Como candidato, quiero importar desde un tablero Greenhouse para obtener datos directos de empresa. | E2-01 | A partir de un tablero conocido, se importan ID, título, ubicación, URL y contenido cuando esté disponible. |
| E3-04 | P1 | Como candidato, quiero el mismo comportamiento con Lever. | E3-03 | El conector respeta el contrato de conector y conserva IDs/URLs/texto originales. |
| E3-05 | P1 | Como candidato, quiero el mismo comportamiento con Ashby. | E3-03 | Se usan solo publicaciones listadas; se conservan modalidad, ubicaciones y compensación si se proporciona. |
| E3-06 | P1 | Como operador, quiero fallos aislados y reintentos seguros por conector. | E3-01 | Una fuente fallida no impide procesar otras y queda un diagnóstico accionable. |

## Épica E4 — Dedupe, filtro y evaluación

| ID | Prioridad | Historia | Dependencias | Criterio de aceptación |
| --- | --- | --- | --- | --- |
| E4-01 | P0 | Como candidato, quiero evitar duplicados exactos. | E2-02, E3-01 | Reimportar la misma fuente/ID/URL actualiza observación sin crear otra oportunidad. |
| E4-02 | P0 | Como candidato, quiero ver si un puesto remoto es compatible con residencia México. | E1-01, E2-01 | Cada ficha presenta elegible, incompatible o incierto y cita la evidencia. |
| E4-03 | P0 | Como candidato, quiero una evaluación inicial que explique requisitos cubiertos, faltantes y desconocidos. | E1-02, E2-01 | El resultado no se presenta como probabilidad de contratación y enlaza sus razones. |
| E4-04 | P1 | Como candidato, quiero revisar y confirmar posibles duplicados entre agregador y ATS. | E4-01 | Las fusiones ambiguas requieren revisión y la decisión puede revertirse. |
| E4-05 | P1 | Como candidato, quiero priorización transparente de puestos relevantes. | E4-02, E4-03 | La lista muestra factores deterministas y evaluación explicable por separado. |

## Épica E5 — Dashboard y seguimiento manual

| ID | Prioridad | Historia | Dependencias | Criterio de aceptación |
| --- | --- | --- | --- | --- |
| E5-01 | P0 | Como candidato, quiero una bandeja Discover para revisar resultados nuevos. | E3-01, E4-02 | Puedo filtrar por fuente, título, fecha, modalidad y elegibilidad. |
| E5-02 | P0 | Como candidato, quiero guardar o descartar puestos sin postular automáticamente. | E5-01 | La decisión no crea una candidatura y queda en actividad. |
| E5-03 | P0 | Como candidato, quiero registrar una postulación manual y moverla por un tablero. | E2-01, E5-02 | Crear una Application requiere una acción confirmada sobre un Job guardado y no se confunde con `saved`. |
| E5-04 | P1 | Como candidato, quiero Overview y Activity para ver volumen, cambios y embudo. | E5-01, E5-03 | Los conteos separan descubiertas, guardadas y candidaturas; la actividad es filtrable. |
| E5-05 | P1 | Como candidato, quiero una ficha de vacante con originales, evidencia, evaluación e historial. | E2-03, E4-03 | La ficha no oculta conflictos ni reemplaza la descripción original. |

## Épica E6 — Base para iteraciones controladas

| ID | Prioridad | Historia | Dependencias | Criterio de aceptación |
| --- | --- | --- | --- | --- |
| E6-01 | P1 | Como mantenedor, quiero contratos de conector independientes para sumar fuentes sin cambiar el dominio. | E3-03 | Un conector nuevo se puede validar y activar sin modificar reglas de oportunidad. |
| E6-02 | P1 | Como candidato, quiero historial y aprobación humana antes de cualquier propuesta de CV. | E1-02, E5-05 | Existe punto de entrada CV Studio sin generación automática. |
| E6-03 | P2 | Como candidato, quiero variantes de CV basadas únicamente en evidencia verificada. | E6-02 | Cada cambio es revisable, versionado y nunca inventa experiencia. |
| E6-04 | P2 | Como candidato, quiero ejecutar descubrimiento programado y detectar cambios. | E3-06, E2-03 | La programación respeta límites por fuente y reporta resultados. |
| E6-05 | P2 | Como candidato, quiero conectar Gmail de forma autorizada para detectar respuestas. | E5-03 | Se solicita consentimiento; señales ambiguas no cambian estados sin aprobación. |

## Orden recomendado de implementación

1. **Fundación funcional:** E1-01, E1-02, E1-03, E2-01, E2-02.
2. **Primer flujo de descubrimiento:** E3-02, E3-01, E3-03.
3. **Decisión inteligente:** E4-01, E4-02, E4-03.
4. **Valor visible:** E5-01, E5-02, E5-03.
5. **Robustez y expansión de fuentes:** E3-06, E2-03, E3-04, E3-05, E4-04, E4-05.
6. **Pulido de portfolio:** E5-04, E5-05, E6-01, E6-02.
7. **Iteraciones posteriores:** E6-03 a E6-05.

## Definition of Done del MVP

- El flujo P0 se ejecuta de punta a punta con muestras reales autorizadas de Remotive, Greenhouse y URL manual.
- Los resultados son trazables y los datos faltantes no son inventados.
- Al menos un caso de duplicado exacto, una elegibilidad México compatible, una incompatible y una incierta se verifican.
- La evaluación inicial se revisa contra una oportunidad real y su explicación es comprensible para el usuario.
- El usuario puede guardar, descartar y registrar una postulación manual sin que el sistema envíe formularios.
- La documentación de uso/limitaciones de fuentes está visible antes de habilitar una fuente.
