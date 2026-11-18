"""Prototipe GDSS untuk evaluasi rumah sakit Alabama."""
from datetime import datetime
from hashlib import sha256
from html import escape
from math import isfinite
import json
from pathlib import Path
from zoneinfo import ZoneInfo

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from autentikasi import ADMIN, authenticate, hash_password
from metode import edas, group_ranking, priority_ratios, validate_form
from penyimpanan import DEMO, KonflikData, read, save
from verifikasi import verify


st.set_page_config(page_title="GDSS Evaluasi Rumah Sakit", page_icon="🏥", layout="wide")
st.html(Path(__file__).with_name("dashboard.css"))
rev, state = read()
config = state["config"]
forms = state["forms"]
alternatives, criteria, dms = (config[k] for k in ("alternatives", "criteria", "dms"))
a_ids = [a["Kode"] for a in alternatives]
c_ids = [c["Kode"] for c in criteria]
dm_ids = [dm["Kode"] for dm in dms]
accounts = state["accounts"]
st.sidebar.title("GDSS Rumah Sakit")
st.sidebar.caption("FUCOM · EDAS · Borda")


def hero(title, context, description):
    st.html(f"""
        <section class="gdss-hero" aria-label="{escape(title)}">
            <p class="gdss-context">{escape(context)}</p>
            <h1>{escape(title)}</h1>
            <p>{escape(description)}</p>
        </section>
    """)


def login():
    hero("Masuk ke GDSS Rumah Sakit", "Evaluasi rumah sakit Alabama",
         "Buka penilaian dan hasil keputusan kelompok dengan akun DM atau admin.")
    form, _ = st.columns([3, 2])
    with form:
        if "notice" in st.session_state:
            st.success(st.session_state.pop("notice"))
        with st.form("login", clear_on_submit=True):
            username = st.text_input("Nama pengguna", max_chars=100, autocomplete="username")
            password = st.text_input("Kata sandi", type="password", max_chars=128,
                                     autocomplete="current-password")
            if st.form_submit_button("Masuk", type="primary"):
                code = authenticate(accounts, username, password)
                if code is None:
                    st.error("Nama pengguna atau kata sandi salah.")
                else:
                    st.session_state["authenticated_user"] = (code, accounts[code])
                    st.rerun()


login_session = st.session_state.get("authenticated_user")
if login_session:
    user, proof = login_session
    if accounts.get(user) != proof or (user != ADMIN and user not in dm_ids):
        st.session_state.clear()
        st.warning("Akses akun berubah. Silakan masuk kembali.")
        login()
        st.stop()
else:
    login()
    st.stop()

is_admin = user == ADMIN
role = "Admin" if is_admin else "Pengambil keputusan"
st.sidebar.html(f'<p class="gdss-account"><strong>{escape(user)}</strong> · {role}</p>')
if st.sidebar.button("Keluar", width="stretch"):
    st.session_state.clear()
    st.rerun()



def token(value):
    return sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()[:16]


def commit(message):
    try:
        save(rev, state)
    except KonflikData as exc:
        st.error(str(exc))
        st.stop()
    st.session_state["notice"] = message
    st.rerun()


def timestamp():
    return datetime.now(ZoneInfo("Asia/Makassar")).strftime("%d-%m-%Y %H:%M:%S WITA")


def records(frame, label, min_count, required):
    rows = frame.fillna("").to_dict("records")
    if len(rows) < min_count:
        raise ValueError(f"{label} memerlukan minimal {min_count} baris.")
    for row in rows:
        for key in required:
            row[key] = str(row[key]).strip()
            if not row[key]:
                raise ValueError(f"{label} · kolom {key} wajib diisi.")
    if len({row["Kode"].casefold() for row in rows}) != len(rows):
        raise ValueError(f"{label} · kode harus unik.")
    return rows


