# Generated Interoperability Matrix

Generated from `receipts/**/receipt.json`.

| Profile | Row | ayder-local | ledger-query | query-suite-example-live |
|---|---|---:|---:|---:|
| Core | Native QUERY with JSON body | PASS | PASS | PASS |
| Core | Supported Content-Type accepted | PASS | PASS | PASS |
| Core | Unsupported Content-Type rejected | PASS | PASS | PASS |
| Core | Missing Content-Type handled | OBSERVED | OBSERVED | OBSERVED |
| Core | Accept-Query advertised | PASS | PASS | PASS |
| Core | POST method override | NOT_SUPPORTED | NOT_SUPPORTED | PASS |
| Core | Identical request repeatability | PASS | PASS | PASS |
| Representation | ETag advertised | PASS | NOT_SUPPORTED | PASS |
| Representation | Conditional revalidation -> 304 | PASS | NOT_SUPPORTED | PASS |
| Representation | Content-Location advertised | NOT_SUPPORTED | NOT_SUPPORTED | PASS |
| Representation | Validator strength | OBSERVED | OBSERVED | OBSERVED |
| Representation | Accept-Encoding: identity probe | OBSERVED | OBSERVED | OBSERVED |
| Semantic identity | Equivalent JSON -> same identity | PASS | NOT_SUPPORTED | NOT_SUPPORTED |
| Safety | No unintended side effects | OBSERVED | OBSERVED | OBSERVED |
| Ayder safety | No committed-offset advance | PASS | NOT_APPLICABLE | NOT_APPLICABLE |
| Ayder safety | No broker-state mutation | PASS | NOT_APPLICABLE | NOT_APPLICABLE |
| Ayder safety | Bounded snapshot stability | PASS | NOT_APPLICABLE | NOT_APPLICABLE |
| Ayder safety | Rate-limit headers sane | PASS | NOT_APPLICABLE | NOT_APPLICABLE |
| Ledger safety | Native QUERY | Pending | PASS | Pending |
| Ledger safety | JSON Content-Type accepted | Pending | PASS | Pending |
| Ledger safety | Unsupported Content-Type rejected | Pending | PASS | Pending |
| Ledger safety | OPTIONS advertises Accept-Query | Pending | PASS | Pending |
| Ledger safety | Body A first request MISS | Pending | PASS | Pending |
| Ledger safety | Body A repeat HIT | Pending | PASS | Pending |
| Ledger safety | Body B request MISS | Pending | PASS | Pending |
| Ledger safety | Body A after B HIT | Pending | PASS | Pending |
| Ledger safety | Cached response replay exact | Pending | PASS | Pending |
| Ledger safety | No cross-body cache collision | Pending | PASS | Pending |
| Ledger safety | Account balance unchanged by QUERY | Pending | PASS | Pending |
| Ledger safety | Entry count unchanged by QUERY | Pending | PASS | Pending |
| Ledger safety | Account count unchanged by QUERY | Pending | PASS | Pending |
| Ledger safety | Read-only pool rejects writes | Pending | PASS | Pending |
| Ledger safety | Project tests | Pending | PASS | Pending |
