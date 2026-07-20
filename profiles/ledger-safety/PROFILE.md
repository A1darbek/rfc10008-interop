# Ledger Safety Profile

This optional profile records implementation-specific evidence for
ledger-backed HTTP QUERY targets.

Rows:

- `ledger.native_query`
- `ledger.json_content_type`
- `ledger.unsupported_content_type_415`
- `ledger.accept_query_options`
- `ledger.cache_first_request_miss`
- `ledger.cache_identical_request_hit`
- `ledger.cache_different_body_miss`
- `ledger.cache_return_to_first_body_hit`
- `ledger.cache_exact_response_replay`
- `ledger.cache_no_cross_body_collision`
- `ledger.account_balance_unchanged`
- `ledger.entry_count_unchanged`
- `ledger.account_count_unchanged`
- `ledger.read_only_pool_rejects_write`
- `ledger.project_tests`

The cache collision sequence is:

1. Body A -> MISS -> result A
2. Body A -> HIT -> exact result A
3. Body B -> MISS -> result B
4. Body A -> HIT -> exact result A

The safety snapshot compares database state before and after QUERY execution.
