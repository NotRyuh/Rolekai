# Rolekai — continuar en casa

Actualización 2026-10-14: se diagnosticó y corrigió el fallo de npm en Linux y se completó la revisión independiente con sus regresiones. Gate actual: **86 API + 17 tooling/continuidad**, diez checks aprobados. CI remoto sigue fallido: este patch no se ha publicado y requiere autorización explícita para commit/push. **03-01 no está cerrado; 04-01 sigue bloqueado.** Consultar `.planning/phases/03-job-ingestion/03-01-UNBLOCK.md` y `docs/development/INGESTION_UNBLOCK_VERIFICATION.json`. El resto de este documento conserva el contexto y las métricas del checkpoint anterior; la actualización anterior prevalece sobre sus pendientes históricos.

Repositorio privado: https://github.com/NotRyuh/Rolekai. Este es un checkpoint autorizado por el usuario; no una declaración de cierre de Job Ingestion.

Autorización posterior 2026-10-14: el usuario aprobó un commit/push de las correcciones revisadas y el handoff en master para verificar Actions. El cierre depende del resultado del nuevo run; no hay autorización para otros commits automáticos.

## Estado real

- Foundation `01-01` y Core Domain `02-01`: completos y aprobados.
- Job Ingestion `03-01`: código implementado y gate local satisfactorio; **revisión independiente y aceptación/cierre de GSD pendientes**.
- Implementado: URL manual, Remotive y tableros Greenhouse conocidos; snapshots/procedencia, deduplicación exacta por propietario, importación asíncrona, Idempotency-Key y worker PostgreSQL con leases/fencing/reintentos. Sin Lever/Ashby, Evaluator, Dashboard, scheduler ni submission clients.
- Captura manual de URL/texto sin HTTP por defecto. Descarga solo para hosts autorizados explícitamente; validación de IP pública, pinning de conexión, TLS/Host, redirects, tamaño y tiempo. HTML original se conserva como evidencia; el texto extraído no ejecuta contenido. No renderizar HTML crudo en UI futura.
- Remotive tiene presupuesto global persistido, máximo cuatro consultas/día y separación mínima de seis horas; atribución/enlace/retraso de fuente se preservan. [Política oficial](https://github.com/remotive-com/remote-jobs-api). Greenhouse usa únicamente lectura pública de boards conocidos con contenido. [Contrato oficial](https://docs.greenhouse.io/job-board.html).
- No se hicieron llamadas de importación a fuentes reales; fixtures sintéticos y servidor HTTP local controlado. Validación de muestras reales corresponde a la fase 6.
- Los nueve documentos aprobados de producto/arquitectura se conservan.

## Verificación guardada

Último gate completo: **80 pruebas API + 13 Agent Continuity**, todas aprobadas; diez checks (tipos, lint, build, Ruff, drift JSON/TypeScript, tests, pip check y smoke web). Los nuevos casos incluyen 24 de conectores/seguridad y 13 de PostgreSQL para ingestión. Ver `docs/development/INGESTION_VERIFICATION.json`.

La revisión independiente no pudo iniciarse por el límite de uso del runtime. No hay aprobación de reviewer; no existe `03-01-SUMMARY.md` de completitud ni se marcaron sus cinco requisitos completos. `.planning/STATE.md`, `.planning/HANDOFF.json` y `.planning/phases/03-job-ingestion/.continue-here.md` son la continuidad nativa. El checklist/diagnóstico está en `03-01-EXECUTION.md`.

## Clonar y preparar otra máquina (Windows)

Prerequisitos: Git, acceso autenticado a NotRyuh, Node 24, Python 3.14 y Docker Desktop funcionando. El entorno existente solo necesita reinstalación al crear **esta nueva máquina**; no reconstruir un entorno que ya sea válido. Para más detalle, `docs/development/SETUP.md`.

```powershell
git clone https://github.com/NotRyuh/Rolekai.git
Set-Location Rolekai
npm.cmd ci
npm.cmd ci --prefix .tools --ignore-scripts --omit=optional --no-audit --no-fund
node scripts/install-gsd.cjs
python -c "import sys; assert sys.version_info[:2] == (3, 14); print(sys.version.split()[0])"
python -m venv .venv
.venv/Scripts/python.exe -m pip install setuptools==82.0.1
.venv/Scripts/python.exe -m pip install --only-binary=:all: --require-hashes -r apps/api/requirements.lock
.venv/Scripts/python.exe -m pip install --no-deps --no-build-isolation -e "apps/api[test]"
node scripts/setup-local-env.cjs
docker compose up -d --wait postgres
docker compose exec -T postgres createdb -U rolekai rolekai_foundation_test
docker compose exec -T postgres createdb -U rolekai rolekai_domain_test
docker compose exec -T postgres createdb -U rolekai rolekai_ingestion_test
.venv/Scripts/python.exe -m alembic -c apps/api/alembic.ini upgrade head
node scripts/agent-continuity.cjs resume --runtime codex --session ingestion-home
```

Usar las credenciales de GitHub mediante Git Credential Manager o `gh auth login`; no pegarlas en comandos/archivos. Si las bases de test ya existen, no repetir `createdb`. Cada suite conserva su base y revisión histórica; ingestion usa solo `rolekai_ingestion_test` y verifica tablas antes de limpiar fixtures.

`node scripts/install-gsd.cjs` reinstala assets nativos ignorados y adapta las rutas a la nueva ubicación. Revisar/trust de hooks en Codex interactivo según su UI; no desactivar seguridad. W010/W019 y la deprecación de ESLint 9 eran avisos conocidos. Regenerar `.env` crea contraseña/token nuevos: **no se subieron `.env`, secretos, node_modules, venv, volúmenes PostgreSQL, logs/checkpoints técnicos ni datos locales**. Las configuraciones públicas están en `.env.example`; no modificar documentos aprobados para reparar paths locales.

## Reanudar exactamente 03-01

1. Leer `AGENTS.md`, `.planning/STATE.md`, el plan `03-01-PLAN.md` y el ledger. Consultar solo dependencias relevantes.
2. Revisar la implementación independientemente antes de darla por cerrada. Enfocar prioridades/procedencia de fuentes y correcciones humanas; rutas reales de `payload_path`; validación de campos por fuente; URL/DNS/TLS/lectura parcial; leases y fencing en lotes; sincronización de disponibilidad comprobada sin tocar Applications.
3. Reproducir hallazgos con pruebas focalizadas antes de corregir. Mantener aislamiento, originales, dedupe conservador e idempotencia. No deducir que todos los puntos de revisión ya fueron aceptados.
4. Verificar el nuevo entorno una vez y luego repetir solo checks afectados por cambios; ejecutar el gate completo al terminar las correcciones.
5. Solo después de aceptación real: generar SUMMARY, verificar GSD, completar los cinco requisitos, actualizar roadmap/STATE y handoff. **Detenerse después de 03-01; no iniciar 04-01 ni hacer commits adicionales sin instrucción.**

```powershell
.venv/Scripts/python.exe -m pytest -c apps/api/pyproject.toml apps/api/tests/test_connectors.py -q
.venv/Scripts/python.exe -m pytest -c apps/api/pyproject.toml apps/api/tests/integration/test_imports.py -q
npm.cmd run contracts:check
npm.cmd run quality
```

El worker se ejecuta explícitamente como un intento pendiente:

```powershell
.venv/Scripts/python.exe -m rolekai.workflows.worker
```

No ejecutarlo sobre trabajos reales sin revisar configuración y límites. `GREENHOUSE_BOARDS` y `MANUAL_FETCH_HOSTS` por defecto están vacíos; Remotive es la única fuente que puede consumir su presupuesto público cuando haya un run solicitado. Las rutas de Evaluation continúan inactivas.

## Execution Performance

Gate completo local: **39.445 s**; API **13.114 s**, Continuity **11.244 s**, ESLint **4.855 s**, Next build **4.177 s**. Estos son tiempos de comandos con startup, no métricas de razonamiento. Instalaciones: ninguna en la máquina de origen. Tiempo total de sesión, revisión independiente y hooks efectivos: no disponible.

Cuellos de botella medidos: API y Continuity. Hubo correcciones diagnosticadas para formas numéricas de IP privada, timestamp/identidad Greenhouse y cierre de socket HTTP tras consumir Content-Length; sus regresiones pasan. Para continuar, reutilizar locks/entorno válido, mantener fixtures focalizados y medir reintentos/continuidad cuando realmente ocurran. No sumar categorías solapadas ni volver a investigar la arquitectura.

## Prompt para el próximo agente

> Continuemos Rolekai desde HANDOFF.md. Recupera GSD y Agent Continuity. Foundation/Core Domain están aprobados; 03-01 tiene implementación y gate local aprobados pero revisión/cierre pendientes. Revisa y termina exclusivamente lo pendiente de 03-01, preservando cambios existentes y la Execution Efficiency Policy. No implementes Lever, Ashby, Evaluator ni Dashboard. No avances a 04-01 ni hagas commits automáticos.
