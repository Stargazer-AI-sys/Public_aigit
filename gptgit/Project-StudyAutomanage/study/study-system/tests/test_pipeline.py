import copy
import csv
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from analyzer.core import analyze, from_collector, load_schema, schema_errors, strict_json
from analyzer.main import convert
from collector.main import process_file, save_inventory

ROOT = Path(__file__).resolve().parent.parent


class Stub:
    name = "test-stub"

    def __init__(self, raw=None, error=None):
        self.raw, self.error, self.called = raw, error, False

    def generate(self, messages):
        self.called = True
        if self.error:
            raise self.error
        return self.raw


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = load_schema(ROOT / "output/study_material_analysis_schema_v0.1.json")
        cls.materials = json.loads((ROOT / "output/representative_4_material_validation_v0.1.json").read_text())["materials"]

    def setUp(self):
        self.row = process_file(ROOT.parent / "sourcefile/12일차.docx")
        self.data = from_collector(self.row)
        self.response = json.loads((ROOT / "fixtures/12_day_mock_response.json").read_text())

    def test_representatives_and_original_bytes(self):
        for path in (ROOT.parent / "sourcefile").iterdir():
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            row = process_file(path)
            self.assertEqual(row["status"], "success")
            self.assertEqual(row["sha256"], before)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), before)
            self.assertEqual(from_collector(row)["extracted_text"], row["text"])
        for material in self.materials:
            self.assertFalse(schema_errors(material, self.schema))

    def test_success_source_override_and_prompt(self):
        response = copy.deepcopy(self.response)
        response["source"] = {"material_id": "fake"}
        result, audit = analyze(self.data, Stub(json.dumps(response)), self.schema)
        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["analysis"]["source"]["material_id"], self.row["sha256"])
        self.assertTrue(audit["trace"]["warnings"])
        self.assertFalse(audit["trace"]["actual_ai_call"])
        payload = json.loads(audit["prompt"][1]["content"].split("\n", 1)[1])
        self.assertEqual(payload["content"], self.row["text"])

    def test_four_error_codes(self):
        for raw, error, code in [(None, TimeoutError("test"), "AI_CALL_ERROR"),
                                 ("```json\n{}\n```", None, "JSON_PARSE_ERROR"),
                                 ('{"summary":"test"}', None, "SCHEMA_VALIDATION_ERROR")]:
            result, _ = analyze(self.data, Stub(raw, error), self.schema)
            self.assertEqual(result["error"]["code"], code)
        provider = Stub("{}")
        result, _ = analyze(dict(self.data, material_id="wrong"), provider, self.schema)
        self.assertEqual(result["error"]["code"], "SOURCE_METADATA_ERROR")
        self.assertFalse(provider.called)

    def test_empty_text_rejected_without_call(self):
        provider = Stub("{}")
        result, _ = analyze(dict(self.data, extracted_text=" \n"), provider, self.schema)
        self.assertEqual(result["error"]["code"], "INPUT_VALIDATION_ERROR")
        self.assertFalse(provider.called)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty.txt"
            path.write_text(" \n")
            self.assertEqual(process_file(path)["status"], "error")

    def test_csv_filter_and_metadata_rules(self):
        rows = [self.row, dict(self.row, status="error"), dict(self.row, sha256="oops"),
                dict(self.row, text=""), dict(self.row, extension=".txt")]
        accepted, rejected = convert(rows)
        self.assertEqual(len(accepted), 1)
        self.assertEqual(len(rejected), 4)

    def test_strict_json_and_array_schema(self):
        for raw in ['{"a":NaN}', '{"a":Infinity}', '{"a":1e999}', '{"a":1,"a":2}', '{} trailing']:
            with self.assertRaises(ValueError):
                strict_json(raw)
        result, _ = analyze(self.data, Stub("[]"), self.schema)
        self.assertEqual(result["error"]["code"], "SCHEMA_VALIDATION_ERROR")

    def test_schema_boundary_conditions(self):
        for field, value in [("practice", []), ("theory", {}), ("memo", "extra")]:
            result, _ = analyze(self.data, Stub(json.dumps(dict(self.response, **{field: value}))), self.schema)
            self.assertEqual(result["error"]["code"], "SCHEMA_VALIDATION_ERROR")
        response = copy.deepcopy(self.response)
        response["material_type"]["confidence"] = 90
        result, _ = analyze(self.data, Stub(json.dumps(response)), self.schema)
        self.assertEqual(result["error"]["code"], "SCHEMA_VALIDATION_ERROR")

    def test_repeat_csv_backup_and_multiline_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inventory.csv"
            save_inventory([self.row], path)
            before = path.read_bytes()
            save_inventory([self.row], path)
            backups = list(path.parent.glob("*.backup_*.csv"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_bytes(), before)
            with path.open(encoding="utf-8-sig", newline="") as file:
                row = next(csv.DictReader(file))
            self.assertEqual(row["text"], self.row["text"])

    def test_evidence_quotes_present(self):
        evidence = [item["evidence"] for items in self.response["theory"].values() for item in items]
        evidence += [item["evidence"] for item in self.response["practice"]]
        for quote in evidence:
            self.assertIn(quote, self.data["extracted_text"])

    def test_cli_saves_success_and_failure_separately(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            inventory = path / "inventory.csv"
            save_inventory([self.row], inventory)
            response = path / "response.json"
            response.write_text(json.dumps(self.response))
            args = [sys.executable, "-m", "analyzer.main", "run", "--inventory", str(inventory),
                    "--filename", "12일차.docx", "--response-file", str(response), "--schema", str(ROOT / 'output/study_material_analysis_schema_v0.1.json'), "--output-dir", str(path / "runs")]
            self.assertEqual(subprocess.run(args, cwd=ROOT, capture_output=True).returncode, 0)
            response.write_text("broken JSON")
            self.assertEqual(subprocess.run(args, cwd=ROOT, capture_output=True).returncode, 1)
            runs = list((path / "runs").iterdir())
            self.assertEqual(len(runs), 2)
            self.assertEqual(sum((run / "success/analysis.json").exists() for run in runs), 1)
            self.assertEqual(sum((run / "failed/result.json").exists() for run in runs), 1)
            for run in runs:
                self.assertFalse(json.loads((run / "trace.json").read_text())["actual_ai_call"])


if __name__ == "__main__":
    unittest.main()
