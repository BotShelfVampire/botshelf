#!/usr/bin/env python3
"""BSV recipe: load a CSV into SQLite and run a small GROUP BY demo.

Input : optional CSV path (default: labeled synthetic sample).
Output: practice.sqlite + groupby.csv
Original BSV code, MIT. Stdlib sqlite3 + csv only.
"""
import csv, os, sqlite3, sys

SAMPLE = """id,city,temp_c,note
1,Tokyo,22.1,example-row
2,Osaka,19.0,example-row
3,Tokyo,21.5,example-row
4,Nagoya,20.0,example-row
5,Osaka,18.2,example-row
"""

def main(path=None):
    if not path:
        path = "sample_labeled.csv"
        open(path, "w", encoding="utf-8").write(SAMPLE)
        print("wrote labeled synthetic sample:", path)
    rows = list(csv.DictReader(open(path, encoding="utf-8", newline="")))
    if not rows:
        raise SystemExit("empty csv")
    cols = list(rows[0].keys())
    db = "practice.sqlite"
    if os.path.exists(db):
        os.remove(db)
    con = sqlite3.connect(db)
    # quote identifiers safely for this demo (alphanumeric + underscore only)
    safe = [c for c in cols if c.replace("_", "").isalnum()]
    if len(safe) != len(cols):
        raise SystemExit("column names must be alphanumeric/underscore for this demo loader")
    con.execute(f"CREATE TABLE t ({', '.join(c + ' TEXT' for c in safe)})")
    con.executemany(f"INSERT INTO t VALUES ({','.join('?' for _ in safe)})",
                    [[r.get(c, "") for c in safe] for r in rows])
    con.commit()
    # Prefer a city-like column for the demo aggregate
    group_col = "city" if "city" in safe else safe[1 if len(safe) > 1 else 0]
    q = f"SELECT {group_col} AS grp, COUNT(*) AS n FROM t GROUP BY {group_col} ORDER BY n DESC, grp"
    out = list(con.execute(q))
    with open("groupby.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["grp", "n"]); w.writerows(out)
    con.close()
    print(f"loaded {len(rows)} rows into {db}; groupby on {group_col} -> groupby.csv ({len(out)} groups)")

if __name__ == "__main__":
    main(*sys.argv[1:2])
