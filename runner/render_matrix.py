#!/usr/bin/env python3
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
ORDER = [
  ("Core", "core.native_query", "Native QUERY with JSON body"), ("Core", "core.json_content_accepted", "Supported Content-Type accepted"), ("Core", "core.unsupported_content_type", "Unsupported Content-Type rejected"), ("Core", "core.missing_content_type", "Missing Content-Type handled"), ("Core", "core.accept_query_advertised", "Accept-Query advertised"), ("Core", "core.method_override", "POST method override"), ("Core", "core.identical_request_repeatability", "Identical request repeatability"),
  ("Representation", "representation.etag_advertised", "ETag advertised"), ("Representation", "representation.conditional_revalidation", "Conditional revalidation -> 304"), ("Representation", "representation.content_location", "Content-Location advertised"), ("Representation", "representation.etag_observed_strength", "Validator strength"), ("Representation", "representation.identity_encoding_probe", "Accept-Encoding: identity probe"),
	  ("Semantic identity", "semantic.equivalent_json_same_identity", "Equivalent JSON -> same identity"), ("Safety", "safety.no_unintended_side_effects", "No unintended side effects"), ("Ayder safety", "ayder.no_committed_offset_advance", "No committed-offset advance"), ("Ayder safety", "ayder.no_broker_state_mutation", "No broker-state mutation"), ("Ayder safety", "ayder.bounded_snapshot_stability", "Bounded snapshot stability"), ("Ayder safety", "ayder.rate_limit_headers_sane", "Rate-limit headers sane"),
	  ("Laravel 13", "laravel13.apache_forwarding", "Apache forwards QUERY"), ("Laravel 13", "laravel13.query_reaches_application", "QUERY reaches Laravel application"), ("Laravel 13", "laravel13.request_all_parses_query_body", "request()->all parses QUERY body"), ("Laravel 13", "laravel13.safe_idempotent_cacheable_flags", "QUERY marked safe/idempotent/cacheable"), ("Laravel 13", "laravel13.native_http_query_client_source", "Http::query source present"), ("Laravel 13", "laravel13.native_route_query_helper", "Route::query helper"), ("Laravel 13", "laravel13.native_query_json_helper", "queryJson helper"), ("Laravel 13", "laravel13.cors_preflight_observed", "CORS preflight observed"), ("Laravel 13", "laravel13.php_cli_server_behavior", "PHP CLI server behavior")]
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
