"""A self-contained HTML report for a MaMaDroid run.

Why a generated page and not a web server: this is a batch pipeline that runs on
a build host. A second listening port there is a firewall conversation, a
certificate conversation and an auth conversation, and none of them are worth it
for a page an analyst reads once per run. ``mamadroid report`` writes one file
with inline CSS, no script tags, no external origin, that opens locally or drops
behind whatever already serves static pages.

What it answers, in the order an analyst asks:

1. Did the run actually work? (stage counts, failures)
2. Is the feature matrix usable? (apps, states, density, all-zero rows)
3. Which apps are broken? (named, not counted)

A value the report cannot compute renders as a named gap, never as a zero. An
all-zero row is not "no features" - it is "this app produced no transitions",
which usually means the APK conversion failed silently upstream.
"""

from __future__ import annotations

import csv
import html
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ModeStats:
    mode: str
    apps: int = 0
    states: int = 0
    columns: int = 0
    non_zero_cells: int = 0
    total_cells: int = 0
    empty_rows: list[str] = field(default_factory=list)
    densest: list[tuple[str, int]] = field(default_factory=list)

    @property
    def density(self) -> float | None:
        if not self.total_cells:
            return None
        return self.non_zero_cells / self.total_cells

    def as_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "apps": self.apps,
            "states": self.states,
            "columns": self.columns,
            "density": self.density,
            "empty_rows": self.empty_rows[:20],
            "empty_row_count": len(self.empty_rows),
            "densest": self.densest[:10],
        }


def analyse_csv(path: Path, mode: str) -> ModeStats:
    """Read one result.csv and describe it without loading it all into memory."""
    stats = ModeStats(mode=mode)
    if not path.is_file():
        return stats

    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration:
            return stats

        stats.columns = max(0, len(header) - 1)  # minus the filename column
        # The state vocabulary is the square root of the pair count.
        stats.states = int(round(stats.columns ** 0.5)) if stats.columns else 0

        for row in reader:
            if not row:
                continue
            stats.apps += 1
            values = row[1:]
            filled = 0
            for cell in values:
                try:
                    if float(cell) != 0.0:
                        filled += 1
                except (TypeError, ValueError):
                    continue
            stats.non_zero_cells += filled
            stats.total_cells += len(values)
            if filled == 0:
                stats.empty_rows.append(row[0])
            else:
                stats.densest.append((row[0], filled))

    stats.densest.sort(key=lambda pair: pair[1], reverse=True)
    return stats


def collect(output_dir: str | Path, summary_path: str | Path | None = None) -> dict[str, Any]:
    """Everything the page shows, derived from files on disk."""
    root = Path(output_dir).expanduser()
    features = root / "MaMadroid" / "Features"

    modes: list[ModeStats] = []
    if features.is_dir():
        for mode_dir in sorted(p for p in features.iterdir() if p.is_dir()):
            modes.append(analyse_csv(mode_dir / "result.csv", mode_dir.name))

    summary = None
    if summary_path:
        path = Path(summary_path).expanduser()
        if path.is_file():
            try:
                summary = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                summary = {"error": "summary file exists but could not be parsed"}

    return {
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "output_dir": str(root),
        "modes": [m.as_dict() for m in modes],
        "mode_count": len(modes) if features.is_dir() else None,
        "summary": summary,
    }


PAGE = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BOLTER — run report</title>
<style>
:root{--bg:#0f1419;--panel:#161d26;--line:#243040;--ink:#e6edf3;--muted:#9aa8b6;
  --faint:#6b7a89;--red:#e5534b;--amber:#d29922;--teal:#2f9e8f;--blue:#3b82f6}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font:14px/1.55 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}
.wrap{max-width:1100px;margin:0 auto;padding:26px 20px 60px}
header{display:flex;justify-content:space-between;align-items:flex-start;gap:20px;
  flex-wrap:wrap;margin-bottom:22px}
h1{margin:0;font-size:20px;letter-spacing:-.01em}
.sub{color:var(--muted);font-size:12.5px;margin-top:4px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;
  margin-bottom:20px}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px 14px}
