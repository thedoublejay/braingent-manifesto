from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from braingent import config_drift, core


def write_contract(directory: Path, service: str, variables: list[str], *, required: list[str] | None = None, sha: str = "abc") -> None:
    payload = {
        "fields": {name.lower(): [name] for name in variables},
        "required_fields": required or [],
        "service": service,
        "source_config_sha256": sha,
        "version": 1,
    }
    (directory / f"{service}.json").write_text(json.dumps(payload), encoding="utf-8")


class ConfigDriftTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.contracts = Path(self._tmp.name) / "contracts"
        self.deployed = Path(self._tmp.name) / "deployed"
        self.contracts.mkdir()
        self.deployed.mkdir()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def run_cli(self, *extra: str) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = core.main(["config-drift", "--contracts", str(self.contracts), "--deployed", str(self.deployed), *extra])
        return code, out.getvalue()

    def test_matching_directories_have_no_drift(self) -> None:
        for directory in (self.contracts, self.deployed):
            write_contract(directory, "app", ["LOG_LEVEL", "PORT"])
        report = config_drift.run_config_drift(self.contracts, self.deployed)
        self.assertFalse(report.has_drift)
        self.assertEqual(report.compared, 1)
        code, text = self.run_cli()
        self.assertEqual(code, 0)
        self.assertIn("No config drift", text)

    def test_reports_keys_missing_on_either_side_and_exits_non_zero(self) -> None:
        write_contract(self.contracts, "app", ["LOG_LEVEL", "NEW_SETTING"], required=["log_level"], sha="one")
        write_contract(self.deployed, "app", ["LOG_LEVEL", "STALE_SETTING"], sha="two")
        code, text = self.run_cli("--json")
        payload = json.loads(text)
        self.assertEqual(code, 1)
        (drift,) = payload["drifted"]
        self.assertEqual(drift["missing_in_deployed"], ["NEW_SETTING"])
        self.assertEqual(drift["missing_in_contract"], ["STALE_SETTING"])
        self.assertEqual(drift["required_only_in_contract"], ["log_level"])
        self.assertEqual(drift["sha_mismatch"], ["one", "two"])

    def test_services_present_on_one_side_only(self) -> None:
        write_contract(self.contracts, "only-contract", ["A"])
        write_contract(self.deployed, "only-deployed", ["A"])
        report = config_drift.run_config_drift(self.contracts, self.deployed)
        self.assertEqual(report.services_only_in_contracts, ("only-contract",))
        self.assertEqual(report.services_only_in_deployed, ("only-deployed",))
        self.assertEqual(self.run_cli()[0], 1)

    def test_unreadable_contract_exits_two(self) -> None:
        (self.contracts / "bad.json").write_text("{not json", encoding="utf-8")
        code, _ = self.run_cli()
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
