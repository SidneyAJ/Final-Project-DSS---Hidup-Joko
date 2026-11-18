# Laporan Akhir Penilaian 6
## Prototipe GDSS FUCOM–EDAS–Borda untuk Evaluasi Rumah Sakit Alabama

**Identitas kelompok**  
Isi nama mata kuliah, kelas, nama kelompok, serta nama dan NIM anggota sebelum pengumpulan.

### 1. Tujuan dan ruang lingkup

Prototipe mendukung evaluasi 20 rumah sakit di Alabama dengan enam kriteria. Pengambil keputusan (decision maker atau DM) menyimpan nilai alternatif dan preferensi melalui akun masing-masing. Login membatasi pengeditan formulir ke DM yang memilikinya. Admin mengelola konfigurasi dan akun. Semua akun yang berhasil masuk dapat melihat hasil. Aplikasi menampilkan hasil tiap DM, lalu menggabungkan peringkat mereka menjadi keputusan kelompok.

Data awal bersumber dari workbook final. Workbook mencatat periode C5 Januari–Desember 2025 dan periode C6 Juli 2024–Juni 2025. Tiga DM latihan memakai matriks awal yang sama dengan urutan prioritas dan rasio berbeda. Peran dan preferensi pada skenario ini merupakan asumsi simulasi akademik.

### 2. Kriteria dan validasi

| Kode | Kriteria | Arah | Skala input awal |
|---|---|---|---|
| C1 | Clinical Outcomes | Benefit | 0–100 |
| C2 | Person and Community Engagement | Benefit | 0–100 |
| C3 | Safety | Benefit | 0–100 |
| C4 | Efficiency and Cost Reduction | Benefit | 0–100 |
| C5 | Emergency Department Length of Stay | Cost | 0–1000 menit |
| C6 | Hospital-Wide All-Cause Readmission | Cost | 0–100% |

Batas 1000 menit untuk C5 dipilih sebagai aturan validasi prototipe dan dapat diedit. C4 adalah skor efisiensi yang meningkat saat kinerja membaik. Tipe dan skala setiap kriteria dapat disesuaikan. Aplikasi memeriksa kode unik, kelengkapan matriks, angka yang berada dalam skala, dan urutan kriteria tanpa duplikasi.

### 3. Perhitungan

**FUCOM.** Urutkan kriteria berdasarkan prioritas DM. Tetapkan bobot mentah pertama sebesar 1. Untuk urutan berikutnya, bagi bobot mentah sebelumnya dengan rasio otomatis. Rasio dihasilkan dari pembagian skor prioritas yang berurutan. Untuk enam kriteria, skor prioritas adalah (7 − urutan) + (7 − indeks kriteria)/7. Normalisasi bobot mentah setelah semua rasio diterapkan. Pendekatan ini merupakan solusi eksak untuk kendala rasio berurutan di workbook. Deviasi mendekati nol terbentuk dari cara bobot dihitung.

**EDAS.** Hitung rata-rata AV setiap kriteria. Untuk Benefit, hitung jarak relatif dengan rumus (nilai − AV)/AV. Untuk Cost, balik arah selisihnya. PDA adalah bagian positif jarak, sedangkan NDA adalah besarnya bagian negatif. Kriteria dengan seluruh nilai nol memberi jarak nol. Jumlah berbobot dari PDA dan NDA menghasilkan SP dan SN. Normalisasi menghasilkan NSP = SP/maksimum SP dan NSN = 1 − SN/maksimum SN. Ketika maksimum penyebut nol, komponen terkait diberi nilai 1 sesuai konvensi workbook. Skor AS adalah rata-rata NSP dan NSN. Urutkan AS menurun dan berikan rata-rata peringkat untuk skor seri.

**Borda.** Setiap DM memberikan N + 1 − rank poin untuk setiap alternatif, dengan N adalah jumlah alternatif aktif. Total poin dari semua DM menentukan ranking kelompok. Posisi seri diberi rata-rata peringkat. Jika total seri, urutan tabel mengikuti urutan data masukan.

### 4. Hasil simulasi dan pengujian

