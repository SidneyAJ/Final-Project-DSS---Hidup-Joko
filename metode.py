"""FUCOM rasio berurutan, EDAS, dan Borda sesuai workbook simulasi."""
import numpy as np
import pandas as pd


def priority_ratios(codes, order):
    """Hitung rasio otomatis mengikuti aturan skor prioritas pada workbook."""
    if sorted(order) != sorted(codes):
        raise ValueError("Urutan prioritas harus memuat setiap kriteria tepat sekali.")
    count = len(codes)
    positions = {code: i for i, code in enumerate(codes, 1)}
    scores = [count + 1 - rank + (count + 1 - positions[code]) / (count + 1)
              for rank, code in enumerate(order, 1)]
    return [a / b for a, b in zip(scores, scores[1:])]


def validate_form(config, form):
    criteria = config["criteria"]
    alternatives = config["alternatives"]
    codes = [c["Kode"] for c in criteria]
    if sorted(form["order"]) != sorted(codes):
        raise ValueError("Urutan prioritas harus memuat setiap kode kriteria tepat sekali.")
    ratios = np.asarray(form["ratios"], dtype=float)
    if len(ratios) != len(codes) - 1 or not np.isfinite(ratios).all() or (ratios < 1).any():
        raise ValueError("Semua rasio setelah prioritas pertama harus berupa angka minimal 1.")
    raw = np.cumprod(np.r_[1.0, 1 / ratios])
    if (raw == 0).any():
        raise ValueError("Kombinasi rasio terlalu ekstrem untuk dihitung.")
    values = np.asarray(form["matrix"], dtype=float)
    if values.shape != (len(alternatives), len(codes)):
        raise ValueError("Dimensi matriks harus sesuai dengan alternatif dan kriteria.")
    for j, criterion in enumerate(criteria):
        col = values[:, j]
        invalid = ~np.isfinite(col) | (col < criterion["Min"]) | (col > criterion["Maks"])
        if invalid.any():
            i = np.flatnonzero(invalid)[0]
            raise ValueError(f"{alternatives[i]['Kode']} / {codes[j]} wajib diisi dalam skala "
                             f"{criterion['Min']:g}–{criterion['Maks']:g}.")
    return values, raw


def average_rank(scores):
    # Excel COUNTIF compares numeric criteria with up to 15 significant digits.
    return pd.Series(scores).map(lambda x: float(f"{x:.15g}")).rank(ascending=False).to_numpy()


def edas(config, form):
    values, raw = validate_form(config, form)
    codes = [c["Kode"] for c in config["criteria"]]
    weights = pd.Series(raw / raw.sum(), index=form["order"]).reindex(codes).to_numpy()
    direction = np.array([1 if c["Tipe"] == "Benefit" else -1 for c in config["criteria"]])
    # Scale internally before averaging to avoid overflow on large inputs.
    maximum = values.max(axis=0)
    scaled = np.divide(values, maximum, out=np.zeros_like(values), where=maximum != 0)
    mean = scaled.mean(axis=0)
    distances = np.divide(scaled - mean, mean, out=np.zeros_like(values), where=mean != 0) * direction
    pda, nda = np.maximum(distances, 0), np.maximum(-distances, 0)
    sp, sn = pda @ weights, nda @ weights
    nsp = sp / sp.max() if sp.max() else np.ones(len(sp))
    nsn = 1 - sn / sn.max() if sn.max() else np.ones(len(sn))
    score = (nsp + nsn) / 2
    scores = np.column_stack([sp, sn, nsp, nsn, score, average_rank(score)])
    adjacent = raw[:-1] / raw[1:] - np.asarray(form["ratios"], dtype=float)
    return dict(weights=weights, average=mean * maximum, pda=pda, nda=nda, scores=scores,
                dfc=max(abs(adjacent), default=0.0))


def group_ranking(config, details):
    alternatives = pd.DataFrame(config["alternatives"])
    dm_ids = [d["Kode"] for d in config["dms"]]
    ranks = np.column_stack([details[dm]["scores"][:, 5] for dm in dm_ids])
    points = len(alternatives) + 1 - ranks
    totals = points.sum(axis=1)
    result = alternatives.assign(**{f"Rank {dm}": ranks[:, j] for j, dm in enumerate(dm_ids)})
    result["Poin Borda"] = totals
    result["Rank grup"] = average_rank(totals)
    return result.sort_values("Poin Borda", ascending=False, kind="stable").reset_index(drop=True), points

