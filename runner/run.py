#!/usr/bin/env python3
import argparse, datetime as dt, hashlib, http.client, json, platform, subprocess, urllib.parse
from pathlib import Path
RESULTS = ["PASS", "FAIL", "NOT_SUPPORTED", "NOT_APPLICABLE", "UNVERIFIED", "OBSERVED"]
SENSITIVE_HEADERS = {"authorization", "cookie", "set-cookie"}

def now(): return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
def repo_root(): return Path(__file__).resolve().parents[1]
def git_commit():
    try: return subprocess.check_output(["git","rev-parse","HEAD"], cwd=repo_root(), text=True).strip()
    except Exception: return "unknown"
def load_json(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def body_bytes(path): return Path(path).read_bytes()
def sha256(data): return hashlib.sha256(data).hexdigest()
def header(headers, name): return headers.get(name.lower())
def etag_strength(value): return "none" if not value else ("weak" if value.strip().startswith("W/") else "strong")
def redacted_headers(headers): return {k: ("<redacted>" if k.lower() in SENSITIVE_HEADERS else v) for k, v in headers.items()}
def row(id, result, **kwargs):
    if result not in RESULTS: raise ValueError(result)
    out = {"id": id, "result": result}; out.update(kwargs); return out
def passfail(ok): return "PASS" if ok else "FAIL"

def request(method, url, headers=None, body=b""):
    headers = dict(headers or {})
    parsed = urllib.parse.urlparse(url)
    path = urllib.parse.urlunparse(("", "", parsed.path or "/", parsed.params, parsed.query, ""))
    conn = http.client.HTTPSConnection(parsed.netloc, timeout=30) if parsed.scheme == "https" else http.client.HTTPConnection(parsed.netloc, timeout=30)
    conn.request(method, path, body=body, headers=headers)
    res = conn.getresponse(); data = res.read(); hdrs = {k.lower(): v for k, v in res.getheaders()}; conn.close()
    return {"status": res.status, "reason": res.reason, "headers": hdrs, "body": data}

def target_headers(target, include_content_type=True):
    h = dict(target.get("headers", {}))
    if not include_content_type: h = {k:v for k,v in h.items() if k.lower() != "content-type"}
    return h

def bootstrap_ayder(target):
    setup = target.get("setup") or {}
    if setup.get("kind") != "ayder_payment_recovery": return
    parsed = urllib.parse.urlparse(target["endpoint"]); base = f"{parsed.scheme}://{parsed.netloc}"
    auth = target.get("headers", {}).get("Authorization")
    headers = {"Content-Type":"application/json"};
    if auth: headers["Authorization"] = auth
    topic = setup.get("topic", "payment-recovery"); group = setup.get("group", "payment-worker")
    request("POST", f"{base}/broker/topics", headers, json.dumps({"name":topic,"partitions":1}).encode())
    ndh = {"Content-Type":"application/x-ndjson"};
    if auth: ndh["Authorization"] = auth
    events = "\n".join([
      '{"event_id":"pay_evt_001","payment_id":"pay_001","provider_order_id":"po_001","provider_commitment":"UNKNOWN","safe_to_close":false,"manual_reconciliation_required":true}',
      '{"event_id":"pay_evt_002","payment_id":"pay_002","provider_order_id":"po_002","provider_commitment":"SUCCESS","safe_to_close":true,"manual_reconciliation_required":false}',
      '{"event_id":"pay_evt_003","payment_id":"pay_003","provider_order_id":"po_003","provider_commitment":"UNKNOWN","safe_to_close":false,"manual_reconciliation_required":true}', ""]).encode()
    request("POST", f"{base}/broker/topics/{topic}/produce-ndjson?partition=0&timeout_ms=5000&idempotency_key=rfc10008_initial", ndh, events)
    request("POST", f"{base}/broker/commit", headers, json.dumps({"topic":topic,"group":group,"partition":0,"offset":0}).encode())

def run(target_path, output):
    root = repo_root(); target = load_json(target_path); output = Path(output); output.mkdir(parents=True, exist_ok=True)
    normal = body_bytes(root / target["request_body_file"]); equiv = body_bytes(root / target["equivalent_request_body_file"])
    endpoint = target["endpoint"]; method = target.get("method", "QUERY"); caps = target.get("capabilities", {})
    bootstrap_ayder(target)
    rows = []
    first = request(method, endpoint, target_headers(target), normal)
    first_text = first["body"].decode("utf-8", "replace"); etag = header(first["headers"], "etag"); body_hash = sha256(first["body"])
    aq = header(first["headers"], "accept-query"); cl = header(first["headers"], "content-location")
    rows += [row("core.native_query", passfail(first["status"] == 200), expected=200, observed=first["status"]), row("core.json_content_accepted", passfail(first["status"] == 200), expected=200, observed=first["status"]), row("core.accept_query_advertised", passfail(bool(aq)), evidence={"accept_query": aq}), row("representation.etag_advertised", passfail(bool(etag)), evidence={"etag": etag}), row("representation.etag_observed_strength", "OBSERVED", evidence={"etag": etag, "strength": etag_strength(etag)}), row("representation.content_location", passfail(bool(cl)), evidence={"content_location": cl})]
    repeat = request(method, endpoint, target_headers(target), normal); repeat_etag = header(repeat["headers"], "etag")
    rows += [row("core.identical_request_repeatability", passfail(repeat["status"] == first["status"] and sha256(repeat["body"]) == body_hash), evidence={"first_body_sha256": body_hash, "repeat_body_sha256": sha256(repeat["body"])}), row("representation.identical_request_stable_validator", passfail(bool(etag) and etag == repeat_etag), evidence={"first_etag": etag, "repeat_etag": repeat_etag})]
    if etag:
        h = target_headers(target); h["If-None-Match"] = etag; reval = request(method, endpoint, h, normal)
        rows.append(row("representation.conditional_revalidation", passfail(reval["status"] == 304), expected=304, observed=reval["status"], evidence={"etag": etag}))
    else: rows.append(row("representation.conditional_revalidation", "UNVERIFIED", evidence={"reason":"no etag"}))
    unsupported = request(method, endpoint, {**target_headers(target, False), "Content-Type":"text/plain"}, b"not json")
    rows.append(row("core.unsupported_content_type", passfail(unsupported["status"] == 415), expected=415, observed=unsupported["status"], evidence={"accept_query": header(unsupported["headers"], "accept-query")}))
    missing = request(method, endpoint, target_headers(target, False), normal)
    rows.append(row("core.missing_content_type", "OBSERVED", observed=missing["status"], evidence={"body_sha256": sha256(missing["body"])}))
    ih = target_headers(target); ih["Accept-Encoding"] = "identity"; identity = request(method, endpoint, ih, normal); ietag = header(identity["headers"], "etag")
    rows.append(row("representation.identity_encoding_probe", "OBSERVED", observed=identity["status"], evidence={"etag": ietag, "strength": etag_strength(ietag), "body_sha256": sha256(identity["body"])}))
    if caps.get("semantic_query_identity"):
        eq = request(method, endpoint, target_headers(target), equiv); fp1 = fp2 = None
        try: fp1 = json.loads(first_text).get("query_fingerprint"); fp2 = json.loads(eq["body"].decode("utf-8", "replace")).get("query_fingerprint")
        except Exception: pass
        same = (fp1 and fp1 == fp2) or (header(eq["headers"], "etag") == etag and sha256(eq["body"]) == body_hash)
        rows.append(row("semantic.equivalent_json_same_identity", passfail(bool(same)), evidence={"first_fingerprint": fp1, "equivalent_fingerprint": fp2, "first_etag": etag, "equivalent_etag": header(eq["headers"], "etag")}))
    else: rows.append(row("semantic.equivalent_json_same_identity", "NOT_SUPPORTED", evidence={"reason":"target does not declare semantic query identity canonicalization"}))
    if caps.get("method_override"):
        h = target_headers(target); h["X-HTTP-Method-Override"] = "QUERY"; over = request("POST", endpoint, h, normal)
        rows.append(row("core.method_override", passfail(over["status"] == 200), expected=200, observed=over["status"]))
    else: rows.append(row("core.method_override", "NOT_APPLICABLE"))
    rows += [row("safety.no_unintended_side_effects", "OBSERVED", evidence={"repeat_status": repeat["status"], "first_body_sha256": body_hash, "repeat_body_sha256": sha256(repeat["body"])}), row("safety.state_before_after_recorded", "OBSERVED", evidence={"generic_http_runner": True})]
    if caps.get("implementation_safety_receipt"):
        try:
            jj = json.loads(first_text); safety = jj.get("safety", {}); explain = jj.get("explain", {})
            rows += [row("ayder.no_committed_offset_advance", passfail(safety.get("committed_offset_before") == safety.get("committed_offset_after")), evidence=safety), row("ayder.no_broker_state_mutation", passfail(safety.get("broker_state_mutated") is False), evidence=safety), row("ayder.bounded_snapshot_stability", passfail(explain.get("messages_scanned") == 3 and explain.get("messages_matched") == 2), evidence=explain)]
        except Exception as exc: rows += [row("ayder.no_committed_offset_advance", "UNVERIFIED", evidence={"error":str(exc)}), row("ayder.no_broker_state_mutation", "UNVERIFIED"), row("ayder.bounded_snapshot_stability", "UNVERIFIED")]
    else: rows += [row("ayder.no_committed_offset_advance", "NOT_APPLICABLE"), row("ayder.no_broker_state_mutation", "NOT_APPLICABLE"), row("ayder.bounded_snapshot_stability", "NOT_APPLICABLE")]
    summary = {k.lower(): 0 for k in RESULTS}
    for r in rows: summary[r["result"].lower()] += 1
    parsed = urllib.parse.urlparse(endpoint)
    receipt = {"schema_version":"0.1", "run_id":f"{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{target['id']}", "generated_at":now(), "runner":{"repository":"A1darbek/rfc10008-interop", "commit":git_commit()}, "target":{"id":target["id"], "name":target.get("name"), "implementation_url":target.get("implementation_url"), "implementation_commit":target.get("implementation_commit", "unknown"), "endpoint":endpoint}, "environment":{"platform":platform.platform(), "transport":parsed.scheme, **target.get("environment", {})}, "observations":{"first_status":first["status"], "first_response_headers":redacted_headers(first["headers"]), "first_body_sha256":body_hash}, "rows":rows, "summary":summary}
    (output/"receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True)+"\n", encoding="utf-8"); write_text(receipt, output/"receipt.txt"); print(output/"receipt.txt"); return 0 if summary.get("fail", 0) == 0 else 1

def write_text(receipt, path):
    s = receipt["summary"]; lines = ["============================================================", " RFC 10008 QUERY INTEROP RECEIPT", "============================================================", f" target       : {receipt['target']['id']}", f" endpoint     : {receipt['target']['endpoint']}", f" generated_at : {receipt['generated_at']}", f" runner       : {receipt['runner']['commit']}", "------------------------------------------------------------", f" summary      : PASS={s['pass']} FAIL={s['fail']} OBSERVED={s['observed']} UNVERIFIED={s['unverified']} NOT_SUPPORTED={s['not_supported']} NOT_APPLICABLE={s['not_applicable']}", "------------------------------------------------------------"]
    for r in receipt["rows"]:
        lines.append(f" {r['result']:<15} {r['id']}")
        if "expected" in r or "observed" in r: lines.append(f"   expected={r.get('expected')} observed={r.get('observed')}")
        if r.get("evidence"): lines.append("   evidence=" + json.dumps(r["evidence"], sort_keys=True)[:300])
    lines.append("============================================================"); path.write_text("\n".join(lines)+"\n", encoding="utf-8")

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--target", required=True); ap.add_argument("--output", required=True); a = ap.parse_args(); return run(a.target, a.output)
if __name__ == "__main__": raise SystemExit(main())