def edit_setup():
    st.header("Alternatif, kriteria, dan DM")
    st.write("Tambah baris dengan tombol + pada tabel. Pilih baris untuk menghapusnya. "
             "Perubahan pada alternatif atau kriteria membatalkan penilaian yang tersimpan.")
    with st.form("setup"):
        st.subheader("Alternatif")
        a = st.data_editor(pd.DataFrame(alternatives), num_rows="dynamic", hide_index=True,
                           key=f"alternatives-{token(alternatives)}")
        st.subheader("Kriteria")
        c = st.data_editor(pd.DataFrame(criteria), num_rows="dynamic", hide_index=True,
                           column_config={"Tipe": st.column_config.SelectboxColumn(options=["Benefit", "Cost"])},
                           key=f"criteria-{token(criteria)}")
        st.subheader("Pengambil keputusan")
        d = st.data_editor(pd.DataFrame(dms), num_rows="dynamic", hide_index=True,
                           key=f"dms-{token(dms)}")
        submitted = st.form_submit_button("Simpan konfigurasi", type="primary")
    if submitted:
        try:
            aa = records(a, "Alternatif", 2, ["Kode", "Nama"])
            cc = records(c, "Kriteria", 1, ["Kode", "Nama", "Tipe"])
            dd = records(d, "DM", 1, ["Kode", "Peran"])
            if any(dm["Kode"].casefold() == ADMIN for dm in dd):
                raise ValueError("Kode admin dicadangkan untuk pengelola aplikasi.")
            if any(len(dm["Kode"]) > 100 for dm in dd):
                raise ValueError("Kode DM maksimal 100 karakter.")
            for row in aa:
                row["Facility ID"] = str(row["Facility ID"]).strip()
            for row in cc:
                lo, hi = row["Min"], row["Maks"]
                if not all(isinstance(x, (int, float)) and isfinite(x) for x in (lo, hi)) or not 0 <= lo < hi:
                    raise ValueError(f"{row['Kode']} memerlukan skala numerik dengan 0 ≤ Min < Maks.")
                if row["Tipe"] not in {"Benefit", "Cost"}:
                    raise ValueError(f"Pilih tipe untuk {row['Kode']}.")
        except ValueError as exc:
            st.error(str(exc))
        else:
            state["config"] = dict(alternatives=aa, criteria=cc, dms=dd)
            if aa != alternatives or cc != criteria:
                state["forms"] = {}
                state["baseline"] = DEMO["baseline"] if aa == DEMO["config"]["alternatives"] and cc == DEMO["config"]["criteria"] else None
            else:
                state["forms"] = {dm["Kode"]: forms[dm["Kode"]] for dm in dd if dm["Kode"] in forms}
            keep_accounts([dm["Kode"] for dm in dd])
            commit("Konfigurasi tersimpan.")
    with st.expander("Pulihkan simulasi Alabama"):
        st.caption("Konfigurasi dan penilaian aktif akan kembali ke data latihan. Riwayat dan diskusi tetap tersedia.")
        if st.button("Muat ulang data simulasi"):
            state.update({key: DEMO[key] for key in ("config", "forms", "baseline")})
            keep_accounts([dm["Kode"] for dm in state["config"]["dms"]])
            commit("Data simulasi dimuat. Buat akun lewat Akun pengguna jika ada DM yang belum punya akses.")


def keep_accounts(active_dms):
    state["accounts"] = {code: credential for code, credential in accounts.items()
                         if code == ADMIN or code in active_dms}


def manage_accounts():
    st.header("Akun pengguna")
    st.write("Buat akun setelah menambah DM di Konfigurasi, atau tetapkan ulang kata sandi akun yang ada.")
    st.dataframe(
        [{"Akun": code, "Akses": "Aktif" if code in accounts else "Belum dibuat"}
         for code in [ADMIN, *dm_ids]],
        hide_index=True,
    )
    code = st.selectbox("Pilih akun", [*dm_ids, ADMIN])
    with st.form("set-password", clear_on_submit=True):
        password = st.text_input("Kata sandi baru", type="password", max_chars=128, autocomplete="new-password")
        repeat = st.text_input("Ulangi kata sandi baru", type="password", max_chars=128, autocomplete="new-password")
        if st.form_submit_button("Simpan kata sandi", type="primary"):
            if len(password.strip()) < 10:
                st.error("Gunakan minimal 10 karakter selain spasi di awal dan akhir.")
            elif password != repeat:
                st.error("Kedua kata sandi harus sama.")
            else:
                accounts[code] = hash_password(password)
                commit(f"Kata sandi {code} tersimpan.")


