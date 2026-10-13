# Rolekai Foundation — entorno de desarrollo

Implementación limitada a `01-01-PLAN.md`: shell Next.js, API FastAPI con health, settings, PostgreSQL/migración vacía, OTel y gates. No hay tablas de dominio, conectores, evaluadores ni dashboard funcional.

## Requisitos y versiones verificadas

- Windows, Node 24.18.0 y npm 11.16.0; versiones mínimas Node 24/npm 10.
- Python **3.14.x** (verificado 3.14.6). `pyproject.toml` admite >=3.14,<3.15; todos los binarios requeridos se instalaron desde wheels cp314.
- Docker Desktop/Engine disponible y Compose (verificados Engine 29.7.2, Compose 5.4.0). No hace falta Bash/WSL para los comandos locales.
- Next 16.4.0, React 19.3.0, TypeScript 6.0.3; FastAPI 0.143.0, Pydantic 2.14.1, Psycopg 3.3.6, SQLAlchemy 2.1.4, Alembic 1.20.0, Uvicorn 0.54.0 y OTel SDK/API 1.45.1.
- PostgreSQL **18.4**, imagen oficial 18-alpine fijada por digest en `compose.yaml`.

Locks: `package-lock.json` (workspaces web), `.tools/package-lock.json` (GSD independiente) y `apps/api/requirements.lock` (dependencias API/test, pins y SHA-256). No se instalan paquetes Python globales. npm lifecycle scripts están deshabilitados localmente en `.npmrc`; no se deshabilita TLS ni la política de PowerShell.

