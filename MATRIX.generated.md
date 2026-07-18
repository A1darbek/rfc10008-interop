# Generated Interoperability Matrix

Generated from `receipts/**/receipt.json`.

| Profile | Row | ayder-local | query-suite-example-live |
|---|---|---:|---:|
| Core | Native QUERY with JSON body | PASS | PASS |
| Core | Supported Content-Type accepted | PASS | PASS |
| Core | Unsupported Content-Type rejected | PASS | PASS |
| Core | Missing Content-Type handled | OBSERVED | OBSERVED |
| Core | Accept-Query advertised | PASS | PASS |
| Core | POST method override | NOT_APPLICABLE | PASS |
| Core | Identical request repeatability | PASS | PASS |
| Representation | ETag advertised | PASS | PASS |
| Representation | Conditional revalidation -> 304 | PASS | PASS |
| Representation | Content-Location advertised | NOT_SUPPORTED | PASS |
| Representation | Validator strength | OBSERVED | OBSERVED |
| Representation | Accept-Encoding: identity probe | OBSERVED | OBSERVED |
| Semantic identity | Equivalent JSON -> same identity | PASS | NOT_SUPPORTED |
| Safety | No unintended side effects | OBSERVED | OBSERVED |
| Ayder safety | No committed-offset advance | PASS | NOT_APPLICABLE |
| Ayder safety | No broker-state mutation | PASS | NOT_APPLICABLE |
| Ayder safety | Bounded snapshot stability | PASS | NOT_APPLICABLE |
| Ayder safety | Rate-limit headers sane | PASS | NOT_APPLICABLE |
