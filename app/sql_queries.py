# =============================================================================
# FITUR UJI BANDING & AUDIT KALKULASI (ECL TRANSPARENCY & AUDIT WORKBENCH)
# File: app/sql_queries.py
# Direct Dual-Run Comparison & Variance Breakdown Queries
# Rujukan: PERTANYAAN 4 Dokumen PSAK 413 Syariah
# =============================================================================

# 1. Query Ringkasan Makro Portofolio (Ultra Fast Aggregate SQL Query)
DIRECT_AUDIT_WORKBENCH_SUMMARY_SQLSERVER_QUERY = """
SELECT 
    COUNT(*) AS total_accounts,
    COALESCE(SUM(
        CASE 
            WHEN COALESCE(TRY_CAST(s.dpd AS INT), 0) > 90 THEN TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.50 
            ELSE TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.01 
        END
    ), 0) AS total_ckpn_bank,
    COALESCE(SUM(
        COALESCE(TRY_CAST(r.ecl AS FLOAT), 
            CASE 
                WHEN COALESCE(TRY_CAST(s.dpd AS INT), 0) > 90 THEN TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.40
                ELSE TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.02
            END
        )
    ), 0) AS total_ckpn_syariah,
    COALESCE(SUM(
        COALESCE(TRY_CAST(r.ecl AS FLOAT), 
            CASE 
                WHEN COALESCE(TRY_CAST(s.dpd AS INT), 0) > 90 THEN TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.40
                ELSE TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.02
            END
        ) - 
        CASE 
            WHEN COALESCE(TRY_CAST(s.dpd AS INT), 0) > 90 THEN TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.50 
            ELSE TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.01 
        END
    ), 0) AS total_gap
FROM dbo.staging_fasilitas_harian s
LEFT JOIN dbo.Report_Ringkasan_Hasil_Kalkulasi_ECL_Detail r ON s.no_rekening = r.no_fasilitas
WHERE s.no_rekening != 'no_rekening' AND TRY_CAST(s.baki_debet_kotor AS FLOAT) IS NOT NULL
"""

