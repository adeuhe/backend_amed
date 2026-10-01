import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from app.database import get_db_connection
from app.config import settings
from app.schemas import AuditWorkbenchResponse, AuditWorkbenchListResponse

router = APIRouter(
    prefix="/api/audit/workbench",
    tags=["ECL Audit & Benchmarking Workbench"]
)

@router.get(
    "/{no_rekening}",
    response_model=AuditWorkbenchResponse,
    summary="Detail Audit Transparansi per Rekening",
    description="Menampilkan perbandingan transparan per rekening antara metode bank (Excel) dengan metode aplikasi syariah (The Grand Master Engine)."
)
def get_audit_workbench_detail(no_rekening: str):
    """
    Menampilkan perbandingan transparan per rekening antara metode bank (Excel) 
    dengan metode aplikasi syariah (The Grand Master Engine).
    Rujukan: Dokumen Pertanyaan 4 - IV. Skrip Python (Backend API untuk Layar Workbench)
    """
    conn = None
    try:
        conn = get_db_connection()
        
        # Penanganan parameter query adaptif (PostgreSQL %s vs SQLite ?)
        param_placeholder = "?" if settings.DB_TYPE.lower() == "sqlite" else "%s"
        
        query = f"""
            SELECT 
                w.no_rekening AS "No Rekening",
                COALESCE(d.nama_debitur, 'Nasabah Non-Nama') AS "Nama Nasabah",
                w.baki_debet_kotor AS "Baki Debet Kotor (Excel Bank)",
                w.ead_bersih_syariah AS "EAD Bersih (Tanpa Margin Riba)",
                w.ckpn_metode_bank AS "CKPN Metode Sederhana (Rp)",
                w.ckpn_metode_aplikasi AS "CKPN Grand Master Syariah (Rp)",
                (w.ckpn_metode_aplikasi - w.ckpn_metode_bank) AS "Selisih Gap (Rp)",
                w.faktor_penyebab_gap AS "Analisis Kepatuhan & Risiko"
            FROM dm_ecl_audit_workbench w
            LEFT JOIN dim_fasilitas d ON w.no_rekening = d.no_rekening
            WHERE w.no_rekening = {param_placeholder}
              AND w.tgl_proses = (SELECT MAX(tgl_proses) FROM dm_ecl_audit_workbench);
        """
        
        df = pd.read_sql(query, conn, params=(no_rekening,))
        
        if df.empty:
            raise HTTPException(
                status_code=404, 
                detail=f"Data audit rekening '{no_rekening}' tidak ditemukan."
            )
            
        record = df.iloc[0].to_dict()
        
        return {
            "status": "success",
            "keterangan_audit": "Fitur ini membuktikan transparansi mutlak perhitungan sistem terhadap metode konvensional bank.",
            "detail_perbandingan": record
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn is not None:
            conn.close()

@router.get(
    "",
    response_model=AuditWorkbenchListResponse,
    summary="Daftar Audit Transparansi Portofolio",
    description="Menampilkan seluruh daftar audit perbandingan portofolio rekening untuk tampilan workbench frontend."
)
def get_audit_workbench_list(
    limit: int = Query(50, ge=1, le=1000, description="Jumlah baris data maksimal yang ditampilkan"),
    search: str = Query(None, description="Pencarian berdasarkan Nomor Rekening atau Nama Debitur")
):
    """
    Endpoint pendukung frontend untuk menampilkan tabel daftar perbandingan seluruh rekening.
    """
    conn = None
    try:
        conn = get_db_connection()
        param_placeholder = "?" if settings.DB_TYPE.lower() == "sqlite" else "%s"
        
        base_query = """
            SELECT 
                w.tgl_proses AS "Tanggal Proses",
                w.no_rekening AS "No Rekening",
                COALESCE(d.nama_debitur, 'Nasabah Non-Nama') AS "Nama Nasabah",
                w.baki_debet_kotor AS "Baki Debet Kotor (Excel Bank)",
                w.ead_bersih_syariah AS "EAD Bersih (Tanpa Margin Riba)",
                w.ckpn_metode_bank AS "CKPN Metode Sederhana (Rp)",
                w.ckpn_metode_aplikasi AS "CKPN Grand Master Syariah (Rp)",
                (w.ckpn_metode_aplikasi - w.ckpn_metode_bank) AS "Selisih Gap (Rp)",
                w.faktor_penyebab_gap AS "Analisis Kepatuhan & Risiko"
            FROM dm_ecl_audit_workbench w
            LEFT JOIN dim_fasilitas d ON w.no_rekening = d.no_rekening
            WHERE w.tgl_proses = (SELECT MAX(tgl_proses) FROM dm_ecl_audit_workbench)
        """
        
        params = []
        if search:
            base_query += f" AND (w.no_rekening LIKE {param_placeholder} OR d.nama_debitur LIKE {param_placeholder})"
            search_param = f"%{search}%"
            params.extend([search_param, search_param])
            
        base_query += f" ORDER BY ABS(w.ckpn_metode_aplikasi - w.ckpn_metode_bank) DESC LIMIT {limit}"
        
        df = pd.read_sql(base_query, conn, params=params if params else None)
        
        records = df.to_dict(orient="records")
        return {
            "status": "success",
            "total_records": len(records),
            "data": records
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn is not None:
            conn.close()
