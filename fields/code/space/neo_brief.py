#!/usr/bin/env python3
"""BSV recipe: near-Earth-object close-approach brief (NASA/JPL SBDB Close-Approach Data API).

Input : start date (default today UTC), days ahead (default 7), max distance in au (default 0.05).
Output: neo_brief_<date>.md (closest first) and neo_brief_<date>.json (the rows used). No API key needed.
Original BSV code, MIT. Data: NASA/JPL Center for Near Earth Object Studies (ssd-api.jpl.nasa.gov/cad.api).
"""
import datetime as dt, json, sys, urllib.parse, urllib.request

AU_KM = 149_597_870.7   # IAU 2012 definition of the astronomical unit
LD_KM = 384_400         # mean Earth-Moon distance used here for "lunar distances"

def fetch(start: str, days: int, dist_max: str) -> list[dict]:
    end = (dt.date.fromisoformat(start) + dt.timedelta(days=days)).isoformat()
    q = urllib.parse.urlencode({"date-min": start, "date-max": end, "dist-max": dist_max, "body": "Earth",
                                "sort": "dist", "fullname": "true", "diameter": "true"})
    with urllib.request.urlopen(f"https://ssd-api.jpl.nasa.gov/cad.api?{q}", timeout=30) as r:
        data = json.load(r)
    f = data.get("fields", [])
    rows = []
    for x in data.get("data", []):
        d = dict(zip(f, x))
        au = float(d["dist"])
        rows.append({"object": (d.get("fullname") or d["des"]).strip(), "time_tdb": d["cd"],
                     "dist_au": au, "dist_km": au * AU_KM, "dist_ld": au * AU_KM / LD_KM,
                     "v_rel_km_s": float(d["v_rel"]), "h_mag": d.get("h"),
                     "diameter_km": d.get("diameter"), "uncertainty": d.get("t_sigma_f")})
    return rows

def brief(start: str, days: int, rows: list[dict]) -> str:
    out = [f"# Close approaches to Earth, {start} + {days} days", "",
           f"{len(rows)} approaches within the distance limit (NASA/JPL CNEOS). Closest first.", "",
           "| Object | Time (TDB) | Distance | Lunar distances | Speed | H (mag) | Diameter |",
           "|---|---|---|---|---|---|---|"]
    for r in rows:
        dia = f"{r['diameter_km']} km" if r["diameter_km"] else "not published"
        out.append(f"| {r['object']} | {r['time_tdb']} ± {r['uncertainty']} | {r['dist_km']:,.0f} km | {r['dist_ld']:.2f} | "
                   f"{r['v_rel_km_s']:.1f} km/s | {r['h_mag']} | {dia} |")
    out += ["", "H is absolute magnitude (smaller = larger object). Size is unknown for most objects; do not guess it.",
            "Source: https://ssd-api.jpl.nasa.gov/cad.api — verify an object on JPL's Small-Body Database before quoting it."]
    return "\n".join(out) + "\n"

if __name__ == "__main__":
    start = sys.argv[1] if len(sys.argv) > 1 else dt.datetime.now(dt.timezone.utc).date().isoformat()
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    rows = fetch(start, days, sys.argv[3] if len(sys.argv) > 3 else "0.05")
    open(f"neo_brief_{start}.md", "w").write(brief(start, days, rows))
    json.dump(rows, open(f"neo_brief_{start}.json", "w"), indent=1)
    print(f"wrote neo_brief_{start}.md with {len(rows)} approaches")