def priority_editor(identity, saved_order):
    st.subheader("Prioritas FUCOM")
    st.caption("Pilih satu kriteria per baris. Setiap kode harus muncul tepat sekali.")
    headers = ("Urutan", "Kriteria", "Dibandingkan dengan", "Rasio FUCOM")
    widths = [1, 2, 2, 2]
    with st.container(border=True, key="priority-table"):
        for column, header in zip(st.columns(widths), headers):
            column.markdown(f"**{header}**")
        order, comparison_cells, ratio_cells = [], [], []
        for index, saved in enumerate(saved_order, 1):
            number, criterion, comparison, ratio = st.columns(widths, vertical_alignment="center")
            number.write(index)
            order.append(criterion.selectbox(
                f"Prioritas {index}", ["", *c_ids], index=c_ids.index(saved) + 1 if saved else 0,
                format_func=lambda code: code or "Pilih kriteria",
                key=f"priority-{identity}-{index}", label_visibility="collapsed",
            ))
            comparison_cells.append(comparison.empty())
            ratio_cells.append(ratio.empty())

        duplicates = [code for code in c_ids if order.count(code) > 1]
        ratios = None
        if duplicates:
            st.error("Kriteria ganda: " + ", ".join(duplicates) + ". Setiap kode hanya boleh dipilih sekali.")
        elif "" in order:
            st.info("Lengkapi semua baris untuk menghitung rasio FUCOM.")
        else:
            ratios = priority_ratios(c_ids, order)

        for cell, previous in zip(comparison_cells, ["", *order[:-1]]):
            cell.write(previous or "—")
        for cell, value in zip(ratio_cells, [None, *ratios] if ratios is not None else [None] * len(order)):
            cell.write(f"{value:.4f}" if value is not None else "—")
    return order, ratios


def assessment():
    dm = user
    st.header(f"Penilaian {dm}")
    st.caption(next(d["Peran"] for d in dms if d["Kode"] == dm))
    current = forms.get(dm)
    empty = [[None for _ in c_ids] for _ in a_ids]
    initial = current["matrix"] if current else state["baseline"] or empty
    labels = [f"{a['Kode']} · {a['Nama']}" for a in alternatives]
    matrix = pd.DataFrame(initial, columns=c_ids, index=pd.Index(labels, name="Alternatif"), dtype=float)
    identity = token([config, dm, current, state["baseline"]])
    order, ratios = priority_editor(identity, current["order"] if current else [""] * len(c_ids))
    st.subheader("Nilai alternatif")
    st.caption("Isi setiap sel sesuai skala kriteria. Arah Benefit berarti nilai lebih tinggi lebih baik, "
               "sedangkan Cost berarti nilai lebih rendah lebih baik.")
    st.dataframe(pd.DataFrame(criteria), hide_index=True)
    values = st.data_editor(matrix, disabled=["_index"], key=f"matrix-{identity}",
                            column_config={c["Kode"]: st.column_config.NumberColumn(
                                min_value=c["Min"], max_value=c["Maks"]) for c in criteria})
    if st.button("Simpan penilaian", type="primary", disabled=ratios is None):
        try:
            form = dict(matrix=values.to_numpy(dtype=float).tolist(), order=order, ratios=ratios)
            validate_form(config, form)
        except ValueError as exc:
            st.error(str(exc))
        else:
            forms[dm] = form
            commit(f"Penilaian {dm} tersimpan.")


def leaders(ranking):
    rows = []
    for item in ranking.head(3).to_dict("records"):
        rows.append(
            f'<li class="gdss-leader"><span class="gdss-leader-rank">{item["Rank grup"]:g}</span>'
            f'<span class="gdss-leader-name">{escape(item["Nama"])}</span>'
            f'<span class="gdss-leader-points">{item["Poin Borda"]:g} poin</span></li>'
        )
    st.html('<ol class="gdss-leaders" aria-label="Peringkat teratas">' + "".join(rows) + "</ol>")


def ranking_chart(ranking, best_score):
    return (
        alt.Chart(ranking).mark_bar(cornerRadiusEnd=5, size=15)
        .encode(
            x=alt.X("Poin Borda:Q", title="Total poin Borda"),
            y=alt.Y("Kode:N", sort=ranking["Kode"].tolist(), title="Alternatif",
                    axis=alt.Axis(labelOverlap=False)),
            color=alt.condition(alt.datum["Poin Borda"] == best_score,
                                alt.value("#087e74"), alt.value("#9ab7d1")),
            tooltip=[alt.Tooltip("Nama:N", title="Rumah sakit"),
                     alt.Tooltip("Rank grup:Q", title="Peringkat"),
                     alt.Tooltip("Poin Borda:Q", title="Poin Borda")],
        )
        .properties(height=max(200, 22 * len(ranking)))
        .configure_view(stroke=None)
    )


