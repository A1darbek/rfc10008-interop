#!/usr/bin/env python3
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
ORDER = [
  ("Core", "core.native_query", "Native QUERY with JSON body"), ("Core", "core.json_content_accepted", "Supported Content-Type accepted"), ("Core", "core.unsupported_content_type", "Unsupported Content-Type rejected"), ("Core", "core.missing_content_type", "Missing Content-Type handled"), ("Core", "core.accept_query_advertised", "Accept-Query advertised"), ("Core", "core.method_override", "POST method override"), ("Core", "core.identical_request_repeatability", "Identical request repeatability"),
  ("Representation", "representation.etag_advertised", "ETag advertised"), ("Representation", "representation.conditional_revalidation", "Conditional revalidation -> 304"), ("Representation", "representation.content_location", "Content-Location advertised"), ("Representation", "representation.etag_observed_strength", "Validator strength"), ("Representation", "representation.identity_encoding_probe", "Accept-Encoding: identity probe"),
	  ("Semantic identity", "semantic.equivalent_json_same_identity", "Equivalent JSON -> same identity"), ("Safety", "safety.no_unintended_side_effects", "No unintended side effects"), ("Ayder safety", "ayder.no_committed_offset_advance", "No committed-offset advance"), ("Ayder safety", "ayder.no_broker_state_mutation", "No broker-state mutation"), ("Ayder safety", "ayder.bounded_snapshot_stability", "Bounded snapshot stability"), ("Ayder safety", "ayder.rate_limit_headers_sane", "Rate-limit headers sane"),
	  ("Nim PR 25933", "nim.method_query_constant", "HttpQuery method constant"), ("Nim PR 25933", "nim.sync_client_body_preserved", "Sync client preserves QUERY body"), ("Nim PR 25933", "nim.async_client_body_preserved", "Async client preserves QUERY body"), ("Nim PR 25933", "nim.server_recognizes_query", "Server recognizes QUERY"), ("Nim PR 25933", "nim.server_content_length", "Server records Content-Length"), ("Nim PR 25933", "nim.server_chunked_body", "Server parses chunked body"), ("Nim PR 25933", "nim.server_expect_100_continue", "Server handles Expect: 100-continue"), ("Nim PR 25933", "nim.ayder_etag_observed", "Nim client observes Ayder ETag"), ("Nim PR 25933", "nim.ayder_conditional_304", "Nim client conditional 304"), ("Nim PR 25933", "nim.redirect_301_preserves_method", "301 preserves QUERY method"), ("Nim PR 25933", "nim.redirect_301_preserves_body", "301 preserves body"), ("Nim PR 25933", "nim.redirect_302_preserves_method", "302 preserves QUERY method"), ("Nim PR 25933", "nim.redirect_302_preserves_body", "302 preserves body"), ("Nim PR 25933", "nim.redirect_303_rewrites_to_get", "303 rewrites to GET"), ("Nim PR 25933", "nim.redirect_303_strips_body", "303 strips body"), ("Nim PR 25933", "nim.redirect_307_preserves_method", "307 preserves QUERY method"), ("Nim PR 25933", "nim.redirect_307_preserves_body", "307 preserves body"), ("Nim PR 25933", "nim.redirect_308_preserves_method", "308 preserves QUERY method"), ("Nim PR 25933", "nim.redirect_308_preserves_body", "308 preserves body")]
def main():
    receipts = sorted((ROOT / "receipts").glob("*/receipt.json")); targets=[]; by={}
    for p in receipts:
        d=json.loads(p.read_text()); tid=d["target"]["id"]; targets.append(tid); by[tid]={r["id"]:r["result"] for r in d.get("rows", [])}
    lines=["# Generated Interoperability Matrix", "", "Generated from `receipts/**/receipt.json`.", ""]
    if not targets: lines.append("No receipts found.")
    else:
        lines.append("| Profile | Row | " + " | ".join(targets) + " |"); lines.append("|---|---|" + "|".join(["---:"]*len(targets)) + "|")
        for profile,rid,label in ORDER: lines.append("| " + profile + " | " + label + " | " + " | ".join(by.get(t,{}).get(rid,"Pending") for t in targets) + " |")
    (ROOT/"MATRIX.generated.md").write_text("\n".join(lines)+"\n"); print(ROOT/"MATRIX.generated.md")
if __name__ == "__main__": main()
