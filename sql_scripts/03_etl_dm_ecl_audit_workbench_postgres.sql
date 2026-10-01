-- =============================================================================
-- FITUR UJI BANDING & AUDIT KALKULASI (ECL TRANSPARENCY & AUDIT WORKBENCH)
-- File: 03_etl_dm_ecl_audit_workbench_postgres.sql
-- Skrip SQL (ETL) Pembentukan Tabel Audit Workbench (PostgreSQL / PL/pgSQL)
-- Rujukan Dokumen: PERTANYAAN 4 - III. Skrip SQL (ETL)
-- =============================================================================

BEGIN;

-- 1. Bersihkan data untuk tanggal proses saat ini
DELETE FROM dm_ecl_audit_workbench WHERE tgl_proses = CURRENT_DATE;

-- 2. Populate data perbandingan ke data mart
INSERT INTO dm_ecl_audit_workbench (
    tgl_proses, 
    no_rekening, 
    baki_debet_kotor, 
    ead_bersih_syariah, 
    ckpn_metode_bank, 
    ckpn_metode_aplikasi, 
    faktor_penyebab_gap
)
SELECT 
    CURRENT_DATE AS tgl_proses,
    s.account_number AS no_rekening,
    COALESCE(bal.os_pokok, 0) AS baki_debet_kotor,
    COALESCE(ead.total_ultimate, 0) AS ead_bersih_syariah,
    
    -- Kalkulasi Sederhana Versi Bank (DPD > 90 -> 50% dari Saldo Kotor, else 1%)
    COALESCE(
        CASE 
            WHEN COALESCE(dpd.days_past_due, 0) > 90 THEN bal.os_pokok * 0.50 
            ELSE bal.os_pokok * 0.01 
        END, 
        0
    )::NUMERIC(18,2) AS ckpn_metode_bank,
    
    -- Kalkulasi Presisi Grand Master Engine Syariah
    COALESCE(fin.total_nominal_ckpn, 0) AS ckpn_metode_aplikasi,
    
    -- Analisis Otomatis Penyebab Gap
    CASE 
        WHEN COALESCE(fin.total_nominal_ckpn, 0) > (COALESCE(bal.os_pokok, 0) * 0.50) 
        THEN 'GAP POSITIF: Sistem mendeteksi risiko kualitatif/Sektor Riil (SICR) yang diabaikan DPD.'
        WHEN COALESCE(fin.total_nominal_ckpn, 0) < (COALESCE(bal.os_pokok, 0) * 0.01)
        THEN 'GAP NEGATIF: Penyesuaian Sterilisasi Unearned Margin Riba memisahkan baki debet pokok riil.'
        ELSE 'ALIGNED: Perhitungan relatif selaras.'
    END AS faktor_penyebab_gap

FROM cltb_account_apps_master s
LEFT JOIN source_clvs_acc_comp_balances_temp bal ON s.account_number = bal.account_number
LEFT JOIN temp_dpd_vmid dpd ON s.account_number = dpd.account_number
LEFT JOIN fact_ultimate_ead_cons ead ON s.account_number = ead.no_rekening
LEFT JOIN fact_psak413_ckpn_final_detail fin ON s.account_number = fin.no_rekening;

COMMIT;
