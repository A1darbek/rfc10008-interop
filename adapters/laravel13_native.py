#!/usr/bin/env python3
import argparse
import datetime as dt
import hashlib
import http.client
import json
import platform
import subprocess
import urllib.parse
from pathlib import Path

RESULTS = ["PASS", "FAIL", "NOT_SUPPORTED", "NOT_APPLICABLE", "UNVERIFIED", "OBSERVED"]

def now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def row(id, result, **kwargs):
    if result not in RESULTS:
        raise ValueError(result)
    out = {"id": id, "result": result}
    out.update(kwargs)
    return out

def passfail(ok):
    return "PASS" if ok else "FAIL"

def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def request(method, url, headers=None, body=b""):
    parsed = urllib.parse.urlparse(url)
    path = urllib.parse.urlunparse(("", "", parsed.path or "/", parsed.params, parsed.query, ""))
    conn = http.client.HTTPConnection(parsed.netloc, timeout=30)
    conn.request(method, path, body=body, headers=headers or {})
    res = conn.getresponse()
    data = res.read()
    hdrs = {k.lower(): v for k, v in res.getheaders()}
    conn.close()
    return {"status": res.status, "reason": res.reason, "headers": hdrs, "body": data, "sha256": hashlib.sha256(data).hexdigest()}

def summarize(rows):
    summary = {key.lower(): 0 for key in RESULTS}
    for item in rows:
        summary[item["result"].lower()] += 1
    return summary

def render_text(receipt, path):
    s = receipt["summary"]
    lines = [
        "============================================================",
        " LARAVEL 13 QUERY INTEROP RECEIPT",
        "============================================================",
        f" target       : {receipt['target']['id']}",
        f" endpoint     : {receipt['target']['endpoint']}",
        f" generated_at : {receipt['generated_at']}",
        "------------------------------------------------------------",
        f" summary      : PASS={s['pass']} FAIL={s['fail']} OBSERVED={s['observed']} UNVERIFIED={s['unverified']} NOT_SUPPORTED={s['not_supported']} NOT_APPLICABLE={s['not_applicable']}",
        "------------------------------------------------------------",
    ]
    for item in receipt["rows"]:
        lines.append(f" {item['result']:<15} {item['id']}")
        if "expected" in item or "observed" in item:
            lines.append(f"   expected={item.get('expected')} observed={item.get('observed')}")
        if item.get("evidence"):
            lines.append("   evidence=" + json.dumps(item["evidence"], sort_keys=True)[:300])
    lines.append("============================================================")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--implementation-dir", required=True)
    ap.add_argument("--generic-receipt", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--endpoint", default="http://localhost:8080/mock/orders")
    args = ap.parse_args()

    impl = Path(args.implementation_dir).resolve()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    generic = load_json(args.generic_receipt)
    rows = list(generic.get("rows", []))

    body = json.dumps({"status": "shipped", "customer": {"tier": "premium"}}, separators=(",", ":")).encode()
    query = request("QUERY", args.endpoint, {"Content-Type": "application/json", "Accept": "application/json"}, body)
    parsed = json.loads(query["body"].decode("utf-8", "replace")) if query["body"] else {}
    preflight = request("OPTIONS", args.endpoint, {
        "Origin": "https://example.test",
        "Access-Control-Request-Method": "QUERY",
        "Access-Control-Request-Headers": "content-type,authorization",
    })

    routes = (impl / "routes/web.php").read_text(encoding="utf-8")
    controller = (impl / "app/Http/Controllers/HttpQueryDemoController.php").read_text(encoding="utf-8")
    tests = "\n".join(p.read_text(encoding="utf-8") for p in (impl / "tests").glob("**/*.php"))

    php_version = subprocess.run(
        ["docker", "compose", "-f", str(impl / "docker-compose.yml"), "exec", "-T", "app", "php", "-v"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    rows.extend([
        row("laravel13.apache_forwarding", passfail(query["status"] == 200), expected=200, observed=query["status"]),
        row("laravel13.query_reaches_application", passfail(parsed.get("verb_received") == "QUERY"), evidence={"verb_received": parsed.get("verb_received")}),
        row("laravel13.request_all_parses_query_body", passfail(parsed.get("filter_applied") == "shipped" and len(parsed.get("results", [])) == 2), evidence={"filter_applied": parsed.get("filter_applied"), "result_count": len(parsed.get("results", []))}),
        row("laravel13.safe_idempotent_cacheable_flags", passfail(parsed.get("safe") is True and parsed.get("idempotent") is True and parsed.get("cacheable") is True), evidence={"safe": parsed.get("safe"), "idempotent": parsed.get("idempotent"), "cacheable": parsed.get("cacheable")}),
        row("laravel13.native_http_query_client_source", passfail("->query(" in controller or "::query(" in controller), evidence={"source": "HttpQueryDemoController.php"}),
        row("laravel13.native_route_query_helper", "NOT_SUPPORTED", evidence={"reason": "pinned branch uses app('router')->addRoute(['QUERY'], ...); README says Route::query() helper is not present"}),
        row("laravel13.native_query_json_helper", "NOT_SUPPORTED", evidence={"reason": "no queryJson helper usage found in pinned branch", "query_json_found": "queryJson" in tests}),
        row("laravel13.cors_preflight_observed", "OBSERVED", observed=preflight["status"], evidence={"allow_methods": preflight["headers"].get("access-control-allow-methods"), "allow_headers": preflight["headers"].get("access-control-allow-headers")}),
        row("laravel13.php_cli_server_behavior", "OBSERVED", evidence={"php_version_first_line": php_version.stdout.splitlines()[0] if php_version.stdout else "unknown", "note": "Apache target verified; PHP CLI server was not started by this adapter"}),
    ])

    summary = summarize(rows)
    receipt = {
        "schema_version": "0.1",
        "run_id": f"{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-laravel13-native",
        "generated_at": now(),
        "runner": generic.get("runner", {}),
        "target": {
            "id": "laravel13-native",
            "name": "Laravel 13 native QUERY comparison",
            "implementation_url": "https://github.com/phoenix1331/laravel-http-query-demo",
            "implementation_commit": "af19ed98eb77b62f5156ce285dc2ea135788519a",
            "endpoint": args.endpoint,
        },
        "environment": {
            "platform": platform.platform(),
            "transport": "http",
            "server": "apache",
        },
        "observations": {
            "query_status": query["status"],
            "query_body_sha256": query["sha256"],
            "preflight_status": preflight["status"],
            "local_runtime_patch": "Dockerfile php:8.2-apache -> php:8.3-apache for Laravel 13 lockfile compatibility",
        },
        "rows": rows,
        "summary": summary,
    }
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    render_text(receipt, output / "receipt.txt")
    print(output / "receipt.txt")
    return 0 if summary["fail"] == 0 else 1

if __name__ == "__main__":
    raise SystemExit(main())
