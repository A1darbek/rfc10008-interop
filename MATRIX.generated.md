# Generated Interoperability Matrix

Generated from `receipts/**/receipt.json`.

| Profile | Row | ayder-local | nim-pr25933-client | nim-pr25933-server | query-suite-example-live |
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
| Nim PR 25933 | HttpQuery method constant | Pending | PASS | Pending | Pending |
| Nim PR 25933 | Sync client preserves QUERY body | Pending | PASS | Pending | Pending |
| Nim PR 25933 | Async client preserves QUERY body | Pending | PASS | Pending | Pending |
| Nim PR 25933 | Server recognizes QUERY | Pending | PASS | Pending | Pending |
| Nim PR 25933 | Server records Content-Length | Pending | PASS | Pending | Pending |
| Nim PR 25933 | Server parses chunked body | Pending | PASS | Pending | Pending |
| Nim PR 25933 | Server handles Expect: 100-continue | Pending | PASS | Pending | Pending |
| Nim PR 25933 | Nim client observes Ayder ETag | Pending | PASS | Pending | Pending |
| Nim PR 25933 | Nim client conditional 304 | Pending | UNVERIFIED | Pending | Pending |
| Nim PR 25933 | 301 preserves QUERY method | Pending | PASS | Pending | Pending |
| Nim PR 25933 | 301 preserves body | Pending | PASS | Pending | Pending |
| Nim PR 25933 | 302 preserves QUERY method | Pending | PASS | Pending | Pending |
| Nim PR 25933 | 302 preserves body | Pending | PASS | Pending | Pending |
| Nim PR 25933 | 303 rewrites to GET | Pending | PASS | Pending | Pending |
| Nim PR 25933 | 303 strips body | Pending | PASS | Pending | Pending |
| Nim PR 25933 | 307 preserves QUERY method | Pending | PASS | Pending | Pending |
| Nim PR 25933 | 307 preserves body | Pending | PASS | Pending | Pending |
| Nim PR 25933 | 308 preserves QUERY method | Pending | PASS | Pending | Pending |
| Nim PR 25933 | 308 preserves body | Pending | PASS | Pending | Pending |
