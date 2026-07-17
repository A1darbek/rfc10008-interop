# Generated Interoperability Matrix

Generated from `receipts/**/receipt.json`.

| Profile | Row | query-suite-example-live |
|---|---|---:|
| Core | Native QUERY with JSON body | PASS |
| Core | Supported Content-Type accepted | PASS |
| Core | Unsupported Content-Type rejected | PASS |
| Core | Missing Content-Type handled | OBSERVED |
| Core | Accept-Query advertised | PASS |
| Core | POST method override | PASS |
| Core | Identical request repeatability | PASS |
| Representation | ETag advertised | PASS |
| Representation | Conditional revalidation -> 304 | PASS |
| Representation | Content-Location advertised | PASS |
| Representation | Validator strength | OBSERVED |
| Representation | Accept-Encoding: identity probe | OBSERVED |
| Semantic identity | Equivalent JSON -> same identity | NOT_SUPPORTED |
| Safety | No unintended side effects | OBSERVED |
| Ayder safety | No committed-offset advance | NOT_APPLICABLE |
| Ayder safety | No broker-state mutation | NOT_APPLICABLE |
| Ayder safety | Bounded snapshot stability | NOT_APPLICABLE |
