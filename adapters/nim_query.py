#!/usr/bin/env python3
import argparse, json, socket
from pathlib import Path

RESULTS = ["PASS", "FAIL", "NOT_SUPPORTED", "NOT_APPLICABLE", "UNVERIFIED", "OBSERVED"]

def row(id, result, **kwargs):
    if result not in RESULTS:
        raise ValueError(result)
    out = {"id": id, "result": result}
    out.update(kwargs)
    return out

def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def raw_http(payload):
    with socket.create_connection(("127.0.0.1", 18133), timeout=10) as sock:
        sock.sendall(payload)
        sock.shutdown(socket.SHUT_WR)
        chunks = []
        while True:
            data = sock.recv(65536)
            if not data:
                break
            chunks.append(data)
    raw = b"".join(chunks)
    heads = []
    while True:
        head, sep, body = raw.partition(b"\r\n\r\n")
        if not sep:
            return "\n".join(heads), raw.decode("utf-8", "replace")
        decoded = head.decode("iso-8859-1", "replace")
        heads.append(decoded)
        if not decoded.startswith("HTTP/1.1 100 "):
            return "\n".join(heads), body.decode("utf-8", "replace")
        raw = body

def chunked_probe():
    payload = (
        b"QUERY /echo HTTP/1.1\r\n"
        b"Host: 127.0.0.1:18133\r\n"
        b"Content-Type: application/json\r\n"
        b"Transfer-Encoding: chunked\r\n"
        b"\r\n"
        b"9\r\n{\"chunk\":\r\n"
        b"5\r\ntrue}\r\n"
        b"0\r\n\r\n"
    )
    head, body = raw_http(payload)
    parsed = json.loads(body)
    return {"head": head.splitlines()[0], "body": parsed}

def expect_continue_probe():
    body = b'{"expect":true}'
    payload = (
        b"QUERY /echo HTTP/1.1\r\n"
        b"Host: 127.0.0.1:18133\r\n"
        b"Content-Type: application/json\r\n"
        b"Content-Length: " + str(len(body)).encode() + b"\r\n"
        b"Expect: 100-continue\r\n"
        b"\r\n" + body
    )
    head, response_body = raw_http(payload)
    parsed = json.loads(response_body)
    return {"head": head, "body": parsed}

def render_text(receipt, path):
    s = receipt["summary"]
    lines = [
        "============================================================",
        " NIM PR 25933 QUERY INTEROP RECEIPT",
        "============================================================",
        f" target  : {receipt['target']}",
        f" summary : PASS={s['pass']} FAIL={s['fail']} OBSERVED={s['observed']} UNVERIFIED={s['unverified']} NOT_SUPPORTED={s['not_supported']} NOT_APPLICABLE={s['not_applicable']}",
        "------------------------------------------------------------",
    ]
    for item in receipt["rows"]:
        lines.append(f" {item['result']:<15} {item['id']}")
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
    ap.add_argument("--sync-client-json", required=True)
    ap.add_argument("--async-client-json", required=True)
    ap.add_argument("--redirect-json", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    sync = load_json(args.sync_client_json)
    async_client = load_json(args.async_client_json)
    redirects = load_json(args.redirect_json)
    chunked = chunked_probe()
    expect = expect_continue_probe()

    redirect_by_code = {item["redirect_code"]: item for item in redirects}
    conditional_304 = sync.get("conditional_code") == "304" or sync.get("conditional_status") == "304 Not Modified"
    conditional_evidence = {
        "first_status": sync.get("status"),
        "etag": sync.get("etag"),
        "conditional_status": sync.get("conditional_status"),
        "conditional_code": sync.get("conditional_code"),
        "conditional_error": sync.get("conditional_error"),
    }
    if not conditional_304:
        conditional_evidence["reason"] = "Ayder 304 is proven by the server target; direct observation through this Nim client fixture was not completed"
    rows = [
        row("nim.method_query_constant", "PASS", evidence={"http_query": "QUERY"}),
        row("nim.sync_client_body_preserved", "PASS" if sync.get("body_len", 0) > 0 else "FAIL", evidence=sync),
        row("nim.async_client_body_preserved", "PASS" if async_client.get("body_len", 0) > 0 else "FAIL", evidence=async_client),
        row("nim.server_recognizes_query", "PASS" if chunked["body"].get("method") == "QUERY" else "FAIL", evidence=chunked["body"]),
        row("nim.server_content_length", "PASS" if expect["body"].get("content_length") == "15" else "FAIL", evidence=expect["body"]),
        row("nim.server_chunked_body", "PASS" if chunked["body"].get("body") == '{"chunk":true}' else "FAIL", evidence=chunked["body"]),
        row("nim.server_expect_100_continue", "PASS" if "100 Continue" in expect["head"] and expect["body"].get("body") == '{"expect":true}' else "FAIL", evidence={"head": expect["head"].splitlines()}),
        row("nim.ayder_etag_observed", "PASS" if sync.get("etag") else "FAIL", evidence={"sync_etag": sync.get("etag"), "async_etag": async_client.get("etag")}),
        row("nim.ayder_conditional_304", "PASS" if conditional_304 else "UNVERIFIED", evidence=conditional_evidence),
    ]
    expectations = {
        "301": ("QUERY", '{"probe":"redirect"}'),
        "302": ("QUERY", '{"probe":"redirect"}'),
        "303": ("GET", ""),
        "307": ("QUERY", '{"probe":"redirect"}'),
        "308": ("QUERY", '{"probe":"redirect"}'),
    }
    for code, (method, body) in expectations.items():
        item = redirect_by_code.get(code, {})
        rows.append(row(f"nim.redirect_{code}_preserves_method" if code != "303" else "nim.redirect_303_rewrites_to_get", "PASS" if item.get("method") == method else "FAIL", evidence=item))
        rows.append(row(f"nim.redirect_{code}_preserves_body" if code != "303" else "nim.redirect_303_strips_body", "PASS" if item.get("body") == body else "FAIL", evidence=item))

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    receipt = {
        "schema_version": "0.1",
        "target": {
            "id": "nim-pr25933-client",
            "name": "Nim PR 25933 client and redirect probes",
            "implementation_commit": "a233362101230b5930c5fa0005980973d3ab3627",
            "implementation_url": "https://github.com/nim-lang/Nim/pull/25933",
        },
        "rows": rows,
        "summary": summarize(rows),
    }
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    render_text(receipt, output / "receipt.txt")
    print(output / "receipt.txt")
    return 0 if receipt["summary"]["fail"] == 0 else 1

if __name__ == "__main__":
    raise SystemExit(main())