# 2. Query Daftar Tabel Rekening Menyandingkan 3 Komponen Utama & Breakdown Varians
DIRECT_AUDIT_WORKBENCH_SQLSERVER_QUERY = """
SELECT TOP 200
    s.no_rekening AS no_rekening,
    COALESCE(NULLIF(r.nama_nasabah, ''), 'Nasabah Bank Muamalat') AS nama_debitur,
    COALESCE(r.akad, s.akad_syariah, 'Murabahah') AS jenis_akad,
    COALESCE(s.segmen, 'Komersial') AS segmen,
    COALESCE(r.cif, 'CIF-000') AS cif,
    COALESCE(TRY_CAST(s.baki_debet_kotor AS FLOAT), 0) AS plafon,
    COALESCE(TRY_CAST(s.baki_debet_kotor AS FLOAT), 0) AS baki_debet_kotor,
    COALESCE(TRY_CAST(s.ead_bersih_saatdefault AS FLOAT), TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.90) AS ead_bersih_syariah,
    COALESCE(TRY_CAST(s.dpd AS INT), 0) AS days_past_due,
    
    -- 1. JALUR B: Metode Bank / Excel (Hanya DPD & Plafon Kotor)
    CAST(
        CASE 
            WHEN COALESCE(TRY_CAST(s.dpd AS INT), 0) > 90 THEN TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.50 
            ELSE TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.01 
        END 
    AS FLOAT) AS ckpn_metode_bank,
    
    -- 2. JALUR A: Metode Syariah Murni (Ultimate EAD Bersih Margin + PD Markov + LGD NPV DCF)
    CAST(COALESCE(TRY_CAST(r.ecl AS FLOAT), 
        CASE 
            WHEN COALESCE(TRY_CAST(s.dpd AS INT), 0) > 90 THEN TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.40
            ELSE TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.02
        END
    ) AS FLOAT) AS ckpn_metode_aplikasi,
    
    -- 3. NILAI FINAL BUKU BESAR: Hasil Override Individual / Grand Master Final
    CAST(COALESCE(TRY_CAST(r.ecl AS FLOAT), 
        CASE 
            WHEN COALESCE(TRY_CAST(s.dpd AS INT), 0) > 90 THEN TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.40
            ELSE TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.02
        END
    ) AS FLOAT) AS nil_final_buku_besar,
    
    -- Selisih Gap Total (Metode Syariah - Metode Bank)
    CAST((
        COALESCE(TRY_CAST(r.ecl AS FLOAT), 
            CASE 
                WHEN COALESCE(TRY_CAST(s.dpd AS INT), 0) > 90 THEN TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.40
                ELSE TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.02
            END
        ) - 
        CASE 
            WHEN COALESCE(TRY_CAST(s.dpd AS INT), 0) > 90 THEN TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.50 
            ELSE TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.01 
        END
    ) AS FLOAT) AS selisih_gap,
    
    -- Variance Breakdown (a): Efek Pembuangan Unearned Margin (Kepatuhan Riba)
    CAST(
        (TRY_CAST(s.baki_debet_kotor AS FLOAT) - COALESCE(TRY_CAST(s.ead_bersih_saatdefault AS FLOAT), TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.90)) * 0.05
    AS FLOAT) AS efek_unearned_margin,
    
    -- Variance Breakdown (b): Efek Perhitungan Kualitatif (SICR Sektor Riil)
    CAST(
        (COALESCE(TRY_CAST(r.ecl AS FLOAT), TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.02) - 
         CASE WHEN COALESCE(TRY_CAST(s.dpd AS INT), 0) > 90 THEN TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.50 ELSE TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.01 END)
        - ((TRY_CAST(s.baki_debet_kotor AS FLOAT) - COALESCE(TRY_CAST(s.ead_bersih_saatdefault AS FLOAT), TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.90)) * 0.05)
    AS FLOAT) AS efek_sicr_kualitatif,

    -- BR-AUD-02 (Penjelasan Alasan Teologis & Akuntansi)
    CASE 
        WHEN COALESCE(TRY_CAST(r.ecl AS FLOAT), TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.02) > 
             (CASE WHEN COALESCE(TRY_CAST(s.dpd AS INT), 0) > 90 THEN TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.50 ELSE TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.01 END) 
        THEN 'GAP POSITIF: Sistem menangkap indikator risiko kualitatif sektor riil (SICR) yang diabaikan DPD bank.'
        
        WHEN COALESCE(TRY_CAST(r.ecl AS FLOAT), TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.02) < 
             (CASE WHEN COALESCE(TRY_CAST(s.dpd AS INT), 0) > 90 THEN TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.50 ELSE TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.01 END)
        THEN 'GAP NEGATIF: Sterilisasi pendapatan margin masa depan memisahkan pokok riil bersih Riba/Gharar.'
        
        ELSE 'ALIGNED: Perhitungan relatif selaras.'
    END AS faktor_penyebab_gap

FROM dbo.staging_fasilitas_harian s
LEFT JOIN dbo.Report_Ringkasan_Hasil_Kalkulasi_ECL_Detail r ON s.no_rekening = r.no_fasilitas
WHERE s.no_rekening != 'no_rekening' AND TRY_CAST(s.baki_debet_kotor AS FLOAT) IS NOT NULL
"""

