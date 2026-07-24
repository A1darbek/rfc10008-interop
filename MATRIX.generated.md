# Generated Interoperability Matrix

Generated from `receipts/**/receipt.json`.

| Profile | Row | ayder-local | laravel12-apache-generic | laravel13-query-comparison | query-suite-example-live |
|---|---|---:|---:|---:|---:|
| Core | Native QUERY with JSON body | PASS | PASS | PASS | PASS |
| Core | Supported Content-Type accepted | PASS | PASS | PASS | PASS |
| Core | Unsupported Content-Type rejected | PASS | OBSERVED | OBSERVED | PASS |
| Core | Missing Content-Type handled | OBSERVED | OBSERVED | OBSERVED | OBSERVED |
| Core | Accept-Query advertised | PASS | NOT_SUPPORTED | NOT_SUPPORTED | PASS |
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
| Laravel 13 | Apache forwards QUERY | Pending | Pending | PASS | Pending |
| Laravel 13 | QUERY reaches Laravel application | Pending | Pending | PASS | Pending |
| Laravel 13 | request()->all parses QUERY body | Pending | Pending | PASS | Pending |
| Laravel 13 | QUERY marked safe/idempotent/cacheable | Pending | Pending | PASS | Pending |
| Laravel 13 | Native router registration | Pending | Pending | PASS | Pending |
| Laravel 13 | Route::query helper | Pending | Pending | NOT_SUPPORTED | Pending |
| Laravel 13 | Http::query source present | Pending | Pending | PASS | Pending |
| Laravel 13 | Http::query JSON-default usage | Pending | Pending | PASS | Pending |
| Laravel 13 | Form QUERY alternative documented | Pending | Pending | OBSERVED | Pending |
| Laravel 13 | queryJson helper | Pending | Pending | NOT_SUPPORTED | Pending |
| Laravel 13 | CORS preflight observed | Pending | Pending | OBSERVED | Pending |
| Laravel 13 | PHP CLI server behavior | Pending | Pending | OBSERVED | Pending |