ESLint 9.39.4 está deprecado upstream. Se mantiene el pin compatible con los peer ranges de `eslint-plugin-react` incluido por Next; no se utilizaron `--force`/`--legacy-peer-deps` para forzar ESLint 10. Es deuda de herramientas a revisar cuando los plugins declaren compatibilidad; [Next documenta esta transición](https://nextjs.org/docs/app/api-reference/config/eslint).

## Instalación limpia en PowerShell

Desde la raíz:

```powershell
npm.cmd ci --ignore-scripts --no-audit --no-fund
python -c "import sys; assert sys.version_info[:2] == (3, 14), 'Selecciona Python 3.14 antes de crear el venv'"
if ($LASTEXITCODE -ne 0) { throw 'El Python de esta terminal no es 3.14' }
python -m venv .venv
.venv/Scripts/python.exe -m pip install --only-binary=:all: setuptools==82.0.1
.venv/Scripts/python.exe -m pip install --only-binary=:all: --require-hashes -r apps/api/requirements.lock
.venv/Scripts/python.exe -m pip install --no-deps --no-build-isolation -e 'apps/api[test]'
node scripts/setup-local-env.cjs
docker compose up -d --wait postgres
```

`setup-local-env.cjs` crea `.env` ignorado con contraseña aleatoria solo si no existe; nunca imprime ni sobrescribe credenciales. Alternativa manual: copiar `.env.example` a `.env` y reemplazar los placeholders consistentemente. PostgreSQL escucha **solo en 127.0.0.1:15432**, proyecto Compose `rolekai-foundation`; no comparte volúmenes con otros proyectos.

Crear una vez la base de integración aislada:

```powershell
$databaseExists = docker compose exec -T postgres psql -U rolekai -d rolekai -tAc "SELECT 1 FROM pg_database WHERE datname='rolekai_foundation_test'"
if ($databaseExists.Trim() -ne '1') {
    docker compose exec -T postgres createdb -U rolekai rolekai_foundation_test
}
.venv/Scripts/python.exe -m alembic -c apps/api/alembic.ini upgrade head
```

Si un proveedor/proxy exige el almacén Windows para TLS Node, usar `$env:NODE_USE_SYSTEM_CA='1'` en esa terminal. No usar certificados ignorados. Si Docker no está instalado/activo, los comandos devolverán un diagnóstico del engine; instalar/iniciar Docker Desktop por el procedimiento habitual antes de ejecutar integración. No cambiar permisos globales desde estos scripts.

En esta máquina se detectaron resoluciones distintas de `python` según la terminal/perfil (3.11 y 3.14). El guard anterior impide crear el venv equivocado. Si falla, invocar el ejecutable 3.14 elegido explícitamente para `-m venv` y usar siempre `.venv/Scripts/python.exe` después. El venv limpio de verificación se creó con el intérprete 3.14 ya validado; TLS permaneció activo.

En un checkout nuevo también regenerar los assets locales GSD según `AGENT_CONTINUITY.md`. Estos no pertenecen a las dependencias npm del producto.

## Ejecutar y detener

En dos terminales desde la raíz:

```powershell
npm.cmd run dev:web
.venv/Scripts/python.exe -m uvicorn rolekai.main:app --host 127.0.0.1 --port 8000
```

Web: `http://127.0.0.1:3000`. API: `http://127.0.0.1:8000`, `/health/live`, `/health/ready`, `/docs`. Importar `rolekai.main:app` no requiere una conexión; al iniciar el servidor se valida la configuración. Liveness no consulta PostgreSQL. Readiness realiza `SELECT 1` con timeout de conexión y statement; un fallo retorna 503 con error seguro y `request_id`, sin detalles de credenciales.

Ctrl+C detiene cada servidor. `docker compose stop postgres` detiene solo PostgreSQL de este proyecto y conserva el volumen. Reiniciar con `docker compose up -d --wait postgres`. No usar `down -v` para la recuperación normal.

## Pruebas y gates

```powershell
npm.cmd run quality
node scripts/test-quality-negative.cjs
```

El gate completo usa exactamente: typecheck, ESLint, build Next, Ruff, todas las pruebas API (incluida integración real), `pip check`, pruebas Agent Continuity y smoke HTTP del servidor web construido. Falla en el primer comando no exitoso y registra solo metadatos/exit codes en `.planning/.continuity/foundation-01-quality.json`, ignorado por Git.

`test-quality-negative.cjs` crea dos archivos nuevos temporales con tipo/test inválidos, comprueba que fallan por la razón esperada y elimina únicamente esos archivos; no sobrescribe trabajo existente. Ejecutar luego `npm.cmd run quality` para confirmar el árbol restaurado.

Las pruebas de integración requieren **TEST_DATABASE_URL apuntando exactamente a rolekai_foundation_test** y rechazan una base con tablas de dominio. Upgrade/downgrade/upgrade se ejecuta ahí; no sobre datos de usuario. Foundation deja únicamente `alembic_version`. El downgrade de desarrollo debe hacerse solo antes de que existan migraciones/datos de dominio futuros.

Modo sin Docker: `npm.cmd run quality -- --unit-only` ejecuta gates web/API unitarios/continuidad/smoke, pero **no certifica integración PostgreSQL ni Foundation completo**. En CI, Ubuntu ejecuta el gate completo sobre Compose aislado; Windows ejecuta unit-only, sin Docker en el runner. El hook Windows se omite explícitamente en plataformas no Windows.

El drift gate de contratos de dominio se incorporará en fase 2; no hay un comando vacío que simule aprobarlo. Los contratos health de Foundation se verifican en pytest/OpenAPI.

## Observabilidad y privacidad

Spans OTel de solicitudes con método, plantilla de ruta, código HTTP y UUID de correlación generado por el servidor. No se capturan URL/query crudos, cabeceras, cuerpo, CV, excepción textual ni datos de conexión. Las rutas no encontradas se registran como `unmatched`. No hay exporter remoto/auto-instrumentación de proveedores en Foundation; las pruebas usan un exporter en memoria. No modificar esta política al agregar instrumentación futura sin sus pruebas de redacción.

## Resultados y límites

Ver evidencia en `01-01-SUMMARY.md` y `01-VERIFICATION.md`. CI está definido pero no se disparó en GitHub: no hay remote/commits y esta instrucción prohíbe crear commits automáticamente. La confianza de hooks del Codex interactivo requiere revisión nativa; el CLI de verificación consultado no cargó la capa local por su perfil de confianza aislado. Se usan checkpoints explícitos sin bypass.

Los documentos históricos de integración describen la entrega anterior sin producto; el gate vigente para este incremento es `npm.cmd run quality`. Los módulos y planes posteriores siguen sin ejecutar.
# Core Domain increment (02-01)

Foundation dependency versions and environment remain valid; no reinstall is required for this increment. Core Domain adds typed profile/evidence, Job snapshots/provenance, versioned Evaluation data, explicit manual Application tracking and append-only Activity. Approved definitions remain in `docs/architecture/DATA_MODEL.md` and `API_CONTRACTS.md`.

The local API uses a server-configured `CURRENT_OWNER_ID` (default `00000000-0000-0000-0000-000000000001`) and a random `API_ACCESS_TOKEN` in ignored `.env`. Domain requests require `Authorization: Bearer <local token>`; headers/body cannot choose another owner. Missing configuration returns safe 503; invalid/missing credentials return 401. Health remains public. Keep Uvicorn bound to loopback as documented; this is a local single-user credential, not registration or hosted multiuser authentication. Never put the token in URLs, tracked files or shared logs. This increment appended missing configuration to the existing local `.env` without changing database credentials; new environments get it from `setup-local-env.cjs`. Existing environments are deliberately preserved by that script and must add the two fields from `.env.example` if absent.

Create the dedicated domain test database once:

```powershell
docker compose exec -T postgres createdb -U rolekai rolekai_domain_test
```

Tests derive its URL from `TEST_DATABASE_URL`, changing only the database name from `rolekai_foundation_test` to `rolekai_domain_test`. They refuse any other source database name and refuse unknown tables before clearing fixtures. Domain tests truncate only this dedicated test schema. Foundation tests continue testing revision `0001_foundation` on their separate database. Never point test configuration at development or production data.

Apply current migrations to the development database before using domain endpoints:

```powershell
.venv/Scripts/python.exe -m alembic -c apps/api/alembic.ini upgrade head
```

Revision `0002_domains` adds ownership/uniqueness/independent-state constraints and PostgreSQL triggers rejecting observation, Activity and transition UPDATE/DELETE. Its downgrade removes domain data; use downgrade only on disposable data. The versioned `schema_v2.py` definition is frozen: future schema changes require another migration rather than editing this historical version. Composite foreign keys prevent cross-owner Job/observation/evidence/evaluation references. P0 retains at most one Application per owner/Job, including terminal records; reapplication history is a later model change.

Profile PUT and repeated identical job decisions emit no duplicate Activity. Applications require saved/owned Jobs and strict boolean confirmation; concurrent creation is serialized and conflicts with 409. Status transitions require confirmation and follow `applications/service.py`'s explicit transition table. Domain write, transition record and Activity insert share one transaction. API responses retain original descriptions/provenance and persisted evaluation requirements/spans; there is no scoring, connector or submission client.

All `/api/v1` lists enforce `1 <= limit <= 100` and return opaque resource-specific cursors containing timestamp/UUID tie-breakers. Activity sorts by `occurred_at DESC, id DESC`, Jobs by discovery time and evidence by creation time. Job date filters use optional inclusive UTC `posted_after`/`posted_before`; unknown dates remain null and do not match a date bound. Decision reasons are retained in Activity metadata atomically. Imports and evaluation enqueue endpoints publish their future schemas but return safe `503 FEATURE_NOT_ENABLED`; no import/evaluation is actually accepted yet. Phase 3 must persist idempotency by owner/key/intent, return the same `run_id` for retries and 409 for changed intent. `ImportAccepted.run_id` is the canonical field, following the approved explicit DTO.

Contracts and gates:

```powershell
npm.cmd run contracts:export
npm.cmd run contracts:check
.venv/Scripts/python.exe -m pytest -c apps/api/pyproject.toml apps/api/tests/test_domain.py apps/api/tests/test_contracts.py -q
.venv/Scripts/python.exe -m pytest -c apps/api/pyproject.toml apps/api/tests/integration/test_domain_transactions.py -q
npm.cmd run quality
```

`contracts:export` generates sorted UTF-8 OpenAPI plus dependency-free TypeScript `components`/`paths` types; review both generated files. `contracts:check` compares current DTOs against both snapshots without writing them and is mandatory in local/CI quality. `apps/web/src/contracts.ts` makes generated types part of frontend compilation. CI creates both isolated test databases and invokes the shared gate; remote CI execution remains pending repository setup. No dependency installation, deployment or Git mutation is performed by these contract commands.

