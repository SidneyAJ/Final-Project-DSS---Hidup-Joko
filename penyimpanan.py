"""Penyimpanan lokal yang dipakai bersama oleh sesi Streamlit."""
import json
import os
import sqlite3
from contextlib import closing
from copy import deepcopy
from pathlib import Path

from autentikasi import ADMIN, DEMO_PASSWORDS, hash_password

ROOT = Path(__file__).resolve().parent
DATABASE = Path(os.environ.get("GDSS_DB", ROOT / "gdss.sqlite3"))
DEMO = json.loads((ROOT / "simulasi.json").read_text(encoding="utf-8"))


class KonflikData(Exception):
    pass


def read():
    with closing(sqlite3.connect(DATABASE, timeout=10)) as db, db:
        db.execute("CREATE TABLE IF NOT EXISTS project (id INTEGER PRIMARY KEY, rev INTEGER, data TEXT)")
        initial = {key: deepcopy(DEMO[key]) for key in ("config", "forms", "baseline")}
        initial.update(history=[], discussion=[])
        db.execute("INSERT OR IGNORE INTO project VALUES (1, 0, ?)", (json.dumps(initial),))
        rev, raw = db.execute("SELECT rev, data FROM project WHERE id=1").fetchone()
        state = json.loads(raw)
        if "accounts" not in state:
            active_codes = {ADMIN, *(dm["Kode"] for dm in state["config"]["dms"])}
            state["accounts"] = {code: hash_password(password)
                                 for code, password in DEMO_PASSWORDS.items() if code in active_codes}
            rev += 1
            db.execute("UPDATE project SET rev=?, data=? WHERE id=1", (rev, json.dumps(state)))
    return rev, state


def save(rev, state):
    payload = json.dumps(state, ensure_ascii=False, allow_nan=False)
    with closing(sqlite3.connect(DATABASE, timeout=10)) as db, db:
        if db.execute("UPDATE project SET rev=rev+1, data=? WHERE id=1 AND rev=?",
                      (payload, rev)).rowcount != 1:
            raise KonflikData("Data baru disimpan dari sesi lain. Muat ulang halaman sebelum mengirim kembali.")

