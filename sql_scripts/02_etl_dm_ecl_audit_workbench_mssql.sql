-- =============================================================================
-- FITUR UJI BANDING & AUDIT KALKULASI (ECL TRANSPARENCY & AUDIT WORKBENCH)
-- File: 02_etl_dm_ecl_audit_workbench_mssql.sql
-- Skrip SQL (ETL) Pembentukan Tabel Audit Workbench (MS SQL Server / T-SQL / SSIS)
-- Rujukan Dokumen: PERTANYAAN 4 - III. Skrip SQL (ETL)
-- =============================================================================

SET NOCOUNT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    DECLARE @TargetDate DATE = (SELECT EOMONTH(DATEADD(m, -1, GETDATE())));

    -- 1. Bersihkan tabel audit workbench untuk periode yang diproses
    DELETE FROM dm_ecl_audit_workbench WHERE tgl_proses = @TargetDate;

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
        @TargetDate AS tgl_proses,
        s.ACCOUNT_NUMBER AS no_rekening,
        ISNULL(bal.OS_POKOK, 0) AS baki_debet_kotor,
        ISNULL(ead.total_ultimate, 0) AS ead_bersih_syariah,
        
        -- Kalkulasi Sederhana Versi Bank (DPD > 90 -> 50% dari Saldo Kotor, else 1%)
        CAST(
            CASE 
                WHEN ISNULL(dpd.days_past_due, 0) > 90 THEN ISNULL(bal.OS_POKOK, 0) * 0.50 
                ELSE ISNULL(bal.OS_POKOK, 0) * 0.01 
            END 
        AS NUMERIC(18,2)) AS ckpn_metode_bank,
        
        -- Kalkulasi Presisi Grand Master Engine Syariah
        ISNULL(fin.total_nominal_ckpn, 0) AS ckpn_metode_aplikasi,
        
        -- Analisis Otomatis Penyebab Gap
        CASE 
            WHEN ISNULL(fin.total_nominal_ckpn, 0) > (ISNULL(bal.OS_POKOK, 0) * 0.50) 
            THEN 'GAP POSITIF: Sistem mendeteksi risiko kualitatif/Sektor Riil (SICR) yang diabaikan DPD.'
            WHEN ISNULL(fin.total_nominal_ckpn, 0) < (ISNULL(bal.OS_POKOK, 0) * 0.01)
            THEN 'GAP NEGARIF: Penyesuaian Sterilisasi Unearned Margin Riba memisahkan baki debet pokok riil.'
            ELSE 'ALIGNED: Perhitungan relatif selaras.'
        END AS faktor_penyebab_gap

    FROM CLTB_ACCOUNT_APPS_MASTER s
    LEFT JOIN Source_CLVS_ACC_COMP_BALANCES_Temp bal ON s.ACCOUNT_NUMBER = bal.ACCOUNT_NUMBER
    LEFT JOIN TEMP_DPD_VMID dpd ON s.ACCOUNT_NUMBER = dpd.ACCOUNT_NUMBER
    LEFT JOIN fact_ultimate_ead_cons ead ON s.ACCOUNT_NUMBER = ead.no_rekening AND ead.tgl_proses = @TargetDate
    LEFT JOIN fact_psak413_ckpn_final_detail fin ON s.ACCOUNT_NUMBER = fin.no_rekening AND fin.tgl_proses = @TargetDate;

    COMMIT TRANSACTION;
    PRINT 'ETL dm_ecl_audit_workbench (MS SQL Server) sukses dieksekusi.';
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
    RAISERROR (@ErrorMessage, 16, 1);
END CATCH;