def results():
    hero("Dashboard keputusan", "Simulasi Alabama" if config == DEMO["config"] else "Konfigurasi aktif",
         "Ranking rumah sakit berdasarkan FUCOM, EDAS, dan Borda.")
    details = {dm: edas(config, forms[dm]) for dm in dm_ids if dm in forms}
    complete = len(details) == len(dm_ids)
    ranking, points = group_ranking(config, details) if complete else (None, None)
    best_score = ranking["Poin Borda"].max() if complete else None

    with st.container(key="dashboard-metrics"):
        metrics = st.columns(4)
        metrics[0].metric("Alternatif", len(a_ids), border=True)
        metrics[1].metric("Kriteria", len(c_ids), border=True)
        metrics[2].metric("DM terisi", f"{len(details)}/{len(dm_ids)}", border=True)
        metrics[3].metric("Poin Borda tertinggi", f"{best_score:g}" if complete else "—", border=True)

    if not details:
        st.info("Isi penilaian minimal satu DM untuk melihat perhitungan EDAS.")
        return
    weights = pd.DataFrame({dm: details[dm]["weights"] for dm in details}, index=c_ids)
    rank_tab, weights_tab, calc_tab = st.tabs(["Ranking kelompok", "Preferensi antar-DM", "Rincian EDAS"])
    with rank_tab:
        if not complete:
            remaining = ", ".join(dm for dm in dm_ids if dm not in details)
            st.info(f"Ranking Borda menunggu penilaian dari {remaining}.")
        else:
            chart_panel, leader_panel = st.columns([5, 4], gap="medium")
            with chart_panel.container(border=True, key="borda-chart"):
                st.subheader("Distribusi poin Borda")
                limit = min(8, len(ranking))
                show_all = st.toggle("Tampilkan semua alternatif", disabled=limit == len(ranking))
                displayed = ranking if show_all else ranking.head(limit)
                st.altair_chart(ranking_chart(displayed, best_score), width="stretch")
            with leader_panel.container(border=True, key="borda-leaders"):
                st.subheader("Peringkat teratas")
                leaders(ranking)
                st.markdown("**Bobot rata-rata tertinggi**")
                criteria_names = {c["Kode"]: c["Nama"] for c in criteria}
                for code, weight in weights.mean(axis=1).nlargest(2).items():
                    st.progress(float(weight), text=f"{code} · {criteria_names[code]} · {weight:.1%}")
            st.subheader("Tabel ranking lengkap")
            st.dataframe(ranking, hide_index=True)
            with st.expander("Poin Borda per DM"):
                st.dataframe(pd.DataFrame(points, index=a_ids, columns=dm_ids))
            st.caption("Poin tiap DM = jumlah alternatif + 1 − rank. Nilai seri mendapat rata-rata peringkat. "
                       "Urutan alternatif pada konfigurasi menentukan urutan tampilan saat total poin seri.")
            left, right = st.columns(2)
            left.download_button("Unduh ranking CSV", ranking.to_csv(index=False).encode("utf-8-sig"),
                                 "ranking_borda.csv", mime="text/csv")
            if right.button("Simpan snapshot keputusan"):
                state["history"].append({"Waktu": timestamp(), "Ranking": ranking.to_dict("records"),
                                         "Konfigurasi": config, "Penilaian": forms})
                commit("Snapshot keputusan tersimpan.")
    with weights_tab:
        st.subheader("Bobot FUCOM per kriteria")
        st.dataframe(weights.assign(**{"Rata-rata DM terisi": weights.mean(axis=1)}))
        long = weights.rename_axis("Kriteria").reset_index().melt("Kriteria", var_name="DM", value_name="Bobot")
        chart = alt.Chart(long).mark_bar().encode(
            x=alt.X("Kriteria:N", sort=c_ids), xOffset="DM:N",
            y=alt.Y("Bobot:Q", axis=alt.Axis(format="%")),
            color=alt.Color("DM:N", scale=alt.Scale(scheme="tableau10")),
            tooltip=["Kriteria", "DM", alt.Tooltip("Bobot:Q", format=".2%")]
        )
        st.altair_chart(chart, width="stretch")
        st.subheader("Perbandingan skor EDAS")
        scores = pd.DataFrame({dm: details[dm]["scores"][:, 4] for dm in details}, index=a_ids)
        st.dataframe(scores)
    with calc_tab:
        dm = st.selectbox("Rincian DM", list(details))
        data = details[dm]
        st.caption(f"Deviasi maksimum rasio FUCOM berurutan: {data['dfc']:.3g}")
        st.dataframe(pd.DataFrame([data["average"], data["weights"]],
                                  index=["Rata-rata nilai (AV)", "Bobot FUCOM"], columns=c_ids))
        left, right = st.columns(2)
        for panel, key, title in ((left, "pda", "PDA · jarak positif relatif"),
                                  (right, "nda", "NDA · jarak negatif relatif")):
            panel.subheader(title)
            panel.dataframe(pd.DataFrame(data[key], index=a_ids, columns=c_ids))
        st.subheader("Normalisasi dan skor per alternatif")
        st.dataframe(pd.DataFrame(data["scores"], index=a_ids, columns=["SP", "SN", "NSP", "NSN", "AS", "Rank"]))


