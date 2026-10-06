#!/usr/bin/env python3
"""BSV recipe: audit and blank identifying fields in a DICOM file before you share it for research or teaching.

Education only. This is a learning exercise based on a small field list, NOT a complete de-identification
tool and not a substitute for the DICOM PS3.15 Annex E confidentiality profiles or your institution's rules.

Input : path to a DICOM file (default: pydicom's bundled public test file CT_small.dcm).
Output: <name>_deid.dcm and deid_report.csv (field, present before, action). Values are never printed.
Original BSV code, MIT. Library: pydicom (MIT).
"""
import csv, sys
import pydicom
from pydicom.data import get_testdata_file

FIELDS = {  # keyword -> action ("blank" keeps the element with an empty value, "remove" deletes it)
    "PatientName": "blank", "PatientID": "blank", "PatientBirthDate": "blank", "PatientSex": "keep",
    "PatientAge": "keep", "PatientAddress": "remove", "OtherPatientIDs": "remove",
    "InstitutionName": "remove", "InstitutionAddress": "remove", "ReferringPhysicianName": "blank",
    "PerformingPhysicianName": "remove", "OperatorsName": "remove", "AccessionNumber": "blank",
    "StudyID": "blank", "StationName": "remove", "DeviceSerialNumber": "remove",
}

def main(path=None):
    path = path or get_testdata_file("CT_small.dcm")
    ds = pydicom.dcmread(path)
    rows = []
    for kw, action in FIELDS.items():
        present = kw in ds and str(ds.data_element(kw).value) != ""
        if present and action == "blank":
            ds.data_element(kw).value = ""
        elif present and action == "remove":
            delattr(ds, kw)
        rows.append({"field": kw, "present_before": present, "action": action if present else "none"})
    n_private = sum(1 for el in ds if el.tag.is_private)
    ds.remove_private_tags()
    rows.append({"field": "private tags", "present_before": n_private > 0, "action": f"removed {n_private}"})
    ds.PatientIdentityRemoved = "YES"
    ds.DeidentificationMethod = "BSV recipe field list (education); not PS3.15 complete"
    out = path.rsplit("/", 1)[-1].replace(".dcm", "") + "_deid.dcm"
    ds.save_as(out)
    with open("deid_report.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["field", "present_before", "action"]); w.writeheader(); w.writerows(rows)
    changed = sum(1 for r in rows if r["action"] not in ("none", "keep"))
    print(f"{out}: {changed} fields changed, {n_private} private tags removed; dates/UIDs untouched (see next step)")
    print(f"pixel data kept: {'PixelData' in ds}, image {ds.Rows}x{ds.Columns}")

if __name__ == "__main__":
    main(*sys.argv[1:])
