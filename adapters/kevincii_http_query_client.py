#!/usr/bin/env python3
"""Receipt adapter for @kevincii/http-query-client."""

import argparse
import json
import os
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
IMPLEMENTATION_COMMIT = "7fb3f7c4ff8b66a5bfd6678006e198ba3d18e647"
IMPLEMENTATION_URL = "https://github.com/Kevinci/http-query"
AYDER_COMMIT = "2ddb6e346194c445445b04a4ffa5d1f9f700eaf2"


def row(row_id, result, **fields):
    if result not in RESULTS:
        raise ValueError(f"invalid result: {result}")
    value = {"id": row_id, "result": result}
    value.update(fields)
    return value


def passfail(condition):
    return "PASS" if condition else "FAIL"


def summarize(rows):
    summary = {result.lower(): 0 for result in RESULTS}
    for item in rows:
        summary[item["result"].lower()] += 1
    return summary


def git_head(path):
    return subprocess.check_output(
        ["git", "-C", str(path), "rev-parse", "HEAD"], text=True
    ).strip()


def run_fixture(example_dir, fixture_name, environment=None):
    env = os.environ.copy()
    env.update(environment or {})
    completed = subprocess.run(
        ["npm", "exec", "--", "tsx", f"src/{fixture_name}"],
        cwd=example_dir,
        env=env,
        text=True,
        capture_output=True,
        timeout=90,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"{fixture_name} failed ({completed.returncode})\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    prefix = "INTEROP_RESULT="
    for line in reversed(completed.stdout.splitlines()):
        if line.startswith(prefix):
            return json.loads(line[len(prefix) :])
    raise RuntimeError(f"{fixture_name} did not emit INTEROP_RESULT")


def methods(trace):
    return [item.get("method") for item in trace if isinstance(item, dict)]


def request_item(trace):
    for item in trace:
        if isinstance(item, dict) and item.get("phase") == "request":
            return item
    return {}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    parser.add_argument("--implementation-dir", required=True)
    parser.add_argument("--example-dir", required=True)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--sanitize", action="store_true")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    target = json.loads(Path(args.target).read_text(encoding="utf-8"))
    implementation_dir = Path(args.implementation_dir)
    example_dir = Path(args.example_dir)
    if target["implementation_commit"] != IMPLEMENTATION_COMMIT:
        raise SystemExit("target implementation commit does not match adapter pin")
    if target["implementation_url"] != IMPLEMENTATION_URL:
        raise SystemExit("target implementation URL does not match adapter pin")
    if target["ayder"]["implementation_commit"] != AYDER_COMMIT:
        raise SystemExit("target Ayder commit does not match adapter pin")
    if git_head(implementation_dir) != IMPLEMENTATION_COMMIT:
        raise SystemExit("checked-out Kevinci implementation does not match target pin")

    native = run_fixture(
        example_dir,
        "interop-ayder-client.ts",
        {"AYDER_URL": urllib.parse.urlsplit(args.endpoint)._replace(path="", query="", fragment="").geturl()},
    )
    fallback = run_fixture(example_dir, "interop-fallback-harness.ts")
    timing = run_fixture(example_dir, "interop-timeout-harness.ts")

    native_trace = native["native"]["trace"]
    native_request = request_item(native_trace)
    native_methods = native["native"]["requestMethods"]
    configured_body = native["configuredBody"]
    request_body = native_request.get("body")
    accept_query = native["native"].get("acceptQuery")
    etag = native["native"].get("etag")
    conditional = native["conditional"]
    conditional_error = conditional.get("error") or {}

    native_fallback_trace = fallback["native"]["trace"]
    post_trace = fallback["post"]["trace"]
    get_trace = fallback["get"]["trace"]
    fallback_body = fallback["configuredBody"]
    post_wire_body = post_trace[-1].get("body") if post_trace else None
    get_url = get_trace[-1].get("url", "") if get_trace else ""
    get_query = urllib.parse.parse_qs(
        urllib.parse.urlsplit(get_url).query, keep_blank_values=True
    )
    get_serialized = (
        get_query.get("stream") == ["events"]
        and get_query.get("limit") == ["10"]
        and get_query.get("filter[active]") == ["true"]
        and get_query.get("tags") == ["priority", "audit"]
    )

    timeout_error = timing["timeout"].get("error") or {}
    abort_error = timing["externalAbort"].get("error") or {}
    timeout_within_bound = (
        timing["timeout"].get("elapsedMs", 10_000) < 1_000
        and timing["timeout"].get("configuredMs") == 50
        and timing.get("delayMs") == 2_000
    )
    abort_within_bound = (
        timing["externalAbort"].get("elapsedMs", 10_000) < 1_000
        and timing["externalAbort"].get("configuredMs") == 50
        and timing["externalAbort"].get("signalAborted") is True
    )
    abort_request_methods = timing["externalAbort"].get("requestMethods") or []

    rows = [
        row(
            "kevincii.native_query_first",
            passfail(native_methods == ["QUERY"]),
            evidence={"observed_request_methods": native_methods, "wire_status": native_trace[-1].get("status")},
        ),
        row(
            "kevincii.json_request_preserved",
            passfail(
                isinstance(configured_body, dict)
                and bool(configured_body)
                and isinstance(request_body, dict)
                and bool(request_body)
                and configured_body == request_body
                and native_request.get("contentType") == "application/json"
            ),
            evidence={
                "body_non_empty": bool(request_body),
                "body_equal": configured_body == request_body,
                "content_type": native_request.get("contentType"),
            },
        ),
        row(
            "kevincii.json_response_parsed",
            passfail(
                native["native"].get("responseParsedAsJsonObject") is True
                and native["native"].get("responseHasRows") is True
            ),
            evidence={
                "parsed_as_json_object": native["native"].get("responseParsedAsJsonObject"),
                "response_has_rows": native["native"].get("responseHasRows"),
                "response_row_count": native["native"].get("responseRowCount"),
            },
        ),
        row(
            "kevincii.accept_query_observed",
            passfail(isinstance(accept_query, str) and "application/json" in accept_query),
            evidence={"accept_query": accept_query, "observation_layer": "after-response middleware"},
        ),
        row(
            "kevincii.etag_observed",
            passfail(isinstance(etag, str) and bool(etag.strip())),
            evidence={"etag": etag, "observation_layer": "after-response middleware"},
        ),
        row(
            "kevincii.conditional_304_wire",
            passfail(
                isinstance(etag, str)
                and bool(etag)
                and conditional.get("wireStatus") == 304
                and conditional.get("requestIfNoneMatch") == etag
            ),
            evidence={
                "wire_status": conditional.get("wireStatus"),
                "etag_replayed_exactly": conditional.get("requestIfNoneMatch") == etag,
            },
        ),
        row(
            "kevincii.conditional_304_api_surface",
            "OBSERVED",
            evidence={
                "wire_status": conditional.get("wireStatus"),
                "public_surface": conditional_error.get("name"),
                "http_error": conditional_error.get("httpError"),
                "error_status": conditional_error.get("status"),
            },
        ),
        row(
            "kevincii.query_to_post_fallback",
            passfail(methods(post_trace) == ["QUERY", "POST"]),
            evidence={"observed_request_methods": methods(post_trace)},
        ),
        row(
            "kevincii.post_body_preserved",
            passfail(
                isinstance(fallback_body, dict)
                and bool(fallback_body)
                and isinstance(post_wire_body, dict)
                and bool(post_wire_body)
                and post_wire_body == fallback_body
            ),
            evidence={
                "body_non_empty": bool(post_wire_body),
                "body_equal": post_wire_body == fallback_body,
            },
        ),
        row(
            "kevincii.query_to_post_to_get_fallback",
            passfail(methods(get_trace) == ["QUERY", "POST", "GET"]),
            evidence={"observed_request_methods": methods(get_trace)},
        ),
        row(
            "kevincii.get_params_serialized",
            passfail(get_serialized),
            evidence={"get_url": get_url, "parsed_query": get_query},
        ),
        row(
            "kevincii.timeout_enforced",
            passfail(
                timeout_error.get("name") == "TimeoutError"
                and timeout_error.get("typed") is True
                and timeout_within_bound
            ),
            evidence={
                "configured_timeout_ms": timing["timeout"].get("configuredMs"),
                "server_delay_ms": timing.get("delayMs"),
                "completed_before_one_second": timeout_within_bound,
                "error_name": timeout_error.get("name"),
                "typed_timeout_error": timeout_error.get("typed"),
                "request_methods": timing["timeout"].get("requestMethods"),
            },
        ),
        row(
            "kevincii.external_abort_enforced",
            passfail(
                timing["externalAbort"].get("signalAborted") is True
                and abort_within_bound
                and abort_request_methods == ["QUERY"]
                and isinstance(abort_error.get("name"), str)
                and bool(abort_error.get("name"))
            ),
            evidence={
                "abort_after_ms": timing["externalAbort"].get("configuredMs"),
                "signal_aborted": timing["externalAbort"].get("signalAborted"),
                "completed_before_one_second": abort_within_bound,
                "request_methods": abort_request_methods,
            },
        ),
        row(
            "kevincii.abort_error_surface",
            "OBSERVED",
            evidence={
                "name": abort_error.get("name"),
                "constructor": abort_error.get("constructorName"),
            },
        ),
    ]

    generated_at = (
        "SANITIZED_EXAMPLE"
        if args.sanitize
        else datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    )
    run_id = (
        "SANITIZED-kevincii-http-query-client"
        if args.sanitize
        else f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-kevincii-http-query-client"
    )
    runner_commit = (
        "SANITIZED_RUNNER_COMMIT" if args.sanitize else git_head(root)
    )
    node_version = subprocess.check_output(["node", "--version"], text=True).strip()
    receipt = {
        "schema_version": "0.1",
        "generated_at": generated_at,
        "run_id": run_id,
        "runner": {
            "repository": "A1darbek/rfc10008-interop",
            "commit": runner_commit,
        },
        "environment": {
            "platform": "SANITIZED" if args.sanitize else platform.platform(),
            "node": "SANITIZED_NODE_20_PLUS" if args.sanitize else node_version,
            "transport": "http",
        },
        "target": {
            "id": target["id"],
            "name": target["name"],
            "implementation_url": target["implementation_url"],
            "implementation_commit": target["implementation_commit"],
            "endpoint": args.endpoint,
            "ayder": target["ayder"],
        },
        "observations": {
            "native_request_methods": native_methods,
            "post_fallback_methods": methods(post_trace),
            "get_fallback_methods": methods(get_trace),
            "conditional_wire_status": conditional.get("wireStatus"),
        },
        "rows": rows,
        "summary": summarize(rows),
    }

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    (output / "receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    summary = receipt["summary"]
    lines = [
        "============================================================",
        " KEVINCII HTTP QUERY CLIENT INTEROP RECEIPT",
        "============================================================",
        f" implementation : {target['implementation_commit']}",
        f" ayder          : {target['ayder']['implementation_commit']}",
        f" endpoint       : {args.endpoint}",
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
    for item in rows:
        lines.append(f" {item['result']:<15} {item['id']}")
        if item.get("evidence"):
            lines.append(
                "   evidence=" + json.dumps(item["evidence"], sort_keys=True)
            )
    lines.append("============================================================")
    (output / "receipt.txt").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(output / "receipt.txt")
    return 0 if summary["fail"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
