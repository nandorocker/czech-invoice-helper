import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AlfredModeTests(unittest.TestCase):
    def test_invalid_date_outputs_json_only(self):
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "czk-exchange.py"),
                "--alfred",
                "--date=bad-date",
                "--alfred-query=EUR",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(result.stdout)

        self.assertEqual(payload["items"][0]["title"], "Invalid date")
        self.assertIs(payload["items"][0]["valid"], False)
