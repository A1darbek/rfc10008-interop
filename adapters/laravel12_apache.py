#!/usr/bin/env python3
import argparse, json, subprocess, urllib.parse, http.client
from pathlib import Path

RESULTS = ["PASS", "FAIL", "NOT_SUPPORTED", "NOT_APPLICABLE", "UNVERIFIED", "OBSERVED"]

def row(id, result, **kwargs):
    if result not in RESULTS:
        raise ValueError(result)
    out = {"id": id, "result": result}
    out.update(kwargs)
    return out

def request(method, url, headers=None, body=b""):
    headers = dict(headers or {})
    parsed = urllib.parse.urlparse(url)
    path = urllib.parse.urlunparse(("", "", parsed.path or "/", parsed.params, parsed.query, ""))
    conn = http.client.HTTPConnection(parsed.netloc, timeout=30)
    conn.request(method, path, body=body, headers=headers)
    res = conn.getresponse()
    data = res.read()
    hdrs = {k.lower(): v for k, v in res.getheaders()}
    conn.close()
    return {"status": res.status, "reason": res.reason, "headers": hdrs, "body": data}

def decode_json(data):
    try:
        return json.loads(data.decode("utf-8", "replace"))
    except Exception:
        return None

def docker_php_version(compose_file):
    try:
        out = subprocess.check_output(
            ["docker", "compose", "-f", compose_file, "exec", "-T", "app", "php", "-v"],
            text=True,
            stderr=subprocess.STDOUT,
            timeout=30,
        )
        return out.splitlines()[0] if out.splitlines() else out.strip()
    except Exception as exc:
        return f"unverified: {exc}"

def render_text(receipt, path):
    s = receipt["summary"]
    lines = [
        "============================================================",
        " LARAVEL 12 APACHE QUERY INFRASTRUCTURE RECEIPT",
        "============================================================",
        f" endpoint : {receipt['endpoint']}",
        f" summary  : PASS={s['pass']} FAIL={s['fail']} OBSERVED={s['observed']} UNVERIFIED={s['unverified']} NOT_SUPPORTED={s['not_supported']} NOT_APPLICABLE={s['not_applicable']}",
        "------------------------------------------------------------",
    ]
    for item in receipt["rows"]:
        lines.append(f" {item['result']:<15} {item['id']}")
        if item.get("evidence"):
            lines.append("   evidence=" + json.dumps(item["evidence"], sort_keys=True)[:300])
    lines.append("============================================================")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--endpoint", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--compose-file")
    args = ap.parse_args()

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    body = json.dumps({"status": "shipped", "customer": {"tier": "premium"}}, separators=(",", ":")).encode()
    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    query = request("QUERY", args.endpoint, headers, body)
    payload = decode_json(query["body"]) or {}
    result_statuses = sorted({item.get("status") for item in payload.get("results", []) if isinstance(item, dict)})

    rows = [
        row("laravel12.apache_query_reaches_application", "PASS" if payload.get("verb_received") == "QUERY" else "FAIL", evidence={"status": query["status"], "verb_received": payload.get("verb_received")}),
        row("laravel12.json_body_preserved", "PASS" if payload.get("filter_applied") == "shipped" and result_statuses == ["shipped"] else "FAIL", evidence={"filter_applied": payload.get("filter_applied"), "result_statuses": result_statuses}),
        row("laravel12.generic_route_dispatch", "PASS" if query["status"] == 200 and payload.get("verb_received") == "QUERY" else "FAIL", evidence={"status": query["status"]}),
        row("laravel12.native_route_helper", "NOT_APPLICABLE", evidence={"reason": "Laravel 12 target registers QUERY directly on the underlying router"}),
        row("laravel12.native_http_client_helper", "NOT_APPLICABLE", evidence={"reason": "Laravel 12 target uses generic Http::send(\"QUERY\") path"}),
    ]

    options_headers = {
        "Origin": "https://example.test",
        "Access-Control-Request-Method": "QUERY",
        "Access-Control-Request-Headers": "content-type,authorization",
    }
    options = request("OPTIONS", args.endpoint, options_headers)
    allow_methods = options["headers"].get("access-control-allow-methods", "")
    rows.append(row(
        "laravel12.cors_preflight_allows_query",
        "OBSERVED",
        evidence={"status": options["status"], "access_control_allow_methods": allow_methods},
    ))

    php_version = docker_php_version(args.compose_file) if args.compose_file else "unverified"
    rows.append(row(
        "laravel12.php_runtime_observed",
        "OBSERVED",
        evidence={
            "runtime": php_version,
            "request_path": "Apache mod_php",
            "known_future_cli_support": {"php_version": "8.6", "php_src_pr": 22615},
        },
    ))
    rows.append(row(
        "laravel12.php_cli_server_behavior",
        "UNVERIFIED",
        evidence={
            "reason": "PHP built-in development server is not executed by this Apache target",
        },
    ))

    summary = {key.lower(): 0 for key in RESULTS}
    for item in rows:
        summary[item["result"].lower()] += 1

    receipt = {"schema_version": "0.1", "target": "laravel12-apache-generic", "endpoint": args.endpoint, "rows": rows, "summary": summary}
    (output / "infrastructure.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    render_text(receipt, output / "infrastructure.txt")
    print(output / "infrastructure.txt")
    return 0 if summary["fail"] == 0 else 1

if __name__ == "__main__":
    raise SystemExit(main())
