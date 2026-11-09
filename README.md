![BOLTER](docs/banner.svg)

# BOLTER

**Markov-chain behavioural features for Android APKs.**

Turns an APK into a fixed-size numeric feature vector by walking its call graph
and recording which abstracted API states transition into which. The vector is
what a classifier consumes; this repository produces the vector, not the
classifier.

This is a maintained fork of the code released with the NDSS 2017 paper
*MaMaDroid: Detecting Android Malware by Building Markov Chains of Behavioral
Models* (Graziano, Canali, Bilge, Rao, Balzarotti). The method is theirs. The
packaging, the path handling and the vectorised matrix build are this fork's.

---

## Capabilities

| | |
|---|---|
| **Three abstraction modes** | `Families`, `Packages` and `Classes`, selectable per run and repeatable. Each defines its own state vocabulary. |
| **Vectorised matrix build** | Transitions are accumulated with a single scatter-add over index arrays rather than a nested loop per call. A test asserts the result matches the reference algorithm exactly. |
| **Portable paths** | Every path resolves from the package directory and is overridable with `MAMADROID_*` environment variables. A missing reference file is reported by name at the start of the run. |
| **Per-app isolation** | An APK that fails to convert is recorded and skipped; the batch continues and the exit code reflects it. |
| **Structured output** | One CSV per mode, one row per APK, a fixed column set so rows from different runs line up. `--json` for machine consumption. |
| **Lazy analysis imports** | `--help` and `--version` work on a bare Python. A missing analysis dependency names the package and the install command. |
| **Honest zero rows** | A state with no outgoing transitions stays all-zero rather than becoming NaN — "never left this state" and "this state does not exist" are different facts. |
| **Run report** | `--report out.html` writes one self-contained page: stage counts, per-mode density, and every app that produced an all-zero row, named. No server, no external requests. |

---

## Install

```bash
git clone https://github.com/TuanCui22/MaMadroid.git
cd MaMadroid
python -m pip install -e .
```

The analysis stages also need a JVM and `apktool` on `PATH` (the APK → call-graph
stage shells out to them). `python -m pip install -e ".[dev]"` adds the test tools.

## Use

```bash
mamadroid -i /path/to/apks -o /path/to/output
```

| Flag | Meaning |
|---|---|
| `-i, --input DIR` | directory of `.apk` files to analyse |
| `-o, --output DIR` | where graphs, sequences and feature CSVs are written |
| `-m, --mode MODE` | `Families`, `Packages` or `Classes`; repeatable. Default: Families and Packages |
| `--data-dir DIR` | where `classes.txt`, `Packages.txt`, `Families11.txt` live |
| `--memory SIZE` | JVM heap for the APK tooling, e.g. `2G` |
| `--json` | print the run summary as JSON instead of text |
| `--report PATH` | also write a self-contained HTML run report |
| `--summary-in PATH` | a run summary JSON to embed in the report |
| `--log-level LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

Exit codes: `0` clean, `1` a stage had failures, `2` a path is wrong, `3` a
required reference file or dependency is missing.

### Output

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
different runs align.

## Reference data

The state vocabulary comes from three lists shipped in the package:
`classes.txt`, `Packages.txt`, `Families11.txt`. Two synthetic states
(`self-defined`, `obfuscated`) are appended, matching the published feature set —
a model trained on the paper's features expects those columns to exist.

To point at reference data elsewhere:

```bash
export MAMADROID_DATA_DIR=/data/mamadroid
# or per file:
export MAMADROID_PACKAGES=/data/mamadroid/Packages.txt
```

## Run report

```bash
mamadroid -i /path/to/apks -o /path/to/output --report output/report.html
```

One self-contained HTML file: inline CSS, no script tags fetching anything, no
listening port. It answers three questions in the order an analyst asks them —
did the run work, is the matrix usable, and which apps are broken.

The third one is the point. An all-zero row is not "no features": it means the
app yielded no API transitions, which almost always means the APK conversion
failed upstream. The page names those apps instead of leaving you to diff the
CSVs. A value it cannot compute renders as a named gap, never as a zero.

Every run also writes `MaMadroid/run-summary.json` next to the output, so the
page and the terminal show the same numbers rather than two recomputations.

## Tests

```bash
python -m pytest -q          # 25 tests, no APKs, no Java, no network
```

Coverage includes the matrix build (compared against the reference algorithm), the
zero-row case, unknown-label handling, CSV quoting, per-app failure isolation, and
path resolution.

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
  FamilytoMak.py       standalone family-mode driver
  PackagetoMak.py      standalone package-mode driver
  tests/test_markov.py
```

`FamilytoMak.py` and `PackagetoMak.py` are the standalone drivers referenced by
the paper's reproduction steps. The `mamadroid` command performs the same work
with portable path handling.

## Citation

> MaMaDroid: Detecting Android Malware by Building Markov Chains of Behavioral Models
> Mariano Graziano, Davide Canali, Leyla Bilge, Ashwin Rao, Davide Balzarotti
> NDSS 2017

## Licence

Private research artefact. Not open source, not for redistribution. See
[`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).
