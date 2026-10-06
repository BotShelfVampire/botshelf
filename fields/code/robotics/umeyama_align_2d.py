#!/usr/bin/env python3
"""BSV recipe: Umeyama 2D similarity align of two point sets (toy).

Research / education only.
Input : optional noise sigma (default 0.02), seed (default 3), n points (default 12).
Output: umeyama_2d.csv with estimated scale, rotation_deg, tx, ty, rmse.
Original BSV code, MIT. Dependency: numpy.
"""
import csv, math, sys
import numpy as np

def umeyama(X, Y):
    # X,Y: (n,2) corresponding points; estimate Y ≈ s R X + t
    mu_x = X.mean(axis=0); mu_y = Y.mean(axis=0)
    Xc = X - mu_x; Yc = Y - mu_y
    var_x = (Xc ** 2).sum() / len(X)
    cov = (Yc.T @ Xc) / len(X)
    U, S, Vt = np.linalg.svd(cov)
    R = U @ Vt
    if np.linalg.det(R) < 0:
        U[:, -1] *= -1
        R = U @ Vt
    s = (S.sum() / var_x) if var_x > 1e-12 else 1.0
    t = mu_y - s * R @ mu_x
    aligned = (s * (R @ X.T)).T + t
    rmse = float(np.sqrt(((aligned - Y) ** 2).sum() / len(X)))
    ang = math.degrees(math.atan2(R[1, 0], R[0, 0]))
    return s, ang, float(t[0]), float(t[1]), rmse

def main(sigma="0.02", seed="3", n="12"):
    sigma, seed, n = float(sigma), int(seed), int(n)
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, 2))
    s_true, th = 1.3, math.radians(35)
    R = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
    t_true = np.array([0.4, -0.2])
    Y = (s_true * (R @ X.T)).T + t_true + rng.normal(scale=sigma, size=X.shape)
    s, ang, tx, ty, rmse = umeyama(X, Y)
    with open("umeyama_2d.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["scale", "rotation_deg", "tx", "ty", "rmse", "scale_true", "rotation_true_deg"])
        w.writeheader()
        w.writerow({"scale": s, "rotation_deg": ang, "tx": tx, "ty": ty, "rmse": rmse,
                    "scale_true": s_true, "rotation_true_deg": math.degrees(th)})
    print(f"Umeyama s={s:.4f} ang={ang:.2f}deg rmse={rmse:.4f} -> umeyama_2d.csv")

if __name__ == "__main__":
    main(*sys.argv[1:4])
