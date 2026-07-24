#!/usr/bin/env python3
"""Evidence adapter for Oharu's RFC 10008 product-search server."""

import argparse
import hashlib
import http.client
import json
import platform
import subprocess
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

RESULTS = (
    "PASS",
    "FAIL",
    "NOT_SUPPORTED",
    "NOT_APPLICABLE",
    "UNVERIFIED",
    "OBSERVED",
)
IMPLEMENTATION_COMMIT = "057d9effae1bc767eaef03fc6cdc1b774cd735ad"
IMPLEMENTATION_URL = "https://github.com/oharu121/http-query-method-rfc10008-demo"


def row(row_id, result, **fields):
    if result not in RESULTS:
        raise ValueError(f"invalid result: {result}")
    value = {"id": row_id, "result": result}
    value.update(fields)
    return value


def passfail(condition):
    return "PASS" if condition else "FAIL"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def request(method, url, headers=None, body=b""):
    parsed = urllib.parse.urlparse(url)
    path = urllib.parse.urlunparse(
        ("", "", parsed.path or "/", parsed.params, parsed.query, "")
    )
    connection = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=15)
    connection.request(method, path, body=body, headers=dict(headers or {}))
    response = connection.getresponse()
    response_body = response.read()
    response_headers = {key.lower(): value for key, value in response.getheaders()}
    result = {
        "status": response.status,
        "reason": response.reason,
        "headers": response_headers,
        "body": response_body,
    }
    connection.close()
    return result


def decode_json(data):
    try:
        return json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def cache_key(response):
    value = response["headers"].get("x-cache-key")
    return value if isinstance(value, str) and value.strip() else None


def cache_state(response):
    value = response["headers"].get("x-cache")
    return value.upper() if isinstance(value, str) and value else None


def expected_cache_key(endpoint, body):
    path = urllib.parse.urlparse(endpoint).path or "/"
    return f"QUERY:{path}:{sha256(body)[:16]}"


def exact_nonempty_bytes_equal(first, second):
    return (
        isinstance(first, bytes)
        and isinstance(second, bytes)
        and len(first) > 0
        and len(second) > 0
        and first == second
    )


def summarize(rows):
    summary = {result.lower(): 0 for result in RESULTS}
    for item in rows:
        summary[item["result"].lower()] += 1
    return summary


def render_text(receipt, output, title):
    summary = receipt["summary"]
    lines = [
        "============================================================",
        f" {title}",
        "============================================================",
        f" implementation : {receipt['target']['implementation_commit']}",
        f" endpoint       : {receipt['target']['endpoint']}",
        (
            " summary        : "
            f"PASS={summary['pass']} FAIL={summary['fail']} "
            f"OBSERVED={summary['observed']} "
            f"UNVERIFIED={summary['unverified']} "
            f"NOT_SUPPORTED={summary['not_supported']} "
            f"NOT_APPLICABLE={summary['not_applicable']}"
        ),
        "------------------------------------------------------------",
    ]
    for item in receipt["rows"]:
        lines.append(f" {item['result']:<15} {item['id']}")
        if item.get("evidence"):
            evidence = json.dumps(item["evidence"], sort_keys=True)
            lines.append(f"   evidence={evidence}")
    lines.append("============================================================")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def git_commit(root):
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNVERIFIED"


