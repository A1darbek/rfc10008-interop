# Laravel 13 QUERY Comparison Target

This target pins Darren's Laravel branch at
`af19ed98eb77b62f5156ce285dc2ea135788519a`.

Observed pieces in this branch:

- Apache forwards native `QUERY`.
- Laravel receives `QUERY /mock/orders`.
- Symfony HttpFoundation 7.4 / Laravel 13 parses the `QUERY` JSON body through
  `request()->all()`.
- Source contains first-class outbound `Http::query()` usage.

Current boundary:

- This branch does not expose `Route::query()`.
- This branch does not include a `queryJson()` test helper.
- The runner creates an ignored `.work` build context and writes a deterministic
  Dockerfile patch from `php:8.2-apache` to `php:8.3-apache` because the pinned
  Laravel 13 lockfile requires PHP `^8.3`.

Those rows are recorded as `NOT_SUPPORTED` rather than failures.
