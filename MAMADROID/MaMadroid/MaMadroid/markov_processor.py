"""Feature-matrix assembly for one mode (class, package or family).

Output goes through ``csv.writer``: a hand-rolled join breaks on any filename
containing a comma and quotes nothing. The function returns a summary rather than
printing, so the caller decides what to show.
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from pathlib import Path

from .Markov import flatten
from .Markov import main as build_matrix

log = logging.getLogger("mamadroid.features")


@dataclass
class FeatureSummary:
    mode: str
    apps: int
    states: int
    output: Path
    failed: list[str]

    def as_dict(self) -> dict[str, object]:
        return {
            "mode": self.mode,
            "apps": self.apps,
            "states": self.states,
            "output": str(self.output),
            "failed": self.failed,
        }


def load_nodes(list_file: str | Path) -> list[str]:
    """The reference list, plus the two synthetic states the model always has."""
    path = Path(list_file)
    if not path.is_file():
        raise FileNotFoundError(
            "reference list not found: %s. This file defines the Markov state "
            "space; without it every app produces a zero matrix." % path)
    with path.open(encoding="utf-8", errors="replace") as handle:
        nodes = [line.strip() for line in handle if line.strip()]
    # Kept for parity with the original model: these two states exist in the
    # published feature set and a model trained on it expects them.
    for synthetic in ("self-defined", "obfuscated"):
        if synthetic not in nodes:
            nodes.append(synthetic)
    return nodes


def build(directory: str | Path, output_path: str | Path, mode: str,
          list_file: str | Path, *, wf: str = "Y") -> FeatureSummary:
    """Build ``result.csv`` for one mode.

    One unreadable app is recorded and skipped; it does not abort the run. That
    matters because a corpus of a few thousand APKs almost always contains one
    that the abstractor could not handle.
    """
    directory = Path(directory)
    output_path = Path(output_path)
    if not directory.is_dir():
        raise FileNotFoundError("graph directory not found: %s" % directory)

    nodes = load_nodes(list_file)
    header = ["filename"]
    for source in nodes:
        for target in nodes:
            header.append("%sTo%s" % (source, target))

    apps = sorted(p for p in directory.iterdir() if p.is_file())
    log.info("%s: %d app(s), %d state(s)", mode, len(apps), len(nodes))

    rows: list[list[object]] = []
    failed: list[str] = []
    for app in apps:
        try:
            with app.open(encoding="utf-8", errors="replace") as handle:
                sequence = [line.rstrip("\n") for line in handle]
            matrix = build_matrix(sequence, nodes, wf)
        except Exception as exc:  # noqa: BLE001 - one bad app must not stop the run
            log.warning("%s: could not build a matrix (%s)", app.name, exc)
            failed.append(app.name)
            continue
        rows.append([app.name] + flatten(matrix))

    out_dir = output_path / mode
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "result.csv"
    with out_file.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)

    log.info("%s: wrote %s (%d row(s), %d failed)", mode, out_file, len(rows), len(failed))
    return FeatureSummary(mode=mode, apps=len(rows), states=len(nodes),
                          output=out_file, failed=failed)


def process_files(directory: str | Path, output_path: str | Path, which_class: str,
                  filename_list: str | Path, logfile: str | Path | None = None,
                  wf: str = "Y") -> FeatureSummary:
    """Compatibility entry point.

    ``logfile`` is accepted and ignored beyond a debug note: the log is already
    on stderr, and re-reading it would duplicate every line.
    """
    if logfile:
        log.debug("logfile argument is accepted for compatibility and not re-read")
    return build(directory, output_path, which_class, filename_list, wf=wf)
