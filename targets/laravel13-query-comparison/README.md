# Laravel 13 QUERY Comparison Target

This target pins Darren's Laravel branch at
`6dad5145eececc7c137b89c9cd4cce56fa83a8b5`.

Observed pieces in this branch:

- Apache forwards native `QUERY`.
- Laravel receives `QUERY /mock/orders`.
- Symfony HttpFoundation 7.4 / Laravel 13 parses the `QUERY` JSON body through
  `request()->all()`.
- Direct native route registration uses
  `app('router')->addRoute(['QUERY'], ...)`.
- The simple and complex outbound examples use plain `Http::query()`, relying
  on its JSON-by-default behavior.
- The README keeps `Http::asForm()->query()` as a documented alternative for
  form-encoded servers.

Current boundary:

- This branch does not expose a `Route::query()` convenience helper; direct
  router registration is the supported native approach.
- This branch does not include a `queryJson()` test helper.
- The runner creates an ignored `.work` build context and writes a deterministic
  Dockerfile patch from `php:8.2-apache` to `php:8.3-apache` because the pinned
  Laravel 13 lockfile requires PHP `^8.3`.

Those rows are recorded as `NOT_SUPPORTED` rather than failures.
