#!/usr/bin/env python3
"""Smoke-run every runnable BSV field recipe script (fields/code/<field>/*.py) and record the result.

Each script runs in a fresh temp dir with the given Python (default: /workspace/tools/fieldsvenv/bin/python).
Writes fields/test_runs.json: per script -> ok (exit 0 + expected output files), date (JST), seconds,
the last stdout lines (shown on the page as the real output of BSV's run), and library versions.
Network APIs are live; a failing upstream is recorded as a failure, never as a pass.
usage: smoke_fields_recipes.py [--python PY] [--only NAME]"""
import argparse, datetime as dt, glob, json, os, subprocess, sys, tempfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPECT = {  # script -> files it must create (glob)
    "neo_brief.py": ["neo_brief_*.md"], "iss_passes.py": ["passes_25544.csv"], "s2_scene_finder.py": ["scenes.csv"],
    "kp_watch.py": ["kp_log.csv"], "chembl_screen.py": ["screen_CHEMBL203.csv"], "afdb_confidence.py": ["afdb_P00533_confidence.csv"],
    "uniprot_profile.py": ["profile_P69905.md"], "pubmed_digest.py": ["digest_*.md"], "vqe_h2_pennylane.py": ["vqe_h2.csv"],
    "bell_noise_qiskit.py": ["bell_counts.csv"], "qaoa_maxcut_pennylane.py": ["qaoa_result.json"], "grover_qiskit.py": ["grover_counts.csv"],
    "mujoco_probe_reach.py": ["probe_reach.csv"], "dicom_deid_audit.py": ["deid_report.csv", "CT_small_deid.dcm"],
    "csv_profile.py": ["profile.csv", "profile.md"], "jsonl_flatten.py": ["flat.csv"],
    "worldbank_series.py": ["wb_series.csv"], "open_meteo_daily.py": ["weather_daily.csv"],
    "csv_schema_diff.py": ["schema_diff.csv", "schema_diff.md"], "sqlite_from_csv.py": ["practice.sqlite", "groupby.csv"],
    "frankfurter_fx.py": ["fx_latest.csv"], "usgs_quakes_day.py": ["quakes_day.csv"],
    "mujoco_pendulum_energy.py": ["pendulum_energy.csv"], "planar_ik_workspace.py": ["ik_workspace.csv"],
    "joint_traj_resample.py": ["traj_resampled.csv"], "dh_fk_chain.py": ["dh_fk.csv"],
}
ARGS = {"chembl_screen.py": ["CHEMBL203", "7", "60"]}
PKGS = ["mujoco", "pydicom", "rdkit", "biopython", "skyfield", "pystac-client", "qiskit", "qiskit-aer", "pennylane", "numpy"]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--python", default="/workspace/tools/fieldsvenv/bin/python"); ap.add_argument("--only")
    a = ap.parse_args()
    out_p = ROOT / "fields/test_runs.json"
    rec = json.loads(out_p.read_text()) if out_p.exists() else {"runs": {}}
    vers = subprocess.run([a.python, "-c", "import importlib.metadata as m,json,sys;print(json.dumps({p:m.version(p) for p in sys.argv[1:]}))", *PKGS],
                          capture_output=True, text=True).stdout
    rec["python"] = subprocess.run([a.python, "-V"], capture_output=True, text=True).stdout.strip()
    rec["versions"] = json.loads(vers or "{}")
    for script in sorted(glob.glob(str(ROOT / "fields/code/*/*.py"))):
        name = os.path.basename(script)
        if name not in EXPECT or (a.only and a.only != name):
            continue
        with tempfile.TemporaryDirectory() as td:
            t0 = time.time()
            try:
                p = subprocess.run([a.python, script, *ARGS.get(name, [])], cwd=td, capture_output=True, text=True, timeout=600)
                code, so, se = p.returncode, p.stdout, p.stderr
            except subprocess.TimeoutExpired:
                code, so, se = -1, "", "timeout"
            files_ok = all(glob.glob(os.path.join(td, g)) for g in EXPECT[name])
            rec["runs"][name] = {"field": Path(script).parent.name, "ok": code == 0 and files_ok, "exit": code, "files_ok": files_ok,
                                 "date_jst": dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).strftime("%Y-%m-%d %H:%M"),
                                 "seconds": round(time.time() - t0, 1), "stdout_tail": [l for l in so.strip().splitlines() if l.strip()][-6:],
                                 "stderr_tail": se.strip().splitlines()[-3:] if code else []}
            print(name, "OK" if rec["runs"][name]["ok"] else f"FAIL exit={code} files={files_ok}", rec["runs"][name]["seconds"], "s")
    out_p.write_text(json.dumps(rec, indent=1, ensure_ascii=False) + "\n")
    return 0 if all(r["ok"] for r in rec["runs"].values()) else 1

if __name__ == "__main__":
    sys.exit(main())
