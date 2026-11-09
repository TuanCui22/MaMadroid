"""Tests for the MaMaDroid HTML report. No APKs, no Java, no network."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from MaMadroid import report


def write_result(path: Path, rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerows(rows)


class TestAnalyseCsv(unittest.TestCase):
    def test_counts_apps_states_and_density(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "result.csv"
            # 2x2 state space -> 4 pair columns
            write_result(path, [
                ["filename", "aToa", "aTob", "bToa", "bTob"],
                ["app1.txt", "1", "0", "0", "1"],
                ["app2.txt", "0", "0", "0", "0"],
            ])
            stats = report.analyse_csv(path, "Packages")

        self.assertEqual(stats.apps, 2)
        self.assertEqual(stats.columns, 4)
        self.assertEqual(stats.states, 2)
        self.assertEqual(stats.non_zero_cells, 2)
        self.assertEqual(stats.total_cells, 8)
        self.assertAlmostEqual(stats.density, 0.25)

    def test_an_all_zero_row_is_named_not_counted_as_fine(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "result.csv"
            write_result(path, [
                ["filename", "aToa"],
                ["empty.txt", "0"],
                ["full.txt", "1"],
            ])
            stats = report.analyse_csv(path, "Families")

        self.assertEqual(stats.empty_rows, ["empty.txt"])

    def test_a_missing_file_yields_an_empty_stat_not_a_crash(self):
        stats = report.analyse_csv(Path("does-not-exist.csv"), "Families")
        self.assertEqual(stats.apps, 0)
        self.assertIsNone(stats.density)

    def test_a_header_only_file_is_zero_apps(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "result.csv"
            write_result(path, [["filename", "aToa", "aTob"]])
            stats = report.analyse_csv(path, "Families")
        self.assertEqual(stats.apps, 0)
        self.assertEqual(stats.columns, 2)

    def test_a_non_numeric_cell_is_skipped_not_counted(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "result.csv"
            write_result(path, [
                ["filename", "aToa", "aTob"],
                ["app.txt", "1", "not-a-number"],
            ])
            stats = report.analyse_csv(path, "Families")
        self.assertEqual(stats.non_zero_cells, 1)


class TestCollectAndRender(unittest.TestCase):
    def test_collect_finds_every_mode_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for mode in ("Families", "Packages"):
                write_result(root / "MaMadroid" / "Features" / mode / "result.csv",
                             [["filename", "aToa"], ["app.txt", "1"]])
            data = report.collect(root)

        self.assertEqual(data["mode_count"], 2)
        self.assertEqual([m["mode"] for m in data["modes"]], ["Families", "Packages"])

    def test_a_missing_features_directory_is_null_not_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = report.collect(Path(tmp))
        # null means "not measured"; 0 would mean "measured, found nothing".
        self.assertIsNone(data["mode_count"])

    def test_the_page_embeds_the_data_and_has_no_external_requests(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_result(root / "MaMadroid" / "Features" / "Families" / "result.csv",
                         [["filename", "aToa"], ["app.txt", "1"]])
            page = report.render(report.collect(root))

        self.assertIn("BOLTER", page)
        self.assertNotIn("src=\"http", page)
        self.assertNotIn("href=\"http", page)
        self.assertIn("<style>", page)

    def test_the_summary_is_embedded_when_supplied(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary = root / "summary.json"
            summary.write_text(json.dumps({
                "ok": False,
                "stages": [{"name": "apk_to_gml", "processed": 3,
                            "failed": ["bad.apk"]}],
            }), encoding="utf-8")
            data = report.collect(root, summary)

        self.assertFalse(data["summary"]["ok"])
        self.assertEqual(data["summary"]["stages"][0]["failed"], ["bad.apk"])

    def test_a_corrupt_summary_is_reported_not_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary = root / "summary.json"
            summary.write_text("{not json", encoding="utf-8")
            data = report.collect(root, summary)

        self.assertIn("error", data["summary"])

    def test_write_creates_the_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "nested" / "report.html"
            written = report.write(root, out)
            self.assertTrue(written.is_file())
            self.assertGreater(written.stat().st_size, 1000)


if __name__ == "__main__":
    unittest.main()