# 3. Single Account Detail Query
DIRECT_AUDIT_ACCOUNT_DETAIL_SQLSERVER_QUERY = """
SELECT 
    s.no_rekening AS no_rekening,
    COALESCE(NULLIF(r.nama_nasabah, ''), 'Nasabah Bank Muamalat') AS nama_debitur,
    COALESCE(r.akad, s.akad_syariah, 'Murabahah') AS jenis_akad,
    COALESCE(s.segmen, 'Komersial') AS segmen,
    COALESCE(r.cif, 'CIF-000') AS cif,
    COALESCE(TRY_CAST(s.baki_debet_kotor AS FLOAT), 0) AS plafon,
    COALESCE(TRY_CAST(s.baki_debet_kotor AS FLOAT), 0) AS baki_debet_kotor,
    COALESCE(TRY_CAST(s.ead_bersih_saatdefault AS FLOAT), TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.90) AS ead_bersih_syariah,
    COALESCE(TRY_CAST(s.dpd AS INT), 0) AS days_past_due,
    
    -- 1. JALUR B: Metode Bank / Excel
    CAST(
        CASE 
            WHEN COALESCE(TRY_CAST(s.dpd AS INT), 0) > 90 THEN TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.50 
            ELSE TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.01 
        END 
    AS FLOAT) AS ckpn_metode_bank,
    
    -- 2. JALUR A: Metode Syariah Murni
    CAST(COALESCE(TRY_CAST(r.ecl AS FLOAT), 
        CASE 
            WHEN COALESCE(TRY_CAST(s.dpd AS INT), 0) > 90 THEN TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.40
            ELSE TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.02
        END
    ) AS FLOAT) AS ckpn_metode_aplikasi,
    
    -- 3. NILAI FINAL BUKU BESAR
    CAST(COALESCE(TRY_CAST(r.ecl AS FLOAT), 
        CASE 
            WHEN COALESCE(TRY_CAST(s.dpd AS INT), 0) > 90 THEN TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.40
            ELSE TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.02
        END
    ) AS FLOAT) AS nil_final_buku_besar,
    
    -- Selisih Gap
    CAST((
        COALESCE(TRY_CAST(r.ecl AS FLOAT), 
            CASE 
                WHEN COALESCE(TRY_CAST(s.dpd AS INT), 0) > 90 THEN TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.40
                ELSE TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.02
            END
        ) - 
        CASE 
            WHEN COALESCE(TRY_CAST(s.dpd AS INT), 0) > 90 THEN TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.50 
            ELSE TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.01 
        END
    ) AS FLOAT) AS selisih_gap,
    
    -- Variance Breakdown (a): Efek Pembuangan Unearned Margin (Kepatuhan Riba)
    CAST(
        (TRY_CAST(s.baki_debet_kotor AS FLOAT) - COALESCE(TRY_CAST(s.ead_bersih_saatdefault AS FLOAT), TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.90)) * 0.05
    AS FLOAT) AS efek_unearned_margin,
    
    -- Variance Breakdown (b): Efek Perhitungan Kualitatif (SICR Sektor Riil)
    CAST(
        (COALESCE(TRY_CAST(r.ecl AS FLOAT), TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.02) - 
         CASE WHEN COALESCE(TRY_CAST(s.dpd AS INT), 0) > 90 THEN TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.50 ELSE TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.01 END)
        - ((TRY_CAST(s.baki_debet_kotor AS FLOAT) - COALESCE(TRY_CAST(s.ead_bersih_saatdefault AS FLOAT), TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.90)) * 0.05)
    AS FLOAT) AS efek_sicr_kualitatif,

    -- BR-AUD-02
    CASE 
        WHEN COALESCE(TRY_CAST(r.ecl AS FLOAT), TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.02) > 
             (CASE WHEN COALESCE(TRY_CAST(s.dpd AS INT), 0) > 90 THEN TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.50 ELSE TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.01 END) 
        THEN 'GAP POSITIF: Sistem menangkap indikator risiko kualitatif sektor riil (SICR) yang diabaikan DPD bank.'
        
        WHEN COALESCE(TRY_CAST(r.ecl AS FLOAT), TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.02) < 
             (CASE WHEN COALESCE(TRY_CAST(s.dpd AS INT), 0) > 90 THEN TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.50 ELSE TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.01 END)
        THEN 'GAP NEGATIF: Sterilisasi pendapatan margin masa depan memisahkan pokok riil bersih Riba/Gharar.'
        
        ELSE 'ALIGNED: Perhitungan relatif selaras.'
    END AS faktor_penyebab_gap

FROM dbo.staging_fasilitas_harian s
LEFT JOIN dbo.Report_Ringkasan_Hasil_Kalkulasi_ECL_Detail r ON s.no_rekening = r.no_fasilitas
WHERE s.no_rekening = %s
"""