.kpi .k{font-size:10.5px;text-transform:uppercase;letter-spacing:.09em;color:var(--faint)}
.kpi .v{font-size:22px;font-weight:600;margin-top:3px;font-variant-numeric:tabular-nums}
.kpi .n{font-size:11px;color:var(--faint);margin-top:2px}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:10px;
  padding:15px 17px;margin-bottom:14px}
.panel h2{margin:0 0 11px;font-size:13px;text-transform:uppercase;
  letter-spacing:.09em;color:var(--faint);font-weight:600}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th{text-align:left;font-weight:600;color:var(--faint);font-size:10.5px;
  text-transform:uppercase;letter-spacing:.07em;padding:0 8px 7px 0;
  border-bottom:1px solid var(--line)}
td{padding:7px 8px 7px 0;border-bottom:1px solid rgba(36,48,64,.5);vertical-align:top}
tr:last-child td{border-bottom:0}
.mono{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:11.5px}
.empty{color:var(--faint);font-size:12.5px;padding:6px 0}
.gap{border-left:3px solid var(--amber);background:rgba(210,153,34,.07);
  border-radius:7px;padding:8px 11px;margin-bottom:7px;font-size:12.5px}
.gap.bad{border-left-color:var(--red);background:rgba(229,83,75,.07)}
.gap b{font-weight:600}
.gap .why{color:var(--faint);font-size:11.5px;margin-top:2px}
.bar{display:grid;grid-template-columns:120px 1fr 60px;gap:9px;align-items:center;
  margin-bottom:5px;font-size:11.5px}
.bar .track{height:8px;background:#0a1219;border:1px solid var(--line);
  border-radius:4px;overflow:hidden}
.bar .fill{display:block;height:100%;background:var(--teal)}
.bar b{text-align:right;font-family:ui-monospace,Menlo,monospace;font-size:11px}
footer{margin-top:26px;padding-top:12px;border-top:1px solid var(--line);
  color:var(--faint);font-size:11.5px}
</style></head><body><div class="wrap">
<header>
  <div><h1>BOLTER</h1>
    <div class="sub">Markov-chain behavioural features — run report</div></div>
  <div class="sub" id="stamp"></div>
