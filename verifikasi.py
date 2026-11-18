"""Bandingkan perhitungan dengan nilai tersimpan di Excel, tanpa memakai nilai itu sebagai input."""
import numpy as np

from metode import edas, group_ranking
from penyimpanan import DEMO


def verify():
    config, forms, expected = (DEMO[k] for k in ("config", "forms", "expected"))
    details = {dm: edas(config, form) for dm, form in forms.items()}
    checks = []
    for dm, detail in details.items():
        for key, label in [("weights", "Bobot FUCOM"), ("average", "Rata-rata"),
                           ("pda", "PDA"), ("nda", "NDA"), ("scores", "Skor & rank EDAS")]:
            actual, ref = np.asarray(detail[key]), np.asarray(expected[dm][key])
            checks.append((f"{dm} · {label}", actual, ref))
    group, points = group_ranking(config, details)
    order = [a["Kode"] for a in config["alternatives"]]
    raw = group.set_index("Kode").loc[order]
    dm_cols = [f"Rank {dm}" for dm in forms]
    checks.append(("Borda · rank DM, poin DM, total & rank grup",
                   np.column_stack([raw[dm_cols], points, raw[["Poin Borda", "Rank grup"]]]),
                   np.asarray(expected["borda"])))
    comparison = [
        dict(Pemeriksaan=name, Elemen=actual.size, **{"Selisih maks.": float(np.abs(actual-ref).max())},
             Cocok=bool(np.allclose(actual, ref, rtol=0, atol=1e-10)))
        for name, actual, ref in checks
    ]
    actual_order = group[["Facility ID", "Nama", *dm_cols, "Poin Borda", "Rank grup"]].values.tolist()
    comparison.append(dict(Pemeriksaan="Ranking akhir · urutan 20 rumah sakit",
                           Elemen=len(actual_order), Cocok=actual_order == expected["ranking"]))
    return comparison


if __name__ == "__main__":
    comparison = verify()
    for row in comparison:
        print(row)
    raise SystemExit(0 if all(row["Cocok"] for row in comparison) else 1)