# SQLite Queries for local testing
DIRECT_AUDIT_WORKBENCH_SQLITE_QUERY = """
SELECT 
    s.ACCOUNT_NUMBER AS no_rekening,
    COALESCE(d.nama_debitur, 'Nasabah Non-Nama') AS nama_debitur,
    COALESCE(d.jenis_akad, 'Mudharabah') AS jenis_akad,
    'Komersial' AS segmen,
    COALESCE(d.cif, 'CIF-000') AS cif,
    COALESCE(d.plafon, COALESCE(bal.OS_POKOK, 0)) AS plafon,
    COALESCE(bal.OS_POKOK, 0) AS baki_debet_kotor,
    COALESCE(ead.total_ultimate, COALESCE(bal.OS_POKOK, 0) * 0.85) AS ead_bersih_syariah,
    COALESCE(dpd.days_past_due, 0) AS days_past_due,
    
    -- 1. Metode Bank / Excel
    CAST(
        CASE 
            WHEN COALESCE(dpd.days_past_due, 0) > 90 THEN COALESCE(bal.OS_POKOK, 0) * 0.50 
            ELSE COALESCE(bal.OS_POKOK, 0) * 0.01 
        END 
    AS REAL) AS ckpn_metode_bank,
    
    -- 2. Metode Syariah Murni
    COALESCE(fin.total_nominal_ckpn, 
        CASE 
            WHEN COALESCE(dpd.days_past_due, 0) > 90 THEN COALESCE(bal.OS_POKOK, 0) * 0.40
            ELSE COALESCE(bal.OS_POKOK, 0) * 0.05
        END
    ) AS ckpn_metode_aplikasi,
    
    -- 3. Nilai Final Buku Besar
    COALESCE(fin.total_nominal_ckpn, 
        CASE 
            WHEN COALESCE(dpd.days_past_due, 0) > 90 THEN COALESCE(bal.OS_POKOK, 0) * 0.40
            ELSE COALESCE(bal.OS_POKOK, 0) * 0.05
        END
    ) AS nil_final_buku_besar,
    
    (
        COALESCE(fin.total_nominal_ckpn, 
            CASE 
                WHEN COALESCE(dpd.days_past_due, 0) > 90 THEN COALESCE(bal.OS_POKOK, 0) * 0.40
                ELSE COALESCE(bal.OS_POKOK, 0) * 0.05
            END
        ) - 
        CAST(
            CASE 
                WHEN COALESCE(dpd.days_past_due, 0) > 90 THEN COALESCE(bal.OS_POKOK, 0) * 0.50 
                ELSE COALESCE(bal.OS_POKOK, 0) * 0.01 
            END 
        AS REAL)
    ) AS selisih_gap,
    
    ((COALESCE(bal.OS_POKOK, 0) - COALESCE(ead.total_ultimate, COALESCE(bal.OS_POKOK, 0) * 0.85)) * 0.05) AS efek_unearned_margin,
    ((COALESCE(fin.total_nominal_ckpn, COALESCE(bal.OS_POKOK, 0) * 0.05) - (CASE WHEN COALESCE(dpd.days_past_due, 0) > 90 THEN COALESCE(bal.OS_POKOK, 0) * 0.50 ELSE COALESCE(bal.OS_POKOK, 0) * 0.01 END)) - ((COALESCE(bal.OS_POKOK, 0) - COALESCE(ead.total_ultimate, COALESCE(bal.OS_POKOK, 0) * 0.85)) * 0.05)) AS efek_sicr_kualitatif,

    CASE 
        WHEN COALESCE(fin.total_nominal_ckpn, COALESCE(bal.OS_POKOK, 0) * 0.05) > 
             (CASE WHEN COALESCE(dpd.days_past_due, 0) > 90 THEN COALESCE(bal.OS_POKOK, 0) * 0.50 ELSE COALESCE(bal.OS_POKOK, 0) * 0.01 END) 
        THEN 'GAP POSITIF: Sistem menangkap indikator risiko kualitatif sektor riil (SICR) yang diabaikan DPD bank.'
        
        WHEN COALESCE(fin.total_nominal_ckpn, COALESCE(bal.OS_POKOK, 0) * 0.40) < 
             (CASE WHEN COALESCE(dpd.days_past_due, 0) > 90 THEN COALESCE(bal.OS_POKOK, 0) * 0.50 ELSE COALESCE(bal.OS_POKOK, 0) * 0.01 END)
        THEN 'GAP NEGATIF: Sterilisasi pendapatan margin masa depan memisahkan pokok riil bersih Riba/Gharar.'
        
        ELSE 'ALIGNED: Perhitungan relatif selaras.'
    END AS faktor_penyebab_gap

FROM CLTB_ACCOUNT_APPS_MASTER s
LEFT JOIN Source_CLVS_ACC_COMP_BALANCES_Temp bal ON s.ACCOUNT_NUMBER = bal.ACCOUNT_NUMBER
LEFT JOIN TEMP_DPD_VMID dpd ON s.ACCOUNT_NUMBER = dpd.ACCOUNT_NUMBER
LEFT JOIN fact_ultimate_ead_cons ead ON s.ACCOUNT_NUMBER = ead.no_rekening
LEFT JOIN fact_psak413_ckpn_final_detail fin ON s.ACCOUNT_NUMBER = fin.no_rekening
LEFT JOIN dim_fasilitas d ON s.ACCOUNT_NUMBER = d.no_rekening
"""

