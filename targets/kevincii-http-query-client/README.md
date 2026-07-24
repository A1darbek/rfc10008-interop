# Kevinci HTTP QUERY client target

This target exercises `@kevincii/http-query-client` from
`Kevinci/http-query` at commit
`7fb3f7c4ff8b66a5bfd6678006e198ba3d18e647`.

The native section runs against Ayder commit
`2ddb6e346194c445445b04a4ffa5d1f9f700eaf2` and uses middleware as the
transport observation layer. It proves:

- the successful native wire trace is exactly `QUERY`
- the JSON request is preserved and the JSON response is parsed
- `Accept-Query` and `ETag` are visible after the response
- replaying the ETag produces wire status `304`
- the public API surfaces that non-2xx response as `HttpError`

The local fallback fixture independently exercises:

- `QUERY` success with no additional request
- `QUERY -> POST` on `405`, preserving the JSON body
- `QUERY -> POST -> GET` on consecutive `405` responses, serializing the
  request body into query parameters

The timeout fixture records the typed `TimeoutError` and observes the exact
external-abort error surface.

`fallback: null` is not described as disabling every fallback. The pinned
resolver always appends GET as its final safety net; native transport is proved
by the observed successful trace being exactly `[QUERY]`.

## Run

From the repository root:

```sh
./scripts/run-kevincii-http-query-client.sh
```

The script checks out both pinned repositories, installs the package-level
example with `npm ci`, runs its typecheck, starts a fresh Ayder container, runs
all three fixtures, writes sanitized receipts, and regenerates the matrix.