def target_metadata(target, endpoint):
    return {
        "id": target["id"],
        "name": target["name"],
        "implementation_url": target["implementation_url"],
        "implementation_commit": target["implementation_commit"],
        "endpoint": endpoint,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--request-a", required=True)
    parser.add_argument("--request-a-equivalent", required=True)
    parser.add_argument("--request-b", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--sanitize", action="store_true")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    target = json.loads(Path(args.target).read_text(encoding="utf-8"))
    if target["implementation_commit"] != IMPLEMENTATION_COMMIT:
        raise SystemExit("target implementation commit does not match adapter pin")
    if target["implementation_url"] != IMPLEMENTATION_URL:
        raise SystemExit("target implementation URL does not match adapter pin")

    body_a = Path(args.request_a).read_bytes()
    body_a_equivalent = Path(args.request_a_equivalent).read_bytes()
    body_b = Path(args.request_b).read_bytes()
    for label, body in (
        ("request A", body_a),
        ("equivalent request A", body_a_equivalent),
        ("request B", body_b),
    ):
        parsed = decode_json(body)
        if not isinstance(parsed, dict) or not parsed:
            raise SystemExit(f"{label} must be a non-empty JSON object")

    json_headers = {"Accept": "application/json", "Content-Type": "application/json"}
    a1 = request("QUERY", args.endpoint, json_headers, body_a)
    a2 = request("QUERY", args.endpoint, json_headers, body_a)
    b1 = request("QUERY", args.endpoint, json_headers, body_b)
    a3 = request("QUERY", args.endpoint, json_headers, body_a)
    equivalent = request("QUERY", args.endpoint, json_headers, body_a_equivalent)

    missing_type = request(
        "QUERY", args.endpoint, {"Accept": "application/json"}, body_a
    )
    unsupported_type = request(
        "QUERY",
        args.endpoint,
        {"Accept": "application/json", "Content-Type": "text/plain"},
        body_a,
    )
    malformed = request(
        "QUERY",
        args.endpoint,
        {"Accept": "application/json", "Content-Type": "application/json"},
        b'{"categories":',
    )
    options = request(
        "OPTIONS",
        args.endpoint,
        {
            "Origin": "https://partner.example",
            "Access-Control-Request-Method": "QUERY",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    responses = {
        "A1": (a1, body_a),
        "A2": (a2, body_a),
        "B1": (b1, body_b),
        "A3": (a3, body_a),
        "A-equivalent": (equivalent, body_a_equivalent),
    }
    sequence = []
    for label, (response, request_body) in responses.items():
        sequence.append(
            {
                "label": label,
                "status": response["status"],
                "x_cache": cache_state(response),
                "cache_key": cache_key(response),
                "request_body_sha256": sha256(request_body),
                "response_body_sha256": sha256(response["body"])
                if response["body"]
                else None,
            }
        )

    keys = {label: cache_key(response) for label, (response, _) in responses.items()}
    states = {
        label: cache_state(response) for label, (response, _) in responses.items()
    }
    payloads = {
        label: decode_json(response["body"])
        for label, (response, _) in responses.items()
    }
    expected_keys = {
        "A1": expected_cache_key(args.endpoint, body_a),
        "A2": expected_cache_key(args.endpoint, body_a),
        "B1": expected_cache_key(args.endpoint, body_b),
        "A3": expected_cache_key(args.endpoint, body_a),
        "A-equivalent": expected_cache_key(args.endpoint, body_a_equivalent),
    }
    keys_nonempty = all(isinstance(value, str) and value for value in keys.values())
    keys_match_raw_bodies = keys_nonempty and keys == expected_keys
    a_exact_replays = exact_nonempty_bytes_equal(a1["body"], a2["body"]) and (
        exact_nonempty_bytes_equal(a1["body"], a3["body"])
    )
    b_differs = (
        isinstance(payloads["A1"], dict)
        and isinstance(payloads["B1"], dict)
        and payloads["A1"] != payloads["B1"]
        and len(a1["body"]) > 0
        and len(b1["body"]) > 0
    )
    equivalent_same_result = (
        isinstance(payloads["A1"], dict)
        and isinstance(payloads["A-equivalent"], dict)
        and payloads["A1"] == payloads["A-equivalent"]
    )

    cache_rows = [
        row(
            "oharu.cache_first_body_miss",
            passfail(a1["status"] == 200 and states["A1"] == "MISS"),
            evidence={"status": a1["status"], "x_cache": states["A1"]},
        ),
        row(
            "oharu.cache_identical_body_hit",
            passfail(
                a2["status"] == 200
                and states["A2"] == "HIT"
                and keys["A2"]
                and keys["A2"] == keys["A1"]
            ),
            evidence={"status": a2["status"], "x_cache": states["A2"], "same_key": keys["A2"] == keys["A1"]},
        ),
        row(
            "oharu.cache_different_body_miss",
            passfail(
                b1["status"] == 200
                and states["B1"] == "MISS"
                and keys["B1"]
                and keys["B1"] != keys["A1"]
                and b_differs
            ),
            evidence={
                "status": b1["status"],
                "x_cache": states["B1"],
                "distinct_key": keys["B1"] != keys["A1"],
                "result_differs": b_differs,
            },
        ),
        row(
            "oharu.cache_return_to_first_body_hit",
            passfail(
                a3["status"] == 200
                and states["A3"] == "HIT"
                and keys["A3"]
                and keys["A3"] == keys["A1"]
            ),
            evidence={"status": a3["status"], "x_cache": states["A3"], "same_key": keys["A3"] == keys["A1"]},
        ),
        row(
            "oharu.cache_exact_replay",
            passfail(a_exact_replays),
            evidence={
                "a1_response_sha256": sha256(a1["body"]) if a1["body"] else None,
                "a2_response_sha256": sha256(a2["body"]) if a2["body"] else None,
                "a3_response_sha256": sha256(a3["body"]) if a3["body"] else None,
                "non_empty": bool(a1["body"] and a2["body"] and a3["body"]),
            },
        ),
        row(
            "oharu.cache_no_cross_body_collision",
            passfail(
                keys_nonempty
                and keys["A1"] != keys["B1"]
                and keys["A1"] == keys["A3"]
                and b_differs
                and a_exact_replays
            ),
            evidence={
                "a_key": keys["A1"],
                "b_key": keys["B1"],
                "a_return_key": keys["A3"],
                "a_returned_exactly": exact_nonempty_bytes_equal(a1["body"], a3["body"]),
            },
        ),
        row(
            "oharu.cache_key_includes_body",
            passfail(keys_match_raw_bodies),
            evidence={
                "method_and_path_prefix": f"QUERY:{urllib.parse.urlparse(args.endpoint).path}:",
                "observed_keys": keys,
                "expected_keys_from_raw_body_sha256": expected_keys,
            },
        ),
        row(
            "oharu.reordered_json_cache_identity",
            "OBSERVED",
            evidence={
                "x_cache": states["A-equivalent"],
                "raw_body_sha256_differs": sha256(body_a) != sha256(body_a_equivalent),
                "cache_key_differs": keys["A1"] != keys["A-equivalent"],
                "semantic_response_equal": equivalent_same_result,
                "interpretation": "Cache identity follows raw request-body bytes.",
            },
        ),
    ]

    accept_query = (
        unsupported_type["headers"].get("accept-query")
        or options["headers"].get("accept-query")
    )
    allow_methods = options["headers"].get("access-control-allow-methods", "")
    allow_headers = options["headers"].get("access-control-allow-headers", "")
    rows = [
        row("core.native_query", passfail(a1["status"] == 200), expected=200, observed=a1["status"]),
        row(
            "core.json_content_accepted",
            passfail(a1["status"] == 200 and isinstance(payloads["A1"], dict)),
            expected=200,
            observed=a1["status"],
        ),
        row(
            "core.unsupported_content_type",
            passfail(
                unsupported_type["status"] == 415
                and isinstance(accept_query, str)
                and "application/json" in accept_query
            ),
            expected=415,
            observed=unsupported_type["status"],
            evidence={"accept_query": accept_query},
        ),
        row(
            "core.missing_content_type",
            passfail(missing_type["status"] == 400),
            expected=400,
            observed=missing_type["status"],
        ),
        row(
            "core.accept_query_advertised",
            passfail(isinstance(accept_query, str) and "application/json" in accept_query),
            evidence={"accept_query": accept_query},
        ),
        row(
            "core.method_override",
            "NOT_SUPPORTED",
            evidence={"reason": "target does not declare a POST method override"},
        ),
        row(
            "core.identical_request_repeatability",
            passfail(a_exact_replays),
            evidence={
                "first_body_sha256": sha256(a1["body"]) if a1["body"] else None,
                "repeat_body_sha256": sha256(a2["body"]) if a2["body"] else None,
                "return_body_sha256": sha256(a3["body"]) if a3["body"] else None,
            },
        ),
        row(
            "representation.etag_advertised",
            "NOT_SUPPORTED",
            evidence={"reason": "pinned implementation does not emit ETag"},
        ),
        row(
            "representation.identical_request_stable_validator",
            "NOT_SUPPORTED",
            evidence={"reason": "pinned implementation does not emit ETag"},
        ),
        row(
            "representation.conditional_revalidation",
            "NOT_SUPPORTED",
            evidence={"reason": "pinned implementation does not expose conditional 304 behavior"},
        ),
        row(
            "representation.content_location",
            "NOT_SUPPORTED",
            evidence={"reason": "pinned implementation does not emit Content-Location"},
        ),
        row(
            "representation.etag_observed_strength",
            "OBSERVED",
            evidence={"etag": a1["headers"].get("etag"), "strength": "none"},
        ),
        row(
            "representation.identity_encoding_probe",
            "OBSERVED",
            observed=a1["status"],
            evidence={
                "body_sha256": sha256(a1["body"]) if a1["body"] else None,
                "etag": a1["headers"].get("etag"),
            },
        ),
        row(
            "semantic.equivalent_json_same_identity",
            "NOT_SUPPORTED",
            evidence={
                "reason": "pinned implementation keys cache identity from raw body bytes",
                "semantic_response_equal": equivalent_same_result,
                "cache_key_equal": keys["A1"] == keys["A-equivalent"],
            },
        ),
        row(
            "safety.no_unintended_side_effects",
            "OBSERVED",
            evidence={
                "fresh_server_process": True,
                "cache_sequence": [item["x_cache"] for item in sequence],
            },
        ),
        row(
            "safety.state_before_after_recorded",
            "OBSERVED",
            evidence={"observable_state": "X-Cache and X-Cache-Key", "sequence": sequence},
        ),
        row("ayder.no_committed_offset_advance", "NOT_APPLICABLE"),
        row("ayder.no_broker_state_mutation", "NOT_APPLICABLE"),
        row("ayder.bounded_snapshot_stability", "NOT_APPLICABLE"),
        row("ayder.rate_limit_headers_sane", "NOT_APPLICABLE"),
        row(
            "oharu.malformed_json_rejected",
            passfail(malformed["status"] == 422),
            expected=422,
            observed=malformed["status"],
        ),
        row(
            "oharu.options_query_cors",
            passfail(
                options["status"] == 200
                and "QUERY" in allow_methods.upper()
                and "CONTENT-TYPE" in allow_headers.upper()
                and isinstance(options["headers"].get("accept-query"), str)
            ),
            evidence={
                "status": options["status"],
                "accept_query": options["headers"].get("accept-query"),
                "access_control_allow_methods": allow_methods,
                "access_control_allow_headers": allow_headers,
            },
        ),
        *cache_rows,
    ]

    generated_at = (
        "SANITIZED_EXAMPLE"
        if args.sanitize
        else datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    )
    run_id = (
        "SANITIZED-oharu-product-search"
        if args.sanitize
        else f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-oharu-product-search"
    )
    runner_commit = "SANITIZED_RUNNER_COMMIT" if args.sanitize else git_commit(root)
    environment_platform = "SANITIZED" if args.sanitize else platform.platform()
    metadata = target_metadata(target, args.endpoint)
    receipt = {
        "schema_version": "0.1",
        "generated_at": generated_at,
        "run_id": run_id,
        "runner": {
            "repository": "A1darbek/rfc10008-interop",
            "commit": runner_commit,
        },
        "environment": {"platform": environment_platform, "transport": "http"},
        "target": metadata,
        "observations": {
            "cache_sequence": sequence,
            "error_statuses": {
                "missing_content_type": missing_type["status"],
                "unsupported_media_type": unsupported_type["status"],
                "malformed_json": malformed["status"],
            },
        },
        "rows": rows,
        "summary": summarize(rows),
    }
    cache_receipt = {
        "schema_version": "0.1",
        "generated_at": generated_at,
        "run_id": f"{run_id}-cache",
        "runner": receipt["runner"],
        "environment": receipt["environment"],
        "target": metadata,
        "sequence": sequence,
        "rows": cache_rows,
        "summary": summarize(cache_rows),
    }

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    (output / "receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output / "cache.json").write_text(
        json.dumps(cache_receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    render_text(receipt, output / "receipt.txt", "OHARU PRODUCT-SEARCH QUERY RECEIPT")
    render_text(cache_receipt, output / "cache.txt", "OHARU PRODUCT-SEARCH CACHE RECEIPT")
    print(output / "receipt.txt")
    print(output / "cache.txt")
    return 0 if receipt["summary"]["fail"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