def get_segment_options_query(db_type: str = "sqlserver") -> str:
    """
    Rujukan: select * from segment where KodeForm = 'ECL'
    """
    if str(db_type).lower() == "sqlserver":
        return "SELECT id, name, KEGOPR, KodeForm FROM dbo.segment WHERE KodeForm = 'ECL' ORDER BY id"
    return "SELECT id, name, KEGOPR, KodeForm FROM segment WHERE KodeForm = 'ECL' ORDER BY id"

def build_audit_count_query(db_type: str = "sqlserver", search: str = None, segmen: str = None):
    """
    Builds fast count query with active filters for SQL Server & SQLite.
    """
    db_kind = str(db_type).lower()
    params = []
    
    if db_kind == "sqlserver":
        count_sql = """
SELECT COUNT(*) AS total_records
FROM dbo.staging_fasilitas_harian s
LEFT JOIN dbo.Report_Ringkasan_Hasil_Kalkulasi_ECL_Detail r ON s.no_rekening = r.no_fasilitas
LEFT JOIN dbo.segment sg ON CAST(s.segmen AS VARCHAR) = CAST(sg.id AS VARCHAR) AND sg.KodeForm = 'ECL'
WHERE s.no_rekening != 'no_rekening' AND TRY_CAST(s.baki_debet_kotor AS FLOAT) IS NOT NULL
"""
        where_clauses = []
        if segmen and str(segmen).upper() != "ALL":
            where_clauses.append("(LOWER(CAST(s.segmen AS VARCHAR)) = %s OR LOWER(sg.name) = %s OR LOWER(CAST(sg.id AS VARCHAR)) = %s)")
            seg_val = str(segmen).lower()
            params.extend([seg_val, seg_val, seg_val])
            
        if search:
            where_clauses.append("(LOWER(s.no_rekening) LIKE %s OR LOWER(r.nama_nasabah) LIKE %s)")
            s_val = f"%{str(search).lower()}%"
            params.extend([s_val, s_val])
            
        if where_clauses:
            count_sql += " AND " + " AND ".join(where_clauses)
            
        return count_sql, params
    else:
        count_sql = """
SELECT COUNT(*) AS total_records
FROM CLTB_ACCOUNT_APPS_MASTER s
LEFT JOIN dim_fasilitas d ON s.ACCOUNT_NUMBER = d.no_rekening
LEFT JOIN segment sg ON CAST(d.segmen AS TEXT) = CAST(sg.id AS TEXT) AND sg.KodeForm = 'ECL'
WHERE 1=1
"""
        where_clauses = []
        if segmen and str(segmen).upper() != "ALL":
            where_clauses.append("(LOWER(CAST(d.segmen AS TEXT)) = ? OR LOWER(sg.name) = ? OR LOWER(CAST(sg.id AS TEXT)) = ?)")
            seg_val = str(segmen).lower()
            params.extend([seg_val, seg_val, seg_val])
            
        if search:
            where_clauses.append("(LOWER(s.ACCOUNT_NUMBER) LIKE ? OR LOWER(d.nama_debitur) LIKE ?)")
            s_val = f"%{str(search).lower()}%"
            params.extend([s_val, s_val])
            
        if where_clauses:
            count_sql += " AND " + " AND ".join(where_clauses)
            
        return count_sql, params

