# Ledger Query Target

This target runs Keshav's Ledger Query implementation at commit
`e60d86d978b212e2b7794b7d6cdb8bf0b03b49c2`.

It verifies the generic HTTP QUERY behavior and the implementation-specific
ledger safety claims:

- Redis cache keys include method, path, and request-body hash.
- Two different QUERY bodies on the same URI do not collide.
- Repeating body A after body B returns body A.
- Account balance, ledger entry count, and account count do not change during
  QUERY.
- PostgreSQL read-only pool rejects writes in the query path.

Run:

```sh
scripts/run-ledger-query.sh
```
