# Backend API Layar Workbench (ECL Transparency & Audit Workbench)

Fitur Uji Banding & Audit Kalkulasi (ECL Transparency & Audit Workbench) berbasis Python FastAPI. Program ini melayani permintaan aplikasi frontend untuk menampilkan rincian audit perbandingan yang transparan per rekening antara metode sederhana bank (Excel/DPD) dan metode presisi aplikasi Syariah (*The Grand Master Engine*).

Rujukan Utama: **Dokumen Pertanyaan 4 - Fitur Uji Banding & Audit Kalkulasi**.

---

## 📌 Alur Proses Bisnis & Aturan Bisnis

### 1. Alur Proses Bisnis (Audit Workbench Flow)
1. **Aksi Pilihan Analis**: Analis di frontend membuka menu **"ECL Audit & Benchmarking Workbench"**.
2. **Input Filter**: Analis memilih nomor rekening tertentu atau memilih seluruh portofolio segmen pada periode tutup buku berjalan.
3. **Eksekusi Pembanding Dual-Run**: Sistem menyandingkan 3 komponen utama secara berdampingan:
   - **Metode Bank / Excel**: Hanya DPD & Plafon Kotor.
   - **Metode Syariah Murni**: Ultimate EAD bersih dari margin Riba + PD Markov/Vasicek + LGD NPV DCF.
   - **Nilai Final Buku Besar**: Hasil override/individual assessment jika ada.
4. **Visualisasi Alasan Selisih (Variance Breakdown)**: Sistem memecah faktor selisih (contoh: Efek sterilisasi unearned margin vs Efek SICR kualitatif sektor riil).

### 2. Aturan Bisnis (Business Rules)
* **BR-AUD-01 (Transparansi Mutlak)**: Modul ini bersifat *Read-Only* untuk analisis, memastikan tidak ada manipulasi data yang dapat mengubah pembukuan di General Ledger secara tak terotorisasi.
* **BR-AUD-02 (Standar Kepatuhan Syariah)**: Penjelasan selisih wajib mencantumkan alasan teologis dan akuntansi (misal: "Selisih Rp X terjadi karena metode bank masih memasukkan pendapatan margin masa depan yang belum terwujud").

---

## 🗄️ Kamus Data & Desain Tabel Data Mart (`dm_ecl_audit_workbench`)

| Nama Kolom | Tipe Data | Constraint | Keterangan |
| :--- | :--- | :--- | :--- |
| `tgl_proses` | `DATE` | PK | Tanggal tutup buku akhir bulan |
| `no_rekening` | `VARCHAR(50)` | PK | Nomor fasilitas pembiayaan |
| `baki_debet_kotor` | `NUMERIC(18,2)` | Not Null | Eksposur versi Excel Bank (Baki Debet Kotor) |
| `ead_bersih_syariah` | `NUMERIC(18,2)` | Not Null | Eksposur versi Aplikasi Syariah (Bersih Riba) |
| `ckpn_metode_bank` | `NUMERIC(18,2)` | Not Null | Hasil hitung sederhana versi bank |
| `ckpn_metode_aplikasi`| `NUMERIC(18,2)` | Not Null | Hasil hitung The Grand Master Engine |
| `faktor_penyebab_gap` | `VARCHAR(255)` | Not Null | Keterangan analitik perbedaan nilai |

---

## 🔌 API Endpoints

### 1. `GET /api/audit/workbench/{no_rekening}`
Menampilkan detail transparansi audit per nomor rekening.

**Contoh Response:**
```json
{
  "status": "success",
  "keterangan_audit": "Fitur ini membuktikan transparansi mutlak perhitungan sistem terhadap metode konvensional bank.",
  "detail_perbandingan": {
    "No Rekening": "10000000012",
    "Nama Nasabah": "PT Barakah Nusantara Sektor Riil",
    "Baki Debet Kotor (Excel Bank)": 1500000000.0,
    "EAD Bersih (Tanpa Margin Riba)": 1200000000.0,
    "CKPN Metode Sederhana (Rp)": 15000000.0,
    "CKPN Grand Master Syariah (Rp)": 75000000.0,
    "Selisih Gap (Rp)": 60000000.0,
    "Analisis Kepatuhan & Risiko": "GAP POSITIF: Sistem mendeteksi risiko kualitatif/Sektor Riil (SICR) yang diabaikan DPD."
  }
}
```

### 2. `GET /api/audit/workbench`
Menampilkan daftar perbandingan seluruh portofolio rekening.

---

## 🛠️ Cara Menjalankan Aplikasi

1. **Jalankan Seed Data (Opsional untuk testing lokal SQLite)**:
   ```bash
   python seed_data.py
   ```

2. **Jalankan FastAPI Server**:
   ```bash
   python main.py
   # atau menggunakan uvicorn
   uvicorn main:app --reload --port 8000
   ```

3. **Buka dokumentasi Swagger UI**:
   Akses `http://localhost:8000/docs` di browser.

4. **Jalankan Automated Tests**:
   ```bash
   pytest test_main.py -v
   ```
