"""Deterministic OpenAPI and dependency-free TypeScript type generation."""

import json

from rolekai.main import app


def schema_text():
    return json.dumps(app.openapi(), sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def ts_type(schema):
    if "$ref" in schema:
        return "components[" + json.dumps(schema["$ref"].split("/")[-1]) + "]"
    if "const" in schema:
        return json.dumps(schema["const"])
    if "enum" in schema:
        return " | ".join(json.dumps(item) for item in schema["enum"])
    for key, separator in (("anyOf", " | "), ("oneOf", " | "), ("allOf", " & ")):
        if key in schema:
            return "(" + separator.join(ts_type(item) for item in schema[key]) + ")"
    kind = schema.get("type")
    if kind == "array":
        return "Array<" + ts_type(schema.get("items", {})) + ">"
    if kind == "object" or "properties" in schema:
        properties = schema.get("properties", {})
        required = set(schema.get("required", []))
        fields = [
            json.dumps(name) + ("" if name in required else "?") + ": " + ts_type(value) + ";"
            for name, value in sorted(properties.items())
        ]
        additional = schema.get("additionalProperties", True)
        if additional is not False:
            fields.append(
                "[key: string]: "
                + (ts_type(additional) if isinstance(additional, dict) else "unknown")
                + ";"
            )
        return "{ " + " ".join(fields) + " }"
    return {
        "string": "string",
        "integer": "number",
        "number": "number",
        "boolean": "boolean",
        "null": "null",
    }.get(kind, "unknown")


def types_text():
    schema = app.openapi()
    lines = [
        "// Generated from Rolekai OpenAPI. Run contracts:export; do not edit.",
        "export interface components {",
    ]
    for name, definition in sorted(schema["components"]["schemas"].items()):
        lines.append("  " + json.dumps(name) + ": " + ts_type(definition) + ";")
    lines.extend(["}", "", "export interface paths {"])
    for path, methods in sorted(schema["paths"].items()):
        lines.append("  " + json.dumps(path) + ": {")
        for method, operation in sorted(methods.items()):
            lines.append("    " + json.dumps(method) + ": {")
            params = operation.get("parameters", [])
            for location in ("path", "query", "header"):
                selected = [p for p in params if p["in"] == location]
                if selected:
                    lines.append(
                        "      "
                        + location
                        + ": "
                        + ts_type(
                            {
                                "type": "object",
                                "properties": {p["name"]: p["schema"] for p in selected},
                                "required": [p["name"] for p in selected if p.get("required")],
                                "additionalProperties": False,
                            }
                        )
                        + ";"
                    )
            body = operation.get("requestBody", {}).get("content", {}).get("application/json")
            if body:
                lines.append("      body: " + ts_type(body["schema"]) + ";")
            lines.append("      responses: {")
            for status, response in sorted(operation["responses"].items()):
                data = response.get("content", {}).get("application/json", {}).get("schema", {})
                lines.append("        " + json.dumps(status) + ": " + ts_type(data) + ";")
            lines.extend(["      };", "    };"])
        lines.append("  };")
    lines.append("}")
    return "\n".join(lines) + "\n"