</header>
<div class="kpis" id="kpis"></div>
<div id="gaps"></div>
<div class="panel"><h2>Feature matrices</h2><div id="modes"></div></div>
<div class="panel"><h2>Stage results</h2><div id="stages"></div></div>
<footer>Generated from the files on disk. A value that could not be computed is
shown as a named gap, never as zero.</footer>
</div>
<script type="application/json" id="data">__DATA__</script>
<script>
(function(){
  var d = JSON.parse(document.getElementById('data').textContent);
  function esc(v){ return String(v==null?'':v).replace(/[&<>"']/g, function(c){
    return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]; }); }
  function dash(v){ return (v==null||v==='') ? '\u2014' : v; }
  function pct(v){ return v==null ? '\u2014' : (v*100).toFixed(2)+'%'; }

  document.getElementById('stamp').textContent = 'generated ' + d.generated;

  var totalApps = 0, totalEmpty = 0;
  d.modes.forEach(function(m){ totalApps += m.apps; totalEmpty += m.empty_row_count; });

  var kpis = [
    ['modes', d.mode_count, d.mode_count==null ? 'Features directory not found' : 'feature matrices on disk'],
    ['apps', totalApps, 'rows across all modes'],
    // Rows, not apps: one broken app appears once per mode, so the sum counts
    // it more than once. Saying "apps" would send someone looking for a second
    // broken APK that does not exist.
    ['empty rows', totalEmpty, 'rows with no transitions, across modes'],
    ['output', null, d.output_dir]
  ];
  document.getElementById('kpis').innerHTML = kpis.map(function(k){
    var cls = '';
    if (k[0]==='empty rows' && k[1]>0) cls = ' style="color:var(--amber)"';
    return '<div class="kpi"><div class="k">'+esc(k[0])+'</div>'+
      '<div class="v"'+cls+'>'+esc(dash(k[1]))+'</div>'+
      '<div class="n">'+esc(k[2])+'</div></div>';
  }).join('');

  var gaps = [];
  if (d.mode_count == null) {
    gaps.push(['bad','No Features directory.',
      'Nothing was written to ' + d.output_dir + '/MaMadroid/Features. The feature stage did not run or was skipped.']);
  } else if (d.mode_count === 0) {
    gaps.push(['bad','The Features directory is empty.',
      'The directory exists but holds no mode subdirectory. Check the run log for a skipped mode.']);
  }
  if (totalApps === 0 && d.mode_count) {
    gaps.push(['bad','No rows in any result.csv.',
      'Every matrix is empty. The reference graph directories were probably missing.']);
  }
  if (totalEmpty > 0) {
    gaps.push(['',' ' + totalEmpty + ' row(s) produced an all-zero row.',
      'An all-zero row is not "no features" - it means the app yielded no API transitions. Usually the APK conversion failed upstream; check the stage table below.']);
  }
  var s = d.summary;
  if (s && s.error) gaps.push(['bad','The run summary could not be parsed.', s.error]);
  if (s && s.ok === false) {
    var failed = [];
    (s.stages||[]).forEach(function(st){ (st.failed||[]).forEach(function(f){ failed.push(st.name+': '+f); }); });
    gaps.push(['bad','The run reported failures.',
      failed.slice(0,6).join(' ') || 'See the stage table.']);
  }
  document.getElementById('gaps').innerHTML = gaps.length ? gaps.map(function(g){
    return '<div class="gap '+g[0]+'"><b>'+esc(g[1])+'</b><div class="why">'+esc(g[2])+'</div></div>';
  }).join('') : '';

  document.getElementById('modes').innerHTML = d.modes.length
    ? '<table><thead><tr><th>mode</th><th>apps</th><th>states</th><th>density</th><th>empty rows</th></tr></thead><tbody>'+
      d.modes.map(function(m){
        return '<tr><td class="mono">'+esc(m.mode)+'</td>'+
          '<td>'+esc(m.apps)+'</td><td>'+esc(m.states)+'</td>'+
          '<td>'+esc(pct(m.density))+'</td>'+
          '<td'+(m.empty_row_count?' style="color:var(--amber)"':'')+'>'+esc(m.empty_row_count)+'</td></tr>';
      }).join('')+'</tbody></table>'
    : '<div class="empty">No feature matrices to describe yet.</div>';

  var stages = (s && s.stages) ? s.stages : [];
  document.getElementById('stages').innerHTML = stages.length
    ? stages.map(function(st){
        var bad = (st.failed||[]).length;
        return '<div class="bar"><span class="mono">'+esc(st.name)+'</span>'+
          '<span class="track"><i class="fill" style="width:'+
            (st.processed ? Math.min(100, 100*st.processed/Math.max(1, st.processed+bad)) : 0)+
            '%;background:'+(bad?'var(--amber)':'var(--teal)')+'"></i></span>'+
          '<b>'+esc(st.processed)+'</b></div>'+
          (bad ? '<div class="empty" style="padding-left:129px">'+bad+' failed</div>' : '');
      }).join('')
    : '<div class="empty">No run summary supplied. Pass --summary PATH to include stage results.</div>';
})();
</script>
</body></html>
"""


def render(data: dict[str, Any]) -> str:
    """The page with the data embedded. No external requests, no inline handlers."""
    payload = json.dumps(data, default=str).replace("</", "<\\/")
    return PAGE.replace("__DATA__", payload)


def write(output_dir: str | Path, out_path: str | Path,
          summary_path: str | Path | None = None) -> Path:
    out = Path(out_path).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(collect(output_dir, summary_path)), encoding="utf-8")
    return out


def _unused(value: Any) -> str:  # pragma: no cover - keeps the html import honest
    return html.escape(str(value))
