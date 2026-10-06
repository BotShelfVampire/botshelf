#!/usr/bin/env python3
"""BSV recipe: inventory DICOM data elements in a sample file (keyword, VR, VM, value length).

Research / education only. Does not de-identify. Values longer than 40 chars are truncated in the CSV
so accidental PHI is less likely to be pasted into chats — still handle real clinical files under institutional rules.

Input : optional DICOM path (default: pydicom public test file CT_small.dcm).
Output: dicom_tags.csv
Original BSV code, MIT. Library: pydicom (MIT).
"""
import csv, sys
import pydicom
from pydicom.data import get_testdata_file

def main(path=None):
    path = path or get_testdata_file("CT_small.dcm")
    ds = pydicom.dcmread(path)
    rows = []
    for el in ds.iterall():
        if el.VR == "SQ":
            val_len = f"seq({len(el.value)})"
            preview = ""
        else:
            s = str(el.value)
            val_len = len(s)
            preview = s if len(s) <= 40 else s[:37] + "..."
        rows.append({"tag": str(el.tag), "keyword": el.keyword or "", "VR": el.VR, "VM": el.VM,
                     "value_len": val_len, "preview": preview, "private": el.tag.is_private})
    with open("dicom_tags.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["tag", "keyword", "VR", "VM", "value_len", "preview", "private"])
        w.writeheader(); w.writerows(rows)
    print(f"inventoried {len(rows)} elements from {path.rsplit('/',1)[-1]} -> dicom_tags.csv")

if __name__ == "__main__":
    main(*sys.argv[1:2])
