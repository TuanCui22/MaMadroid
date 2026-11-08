# MaMaDroid — Markov-chain behavioural features for Android APKs

Turns an APK into a fixed-size numeric feature vector by walking its call graph
and recording which abstracted API states transition into which. The vector is
what a classifier consumes; this repository produces the vector, not the
classifier.

This is a maintained fork of the code released with the NDSS 2017 paper
*MaMaDroid: Detecting Android Malware by Building Markov Chains of Behavioral
Models* (Graziano, Canali, Bilge, Rao, Balzarotti). The method is theirs. The
packaging, the path handling and the vectorised matrix build are this fork's.

---

## What changed in 2.0

The 1.x code worked on exactly one machine, and the README told you to install a
`requirements.txt` that did not exist.

| 1.x | 2.0 |
|---|---|
| three absolute `C:\Users\thanh\...` paths inside `mamadroid_main` | every path resolves from the package directory, overridable by `MAMADROID_*` env vars |
| `requirements.txt` referenced but absent | dependencies declared in `pyproject.toml` |
| `python mamadroid.py -f … -d …` | `mamadroid -i … -o …`, plus `--json` for machine output |
| triple Python loop per app for the matrix | `numpy.add.at` scatter-add; same matrix, verified against the old algorithm in a test |
| `except Exception` + log line, exit 0 | per-stage failure lists, exit code reflects them |
| CSV written with `','.join` | `csv.writer` — a filename containing a comma no longer breaks the row |
| bare-name imports (`from gml2txt import …`) | relative imports with a script-mode fallback, so both invocation styles work |
| `--help` failed without igraph installed | analysis imports are lazy; `--help` and `--version` work on a bare Python |
| log file read back and printed | logging goes to the file and to stderr, once |

The matrix build is the change that matters for throughput. The original did, for
every call in every app, a nested loop over the whole state space. For a few
thousand APKs against a 400-node vocabulary that is tens of millions of
interpreted iterations. The replacement encodes once, scatter-adds once, and
normalises once — and a test asserts it produces the same matrix as the original
loop, so the speedup is not a behaviour change.

---

## Install

```bash
git clone https://github.com/TuanCui22/MaMadroid.git
cd MaMadroid
python -m pip install -e .
```

The analysis stages also need a JVM and `apktool` on `PATH` (the APK → call-graph
stage shells out to them). `python -m pip install -e ".[dev]"` adds the test
tools.

## Use

```bash
mamadroid -i /path/to/apks -o /path/to/output
```

| flag | meaning |
|---|---|
| `-i, --input DIR` | directory of `.apk` files to analyse |
| `-o, --output DIR` | where graphs, sequences and feature CSVs are written |
| `-m, --mode MODE` | `Families`, `Packages` or `Classes`; repeatable. Default: Families and Packages |
| `--data-dir DIR` | where `classes.txt`, `Packages.txt`, `Families11.txt` live |
| `--memory SIZE` | JVM heap for the APK tooling, e.g. `2G` |
| `--json` | print the run summary as JSON instead of text |

Exit codes: `0` clean, `1` a stage had failures, `2` a path is wrong, `3` a
required reference file or dependency is missing.

### What it produces

```
output/
  MaMadroid/
    run.log              every stage, every file, timestamped
    gml/                 one call graph per APK
    graphs/Trial1/       one caller→callee sequence per APK
    Features/
      Families/result.csv
      Packages/result.csv
```

Each `result.csv` has one row per APK: `filename`, then one column per
`stateAToB` pair. The column set is fixed by the reference list, so rows from
different runs line up.

## Reference data

The state vocabulary comes from three lists shipped in the package:
`classes.txt`, `Packages.txt`, `Families11.txt`. Two synthetic states
(`self-defined`, `obfuscated`) are appended, matching the published feature set —
a model trained on the paper's features expects those columns to exist.

If your reference data lives elsewhere, point at it:

```bash
export MAMADROID_DATA_DIR=/data/mamadroid
# or per file:
export MAMADROID_PACKAGES=/data/mamadroid/Packages.txt
```

A missing reference file is reported by name with the variable to set, at the
start of the run — not as a `FileNotFoundError` after twenty minutes of APK
conversion.

## Tests

```bash
python -m pytest -q          # 14 tests, no APKs, no Java, no network
```

The suite covers the matrix build (including a comparison against the original
loop algorithm), the zero-row case, unknown-label handling, CSV quoting, per-app
failure isolation, and the path resolution that used to be hard-coded.

## Layout

```
MAMADROID/MaMadroid/MaMadroid/
  cli.py               argument parsing, exit codes
  mamadroid.py         the pipeline: apk → gml → txt → abstract → features
  paths.py             every path, resolved once, env-overridable
  Markov.py            the transition matrix (vectorised)
  markov_processor.py  feature-matrix assembly and CSV output
  abstractGraph.py     call → abstract state mapping
  apk2graph.py         APK → call graph
  gml2txt.py           graph → caller/callee sequences
  parse.py             label parsing
  FamilytoMak.py       standalone family-mode driver (legacy)
  PackagetoMak.py      standalone package-mode driver (legacy)
  tests/test_markov.py
```

`FamilytoMak.py` and `PackagetoMak.py` are the original standalone drivers, kept
because the paper's reproduction steps reference them. The `mamadroid` command
does the same work with path handling that is not machine-specific.

## Citation

> MaMaDroid: Detecting Android Malware by Building Markov Chains of Behavioral Models
> Mariano Graziano, Davide Canali, Leyla Bilge, Ashwin Rao, Davide Balzarotti
> NDSS 2017

## Licence

Private research artefact. Not open source, not for redistribution. See
[`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).
