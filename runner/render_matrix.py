#!/usr/bin/env python3
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
ORDER = [
  ("Core", "core.native_query", "Native QUERY with JSON body"), ("Core", "core.json_content_accepted", "Supported Content-Type accepted"), ("Core", "core.unsupported_content_type", "Unsupported Content-Type rejected"), ("Core", "core.missing_content_type", "Missing Content-Type handled"), ("Core", "core.accept_query_advertised", "Accept-Query advertised"), ("Core", "core.method_override", "POST method override"), ("Core", "core.identical_request_repeatability", "Identical request repeatability"),
  ("Representation", "representation.etag_advertised", "ETag advertised"), ("Representation", "representation.conditional_revalidation", "Conditional revalidation -> 304"), ("Representation", "representation.content_location", "Content-Location advertised"), ("Representation", "representation.etag_observed_strength", "Validator strength"), ("Representation", "representation.identity_encoding_probe", "Accept-Encoding: identity probe"),
	  ("Semantic identity", "semantic.equivalent_json_same_identity", "Equivalent JSON -> same identity"), ("Safety", "safety.no_unintended_side_effects", "No unintended side effects"), ("Ayder safety", "ayder.no_committed_offset_advance", "No committed-offset advance"), ("Ayder safety", "ayder.no_broker_state_mutation", "No broker-state mutation"), ("Ayder safety", "ayder.bounded_snapshot_stability", "Bounded snapshot stability"), ("Ayder safety", "ayder.rate_limit_headers_sane", "Rate-limit headers sane"),
	  ("Ledger safety", "ledger.native_query", "Native QUERY"), ("Ledger safety", "ledger.json_content_type", "JSON Content-Type accepted"), ("Ledger safety", "ledger.unsupported_content_type_415", "Unsupported Content-Type rejected"), ("Ledger safety", "ledger.accept_query_options", "OPTIONS advertises Accept-Query"), ("Ledger safety", "ledger.cache_first_request_miss", "Body A first request MISS"), ("Ledger safety", "ledger.cache_identical_request_hit", "Body A repeat HIT"), ("Ledger safety", "ledger.cache_different_body_miss", "Body B request MISS"), ("Ledger safety", "ledger.cache_return_to_first_body_hit", "Body A after B HIT"), ("Ledger safety", "ledger.cache_exact_response_replay", "Cached response replay exact"), ("Ledger safety", "ledger.cache_no_cross_body_collision", "No cross-body cache collision"), ("Ledger safety", "ledger.account_balance_unchanged", "Account balance unchanged by QUERY"), ("Ledger safety", "ledger.entry_count_unchanged", "Entry count unchanged by QUERY"), ("Ledger safety", "ledger.account_count_unchanged", "Account count unchanged by QUERY"), ("Ledger safety", "ledger.read_only_pool_rejects_write", "Read-only pool rejects writes"), ("Ledger safety", "ledger.project_tests", "Project tests")]
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
