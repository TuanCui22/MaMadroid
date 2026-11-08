"""Tests for the MaMaDroid feature pipeline. No APKs, no Java, no network."""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

import numpy as np

from MaMadroid import Markov, markov_processor, paths


class TestMarkov(unittest.TestCase):
    def test_a_single_transition_normalises_to_one(self):
        matrix = Markov.main(["a\tb"], ["a", "b"])
        self.assertEqual(matrix.shape, (2, 2))
        # Every call transitions from the first state to that call, so a→b is 1.0
        self.assertAlmostEqual(matrix[0][1], 1.0)

    def test_a_row_with_no_transitions_stays_zero_not_nan(self):
        # "never left this state" and "this state does not exist" are different
        # facts; a NaN would poison every downstream feature.
        matrix = Markov.main(["a"], ["a", "b"])
        self.assertFalse(np.isnan(matrix).any())
        self.assertEqual(matrix[1].sum(), 0.0)

    def test_unknown_labels_are_dropped_not_crashed(self):
        matrix = Markov.main(["a\tzzz\tb"], ["a", "b"])
        self.assertEqual(matrix.shape, (2, 2))
        self.assertAlmostEqual(matrix[0][1], 1.0)

    def test_rows_sum_to_one_or_zero(self):
        matrix = Markov.main(["a\tb\tb\ta"], ["a", "b"])
        for row in matrix:
            total = row.sum()
            self.assertTrue(total == 0.0 or abs(total - 1.0) < 1e-9)

    def test_wf_y_splits_a_line_into_one_sequence(self):
        # wf='Y' is the abstracted-graph format: one app per line, calls tab-separated.
        matrix = Markov.main(["a\tb\tc"], ["a", "b", "c"], wf="Y")
        self.assertAlmostEqual(matrix[0][1], 0.5)
        self.assertAlmostEqual(matrix[0][2], 0.5)

    def test_wf_n_treats_each_line_as_its_own_sequence(self):
        # With wf='N' each line is a separate sequence of one state, so there is
        # no transition to count and the matrix is all zeros. This differs from
        # wf='Y' by design, not by accident.
        matrix = Markov.main(["a", "b"], ["a", "b"], wf="N")
        self.assertEqual(matrix.sum(), 0.0)

    def test_flatten_is_row_major(self):
        matrix = np.array([[1.0, 2.0], [3.0, 4.0]])
        self.assertEqual(Markov.flatten(matrix), [1.0, 2.0, 3.0, 4.0])

    def test_the_vectorised_version_matches_a_naive_loop(self):
        """The rewrite must produce the same matrix as the original algorithm."""
        nodes = ["a", "b", "c"]
        sequences = ["a\tb\tc", "b\tc", "a\tc"]

        # The 1.x algorithm, kept here as the reference implementation.
        index = {n: i for i, n in enumerate(nodes)}
        expected = np.zeros((3, 3))
        for line in sequences:
            coded = [index[x] for x in line.split("\t") if x in index]
            for i in range(1, len(coded)):
                expected[coded[0], coded[i]] += 1
        for i in range(3):
            total = expected[i].sum()
            if total:
                expected[i] = expected[i] / total

        actual = Markov.main(sequences, nodes)
        self.assertTrue(np.allclose(actual, expected))


class TestFeatureBuild(unittest.TestCase):
    def test_build_writes_a_csv_with_the_expected_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            graphs = root / "graphs"
            graphs.mkdir()
            (graphs / "app1.txt").write_text("a\tb\n", encoding="utf-8")
            lists = root / "nodes.txt"
            lists.write_text("a\nb\n", encoding="utf-8")

            summary = markov_processor.build(graphs, root / "out", "Packages", lists)
            self.assertEqual(summary.apps, 1)
            self.assertEqual(summary.states, 4)  # a, b + the two synthetic states

            with summary.output.open(encoding="utf-8") as handle:
                rows = list(csv.reader(handle))
            self.assertEqual(rows[0][0], "filename")
            self.assertIn("aTob", rows[0])
            self.assertEqual(rows[1][0], "app1.txt")
            self.assertEqual(len(rows[0]), len(rows[1]))

    def test_one_unreadable_app_does_not_abort_the_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            graphs = root / "graphs"
            graphs.mkdir()
            (graphs / "good.txt").write_text("a\tb\n", encoding="utf-8")
            lists = root / "nodes.txt"
            lists.write_text("a\nb\n", encoding="utf-8")

            original = markov_processor.build_matrix
            calls = {"n": 0}

            def flaky(sequence, nodes, wf):
                # Fail on the second app processed, whichever it is: the point is
                # that one failure does not stop the loop, not which file it was.
                calls["n"] += 1
                if calls["n"] == 2:
                    raise ValueError("synthetic failure")
                return original(sequence, nodes, wf)

            (graphs / "boom.txt").write_text("a\tb\n", encoding="utf-8")
            markov_processor.build_matrix = flaky
            try:
                summary = markov_processor.build(graphs, root / "out", "Packages", lists)
            finally:
                markov_processor.build_matrix = original

            self.assertEqual(summary.apps, 1)
            self.assertEqual(len(summary.failed), 1)

    def test_a_missing_reference_list_is_named(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            graphs = root / "graphs"
            graphs.mkdir()
            with self.assertRaises(FileNotFoundError) as ctx:
                markov_processor.build(graphs, root / "out", "Packages",
                                       root / "nope.txt")
            self.assertIn("reference list", str(ctx.exception))

    def test_a_filename_with_a_comma_survives_the_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            graphs = root / "graphs"
            graphs.mkdir()
            (graphs / "weird,name.txt").write_text("a\tb\n", encoding="utf-8")
            lists = root / "nodes.txt"
            lists.write_text("a\nb\n", encoding="utf-8")

            summary = markov_processor.build(graphs, root / "out", "Packages", lists)
            with summary.output.open(encoding="utf-8") as handle:
                rows = list(csv.reader(handle))
        self.assertEqual(rows[1][0], "weird,name.txt")


class TestPaths(unittest.TestCase):
    def test_paths_resolve_inside_the_package_by_default(self):
        # The 1.x code hard-coded C:\Users\thanh\..., so the repo only ran on one
        # machine. Everything must resolve relative to the package.
        self.assertTrue(str(paths.DATA_DIR).startswith(str(paths.PACKAGE_DIR)))

    def test_require_names_the_environment_variable(self):
        with self.assertRaises(FileNotFoundError) as ctx:
            paths.require(Path("does-not-exist.txt"), "classes.txt")
        self.assertIn("MAMADROID_", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
