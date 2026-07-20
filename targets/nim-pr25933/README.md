# Nim PR 25933 QUERY Target

This target is pinned to Caner's HTTP QUERY PR head:

`a233362101230b5930c5fa0005980973d3ab3627`

Run:

```bash
scripts/run-nim-pr25933.sh
```

The script clones Nim under `.work/Nim`, fetches PR `25933`, builds the pinned
compiler, compiles the fixtures, starts a local `asynchttpserver` target on
`127.0.0.1:18133`, and writes receipts under:

- `receipts/nim-pr25933-server/`
- `receipts/nim-pr25933-client/`

The target validates QUERY as both a server-side request method and a sync/async
HTTP client method. It also records redirect behavior, chunked QUERY body
parsing, and `Expect: 100-continue` behavior.
