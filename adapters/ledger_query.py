#!/usr/bin/env python3
import argparse
import datetime as dt
import hashlib
import http.client
import json
import os
import shutil
import platform
import subprocess
import urllib.parse
from pathlib import Path

RESULTS = ["PASS", "FAIL", "NOT_SUPPORTED", "NOT_APPLICABLE", "UNVERIFIED", "OBSERVED"]
ACCOUNT_ID = "11111111-1111-1111-1111-111111111111"

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

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

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
    return {"status": res.status, "reason": res.reason, "headers": hdrs, "body": data, "sha256": sha256(data)}

def run_cmd(cmd, cwd, env=None):
    merged = os.environ.copy()
    merged.update(env or {})
    proc = subprocess.run(cmd, cwd=cwd, env=merged, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return {"code": proc.returncode, "output": proc.stdout[-4000:]}

def go_cmd(impl, go_image, args):
    if shutil.which("go"):
        return ["go", *args]
    return [
        "docker",
        "run",
        "--rm",
        "--add-host",
        "host.docker.internal:host-gateway",
        "-v",
        f"{impl}:/src",
        "-w",
        "/src",
        "-e",
        "DATABASE_URL=postgres://ledger:ledger@host.docker.internal:5434/ledger",
        "-e",
        "REDIS_ADDR=host.docker.internal:6379",
        go_image,
        "go",
        *args,
    ]

def go_execution_metadata(impl, go_image):
    uses_local_go = bool(shutil.which("go"))
    result = run_cmd(go_cmd(impl, go_image, ["version"]), impl)
    metadata = {
        "go_execution": "local" if uses_local_go else "docker-fallback",
        "docker_image": None if uses_local_go else go_image,
        "go_version": result["output"].strip().splitlines()[-1] if result["output"].strip() else "",
    }
    if result["code"] != 0:
        metadata["go_version_error"] = result["output"]
    return metadata

def compose_cmd(compose_file, args):
    return ["docker", "compose", "-f", str(compose_file), *args]

def psql_scalar(compose_file, sql):
    proc = subprocess.run(
        compose_cmd(compose_file, ["exec", "-T", "postgres", "psql", "-U", "ledger", "-d", "ledger", "-tA", "-c", sql]),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )
    return proc.stdout.strip()

def snapshot(compose_file):
    return {
        "account_balance": int(psql_scalar(compose_file, f"SELECT balance_cents FROM accounts WHERE id = '{ACCOUNT_ID}'")),
        "ledger_entry_count": int(psql_scalar(compose_file, "SELECT count(*) FROM ledger_entries")),
        "account_count": int(psql_scalar(compose_file, "SELECT count(*) FROM accounts")),
    }

def flush_redis(compose_file):
    subprocess.run(compose_cmd(compose_file, ["exec", "-T", "redis", "redis-cli", "FLUSHDB"]), check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

def render_text(receipt, path):
    s = receipt["summary"]
    lines = [
        "============================================================",
        " LEDGER QUERY INTEROP RECEIPT",
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

def summarize(rows):
    summary = {key.lower(): 0 for key in RESULTS}
    for item in rows:
        summary[item["result"].lower()] += 1
    return summary

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--implementation-dir", required=True)
    ap.add_argument("--generic-receipt", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--endpoint", default="http://localhost:8080/transactions")
    ap.add_argument("--go-image", default=os.environ.get("GO_IMAGE", "golang@sha256:3aff6657219a4d9c14e27fb1d8976c49c29fddb70ba835014f477e1c70636647"))
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[1]
    impl = Path(args.implementation_dir).resolve()
    compose_file = impl / "docker-compose.yml"
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    generic = load_json(args.generic_receipt)
    rows = list(generic.get("rows", []))
    go_metadata = go_execution_metadata(impl, args.go_image)

    body_a = (root / "targets/ledger-query/request.json").read_bytes()
    body_b = (root / "targets/ledger-query/request-b.json").read_bytes()
    headers = {"Content-Type": "application/json"}

    flush_redis(compose_file)
    before = snapshot(compose_file)

    a1 = request("QUERY", args.endpoint, headers, body_a)
    a2 = request("QUERY", args.endpoint, headers, body_a)
    b1 = request("QUERY", args.endpoint, headers, body_b)
    a3 = request("QUERY", args.endpoint, headers, body_a)
    unsupported = request("QUERY", args.endpoint, {"Content-Type": "text/plain"}, b"not json")
    options = request("OPTIONS", args.endpoint)
    after = snapshot(compose_file)

    read_only = run_cmd(go_cmd(impl, args.go_image, ["test", "./internal/api", "-run", "TestReadOnlyPool_RejectsWrites", "-count=1"]), impl, {"DATABASE_URL": "postgres://ledger:ledger@localhost:5434/ledger"})
    project_tests = run_cmd(go_cmd(impl, args.go_image, ["test", "./...", "-race", "-p", "1"]), impl, {"DATABASE_URL": "postgres://ledger:ledger@localhost:5434/ledger"})

    rows.extend([
        row("ledger.native_query", passfail(a1["status"] == 200), expected=200, observed=a1["status"]),
        row("ledger.json_content_type", passfail(a1["status"] == 200), expected=200, observed=a1["status"]),
        row("ledger.unsupported_content_type_415", passfail(unsupported["status"] == 415), expected=415, observed=unsupported["status"]),
        row("ledger.accept_query_options", passfail(options["status"] == 204 and options["headers"].get("accept-query") == "application/json"), expected=204, observed=options["status"], evidence={"accept_query": options["headers"].get("accept-query")}),
        row("ledger.cache_first_request_miss", passfail(a1["headers"].get("x-cache") == "MISS"), evidence={"x_cache": a1["headers"].get("x-cache")}),
        row("ledger.cache_identical_request_hit", passfail(a2["headers"].get("x-cache") == "HIT"), evidence={"x_cache": a2["headers"].get("x-cache")}),
        row("ledger.cache_different_body_miss", passfail(b1["headers"].get("x-cache") == "MISS"), evidence={"x_cache": b1["headers"].get("x-cache")}),
        row("ledger.cache_return_to_first_body_hit", passfail(a3["headers"].get("x-cache") == "HIT"), evidence={"x_cache": a3["headers"].get("x-cache")}),
        row("ledger.cache_exact_response_replay", passfail(a1["sha256"] == a2["sha256"] == a3["sha256"]), evidence={"a1": a1["sha256"], "a2": a2["sha256"], "a3": a3["sha256"]}),
        row("ledger.cache_no_cross_body_collision", passfail(a1["sha256"] != b1["sha256"]), evidence={"body_a": a1["sha256"], "body_b": b1["sha256"]}),
        row("ledger.account_balance_unchanged", passfail(before["account_balance"] == after["account_balance"]), evidence={"before": before["account_balance"], "after": after["account_balance"]}),
        row("ledger.entry_count_unchanged", passfail(before["ledger_entry_count"] == after["ledger_entry_count"]), evidence={"before": before["ledger_entry_count"], "after": after["ledger_entry_count"]}),
        row("ledger.account_count_unchanged", passfail(before["account_count"] == after["account_count"]), evidence={"before": before["account_count"], "after": after["account_count"]}),
        row("ledger.read_only_pool_rejects_write", passfail(read_only["code"] == 0), evidence={"exit_code": read_only["code"], "output_tail": read_only["output"]}),
        row("ledger.project_tests", passfail(project_tests["code"] == 0), evidence={"exit_code": project_tests["code"], "output_tail": project_tests["output"]}),
    ])

    summary = summarize(rows)
    receipt = {
        "schema_version": "0.1",
        "run_id": f"{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-ledger-query",
        "generated_at": now(),
        "runner": generic.get("runner", {}),
        "target": {
            "id": "ledger-query",
            "name": "Ledger Query",
            "implementation_url": "https://github.com/Keshav-behl/LEDGER-QUERY",
            "implementation_commit": "e60d86d978b212e2b7794b7d6cdb8bf0b03b49c2",
            "endpoint": args.endpoint,
        },
        "environment": {
            "platform": platform.platform(),
            "transport": "http",
            "database": "postgres",
            "cache": "redis",
            **go_metadata,
        },
        "observations": {
            "before": before,
            "after": after,
            "cache_sequence": {
                "a1": a1["headers"].get("x-cache"),
                "a2": a2["headers"].get("x-cache"),
                "b1": b1["headers"].get("x-cache"),
                "a3": a3["headers"].get("x-cache"),
            },
        },
        "rows": rows,
        "summary": summary,
    }
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    render_text(receipt, output / "receipt.txt")
    (output / "safety.json").write_text(json.dumps({"before": before, "after": after}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(output / "receipt.txt")
    return 0 if summary["fail"] == 0 else 1

if __name__ == "__main__":
    raise SystemExit(main())
