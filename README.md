# RFC 10008 Interoperability

An evidence-first interoperability project for the HTTP QUERY method defined by
RFC 10008.

This repository runs portable checks against independent HTTP QUERY
implementations and publishes machine-readable and human-readable receipts.

It is not an official certification suite.

## Principles

- Test observable behavior.
- Separate RFC requirements from optional capabilities.
- Preserve implementation-specific boundaries.
- Record evidence rather than hiding infrastructure differences.
- Never classify unsupported optional behavior as a conformance failure.

## Result States

- `PASS` — the declared expectation was observed.
- `FAIL` — the implementation claims the behavior, but the observation differed.
- `NOT_SUPPORTED` — the implementation intentionally does not expose the capability.
- `NOT_APPLICABLE` — the check does not apply to this target.
- `UNVERIFIED` — the behavior has not yet been tested in the required environment.
- `OBSERVED` — evidence was recorded, but the row is not pass/fail.

## Run

Ayder, assuming Ayder is available on `localhost:1109`:

```bash
python3 runner/run.py --target targets/ayder/target.json --output receipts/ayder
```

Dan's live Cloudflare Workers example:

```bash
python3 runner/run.py   --target targets/query-suite-example/target.json   --output receipts/query-suite-example
```

Generate a matrix from receipts:

```bash
python3 runner/render_matrix.py
```

See [MATRIX.generated.md](./MATRIX.generated.md) for the latest recorded run when
receipts have been generated locally or in CI.

## Targets

- Ayder: <https://github.com/A1darbek/ayder>
- query-suite-example: <https://github.com/DanMat/query-suite-example>

## Optional Capabilities

Semantic query identity is intentionally optional. For example, canonical JSON
fingerprinting can be useful for cache identity, but RFC 10008 interoperability
does not require every implementation to canonicalize semantically equivalent
JSON bodies.

## Target Contract

Target files use JSON so the runner remains dependency-free. `schema_version`
`0.2` separates declared capabilities from target-specific expectations:

```json
{
  "schema_version": "0.2",
  "capabilities": {
    "accept_query": true,
    "etag": true,
    "conditional_revalidation": true,
    "content_location": false,
    "semantic_query_identity": false,
    "method_override": false,
    "cors_preflight": false,
    "cache_observability": false,
    "implementation_safety_receipt": false
  },
  "expectations": {
    "native_query_status": 200,
    "supported_content_type_status": 200,
    "unsupported_content_type_status": 415,
    "missing_content_type_mode": "observe"
  }
}
```

Declared capabilities that are observed produce `PASS`. Declared capabilities
that are absent produce `FAIL`. Undeclared optional capabilities produce
`NOT_SUPPORTED`. Expectation modes are `assert`, `observe`, `not_supported`,
and `not_applicable`.
