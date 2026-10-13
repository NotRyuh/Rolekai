import argparse
from pathlib import Path

from openapi_artifacts import schema_text, types_text

parser = argparse.ArgumentParser()
parser.add_argument("--snapshot", type=Path)
args = parser.parse_args()
target = Path(__file__).resolve().parents[1] / "packages/contracts"
files = [(args.snapshot or target / "openapi.json", schema_text())]
if args.snapshot is None:
    files.append((target / "api-types.ts", types_text()))
drift = any(
    not file.exists() or file.read_text(encoding="utf-8") != expected for file, expected in files
)
print(
    "Contract drift detected; run contracts:export and review changes"
    if drift
    else "Contracts match"
)
raise SystemExit(1 if drift else 0)
