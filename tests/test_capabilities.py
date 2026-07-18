import importlib.util
import unittest
from pathlib import Path


RUNNER_PATH = Path(__file__).resolve().parents[1] / "runner" / "run.py"
SPEC = importlib.util.spec_from_file_location("runner_run", RUNNER_PATH)
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class CapabilityMappingTests(unittest.TestCase):
    def test_declared_capability_passes_when_observed(self):
        actual = runner.capability_row(
            "representation.etag_advertised",
            {"etag": True},
            "etag",
            True,
            evidence={"etag": '"abc"'},
        )
        self.assertEqual(actual["result"], "PASS")

    def test_declared_capability_fails_when_missing(self):
        actual = runner.capability_row(
            "representation.etag_advertised",
            {"etag": True},
            "etag",
            False,
        )
        self.assertEqual(actual["result"], "FAIL")

    def test_undeclared_optional_capability_is_not_supported(self):
        actual = runner.capability_row(
            "representation.content_location",
            {"content_location": False},
            "content_location",
            False,
        )
        self.assertEqual(actual["result"], "NOT_SUPPORTED")

    def test_status_expectation_observe_mode(self):
        actual = runner.status_row(
            "core.missing_content_type",
            observed_status=400,
            expected_status=None,
            mode="observe",
        )
        self.assertEqual(actual["result"], "OBSERVED")
        self.assertEqual(actual["observed"], 400)


if __name__ == "__main__":
    unittest.main()
