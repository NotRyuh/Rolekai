# Rolekai — Product Requirements Document (PRD) v1.0

**Producto:** Rolekai  
**Tagline:** *Your career, intelligently guided.*  
**Descripción para GitHub:** Multi-agent AI platform for intelligent job discovery, skill matching, resume tailoring, and application tracking.  
**Estado:** Aprobado para diseño de arquitectura (sin implementación)  
**Fecha:** 2026-10-13

## 1. Resumen ejecutivo

Rolekai es una plataforma de inteligencia de carrera que ayuda a un candidato residente en México a descubrir oportunidades remotas internacionales, conservar la evidencia de cada vacante, evaluar su compatibilidad y gestionar el proceso de postulación sin automatizar decisiones o envíos sensibles.

El primer flujo end-to-end será: descubrir o importar una vacante → extraer y conservar su descripción → normalizar y deduplicar → filtrar por elegibilidad desde México → evaluar la compatibilidad contra un perfil respaldado por evidencia → guardar/descartar → registrar manualmente una postulación. El resultado debe ser una herramienta útil por sí misma y una demostración profesional de integración de fuentes, automatización controlada y razonamiento explicable.

## 2. Problema y oportunidad

Las vacantes, los CV usados, los requisitos y los estados de candidatura suelen quedar dispersos entre pestañas, bolsas de empleo y hojas de cálculo. Herramientas como [Teal](https://www.tealhq.com/tools/job-tracker), [Huntr](https://help.huntr.co/en/articles/9883324-job-tracker) y [Simplify](https://help.simplify.jobs/help/collections/1126456-tracking-your-job-search) ya resuelven tracking, documentos, contactos, palabras clave e incluso sincronización de correo. Rolekai no intentará replicarlas en v0.1.

La diferenciación propuesta es una capa de inteligencia verificable: procedencia por dato, elegibilidad explícita para un candidato en México, deduplicación entre fuentes, explicación de cada recomendación y una frontera humana clara antes de adaptar un CV, cambiar una postulación o enviar una solicitud.

En open source ya existen propuestas de tracking local/privado, como [JobNest](https://github.com/maerzhase/jobnest), y de automatización desde Gmail, como [ApplyTrail](https://github.com/rutuu/ApplyTrail). Esto confirma que el tracking y la privacidad no son una diferenciación suficiente por sí solos. Rolekai debe destacar por el ciclo completo de descubrimiento autorizado, fusión de evidencia entre agregador y ATS directo, y evaluación geográfica explicable para México; Gmail sigue fuera de v0.1.

## 3. Objetivos

### Objetivos de producto

1. Encontrar y consolidar oportunidades remotas relevantes sin depender de una sola bolsa.
2. Reducir el tiempo para decidir si una oportunidad merece atención.
3. Separar datos confirmados, inferencias y datos desconocidos para que el usuario pueda confiar en el sistema.
4. Crear una base que pueda evolucionar de uso personal a multiusuario sin añadir complejidad prematura.
5. Mostrar un flujo coherente de agentes especializados, donde cada agente tenga una responsabilidad concreta.

### Métricas iniciales

- Al menos 90% de las importaciones manuales válidas producen una oportunidad revisable o un error accionable.
- Al menos 95% de las oportunidades repetidas de la misma fuente se consolidan correctamente; falsos positivos de deduplicación se corrigen manualmente y se miden.
- Toda evaluación de compatibilidad incluye requisitos detectados, evidencia utilizada y elementos faltantes o desconocidos.
- 100% de los cambios automáticos conservan fuente, momento de observación y valor previo cuando aplique.
- El usuario puede pasar de una URL de vacante a una decisión de guardar/descartar con una sola revisión de ficha.

### No objetivos del MVP

- Envío automático de postulaciones, autofill de formularios o interacción con sitios de terceros.
- Lectura de Gmail, detección automática de respuestas o monitor de aplicaciones automático.
- Generación final de CV o carta de presentación sin revisión y aprobación humana.
- Búsqueda universal en LinkedIn, Indeed, Glassdoor u otros sitios sin una integración autorizada.
- Predicción de probabilidad de contratación, salario real o elegibilidad migratoria/legal.
- Producto multiusuario, facturación, permisos organizacionales o marketplace.

## 4. Usuarios y casos de uso

### Usuario principal de v0.1

AI Engineer residente en México que busca roles remotos internacionales: AI Engineer, Agentic AI Engineer, AI Research Engineer, Full-Stack AI Engineer, Forward Deployed Engineer y Applied AI Engineer.

### Personas futuras

- Candidato técnico que necesita una vista auditable de su búsqueda.
- Usuario individual que quiere adaptar materiales sin que el sistema invente logros.
- Profesional con varias zonas o restricciones geográficas que necesita filtrar elegibilidad antes de invertir tiempo.

### Casos de uso prioritarios

1. Configurar títulos, tecnologías, modalidad remota, países elegibles, idiomas, contrato, seniority, salario y exclusiones.
2. Descubrir vacantes nuevas desde Remotive y, cuando se conozcan tableros de compañía, desde Greenhouse, Lever o Ashby.
3. Pegar una URL y guardar la vacante aun cuando no se pueda enriquecer automáticamente.
4. Identificar la misma vacante publicada por un agregador y por el ATS de la empresa.
5. Revisar por qué una vacante es relevante, no elegible, incierta o de baja prioridad.
6. Marcar una vacante como guardada, descartada o aplicada y registrar un historial manual de actividad.

## 5. Alcance funcional

### MVP v0.1

| Área | Incluido |
| --- | --- |
| Perfil de búsqueda | Preferencias editables, separando criterios obligatorios y negociables. |
| Ingesta | **P0:** Remotive, URL manual y Greenhouse. Lever y Ashby son conectores seleccionados que se activarán en P1 tras validar muestras reales, bajo el mismo contrato. |
| Jobs | Normalización, conservación de descripción original, deduplicación y procedencia. El historial de cambios por verificación queda en P1. |
| Relevancia | Filtros deterministas y una evaluación inicial explicable contra un perfil de evidencia. |
| Dashboard | Overview, Discover, Saved Jobs, Applications, Activity y Settings en alcance inicial; CV Studio como acceso informativo sin tailoring automático. |
| Seguimiento | Estado y eventos manuales de postulación. |
| Control humano | Confirmación para descartar, editar datos normalizados, registrar postulación o producir una futura variante de CV. |

### Posterior al MVP

1. CV Tailor con catálogo de evidencia, control de versiones y aprobación humana.
2. Ejecuciones programadas de fuentes y verificación de cambios.
3. Conexión autorizada a Gmail para clasificar señales, siempre con confirmación antes de alterar estados.
4. Application Monitor, analítica de conversión y Career Strategy Agent.
5. Descubrimiento de más fuentes autorizadas y soporte multiusuario.

## 6. Requisitos funcionales

### RF-01 — Perfil de búsqueda

El usuario puede definir títulos deseados, seniority, tecnologías, idioma, modalidad, países o regiones elegibles, restricciones geográficas, salario mínimo/deseado, moneda, tipo de contratación, preferencias y exclusiones. Cada regla se marca como **obligatoria**, **preferida** o **informativa**. La configuración predeterminada debe priorizar remoto internacional con residencia en México, sin afirmar elegibilidad cuando la vacante no la declare.

### RF-02 — Descubrimiento e importación

Rolekai puede incorporar oportunidades desde conectores independientes y desde una URL manual. Cada ejecución genera un registro de origen y resultados (creado, actualizado, duplicado, omitido o fallido). Una fuente agregada descubre empresas nuevas; una fuente directa las enriquece cuando existe un tablero reconocible y accesible.

### RF-03 — Conservación y normalización

La oportunidad conserva una copia inmutable de la respuesta o descripción original y una representación normalizada. Campos no encontrados se guardan como `unknown`/ausentes, nunca con valores estimados presentados como hechos.

### RF-04 — Deduplicación y cambios

El sistema detecta coincidencias exactas por fuente/identificador/URL y candidatos a coincidencia entre fuentes. Las coincidencias de alta confianza se consolidan; las ambiguas se muestran para revisión. Cada consolidación mantiene enlaces a todas las observaciones. Los cambios de contenido, disponibilidad y datos clave generan eventos auditables.

### RF-05 — Evaluación inicial

Rolekai Evaluator extrae requisitos, los clasifica y los contrasta contra un perfil profesional basado en evidencia. El resultado contiene: resumen, requisitos cubiertos, faltantes, desconocidos, bloqueadores y razones de priorización. Una puntuación solo expresa ajuste relativo configurado; no es una probabilidad de contratación ni una recomendación de postular.

### RF-06 — Gestión manual de candidaturas

Una oportunidad puede existir sin postulación. Solo una acción explícita del usuario crea una candidatura. El usuario puede actualizar su estado, notas, fechas y eventos. Los eventos de comunicación no confirman un avance salvo que el usuario lo marque o una futura integración aporte evidencia inequívoca y solicite confirmación.

### RF-07 — Dashboard

El dashboard ofrece vistas coherentes, filtros y enlaces a evidencia. Ninguna vista debe mezclar el estado de descubrimiento, de evaluación y de postulación en un único campo.

## 7. Estados y reglas de negocio

### Estados independientes

| Dimensión | Estados v0.1 |
| --- | --- |
| Descubrimiento | `new`, `imported`, `normalized`, `duplicate_candidate`, `merged`, `archived`, `unavailable`, `unknown_availability` |
| Evaluación | `not_queued`, `queued`, `evaluating`, `evaluated`, `needs_review`, `failed` |
| Decisión de oportunidad | `inbox`, `saved`, `dismissed` |
| Postulación | `not_applied`, `preparing`, `applied`, `interviewing`, `offer`, `rejected`, `withdrawn`, `closed_unknown` |
| Actividad | Evento inmutable: descubrimiento, cambio observado, edición humana, evaluación, nota, cambio de candidatura. |

### Reglas

- `not_applied` es el valor inicial de toda oportunidad; no equivale a que el usuario haya decidido no postular.
- Una transición a `applied` requiere confirmación explícita y, si se conoce, fecha y URL o canal de postulación.
- Una respuesta de reclutador crea un evento; solo cambia el estado a `interviewing`, `offer` o `rejected` tras confirmación humana en v0.1.
- `unavailable` indica que la fuente directa ya no ofrece la vacante; no borra la evidencia ni modifica automáticamente una candidatura existente.
- Un criterio obligatorio incumplido marca `not_eligible` en el resultado de filtro; información insuficiente marca `eligibility_unknown`.

## 8. Experiencia y dashboard

### Navegación

1. **Overview:** conteos por decisión y postulación, oportunidades nuevas, cambios recientes, pendientes de revisión y embudo manual.
2. **Discover:** bandeja de resultados no revisados; filtros por fuente, elegibilidad México/remoto, fecha, título y relevancia.
3. **Saved Jobs:** oportunidades elegidas por el usuario, con evaluación, notas y siguiente acción.
4. **Applications:** tablero de candidaturas manuales por estado; no incluye empleos meramente guardados.
5. **Activity:** línea de tiempo filtrable de observaciones, ediciones, evaluaciones y cambios de estado.
6. **CV Studio:** en v0.1 muestra el CV base y el aviso de que tailoring es una iteración posterior; conservará el punto de entrada sin prometer generación.
7. **Settings:** perfil de evidencia, preferencias de búsqueda, fuentes habilitadas y reglas de filtrado.

### Wireframes conceptuales

```text
Overview
+-------------------+-------------------+-------------------+
| Nuevas: 12        | Por revisar: 5    | Aplicadas: 3      |
+-------------------+-------------------+-------------------+
| Cambios recientes |  Próximas acciones / notas                 |
+-------------------+--------------------------------------------+

Discover
[filtros: fuente | remoto elegible MX | fecha | título | ajuste]
-----------------------------------------------------------------
| Empresa / rol       | elegibilidad | ajuste explicado | decisión |
| ...                 | confirmado  | ver evidencia    | guardar  |
-----------------------------------------------------------------

Job Detail
[descripción original] [normalizada] [fuentes] [historial]
Elegibilidad: confirmada / incierta / no elegible
Evaluación: cubierto | faltante | desconocido | razones
[Guardar] [Descartar] [Registrar postulación]
```

## 9. Orquestación conceptual

| Componente | Responsabilidad | Tipo de trabajo | Aprobación humana |
| --- | --- | --- | --- |
| Rolekai Hunter | Descubrir, importar, extraer, normalizar, deduplicar y detectar cambios. | Conectores y reglas deterministas; LLM opcional para extracción difícil con evidencia. | Guardar/descartar en la bandeja y correcciones. |
| Rolekai Evaluator | Comparar requisitos con evidencia profesional y explicar huecos. | Reglas + LLM acotado para clasificación y síntesis. | Validar perfil/evidencia y usar el resultado para actuar. |
| Rolekai Tailor | Proponer versiones de CV basadas solo en evidencia aprobada. | LLM controlado y validaciones deterministas. | Obligatoria antes de crear/exportar una variante. |
| Rolekai Monitor | Mantener actividad y, más adelante, interpretar fuentes autorizadas. | Reglas de estado; LLM solo para clasificar texto ambiguo. | Obligatoria para transiciones sensibles. |

Los conectores no son agentes: son adaptadores deterministas con contratos comunes. Un coordinador crea una cola de evaluación después de que Hunter persiste una oportunidad válida. Un fallo se aísla por conector, conserva el error y permite reintento sin detener las demás fuentes.

## 10. Requisitos no funcionales

- **Trazabilidad:** dato normalizado enlazable a observación, fuente y fecha.
- **Exactitud semántica:** diferenciar hecho, inferencia y desconocido.
- **Privacidad:** perfil, CV y cualquier futura cuenta de correo son datos sensibles; acceso mínimo y consentimiento explícito.
- **Confiabilidad:** reintentos acotados, idempotencia por ejecución e historial no destructivo.
- **Explicabilidad:** resultados de IA con evidencia textual; edición humana visible.
- **Accesibilidad y lenguaje:** interfaz inicialmente en inglés o bilingüe, con fechas/monedas explícitas y contenido original preservado.
- **Escalabilidad progresiva:** identidad de propietario en el dominio desde el diseño, sin construir multitenancy en v0.1.

## 11. Criterios de aceptación del MVP

1. El usuario puede configurar al menos un título, una regla obligatoria de ubicación y una tecnología preferida.
2. Una importación desde cada fuente **habilitada en P0** (Remotive, URL manual y Greenhouse) crea o actualiza jobs con URL y procedencia; una falla ofrece motivo y posibilidad de reintentar.
3. Una URL manual se guarda con contenido disponible y etiqueta de confianza, aun si no se reconoce ATS.
4. Una vacante detectada por Remotive y Greenhouse queda enlazada o se presenta como candidata a fusión sin perder ninguna observación.
5. La ficha muestra descripción original, atributos normalizados, información desconocida, fuente, fechas y cambios.
6. El filtro identifica explícitamente remoto confirmado, restricción incompatible, elegibilidad incierta y coincidencia con México cuando la fuente lo declara.
7. La evaluación distingue requisitos cubiertos, faltantes y desconocidos, y enlaza cada conclusión a texto de vacante o evidencia de perfil.
8. Registrar una postulación no se ejecuta automáticamente por guardar, evaluar o abrir una vacante.
9. El dashboard separa oportunidades descubiertas, guardadas y candidaturas.
10. No existe una acción de envío automático de postulaciones en el MVP.

## 12. Fuentes y diferenciación

- **Mercado:** Teal concentra tracker, bookmarking, palabras clave, CV y seguimiento; Huntr incluye tablero, actividad, métricas, contactos y documentos; Simplify ofrece pipeline, embudo y sincronización de Gmail. En open source, JobNest prioriza tracking local y privacidad, mientras ApplyTrail prioriza correo y clasificación local. Rolekai debe evitar competir con su amplitud inicial y enfocarse en procedencia, conectores directos y elegibilidad internacional explicable.
- **Diferenciación viable:** priorización para residencia en México basada en evidencia de la vacante, jerarquía de fuentes directas sobre agregadas y auditoría de cada conclusión de IA.
- **No afirmación de marca:** `Rolekai` es un nombre de trabajo. La disponibilidad de dominio y marca requiere una revisión legal/comercial independiente antes de lanzamiento.

## 13. Siguiente paso recomendado

Revisar estos documentos, congelar el MVP v0.1 y pasar a una especificación de arquitectura que defina contratos de conector, modelo persistente, estrategia de ejecución, seguridad, observabilidad y selección tecnológica. No iniciar código hasta aprobar ese diseño.
