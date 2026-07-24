#!/usr/bin/env python3
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
ORDER = [
  ("Core", "core.native_query", "Native QUERY with JSON body"), ("Core", "core.json_content_accepted", "Supported Content-Type accepted"), ("Core", "core.unsupported_content_type", "Unsupported Content-Type rejected"), ("Core", "core.missing_content_type", "Missing Content-Type handled"), ("Core", "core.accept_query_advertised", "Accept-Query advertised"), ("Core", "core.method_override", "POST method override"), ("Core", "core.identical_request_repeatability", "Identical request repeatability"),
  ("Representation", "representation.etag_advertised", "ETag advertised"), ("Representation", "representation.conditional_revalidation", "Conditional revalidation -> 304"), ("Representation", "representation.content_location", "Content-Location advertised"), ("Representation", "representation.etag_observed_strength", "Validator strength"), ("Representation", "representation.identity_encoding_probe", "Accept-Encoding: identity probe"),
  ("Semantic identity", "semantic.equivalent_json_same_identity", "Equivalent JSON -> same identity"), ("Safety", "safety.no_unintended_side_effects", "No unintended side effects"), ("Ayder safety", "ayder.no_committed_offset_advance", "No committed-offset advance"), ("Ayder safety", "ayder.no_broker_state_mutation", "No broker-state mutation"), ("Ayder safety", "ayder.bounded_snapshot_stability", "Bounded snapshot stability"), ("Ayder safety", "ayder.rate_limit_headers_sane", "Rate-limit headers sane"),
  ("Kevinci client", "kevincii.native_query_first", "Native QUERY first"), ("Kevinci client", "kevincii.json_request_preserved", "JSON request preserved"), ("Kevinci client", "kevincii.json_response_parsed", "JSON response parsed"), ("Kevinci client", "kevincii.accept_query_observed", "Accept-Query observed"), ("Kevinci client", "kevincii.etag_observed", "ETag observed"), ("Kevinci client", "kevincii.conditional_304_wire", "Conditional wire 304"), ("Kevinci client", "kevincii.conditional_304_api_surface", "Conditional API surface"), ("Kevinci client", "kevincii.query_to_post_fallback", "QUERY to POST fallback"), ("Kevinci client", "kevincii.post_body_preserved", "POST body preserved"), ("Kevinci client", "kevincii.query_to_post_to_get_fallback", "QUERY to POST to GET fallback"), ("Kevinci client", "kevincii.get_params_serialized", "GET params serialized"), ("Kevinci client", "kevincii.timeout_enforced", "Timeout enforced"), ("Kevinci client", "kevincii.external_abort_enforced", "External abort enforced"), ("Kevinci client", "kevincii.abort_error_surface", "Abort error surface")]
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
