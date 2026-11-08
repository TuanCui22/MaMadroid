"""Command-line entry point for MaMaDroid.

Exit codes, because a pipeline that converts nothing should not exit 0:

  0  every stage clean
  1  a stage had failures (listed on stderr)
  2  the input or output path is wrong
  3  a required reference file is missing
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from . import __version__, paths
from .mamadroid import MissingDependency, run
from .report import write as write_report

EXIT_OK = 0
EXIT_PARTIAL = 1
EXIT_PATH = 2
EXIT_DATA = 3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mamadroid",
        description="Build MaMaDroid Markov-chain features from a directory of APK files.",
        epilog="Reference data resolves from the package directory. Override with "
               "MAMADROID_DATA_DIR or --data-dir.",
    )
    parser.add_argument("--version", action="version",
                        version="mamadroid %s" % __version__)
    parser.add_argument("-i", "--input", required=True, metavar="DIR",
                        help="directory containing the APK files to analyse")
    parser.add_argument("-o", "--output", required=True, metavar="DIR",
                        help="directory for graphs, sequences and feature CSVs")
    parser.add_argument("-m", "--mode", action="append", metavar="MODE",
                        choices=["Families", "Packages", "Classes"],
                        help="feature mode; repeatable (default Families and Packages)")
    parser.add_argument("--data-dir", metavar="DIR",
                        help="directory holding classes.txt, Packages.txt, Families11.txt")
    parser.add_argument("--memory", metavar="SIZE",
                        help="JVM heap for the APK tooling, e.g. 2G (default %s)"
                             % paths.DEFAULT_MEMORY)
    parser.add_argument("--log-level", metavar="LEVEL", default="INFO",
                        help="DEBUG, INFO, WARNING, ERROR (default INFO)")
    parser.add_argument("--json", dest="json_out", action="store_true",
                        help="print the run summary as JSON on stdout")
    parser.add_argument("--report", metavar="PATH",
                        help="also write a self-contained HTML run report")
    parser.add_argument("--summary-in", metavar="PATH",
                        help="a run summary JSON to embed in the report "
                             "(default: the one this run wrote)")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    modes = tuple(args.mode) if args.mode else ("Families", "Packages")

    try:
        summary = run(args.input, args.output, data_dir=args.data_dir,
                      memory=args.memory or paths.DEFAULT_MEMORY,
                      modes=modes, log_level=args.log_level)
    except MissingDependency as exc:
        print("error: %s" % exc, file=sys.stderr)
        return EXIT_DATA
    except FileNotFoundError as exc:
        # A missing reference file is a setup problem, not a run failure.
        message = str(exc)
        code = EXIT_DATA if "MAMADROID_" in message else EXIT_PATH
        print("error: %s" % message, file=sys.stderr)
        return code

    if args.json_out:
        print(json.dumps(summary.as_dict(), indent=2, sort_keys=True))
    else:
        print("\nstages:")
        for stage in summary.stages:
            mark = "ok" if stage.ok else "FAILED"
            print("  %-12s %-6s %d processed, %d failed"
                  % (stage.name, mark, stage.processed, len(stage.failed)))
            for name in stage.failed[:10]:
                print("      %s" % name)
            if len(stage.failed) > 10:
                print("      … and %d more" % (len(stage.failed) - 10))
        if summary.features:
            print("\nfeatures:")
            for entry in summary.features:
                if "skipped" in entry:
                    print("  %-10s skipped: %s" % (entry.get("mode"), entry["skipped"]))
                else:
                    print("  %-10s %d app(s), %d state(s) -> %s"
                          % (entry["mode"], entry["apps"], entry["states"],
                             entry["output"]))
        print("\nfinished in %.1fs" % summary.seconds)

    if args.report:
        summary_path = args.summary_in
        if not summary_path:
            # The run already wrote one next to the output; use it so the page
            # shows the same numbers this process just printed.
            candidate = Path(args.output).expanduser() / "MaMadroid" / "run-summary.json"
            summary_path = str(candidate) if candidate.is_file() else None
        out = write_report(args.output, args.report, summary_path=summary_path)
        print("wrote %s" % out)

    return EXIT_OK if summary.ok else EXIT_PARTIAL


if __name__ == "__main__":
    raise SystemExit(main())
