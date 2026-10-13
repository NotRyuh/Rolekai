from pathlib import Path

from openapi_artifacts import schema_text, types_text

target = Path(__file__).resolve().parents[1] / "packages/contracts"
target.mkdir(parents=True, exist_ok=True)
(target / "openapi.json").write_text(schema_text(), encoding="utf-8", newline="\n")
(target / "api-types.ts").write_text(types_text(), encoding="utf-8", newline="\n")
print("Exported OpenAPI and TypeScript contracts")
