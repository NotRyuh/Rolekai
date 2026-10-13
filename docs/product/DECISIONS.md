# Rolekai — Product Decisions, Assumptions and Risks

**Fecha:** 2026-10-13  
**Ámbito:** Product Discovery / Functional Specification v1.0

## Decisiones tomadas

| ID | Decisión | Motivo | Consecuencia |
| --- | --- | --- | --- |
| D-01 | El producto se llama **Rolekai** y usa la identidad “Your career, intelligently guided.” | Nombre corto, orientado a oportunidades y mejora profesional. | Es nombre provisional; no implica disponibilidad legal o de dominio. |
| D-02 | El MVP es híbrido: Remotive agrega descubrimiento; Greenhouse, Lever y Ashby son fuentes directas; URL manual es siempre válida. | Equilibra cobertura, trazabilidad y realismo técnico. | Se necesitan conectores independientes y política de fuente. |
| D-03 | Rolekai no se limita a una lista fija de empresas. | Debe descubrir compañías nuevas desde fuente agregada. | Los tableros directos se usan tras identificar/conocer una compañía/URL, no como buscador universal de ATS. |
| D-04 | Los conectores son adaptadores deterministas, no agentes autónomos. | Reduce complejidad, costo, fallos opacos y superficie de automatización. | LLM se reserva para extracción/evaluación donde aporta criterio. |
| D-05 | La residencia en México y remoto internacional son criterios de primera clase. | Es el objetivo del usuario principal. | Elegibilidad se expresa como confirmada, incompatible o incierta según evidencia. |
| D-06 | La descripción original y procedencia se conservan siempre. | Soporta confianza, corrección, dedupe y auditoría. | Se requiere modelo de observaciones/historial, no solo una tabla plana de puestos. |
| D-07 | Las dimensiones descubrimiento, evaluación, decisión y postulación son independientes. | Evita errores semánticos y un pipeline engañoso. | Dashboard y modelo usan estados distintos. |
| D-08 | No se automatizan postulaciones en MVP ni como comportamiento predeterminado posterior. | Protege al usuario y respeta condiciones de sitios. | La acción final permanece humana. |
| D-09 | Una puntuación de ajuste es relativa y explicable, no una probabilidad de contratación. | Evita falsas promesas y sesgos de interpretación. | La interfaz muestra evidencia, faltantes e incertidumbre. |
| D-10 | CV Tailor, Gmail y Application Monitor automático se posponen. | El primer valor demostrable está en discovery, evaluación y tracking manual. | CV Studio queda como punto de entrada, sin generación v0.1. |
| D-11 | El primer corte implementable de v0.1 habilita Remotive, URL manual y Greenhouse; Lever y Ashby se activan como P1 tras validar muestras reales. | Resuelve la contradicción entre el catálogo de fuentes deseado y un primer flujo verdaderamente acotado. | Las cuatro fuentes mantienen el mismo contrato, pero no bloquean el primer hito. |
| D-12 | Job, Evaluation, Application y Activity son agregados separados. | Un Job puede tener varias evaluaciones y una Application explícita; la actividad es auditable, no un estado. | No se almacenará `application_status` ni `evaluation_status` como atributo del Job. |

## Registro de revisión de consistencia

- Se alineó el primer flujo end-to-end con el backlog P0: Remotive + URL manual + Greenhouse.
- Lever y Ashby siguen seleccionados, pero pasan a activación P1 después de fixtures/muestras reales; no se elimina su diseño de conector.
- Se promovió la configuración mínima de tecnologías a P0 porque la evaluación inicial la necesita.
- Se eliminó el estado de postulación del registro Job y se hizo explícita la separación Job/Evaluation/Application/Activity.

## Supuestos documentados

