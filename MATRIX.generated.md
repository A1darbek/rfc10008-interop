# Generated Interoperability Matrix

Generated from `receipts/**/receipt.json`.

| Profile | Row | ayder-local | laravel12-apache-generic | oharu-product-search | query-suite-example-live |
|---|---|---:|---:|---:|---:|
| Core | Native QUERY with JSON body | PASS | PASS | PASS | PASS |
| Core | Supported Content-Type accepted | PASS | PASS | PASS | PASS |
| Core | Unsupported Content-Type rejected | PASS | OBSERVED | PASS | PASS |
| Core | Missing Content-Type handled | OBSERVED | OBSERVED | PASS | OBSERVED |
| Core | Accept-Query advertised | PASS | NOT_SUPPORTED | PASS | PASS |
| Core | POST method override | NOT_SUPPORTED | NOT_SUPPORTED | NOT_SUPPORTED | PASS |
| Core | Identical request repeatability | PASS | PASS | PASS | PASS |
| Representation | ETag advertised | PASS | NOT_SUPPORTED | NOT_SUPPORTED | PASS |
| Representation | Conditional revalidation -> 304 | PASS | NOT_SUPPORTED | NOT_SUPPORTED | PASS |
| Representation | Content-Location advertised | NOT_SUPPORTED | NOT_SUPPORTED | NOT_SUPPORTED | PASS |
| Representation | Validator strength | OBSERVED | OBSERVED | OBSERVED | OBSERVED |
| Representation | Accept-Encoding: identity probe | OBSERVED | OBSERVED | OBSERVED | OBSERVED |
| Semantic identity | Equivalent JSON -> same identity | PASS | NOT_SUPPORTED | NOT_SUPPORTED | NOT_SUPPORTED |
| Safety | No unintended side effects | OBSERVED | OBSERVED | OBSERVED | OBSERVED |
| Ayder safety | No committed-offset advance | PASS | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE |
| Ayder safety | No broker-state mutation | PASS | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE |
| Ayder safety | Bounded snapshot stability | PASS | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE |
| Ayder safety | Rate-limit headers sane | PASS | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE |
| Oharu product search | Malformed JSON -> 422 | Pending | Pending | PASS | Pending |
| Oharu product search | OPTIONS and QUERY-aware CORS | Pending | Pending | PASS | Pending |
| Oharu product search | First body cache MISS | Pending | Pending | PASS | Pending |
| Oharu product search | Identical body cache HIT | Pending | Pending | PASS | Pending |
| Oharu product search | Different body cache MISS | Pending | Pending | PASS | Pending |
| Oharu product search | Return to first body cache HIT | Pending | Pending | PASS | Pending |
| Oharu product search | Exact replay response | Pending | Pending | PASS | Pending |
| Oharu product search | No cross-body collision | Pending | Pending | PASS | Pending |
| Oharu product search | Cache key includes raw body | Pending | Pending | PASS | Pending |
| Oharu product search | Reordered JSON byte-key identity | Pending | Pending | OBSERVED | Pending |
