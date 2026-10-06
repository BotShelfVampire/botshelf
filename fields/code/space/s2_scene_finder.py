#!/usr/bin/env python3
"""BSV recipe: find low-cloud Sentinel-2 L2A scenes for an area (Earth Search STAC API + pystac-client).

Input : bounding box (min_lon min_lat max_lon max_lat), date range, max cloud cover %.
Output: scenes.csv (id, date, cloud %, thumbnail URL, true-colour COG URL), least cloudy first.
Original BSV code, MIT. Catalogue: Element 84 Earth Search (Sentinel-2 COGs on AWS Open Data).
Data: Copernicus Sentinel data, subject to the Copernicus data terms.
"""
import csv, sys
from pystac_client import Client

def main(bbox="139.70,35.62,139.82,35.72", dates="2026-08-01/2026-09-30", max_cloud="20"):
    cat = Client.open("https://earth-search.aws.element84.com/v1")
    search = cat.search(collections=["sentinel-2-l2a"], bbox=[float(x) for x in bbox.split(",")],
                        datetime=dates, query={"eo:cloud_cover": {"lt": float(max_cloud)}}, max_items=50)
    items = sorted(search.items(), key=lambda it: it.properties.get("eo:cloud_cover", 100))
    with open("scenes.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "date", "cloud_pct", "thumbnail", "visual_cog"])
        for it in items:
            a = it.assets
            w.writerow([it.id, it.datetime.date().isoformat(), round(it.properties.get("eo:cloud_cover", -1), 2),
                        a["thumbnail"].href if "thumbnail" in a else "", a["visual"].href if "visual" in a else ""])
    print(f"{len(items)} scenes under {max_cloud}% cloud -> scenes.csv")
    if items:
        print("least cloudy:", items[0].id, items[0].properties.get("eo:cloud_cover"))

if __name__ == "__main__":
    main(*sys.argv[1:])
