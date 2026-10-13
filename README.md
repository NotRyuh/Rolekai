# Rolekai

Descubrimiento de vacantes respaldado por evidencia y seguimiento manual explícito de postulaciones.

Monolito modular: Next.js/TypeScript, FastAPI/Pydantic y PostgreSQL. Fuentes P0: URL manual, Remotive y Greenhouse; sin envíos automáticos.

Foundation y Core Domain están aprobados. Job Ingestion tiene implementación y verificaciones locales satisfactorias; su revisión independiente y cierre de GSD siguen pendientes.

- [Continuar desde otra máquina](HANDOFF.md)
- [Preparación del entorno](docs/development/SETUP.md)
- [Estado GSD](.planning/STATE.md)
- [Plan activo](.planning/phases/03-job-ingestion/03-01-PLAN.md)

El repositorio excluye credenciales, entornos instalados y datos locales. Regenerar `.env` en cada máquina; no renderizar HTML de fuentes sin sanitizar.
