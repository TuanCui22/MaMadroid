"""MaMaDroid pipeline: APK → call graph → abstracted sequence → Markov matrix.

Three properties shape it:

* every path resolves from the package directory and is overridable by
  environment, so a clone runs anywhere;
* a stage that fails is reported per file, and the exit code reflects it;
* the run returns a summary object rather than printing as it goes.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path

from . import paths

log = logging.getLogger("mamadroid")

#: Package that provides each stage, so a missing dependency names itself.
STAGE_REQUIREMENTS = {
    "apk_to_gml": ("androguard", "networkx"),
    "gml_to_txt": ("igraph",),
    "abstract": (),
    "features": ("numpy",),
}


class MissingDependency(Exception):
    """A stage's third-party dependency is not installed."""

    def __init__(self, stage: str, packages: tuple[str, ...]):
        self.stage = stage
        self.packages = packages
        super().__init__(
            "stage %r needs %s. Install with: python -m pip install %s"
            % (stage, ", ".join(packages), " ".join(packages)))


def _require(stage: str) -> None:
    """Import the stage's dependencies, or say exactly what is missing."""
    import importlib
    missing = []
    for package in STAGE_REQUIREMENTS.get(stage, ()):
        try:
            importlib.import_module(package)
        except ImportError:
            missing.append(package)
    if missing:
        raise MissingDependency(stage, tuple(missing))


@dataclass
class StageResult:
    name: str
    processed: int = 0
    failed: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.failed


@dataclass
class RunSummary:
    apk_dir: Path
    output_dir: Path
    stages: list[StageResult] = field(default_factory=list)
    features: list[dict] = field(default_factory=list)
    seconds: float = 0.0

    @property
    def ok(self) -> bool:
        return all(stage.ok for stage in self.stages)

    def as_dict(self) -> dict:
        return {
            "apk_dir": str(self.apk_dir),
            "output_dir": str(self.output_dir),
            "seconds": round(self.seconds, 2),
            "ok": self.ok,
            "stages": [
                {"name": s.name, "processed": s.processed, "failed": s.failed}
                for s in self.stages
            ],
            "features": self.features,
        }


def setup_logging(output: Path, level: str = "INFO") -> Path:
    """Log to a file inside the output tree, and to stderr."""
    log_dir = output / "MaMadroid"
    log_dir.mkdir(parents=True, exist_ok=True)
    logfile = log_dir / "run.log"

    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    for handler in list(root.handlers):
        root.removeHandler(handler)

    file_handler = logging.FileHandler(logfile, encoding="utf-8")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    root.addHandler(file_handler)

    stream = logging.StreamHandler()
    stream.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    root.addHandler(stream)
    return logfile


def apk_to_gml(apk_dir: Path, gml_dir: Path) -> StageResult:
    """APK → call graph in GML. One bad APK does not stop the batch."""
    _require("apk_to_gml")
    from .apk2graph import extractcg

    result = StageResult("apk_to_gml")
    gml_dir.mkdir(parents=True, exist_ok=True)
    for apk in sorted(apk_dir.glob("*.apk")):
        target = gml_dir / (apk.stem + ".gml")
        try:
            extractcg(str(apk), str(target))
        except Exception as exc:  # noqa: BLE001 - per-file isolation is the point
            log.warning("%s: could not extract a call graph (%s)", apk.name, exc)
            result.failed.append(apk.name)
        else:
            result.processed += 1
            log.info("%s: call graph written", apk.name)
    return result


def gml_to_txt(gml_dir: Path, txt_dir: Path) -> StageResult:
    """GML → caller/callee sequences, one line per call."""
    _require("gml_to_txt")
    from .gml2txt import caller2callee, gml2graph

    result = StageResult("gml_to_txt")
    txt_dir.mkdir(parents=True, exist_ok=True)
    for gml in sorted(gml_dir.glob("*.gml")):
        target = txt_dir / (gml.stem + ".txt")
        try:
            graph, edges = gml2graph(str(gml))
            caller2callee(edges, graph.vs, str(target))
        except Exception as exc:  # noqa: BLE001
            log.warning("%s: could not flatten the graph (%s)", gml.name, exc)
            result.failed.append(gml.name)
        else:
            result.processed += 1
    return result


def abstract(txt_dir: Path, data_dir: Path) -> StageResult:
    """Map raw calls onto the class/package/family vocabulary."""
    _require("abstract")
    from .abstractGraph import _preprocess_graph

    result = StageResult("abstract")
    for txt in sorted(txt_dir.glob("*.txt")):
        try:
            _preprocess_graph(str(txt), str(data_dir))
        except Exception as exc:  # noqa: BLE001
            log.warning("%s: could not abstract (%s)", txt.name, exc)
            result.failed.append(txt.name)
        else:
            result.processed += 1
            log.info("%s: abstracted", txt.name)
    return result


def run(apk_dir: str | Path, output_dir: str | Path, *,
        data_dir: str | Path | None = None,
        memory: str | None = None,
        modes: tuple[str, ...] = ("Families", "Packages"),
        log_level: str = "INFO") -> RunSummary:
    """The whole pipeline. Returns a summary; never raises for one bad APK."""
    started = time.time()
    apk_dir = Path(apk_dir).expanduser().resolve()
    output_dir = Path(output_dir).expanduser().resolve()
    data_dir = Path(data_dir).expanduser().resolve() if data_dir else paths.DATA_DIR

    if not apk_dir.is_dir():
        raise FileNotFoundError("APK directory not found: %s" % apk_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if memory:
        os.environ["JAVA_TOOL_OPTIONS"] = "-Xmx%s" % memory

    setup_logging(output_dir, log_level)
    summary = RunSummary(apk_dir=apk_dir, output_dir=output_dir)
    log.info("MaMaDroid run: %s -> %s", apk_dir, output_dir)

    gml_dir = output_dir / "MaMadroid" / "gml"
    txt_dir = output_dir / "MaMadroid" / "graphs" / "Trial1"

    summary.stages.append(apk_to_gml(apk_dir, gml_dir))
    summary.stages.append(gml_to_txt(gml_dir, txt_dir))
    summary.stages.append(abstract(txt_dir, data_dir))

    features_root = output_dir / "MaMadroid" / "Features"
    reference = {
        "Families": (paths.FAMILY_GRAPHS_DIR, paths.FAMILIES_FILE),
        "Packages": (paths.PACKAGE_GRAPHS_DIR, paths.PACKAGES_FILE),
        "Classes": (paths.CLASS_GRAPHS_DIR, paths.CLASSES_FILE),
    }
    for mode in modes:
        graph_dir, list_file = reference[mode]
        if not graph_dir.is_dir():
            log.warning("%s: reference graphs missing at %s; skipping this mode",
                        mode, graph_dir)
            summary.features.append({"mode": mode, "skipped": "reference graphs missing"})
            continue
        _require("features")
        from .markov_processor import build as build_features

        try:
            built = build_features(graph_dir, features_root, mode, list_file)
        except FileNotFoundError as exc:
            log.warning("%s: %s", mode, exc)
            summary.features.append({"mode": mode, "skipped": str(exc)})
        else:
            summary.features.append(built.as_dict())

    summary.seconds = time.time() - started
    log.info("finished in %.1fs (%s)", summary.seconds,
             "clean" if summary.ok else "with failures")
    return summary
