# Generated Interoperability Matrix

Generated from `receipts/**/receipt.json`.

| Profile | Row | ayder-local | kevincii-http-query-client | laravel12-apache-generic | query-suite-example-live |
|---|---|---:|---:|---:|---:|
| Core | Native QUERY with JSON body | PASS | Pending | PASS | PASS |
| Core | Supported Content-Type accepted | PASS | Pending | PASS | PASS |
| Core | Unsupported Content-Type rejected | PASS | Pending | OBSERVED | PASS |
| Core | Missing Content-Type handled | OBSERVED | Pending | OBSERVED | OBSERVED |
| Core | Accept-Query advertised | PASS | Pending | NOT_SUPPORTED | PASS |
| Core | POST method override | NOT_SUPPORTED | Pending | NOT_SUPPORTED | PASS |
| Core | Identical request repeatability | PASS | Pending | PASS | PASS |
| Representation | ETag advertised | PASS | Pending | NOT_SUPPORTED | PASS |
| Representation | Conditional revalidation -> 304 | PASS | Pending | NOT_SUPPORTED | PASS |
| Representation | Content-Location advertised | NOT_SUPPORTED | Pending | NOT_SUPPORTED | PASS |
| Representation | Validator strength | OBSERVED | Pending | OBSERVED | OBSERVED |
| Representation | Accept-Encoding: identity probe | OBSERVED | Pending | OBSERVED | OBSERVED |
| Semantic identity | Equivalent JSON -> same identity | PASS | Pending | NOT_SUPPORTED | NOT_SUPPORTED |
| Safety | No unintended side effects | OBSERVED | Pending | OBSERVED | OBSERVED |
| Ayder safety | No committed-offset advance | PASS | Pending | NOT_APPLICABLE | NOT_APPLICABLE |
| Ayder safety | No broker-state mutation | PASS | Pending | NOT_APPLICABLE | NOT_APPLICABLE |
| Ayder safety | Bounded snapshot stability | PASS | Pending | NOT_APPLICABLE | NOT_APPLICABLE |
| Ayder safety | Rate-limit headers sane | PASS | Pending | NOT_APPLICABLE | NOT_APPLICABLE |
| Kevinci client | Native QUERY first | Pending | PASS | Pending | Pending |
| Kevinci client | JSON request preserved | Pending | PASS | Pending | Pending |
| Kevinci client | JSON response parsed | Pending | PASS | Pending | Pending |
| Kevinci client | Accept-Query observed | Pending | PASS | Pending | Pending |
| Kevinci client | ETag observed | Pending | PASS | Pending | Pending |
| Kevinci client | Conditional wire 304 | Pending | PASS | Pending | Pending |
| Kevinci client | Conditional API surface | Pending | OBSERVED | Pending | Pending |
| Kevinci client | QUERY to POST fallback | Pending | PASS | Pending | Pending |
| Kevinci client | POST body preserved | Pending | PASS | Pending | Pending |
| Kevinci client | QUERY to POST to GET fallback | Pending | PASS | Pending | Pending |
| Kevinci client | GET params serialized | Pending | PASS | Pending | Pending |
| Kevinci client | Timeout enforced | Pending | PASS | Pending | Pending |
| Kevinci client | External abort enforced | Pending | PASS | Pending | Pending |
| Kevinci client | Abort error surface | Pending | OBSERVED | Pending | Pending |
