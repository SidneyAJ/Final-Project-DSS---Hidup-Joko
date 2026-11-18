# GDSS Evaluasi Rumah Sakit Alabama

Prototipe Streamlit untuk Penilaian 6. Versi ini memakai workbook `GDSS_FUCOM_EDAS_DOCUMENTED_3.xlsx` dan memulai database baru di folder hasil ekstraksi. Pada data awal, Jackson Hospital & Clinic Inc menempati peringkat pertama dengan 60 poin Borda. Jalankan dari folder hasil ekstraksi, yaitu folder yang berisi `app.py` dan `simulasi.json`.

## Instalasi dan demo di Windows

Gunakan Python 3.12, buka PowerShell di folder proyek, lalu jalankan:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
```
Jika saat mengikuti langkah-langkah di atas muncul pemberitahuan pembaruan pip atau terjadi kendala ketika menjalankan salah satu perintah, jalankan perintah berikut untuk memperbarui pip. Setelah itu, ulangi perintah yang sebelumnya mengalami kendala.

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
```

Buka `http://127.0.0.1:8501` jika browser tidak terbuka otomatis. Jika Python tersedia melalui perintah `python`, gunakan `python -m venv .venv` pada langkah pertama. Tekan Ctrl+C pada terminal untuk menghentikan server.

Penggunaan pertama memuat data simulasi lengkap. Data perubahan disimpan di `gdss.sqlite3` pada folder proyek. Untuk menggunakan file SQLite lain, tetapkan `$env:GDSS_DB` ke path absolut file sebelum menjalankan aplikasi. Login diperlukan untuk membuka seluruh halaman aplikasi.

## Akun demo lokal

| Nama pengguna | Kata sandi awal | Akses |
|---|---|---|
| `Admin` | `AlabamaAdmin26!` | Konfigurasi, pengelolaan akun, dan hasil |
| `dm1` | `AlabamaDM1-26!` | Form DM1 dan hasil |
| `dm2` | `AlabamaDM2-26!` | Form DM2 dan hasil |
| `dm3` | `AlabamaDM3-26!` | Form DM3 dan hasil |

Pilih **Keluar** di sidebar untuk berganti akun. Untuk memberi DM baru akses, masuk sebagai admin, tambahkan kode DM pada **Konfigurasi**, lalu buat kata sandinya di **Akun pengguna**. Mengubah kata sandi mengakhiri akses sesi lama saat sesi tersebut memuat ulang atau melakukan tindakan. Simpan kata sandi demo untuk pengujian di localhost. Jika dipakai bersama, tetapkan kata sandi baru tiap akun dan berikan masing-masing kredensial kepada pemilik akun. SQLite menyimpan hash kata sandi dengan salt individual.

## Alur penggunaan

1. **Konfigurasi (admin)** — tambah, ubah, atau hapus alternatif, kriteria, dan DM. Isi kode unik. Kriteria memakai tipe Benefit/Cost dan rentang minimum hingga maksimum. Perubahan pada alternatif/kriteria membuat penilaian lama perlu diisi kembali.
2. **Penilaian DM** — masuk dengan akun DM, isi matriks miliknya, susun semua kriteria tepat sekali, lihat rasio FUCOM yang otomatis diperbarui saat semua posisi terisi, lalu simpan. Perhatikan status di sidebar.
3. **Hasil** — lihat bobot FUCOM, PDA/NDA, SP/SN, NSP/NSN, AS dan rank tiap DM. Ranking Borda tampil setelah seluruh DM mengirim penilaian. Klik **Simpan snapshot keputusan** jika hasil perlu diarsipkan.
4. **Diskusi & riwayat** — simpan catatan per DM, lihat snapshot terdahulu, atau unduh snapshot JSON.
5. **Verifikasi Excel** — jalankan pemeriksaan pada dataset simulasi asli. Untuk mengulang demo dengan data awal, klik **Konfigurasi → Pulihkan simulasi Alabama → Muat ulang data simulasi**. Riwayat dan catatan sebelumnya tetap tersimpan.

## Perintah verifikasi

```powershell
.\.venv\Scripts\python.exe verifikasi.py
```

Verifikasi membaca nilai acuan yang diekstrak setelah Microsoft Excel menghitung ulang salinan workbook terbaru. Aplikasi menghitung bobot dan ranking dari input simulasi. Workbook Excel tidak diperlukan untuk menjalankan aplikasi.

## Isi paket

- `app.py` — halaman dan form Streamlit.
- `metode.py` — validasi, bobot FUCOM, EDAS, dan agregasi Borda.
- `autentikasi.py` — verifikasi login dan hashing kata sandi.
- `penyimpanan.py` — penyimpanan SQLite bersama antarsesi.
- `simulasi.json` — konfigurasi, input demo, dan nilai pembanding Excel.
- `verifikasi.py` — pemeriksaan regresi dataset simulasi.
- `Materi/` — laporan akhir dan slide presentasi.

Rujukan API antarmuka: [Streamlit data editor](https://docs.streamlit.io/develop/api-reference/data/st.data_editor).