1. El primer usuario es individual y controla los perfiles, fuentes y decisiones; se reserva `owner_id` para evolución futura, sin construir multitenancy.
2. El usuario aceptará una revisión de resultados con elegibilidad incierta en lugar de perder oportunidades potenciales.
3. La frecuencia de Remotive se configurará dentro de sus límites publicados (recomendación de hasta cuatro consultas diarias y sin ráfagas).
4. Un tablero directo se integra cuando hay una URL o identificador de tablero válido; no se hará enumeración agresiva de sitios.
5. Para URL manual, el usuario puede aportar descripción pegada si una página no es accesible o no tiene estructura compatible.
6. El perfil profesional se construirá a partir de evidencia verificable proporcionada por el usuario antes de confiar en una evaluación semántica.

## Restricciones y riesgos

| Riesgo | Impacto | Mitigación de producto |
| --- | --- | --- |
| Términos, cuotas o formatos de fuentes cambian | Discovery incompleto o interrupciones. | Conectores aislados, registro de capacidades, atribución visible, límites configurables y desactivación selectiva. |
| Remotive publica con retraso y exige enlace/atribución | Vacantes menos frescas o incumplimiento. | Mostrar fuente/enlace, etiquetar frescura y respetar máximo recomendado; validar términos antes de producción. |
| No existe búsqueda global oficial para los ATS directos | Cobertura inicial limitada. | Remotive descubre; URL manual captura; agregar fuentes autorizadas después de validar contratos. |
| “Remote” no implica elegibilidad desde México | Prioridad errónea y pérdida de tiempo. | Modelo de elegibilidad con evidencia y estado incierto. |
| Falsos positivos de dedupe | Se pueden mezclar roles distintos. | Umbral conservador, revisión humana, reversión y observaciones preservadas. |
| Extracción con LLM alucina requisitos o habilidades | Evaluación engañosa. | Conservar texto, citar evidencia, usar estados desconocidos y permitir corrección. |
| Datos sensibles de CV/perfil/correo | Riesgo de privacidad y confianza. | Consentimiento, minimización, trazabilidad y no conectar Gmail en MVP. |
| Nombre Rolekai tiene conflicto comercial | Riesgo de rebranding. | Realizar búsqueda de marca, dominios y redes antes de identidad pública. |
| Métricas de postulación se interpretan como causalidad | Decisiones poco fundamentadas. | Presentarlas como observaciones descriptivas con tamaño de muestra y filtros. |

## Preguntas abiertas

1. ¿Qué títulos, tecnologías y rango de seniority exactos integran el perfil inicial?
2. ¿La elegibilidad “Americas” debe incluir México automáticamente o requerir confirmación manual? Recomendación inicial: **incierta** hasta que una política explícita la defina.
3. ¿Qué fuentes de evidencia componen el perfil profesional: CV actual, LinkedIn exportado, proyectos, GitHub, portfolio y certificaciones?
4. ¿Qué frecuencia de actualización aporta valor antes de habilitar ejecuciones programadas?
5. ¿El producto se lanzará inicialmente bilingüe o con interfaz en inglés y documentación de producto en español?
6. ¿Cómo se evaluará la calidad de extracción/evaluación con ejemplos reales y revisión humana?
7. ¿Qué límites de retención/exportación aplicarán a snapshots de descripciones de terceros?

## Temas reservados para arquitectura

- Persistencia concreta, esquema físico, búsquedas y vectorización.
- Framework de orquestación y decisión sobre LangGraph u otra alternativa.
- Modelo/proveedor LLM, prompts, herramientas, costos y evaluaciones.
- Autenticación, autorización, cifrado, secretos y aislamiento multiusuario.
- Cola, scheduler, límites, caché y estrategia de reintentos.
- Detección técnica de ATS desde URL y manejo seguro de contenido HTML.
- Observabilidad, auditoría, logs, alertas y métricas técnicas.
- Estrategia de pruebas, fixtures de fuentes y entorno de desarrollo.
- Diseño visual, stack frontend/backend, despliegue y CI/CD.

## Criterio para pasar a arquitectura

Pasar a diseño técnico cuando se aprueben el alcance P0, las reglas de elegibilidad México/remoto, el modelo de evidencia profesional y las limitaciones de fuentes. La arquitectura deberá comenzar con el primer flujo end-to-end y no con una implementación simultánea de todos los agentes.