| Peringkat kelompok | Rumah sakit | Rank DM1 | Rank DM2 | Rank DM3 | Poin Borda |
|---:|---|---:|---:|---:|---:|
| 1 | Jackson Hospital & Clinic Inc | 1 | 1 | 1 | 60 |
| 2 | Southeast Health Medical Center | 2 | 4 | 7 | 50 |
| 3 | Baptist Medical Center South | 4 | 7 | 3 | 49 |

Seluruh 17 pemeriksaan lulus dengan toleransi absolut 10⁻¹⁰. Pemeriksaan mencakup bobot FUCOM, rata-rata, matriks PDA/NDA, skor dan rank EDAS tiga DM, detail Borda, serta urutan 20 rumah sakit. Selisih numerik terbesar sekitar 5,68 × 10⁻¹⁴. Poin Borda tepat sama. Workbook menandai hasil sebagai ranking simulasi.

### 5. Pemetaan terhadap rubrik

| Butir | Bukti yang ditunjukkan saat presentasi |
|---|---|
| 6.1 | Konfigurasi → Penilaian DM → hasil antara FUCOM/EDAS → Borda. |
| 6.2 | Masuk sebagai DM1, lihat form DM1, keluar, lalu masuk sebagai DM2. |
| 6.3 | Tambah, ubah, dan hapus baris dalam tabel Konfigurasi. |
| 6.4 | Buka Verifikasi Excel dan lihat 17 pemeriksaan. |
| 6.5 | Tampilkan matriks PDA/NDA, bobot dan skor EDAS tiap DM. |
| 6.6 | Buka grafik ranking Borda dan grafik bobot antar-DM. |
| 6.7 | Kosongkan nilai atau masukkan prioritas ganda. Tunjukkan batas skala pada kolom matriks. |
| 6.8 | Gunakan halaman login, navigasi sesuai peran, dan status pengisian. |
| 6.9 | Kirim satu catatan, simpan snapshot, dan buka snapshot dari riwayat. |
| 6.10 | Jalankan demonstrasi pada laptop presentasi mengikuti panduan instalasi. |
| 6.11 | Lampirkan laporan ini, sumber kode, panduan instalasi dan slide. |
| 6.12 | Bagi topik di bawah sesuai jumlah anggota dan latih tanya jawab. |

### 6. Pembagian materi tanya jawab

- **Data dan konfigurasi.** Jelaskan sumber matriks, enam kriteria, perbedaan Benefit dan Cost, serta alasan C4 bertipe Benefit.
- **FUCOM.** Beri contoh rasio 1,15. Bobot mentah setelah prioritas pertama menjadi 1/1,15. Jelaskan mengapa DFC kecil ketika rasio berurutan dipenuhi oleh konstruksi.
- **EDAS.** Jelaskan AV, PDA/NDA, dan bagaimana bobot DM yang berbeda menghasilkan ranking yang berbeda meski matriks awal sama.
- **Borda, aplikasi, dan verifikasi.** Jackson memperoleh (21 − 1) + (21 − 1) + (21 − 1) = 60 poin. Jelaskan aturan seri, batas akses form, dan cara membandingkan hasil dengan Excel.

### 7. Kesimpulan

Prototipe menjalankan evaluasi multi-DM dan memperlihatkan perhitungan hingga rekap Borda. Jackson Hospital & Clinic Inc berada di peringkat pertama pada skenario simulasi workbook. Hasil memuat asumsi preferensi akademik dan menggunakan penyimpanan SQLite lokal. Kata sandi disimpan sebagai hash PBKDF2-SHA256 dengan salt individual. Sesi Streamlit menyimpan identitas pengguna sampai logout atau akses akun berubah.

### Sumber

- `GDSS_FUCOM_EDAS_DOCUMENTED_3.xlsx` — `KRITERIA`, `MATRIKS_FINAL`, `DM1–DM3`, `FUCOM_DM1–3`, `EDAS_DM1–3`, `BORDA`, `RANKING_AKHIR`.
- Rubrik **Penilaian 6 — Prototype dan presentasi akhir**, lampiran gambar.
- [Dokumentasi Streamlit untuk tabel interaktif](https://docs.streamlit.io/develop/api-reference/data/st.data_editor).