def collaboration_page():
    st.header("Diskusi dan riwayat")
    with st.form("discussion"):
        st.caption(f"Penulis catatan · {user}")
        message = st.text_area("Catatan diskusi", max_chars=2000)
        if st.form_submit_button("Kirim catatan"):
            if not message.strip():
                st.error("Isi catatan diskusi.")
            else:
                state["discussion"].append({"Waktu": timestamp(), "DM": user, "Catatan": message.strip()})
                commit("Catatan tersimpan.")
    for note in reversed(state["discussion"]):
        st.caption(f"{note['DM']} · {note['Waktu']}")
        st.text(note["Catatan"])
    st.subheader("Snapshot keputusan")
    if not state["history"]:
        st.caption("Snapshot dapat disimpan dari halaman Hasil setelah ranking kelompok tersedia.")
    for i, record in reversed(list(enumerate(state["history"], 1))):
        with st.expander(f"Keputusan {i} · {record['Waktu']}"):
            st.dataframe(pd.DataFrame(record["Ranking"]), hide_index=True)
            st.download_button("Unduh snapshot JSON", json.dumps(record, ensure_ascii=False, indent=2),
                               f"keputusan-{i}.json", mime="application/json", key=f"snapshot-{i}")


def check_excel():
    st.header("Verifikasi terhadap Excel")
    st.write("Aplikasi menghitung ulang dataset simulasi asli lalu membandingkannya dengan nilai yang tersimpan "
             "di workbook sumber. Toleransi absolut untuk nilai numerik adalah 10⁻¹⁰.")
    reports = verify()
    count = sum(row["Cocok"] for row in reports)
    (st.success if count == len(reports) else st.error)(f"{count}/{len(reports)} pemeriksaan cocok.")
    st.dataframe(pd.DataFrame(reports), hide_index=True)
    st.caption("Acuan: GDSS_FUCOM_EDAS_DOCUMENTED_3.xlsx. "
               "Perbandingan mencakup keluaran numerik dan urutan rumah sakit.")


pages = {"Hasil": results}
if is_admin:
    pages.update({"Konfigurasi": edit_setup, "Akun pengguna": manage_accounts})
else:
    pages["Penilaian DM"] = assessment
pages.update({"Diskusi & riwayat": collaboration_page, "Verifikasi Excel": check_excel})
page = st.sidebar.radio("Navigasi", list(pages), key=f"navigation-{user}")
st.sidebar.divider()
st.sidebar.subheader("Status pengisian")
st.sidebar.progress(len(forms) / len(dms), text=f"{len(forms)} dari {len(dms)} DM terisi")
for dm in dm_ids:
    st.sidebar.text(f"{dm} · {'Terisi' if dm in forms else 'Menunggu'}")
if st.sidebar.button("Muat ulang data aktif"):
    st.rerun()

if "notice" in st.session_state:
    st.success(st.session_state.pop("notice"))
pages[page]()

