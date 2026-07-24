# Oharu product-search target

This target exercises Oharu's independent RFC 10008 product-search server at
implementation commit `057d9effae1bc767eaef03fc6cdc1b774cd735ad`.

The adapter starts from a fresh server process and sends this exact sequence:

1. request A: cache `MISS`
2. identical request A: cache `HIT`
3. request B on the same URI: cache `MISS`
4. request A again: cache `HIT`
5. semantically equivalent, reordered request A: a distinct byte-key `MISS`

It also verifies missing `Content-Type` (`400`), unsupported media type (`415`
with `Accept-Query`), malformed JSON (`422`), and QUERY-aware OPTIONS/CORS
discovery.

The implementation hashes the raw request-body bytes. Reordered equivalent
JSON is therefore recorded as observed byte-key behavior, while
`semantic.equivalent_json_same_identity` is `NOT_SUPPORTED`. ETag,
conditional `304`, and Content-Location are also `NOT_SUPPORTED`.

## Run

From the repository root:

```sh
./scripts/run-oharu-product-search.sh
```

The script checks out the pinned implementation, creates an isolated Python
environment under `.work/`, launches the server on `127.0.0.1:18082`, writes
JSON and text receipts, regenerates the matrix, and exits non-zero if any
assertion fails. Override the port with `OHARU_PORT`.

Generated evidence:

- `receipts/oharu-product-search/receipt.json`
- `receipts/oharu-product-search/receipt.txt`
- `receipts/oharu-product-search/cache.json`
- `receipts/oharu-product-search/cache.txt`
