-- =============================================================================
-- FITUR UJI BANDING & AUDIT KALKULASI (ECL TRANSPARENCY & AUDIT WORKBENCH)
-- File: 01_ddl_dm_ecl_audit_workbench.sql
-- Desain Tabel & Kamus Data (PERTANYAAN 4)
-- =============================================================================

-- 1. Skema Tabel Data Mart: dm_ecl_audit_workbench
-- Menampung perbandingan transparan per rekening antara metode bank (Excel)
-- dengan metode aplikasi syariah (The Grand Master Engine).

-- Dialek PostgreSQL / SQL Server Compatible DDL
CREATE TABLE IF NOT EXISTS dm_ecl_audit_workbench (
    tgl_proses          DATE            NOT NULL, -- Tanggal tutup buku akhir bulan
    no_rekening         VARCHAR(50)     NOT NULL, -- Nomor fasilitas pembiayaan
    baki_debet_kotor    NUMERIC(18,2)   NOT NULL, -- Eksposur versi Excel Bank (Baki Debet Kotor)
    ead_bersih_syariah  NUMERIC(18,2)   NOT NULL, -- Eksposur versi Aplikasi Syariah (Bersih Margin Riba)
    ckpn_metode_bank    NUMERIC(18,2)   NOT NULL, -- Hasil hitung sederhana versi bank (DPD)
    ckpn_metode_aplikasi NUMERIC(18,2)  NOT NULL, -- Hasil hitung The Grand Master Engine Syariah
    faktor_penyebab_gap VARCHAR(255)    NOT NULL, -- Keterangan analitik perbedaan nilai
    PRIMARY KEY (tgl_proses, no_rekening)
);

-- Indexing untuk mempercepat query API Workbench berdasarkan no_rekening dan tgl_proses
CREATE INDEX IF NOT EXISTS idx_audit_wb_rekening ON dm_ecl_audit_workbench (no_rekening);
CREATE INDEX IF NOT EXISTS idx_audit_wb_tgl ON dm_ecl_audit_workbench (tgl_proses);

-- 2. Skema Tabel Dimensi Fasilitas / Nasabah (dim_fasilitas)
CREATE TABLE IF NOT EXISTS dim_fasilitas (
    no_rekening         VARCHAR(50)     PRIMARY KEY,
    nama_debitur        VARCHAR(150)    NOT NULL,
    cif                 VARCHAR(50)     NULL,
    jenis_akad          VARCHAR(50)     NULL, -- Mudharabah, Musyarakah, Murabahah, dll
    plafon              NUMERIC(18,2)   NULL
);
