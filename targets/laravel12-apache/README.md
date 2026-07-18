# Laravel 12 Through Apache Target

This target records Darren's Laravel 12 HTTP QUERY demo through Apache on
`localhost:8080`.

The implementation is pinned in `target.json`. The third-party application is
cloned locally under `implementations/laravel-http-query-demo` by the run script
and is not committed to this repository.

Run:

```bash
scripts/run-laravel12-apache.sh
```

The portable runner records generic HTTP QUERY behavior. The Laravel adapter
records framework and transport evidence such as Apache forwarding, JSON body
preservation, generic route dispatch, and CORS preflight behavior.

Current pinned observation: Apache forwards native `QUERY` and Laravel receives
the JSON body. The pinned app does not currently advertise `QUERY` in CORS
preflight response headers, so the adapter records that row as `OBSERVED`.