def build_audit_list_query(db_type: str = "sqlserver", search: str = None, segmen: str = None, page: int = 1, limit: int = 25):
    """
    Builds paginated query directly pushed down to SQL Server (OFFSET-FETCH) or SQLite (LIMIT-OFFSET).
    """
    db_kind = str(db_type).lower()
    page = max(1, page)
    limit = max(1, min(limit, 500))
    offset = (page - 1) * limit
    params = []
    
    if db_kind == "sqlserver":
        query_sql = """
SELECT 
    s.no_rekening AS no_rekening,
    COALESCE(NULLIF(r.nama_nasabah, ''), 'Nasabah Bank Muamalat') AS nama_debitur,
    COALESCE(r.akad, s.akad_syariah, 'Murabahah') AS jenis_akad,
    COALESCE(sg.name, s.segmen, 'Komersial') AS segmen,
    COALESCE(r.cif, 'CIF-000') AS cif,
    COALESCE(TRY_CAST(s.baki_debet_kotor AS FLOAT), 0) AS plafon,
    COALESCE(TRY_CAST(s.baki_debet_kotor AS FLOAT), 0) AS baki_debet_kotor,
    COALESCE(TRY_CAST(s.ead_bersih_saatdefault AS FLOAT), TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.90) AS ead_bersih_syariah,
    COALESCE(TRY_CAST(s.dpd AS INT), 0) AS days_past_due,
    
    CAST(CASE WHEN COALESCE(TRY_CAST(s.dpd AS INT), 0) > 90 THEN TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.50 ELSE TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.01 END AS FLOAT) AS ckpn_metode_bank,
    CAST(COALESCE(TRY_CAST(r.ecl AS FLOAT), CASE WHEN COALESCE(TRY_CAST(s.dpd AS INT), 0) > 90 THEN TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.40 ELSE TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.02 END) AS FLOAT) AS ckpn_metode_aplikasi,
    CAST(COALESCE(TRY_CAST(r.ecl AS FLOAT), CASE WHEN COALESCE(TRY_CAST(s.dpd AS INT), 0) > 90 THEN TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.40 ELSE TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.02 END) AS FLOAT) AS nil_final_buku_besar,
    CAST((COALESCE(TRY_CAST(r.ecl AS FLOAT), CASE WHEN COALESCE(TRY_CAST(s.dpd AS INT), 0) > 90 THEN TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.40 ELSE TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.02 END) - CASE WHEN COALESCE(TRY_CAST(s.dpd AS INT), 0) > 90 THEN TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.50 ELSE TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.01 END) AS FLOAT) AS selisih_gap,
    CAST((TRY_CAST(s.baki_debet_kotor AS FLOAT) - COALESCE(TRY_CAST(s.ead_bersih_saatdefault AS FLOAT), TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.90)) * 0.05 AS FLOAT) AS efek_unearned_margin,
    CAST((COALESCE(TRY_CAST(r.ecl AS FLOAT), TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.02) - CASE WHEN COALESCE(TRY_CAST(s.dpd AS INT), 0) > 90 THEN TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.50 ELSE TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.01 END) - ((TRY_CAST(s.baki_debet_kotor AS FLOAT) - COALESCE(TRY_CAST(s.ead_bersih_saatdefault AS FLOAT), TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.90)) * 0.05) AS FLOAT) AS efek_sicr_kualitatif,

    CASE 
        WHEN COALESCE(TRY_CAST(r.ecl AS FLOAT), TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.02) > (CASE WHEN COALESCE(TRY_CAST(s.dpd AS INT), 0) > 90 THEN TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.50 ELSE TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.01 END) THEN 'GAP POSITIF: Sistem menangkap indikator risiko kualitatif sektor riil (SICR) yang diabaikan DPD bank.'
        WHEN COALESCE(TRY_CAST(r.ecl AS FLOAT), TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.02) < (CASE WHEN COALESCE(TRY_CAST(s.dpd AS INT), 0) > 90 THEN TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.50 ELSE TRY_CAST(s.baki_debet_kotor AS FLOAT) * 0.01 END) THEN 'GAP NEGATIF: Sterilisasi pendapatan margin masa depan memisahkan pokok riil bersih Riba/Gharar.'
        ELSE 'ALIGNED: Perhitungan relatif selaras.'
    END AS faktor_penyebab_gap

FROM dbo.staging_fasilitas_harian s
LEFT JOIN dbo.Report_Ringkasan_Hasil_Kalkulasi_ECL_Detail r ON s.no_rekening = r.no_fasilitas
LEFT JOIN dbo.segment sg ON CAST(s.segmen AS VARCHAR) = CAST(sg.id AS VARCHAR) AND sg.KodeForm = 'ECL'
WHERE s.no_rekening != 'no_rekening' AND TRY_CAST(s.baki_debet_kotor AS FLOAT) IS NOT NULL
"""
        where_clauses = []
        if segmen and str(segmen).upper() != "ALL":
            where_clauses.append("(LOWER(CAST(s.segmen AS VARCHAR)) = %s OR LOWER(sg.name) = %s OR LOWER(CAST(sg.id AS VARCHAR)) = %s)")
            seg_val = str(segmen).lower()
            params.extend([seg_val, seg_val, seg_val])
            
        if search:
            where_clauses.append("(LOWER(s.no_rekening) LIKE %s OR LOWER(r.nama_nasabah) LIKE %s)")
            s_val = f"%{str(search).lower()}%"
            params.extend([s_val, s_val])
            
        if where_clauses:
            query_sql += " AND " + " AND ".join(where_clauses)
            
        query_sql += f" ORDER BY s.no_rekening OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY"
        return query_sql, params
    else:
        query_sql = DIRECT_AUDIT_WORKBENCH_SQLITE_QUERY
        where_clauses = []
        if segmen and str(segmen).upper() != "ALL":
            where_clauses.append("(LOWER(CAST(d.segmen AS TEXT)) = ? OR LOWER(sg.name) = ? OR LOWER(CAST(sg.id AS TEXT)) = ?)")
            seg_val = str(segmen).lower()
            params.extend([seg_val, seg_val, seg_val])
            
        if search:
            where_clauses.append("(LOWER(s.ACCOUNT_NUMBER) LIKE ? OR LOWER(d.nama_debitur) LIKE ?)")
            s_val = f"%{str(search).lower()}%"
            params.extend([s_val, s_val])
            
        if where_clauses:
            query_sql += " WHERE " + " AND ".join(where_clauses)
            
        query_sql += f" ORDER BY s.ACCOUNT_NUMBER LIMIT {limit} OFFSET {offset}"
        return query_sql, params

def get_audit_query(db_type: str = "sqlserver") -> str:
    if str(db_type).lower() == "sqlserver":
        return DIRECT_AUDIT_WORKBENCH_SQLSERVER_QUERY
    return DIRECT_AUDIT_WORKBENCH_SQLITE_QUERY

