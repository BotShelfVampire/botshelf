#!/usr/bin/env python3
"""BSV recipe: flatten a small FHIR R4 Bundle (Patient + Observations) into CSVs.

Education / research data-handling only. Synthetic bundle is labeled example data — not a real patient.
Not a clinical system, not PHI handling guidance, and not a claim of FHIR conformance for production.

Input : optional path to a FHIR Bundle JSON (default: writes a labeled synthetic sample).
Output: fhir_patients.csv + fhir_observations.csv
Original BSV code, MIT.
"""
import csv, json, sys

SAMPLE = {
  "resourceType": "Bundle", "type": "collection", "entry": [
    {"resource": {"resourceType": "Patient", "id": "example-1",
                  "name": [{"family": "Example", "given": ["Practice"]}],
                  "gender": "unknown", "birthDate": "1970-01-01"}},
    {"resource": {"resourceType": "Observation", "id": "obs-1", "status": "final",
                  "code": {"text": "example-heart-rate"}, "subject": {"reference": "Patient/example-1"},
                  "valueQuantity": {"value": 72, "unit": "beats/min"}}},
    {"resource": {"resourceType": "Observation", "id": "obs-2", "status": "final",
                  "code": {"text": "example-temp-c"}, "subject": {"reference": "Patient/example-1"},
                  "valueQuantity": {"value": 36.6, "unit": "Cel"}}},
  ]
}

def main(path=None):
    if not path:
        path = "sample_fhir_bundle_labeled.json"
        open(path, "w", encoding="utf-8").write(json.dumps(SAMPLE, indent=2) + "\n")
        print("wrote labeled synthetic FHIR Bundle:", path)
    bundle = json.load(open(path, encoding="utf-8"))
    patients, obs = [], []
    for e in bundle.get("entry") or []:
        r = e.get("resource") or {}
        rt = r.get("resourceType")
        if rt == "Patient":
            nm = (r.get("name") or [{}])[0]
            patients.append({"id": r.get("id"), "family": nm.get("family"), "given": " ".join(nm.get("given") or []),
                             "gender": r.get("gender"), "birthDate": r.get("birthDate")})
        elif rt == "Observation":
            vq = r.get("valueQuantity") or {}
            patients_ref = (r.get("subject") or {}).get("reference")
            obs.append({"id": r.get("id"), "status": r.get("status"), "code": (r.get("code") or {}).get("text"),
                        "subject": patients_ref, "value": vq.get("value"), "unit": vq.get("unit")})
    with open("fhir_patients.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "family", "given", "gender", "birthDate"])
        w.writeheader(); w.writerows(patients)
    with open("fhir_observations.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "status", "code", "subject", "value", "unit"])
        w.writeheader(); w.writerows(obs)
    print(f"flattened {len(patients)} patients, {len(obs)} observations -> fhir_patients.csv, fhir_observations.csv")

if __name__ == "__main__":
    main(*sys.argv[1:2])
