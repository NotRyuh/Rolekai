# Rolekai — GSD + Agent Continuity

Integración local preparada el 2026-10-13. **No se implementó el producto.** Los nueve documentos de producto/arquitectura conservan su contenido y autoridad; sus hashes están en `.planning/intel/sources.json`.

## Componentes y procedencia

- GSD Core **1.16.0**, paquete `@opengsd/gsd-core`, repositorio [open-gsd/gsd-core](https://github.com/open-gsd/gsd-core). El repositorio originalmente señalado aparece como fork; se eligió el repositorio y paquete canónicos actuales, no un fork por similitud de nombre.
- Perfil oficial `standard`: 23 comandos por cierre de dependencias, incluyendo ingesta, fases, progreso, pausa/reanudación; 22 roles instalados. Las herramientas opcionales del perfil completo no se activaron.
- Node **24.18.0**, npm **11.16.0**, Python **3.14.6**, Codex **0.162.0-alpha.17.2**, Claude Code **2.1.222**. GSD requiere Node >=24 y npm >=10. Python no es dependencia de estos hooks.
- `.tools/package.json` y su lock fijan la dependencia de desarrollo. `GSD_PROVENANCE.json` registra URL, integridad y revisión; la instalación oficial convierte los artefactos para cada runtime.

Se descargó el tarball sin lifecycle scripts, se revisó el instalador y sus superficies de escritura, y se ejecutó su CLI directamente. npm no ejecutó `prepare/prepack/install/postinstall` de dependencias: instalación con `--ignore-scripts --omit=optional`. No se necesitan compilación local ni dependencias opcionales para el instalador/CLI compilados. Los hashes verifican integridad, no constituyen una auditoría exhaustiva del proyecto upstream.

## Instalación y actualización

Desde la raíz, en PowerShell:

```powershell
npm.cmd ci --prefix .tools --ignore-scripts --omit=optional --no-audit --no-fund
node scripts/install-gsd.cjs
node scripts/verify-environment.cjs
node scripts/probe-runtimes.cjs
```

Si Node rechaza la cadena TLS corporativa, usar `$env:NODE_USE_SYSTEM_CA='1'` **solo en esa terminal** y repetir npm. No usar `strict-ssl=false`, certificados ignorados ni ExecutionPolicy Bypass. `npm.cmd` respeta la política de ejecución existente de PowerShell.

El wrapper ejecuta el instalador oficial con `--claude --codex --local --profile=standard --relative-includes --no-legacy-cleanup`. Un preload exclusivo del proceso instalador dirige `os.homedir()` a `.tools/home`: evita que el instalador escriba sus defaults/cache en el home real. No se aplica al runtime ni altera sus credenciales/configuración. El primer intento sin confinamiento recibió EPERM al intentar defaults globales; no se forzó ese acceso. Reinstalación local comprobada, sin hooks duplicados.

El postproceso conserva guards nativos JS, elimina los permisos automáticos añadidos por el instalador y el chequeo de actualizaciones online; sustituye los comandos shell por invocaciones Node. Los hooks `.sh` de funciones opt-in inactivas no se registran. No se copian skills manualmente entre runtimes.

Para actualizar: verificar nueva versión/repo/tarball/scripts, cambiar la versión exacta y lock, revisar el pin de `install-gsd.cjs`, reinstalar, repetir todas las verificaciones y revisar de nuevo la confianza de hooks. No usar `/gsd-update` sin esa revisión: puede restaurar defaults/permisos upstream. No efectuar commits automáticamente.

## Codex

Instalación en `.codex/skills`, `.codex/agents`, `.codex/gsd-core`. Descubrimiento real de los 23 comandos confirmado por `skills/list` del CLI, sin turno de modelo. Configuración local `.codex/config.toml`: hooks habilitados; profundidad de roles nativa 1. No se habilita autoaprobación ni se modifica sandbox global.

Comandos principales: `$gsd-ingest-docs`, `$gsd-plan-phase`, `$gsd-execute-phase`, `$gsd-progress`, `$gsd-pause-work`, `$gsd-resume-work`, `$gsd-phase`, `$gsd-manager`, `$gsd-help`. Los nombres son los descubiertos en `RUNTIME_VERIFICATION.json`.

**Activación pendiente:** Codex exige revisar/confiar las definiciones exactas en `/hooks`, además de confiar la capa del proyecto. Instalación y descubrimiento no otorgan confianza automáticamente. No se usó el flag de bypass. [Referencia oficial](https://learn.chatgpt.com/docs/hooks).

## Claude Code

Comandos oficiales convertidos en `.claude/commands/gsd-*.md`; mismos 23 comandos descubiertos mediante inicialización real del CLI. Hooks en `.claude/settings.json`, invocaciones exec-form `command: node` y `args`, sin requisito de Bash/WSL. `settings.local.json` queda vacío para evitar duplicaciones/grants. Comandos equivalentes `/gsd-progress`, `/gsd-plan-phase`, `/gsd-pause-work`, `/gsd-resume-work`.

La status line nativa usa `node .claude/hooks/gsd-statusline.js`: iniciar Claude desde la raíz. Sus métricas oficiales alimentan el monitor nativo; no se instala otro monitor. Los guards para herramientas de shell también registran PowerShell. [Hooks oficiales de Claude](https://code.claude.com/docs/en/hooks).

## GSD y matriz de cobertura

| Necesidad | Cobertura GSD 1.16.0 / runtime | Extensión aplicada |
| --- | --- | --- |
| Tarea activa/fase/plan | Completa: STATE, PLAN, handoff nativo | Ningún tracker alternativo |
| Captura de nuevas tareas | Parcial: workflow de todo; sin CLI determinista create expuesto | Comando explícito `task` escribe un único todo nativo, idempotente; no infiere prompts/severidad |
| Progreso/completadas/bloqueos | Completa: STATE, SUMMARY, `todo complete`, progress | Wrapper de mutaciones; no duplica progreso |
| Contexto/decisiones entre sesiones | Completa: STATE, PROJECT, CONTEXT/SUMMARY | Lectura mínima de orientación |
| Handoff semántico/recuperación | Completa: HANDOFF.json + .continue-here.md, pause/resume | Ningún HANDOFF alternativo |
| Checkpoint Git/sesión/pruebas | Parcial: handoff registra cambios, no snapshot técnico automático completo | JSON auxiliar por sesión, fuera de Git |
| Compactación | Runtime nativo; GSD Claude resetea métricas antes de compactar | Checkpoints PreCompact/PostCompact y orientación SessionStart |
| Contexto Claude | Completa cuando status line entrega métricas | Adapter consume advertencia nativa y crea checkpoint; no calcula porcentajes |
| Contexto Codex porcentual | No soportado por el payload GSD/CLI observado | Eventos oficiales; ningún porcentaje inventado |
| Cambio Codex ↔ Claude | Parcial: artefactos compartidos, no snapshot técnico uniforme | Mismo STATE/handoff, orientación/checkpoint técnicos |
| Escrituras concurrentes | Parcial: locks atómicos nativos STATE, sin protección de intención obsoleta | Lock del wrapper + hash observado; checkpoints separados por sesión |

## Hooks y checkpoints

Agent Continuity registra **SessionStart, PreCompact, PostCompact, Stop, SessionEnd**; Codex añade **Interrupt**. No agrega UserPromptSubmit ni un checkpoint por herramienta. Claude mantiene el monitor/guards nativos en sus eventos apropiados. Cada hook técnico:

- Obtiene raíz Git/`.planning` dinámicamente; valida cwd y runtime.
- Guarda ID de sesión hasheado, runtime, fecha UTC, evento, rama/HEAD (null si todavía no hay commit), archivos y huella del estado Git, fase/plan/status, referencia/hash STATE y último resultado de pruebas **conocido para esa sesión**.
- No guarda contenidos de archivos, diffs, prompt, transcript, respuestas de herramientas ni variables de entorno. Filtra rutas habituales de credenciales; rechaza metadatos explícitos que parezcan secretos. El usuario debe aportar títulos/siguientes acciones cortos y no sensibles.
- Usa creación exclusiva de locks y temp+rename; un evento con los mismos metadatos es no-op. Los snapshots son referencias de recuperación, **no backups del contenido**.
- Falla abierto en modo hook y no llama al LLM, modifica archivos de producto ni reinicia sesiones. En CLI explícito devuelve errores accionables.

Los checkpoints viven en `.planning/.continuity/sessions/<hash>/checkpoint-<hash>.json`. Logs técnicos/transitorios y IDs quedan ignorados. Pruebas ausentes se representan con null, nunca como éxito. `test-result` registra una observación explícita (no ejecuta una prueba); `verify-environment.cjs` ejecuta los checks y registra su exit code observado. Su evidencia es un reporte explícito del verificador, con fecha/label.

## Thresholds y límites

`.planning/config.json` configura **25% restante (75% usado)** y **15% restante (85% usado)**. GSD aplica debounce y escalada; status line recibe `context_window.remaining_percentage` del runtime. El adapter crea un checkpoint únicamente cuando la salida del monitor contiene WARNING/CRITICAL. No reinterpreta tokens ni porcentajes.

En crítico, el propio GSD puede actualizar una única breadcrumb `Stopped at` mediante su `state record-session` atómico. Esa escritura nativa puede invalidar el hash observado de un escritor: reanudar/revisar antes de continuar. Los hooks personalizados nunca escriben estado semántico.

Codex usa compactación/ciclo de vida; no hay monitor porcentual. Las pruebas de threshold/compactación son señales sintéticas con el formato oficial y monitor real, sin forzar `/compact`/`/clear`. No se reinicia automáticamente ninguna sesión. El camino normal no añade LLMs.

## Tareas, progreso, pausa y reanudación

```powershell
node scripts/agent-continuity.cjs resume --runtime codex --session mi-sesion
node scripts/agent-continuity.cjs task --session mi-sesion --title "Revisar quality gates" --phase 1 --next "Leer el plan 01-01"
node .codex/gsd-core/bin/gsd-tools.cjs list-todos
node .codex/gsd-core/bin/gsd-tools.cjs progress json
node scripts/agent-continuity.cjs checkpoint --runtime codex --session mi-sesion
```

Capture registra un todo en `.planning/todos/pending`, no cambia la tarea activa. La tarea activa está en el plan/handoff; no duplicar tareas de un plan como todos. Puede usarse el workflow de captura nativo de GSD cuando se necesite su clasificación interactiva. Para progreso verificado usar SUMMARY tras ejecutar realmente el plan; bloqueos/decisiones usan el CLI state. Ejemplo de modificación protegida:

```powershell
node scripts/agent-continuity.cjs resume --runtime codex --session mi-sesion
node scripts/agent-continuity.cjs gsd --runtime codex --session mi-sesion -- state update Status "Blocked"
# Tras revisar el todo y su resultado real:
node scripts/agent-continuity.cjs gsd --runtime codex --session mi-sesion -- todo complete nombre-del-todo.md
```

Pausa semántica: `$gsd-pause-work` en Codex o `/gsd-pause-work` en Claude; prepara **los formatos nativos** HANDOFF.json y .continue-here.md. `planning.commit_docs=false` y AGENTS prohíben los commits automáticos; omitir los pasos Git sugeridos por workflows.

Reanudar: iniciar desde la raíz, correr `resume` con runtime e ID estable, revisar Git/estado/handoff y comprobar pruebas/archivos antes de `$gsd-resume-work` o `/gsd-resume-work`. El handoff nativo es de consumo único; GSD puede eliminarlo tras una reanudación exitosa. Cambiar de runtime no requiere copiar conversaciones; ambos leen `.planning/STATE.md` y el mismo handoff. El estado técnico de cada sesión permanece separado.

## Concurrencia y recuperación

`resume` registra el hash de los artefactos de planificación observados. La operación `gsd` obtiene un lock exclusivo, rechaza `STALE_STATE` si cambió la planificación y utiliza el writer nativo. Dos sesiones tienen directorios técnicos independientes. Hooks/checkpoints no actualizan el hash observado de un escritor salvo al reorientarse explícitamente mediante resume/SessionStart.

**Límite:** esta protección aplica al wrapper; las escrituras directas a PLAN/HANDOFF/STATE y los comandos GSD ejecutados fuera de él pueden bypassarla. Mantener un solo escritor semántico, volver a leer antes de editar y revisar diferencias. No se afirma coordinación distribuida ni protección automática de cualquier editor.

Si un proceso termina abruptamente, los checkpoints completos previos permanecen válidos; un `.tmp` incompleto no se consume. Un lock auxiliar abandonado no se roba automáticamente. Leer su PID/fecha, comprobar con `Get-Process -Id <pid>` y confirmar que no hay una operación activa; después retirar **solo** ese lock con `Remove-Item -LiteralPath` dentro de `.planning/.continuity`. Si hay duda, conservarlo. Nunca eliminar locks nativos de Git/GSD a ciegas. Recuperar el snapshot, revisar Git y volver a resume; no sobrescribir estado reciente con un checkpoint viejo.

## Versionado, deshabilitación y desinstalación

Versionar instrucciones, scripts/pruebas, config local portable, `.tools/package*.json`, documentos y artefactos GSD de planificación. Assets GSD generados, node_modules, home confinado, checkpoints/IDs/logs y `settings.local.json` están en `.gitignore`. No hay commits en esta entrega.

Deshabilitar: en `/hooks` de Codex desactivar las entradas Agent Continuity. En `.claude/settings.json` retirar solo las entradas `agent-continuity.cjs`; reemplazar `claude-context.cjs` por el monitor nativo `.claude/hooks/gsd-context-monitor.js` para conservar sus advertencias. Reiniciar el runtime. Los comandos explícitos siguen disponibles.

Desinstalar: guardar un checkpoint/handoff; retirar de ambas configuraciones únicamente los hooks que referencian estos scripts o assets GSD y la status line GSD; ejecutar el instalador oficial local:

```powershell
node --require ./scripts/gsd-local-home.cjs .tools/node_modules/@opengsd/gsd-core/bin/install.js --claude --codex --local --uninstall --no-legacy-cleanup
```

Conservar `.planning/` y los documentos aprobados. Quitar manualmente la dependencia de `.tools` si ya no se necesita. Este procedimiento está documentado, no se ejecutó sobre la instalación final. Rehabilitación: `node scripts/install-gsd.cjs`, verificar y revisar confianza.

## Troubleshooting

- `PROJECT_NOT_FOUND`: arrancar dentro del repo con Git + `.planning`; no usar otro repositorio.
- `STALE_STATE`: ejecutar resume, revisar cambios y repetir la mutación conscientemente.
- `BUSY_LOCK`: esperar/reintentar; si quedó abandonado, aplicar la recuperación segura anterior.
- Sin advertencias Claude: verificar status line, cwd raíz, métricas disponibles y configuración; no fabricar el porcentaje.
- Sin hooks Codex: revisar confianza del proyecto y definiciones en `/hooks`. La sesión actual no recarga necesariamente assets instalados durante ella; abrir una nueva sesión.
- EPERM en `.codex`: el sandbox protege esa carpeta; la instalación local necesita la autorización normal del host. No cambiar protecciones globales.
- `validate health` devuelve `degraded`: **W010** reconoce 13 roles opcionales ausentes del perfil standard; **W019** no reconoce INGEST-CONFLICTS.md aunque el workflow oficial lo produce. Se mantienen explícitos; no instalar full ni borrar el reporte para ocultarlos. Sin errores de planificación. I001 refleja seis planes todavía sin SUMMARY, como corresponde.

## Verificación y benchmarks

`node scripts/verify-environment.cjs`: suite A–I y 21 checks de entorno. Incluye umbral nativo → checkpoint técnico, los seis esquemas/estructuras de plan, roadmap/consistencia, snapshot nativo, nueve hashes preservados, hooks sin duplicados y ausencia de producto. `VERIFICATION.json` conserva el resultado final y exit code; no se ejecutaron comandos de producto previstos en PLAN.

`node scripts/probe-runtimes.cjs`: inicialización real sin turno LLM; Codex y Claude descubren los 23 comandos. No equivale a ejecutar los workflows especializados ni a confiar los hooks de Codex.

`node scripts/benchmark-hooks.cjs`: 15 muestras por camino, tras una de warmup, incluye arranque de procesos y árbol Git sin commits. Medición final ejecutada sin el verificador/probe en paralelo. Resultado exacto en `HOOK_BENCHMARK.json`. Medianas observadas: Node vacío 67.26 ms; checkpoint repetido 335.34 ms (p95 857.82 ms); SessionStart técnico 569.23 ms; monitor Claude sin métrica 71.81 ms; adapter Claude sin métrica 176.66 ms; PowerShell vacío 229.91 ms; invocación Windows Stop desde PowerShell 836.60 ms (p95 885.06 ms). La última incluye el launcher PowerShell y el shell de la prueba; no es un benchmark universal del runtime. Los checkpoints cuestan cientos de ms en eventos acotados; no se ejecutan por operación trivial. El adapter agrega aproximadamente 105 ms al monitor nativo en el camino sin métricas observado.

Pendiente: revisión/confianza nativa de hooks Codex, validación interactiva de pausa/reanudación/compactación real y de métricas entregadas por una sesión Claude viva. Contratos/eventos simulados, monitor nativo y descubrimiento real están verificados; **no se declara completada la activación automática de Codex ni un ensayo live de compactación**.

## Plan P0 y primera acción posterior

Único roadmap: `.planning/ROADMAP.md`, seis fases dependientes: Foundation → Core Domain → Job Ingestion → Job Intelligence → Dashboard → End-to-End Validation. Cada PLAN nativo define tres tareas, módulos previstos, dependencias, aceptación, pruebas y DoD. REQUIREMENTS contiene los 14 IDs P0 del backlog más siete requisitos habilitadores, todos pendientes.

Estado: `planning`, 0/6 planes completados, handoff nativo preparado para revisión. Primer incremento posterior: fase 01, tarea 1 de `01-01-PLAN.md`: crear npm workspaces `apps/web` y el paquete FastAPI `apps/api`, documentando entorno Windows y verificando compatibilidad de versiones antes de fijarlas. **Requiere una nueva instrucción de implementación; no se ejecutó.**
