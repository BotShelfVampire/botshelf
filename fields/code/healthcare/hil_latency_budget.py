#!/usr/bin/env python3
"""BSV recipe: teleop HIL latency budget (one-way + round-trip cartoon).

Research / education / simulation literacy only — not a clinical or safety analysis.
Input : one_way_ms, encode_ms, decode_ms, display_ms (defaults 40 8 8 16), samples (default 1).
Output: hil_latency.csv with components and round_trip_ms.
Original BSV code, MIT. Dependency: none.
"""
import csv, sys

def main(one_way="40", encode="8", decode="8", display="16"):
    a,b,c,d = map(float, (one_way, encode, decode, display))
    rtt = 2 * a + b + c + d
    row = {"one_way_ms": a, "encode_ms": b, "decode_ms": c, "display_ms": d,
           "round_trip_ms": rtt, "note": "toy sum — not a measured system"}
    with open("hil_latency.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(row.keys())); w.writeheader(); w.writerow(row)
    print(f"RTT cartoon={rtt:.1f}ms -> hil_latency.csv (research/sim only)")

if __name__ == "__main__":
    main(*sys.argv[1:5])
