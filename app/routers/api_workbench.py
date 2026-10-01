import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from app.database import get_db_connection
from app.config import settings
from app.sql_queries import get_audit_query, DIRECT_AUDIT_ACCOUNT_DETAIL_SQLSERVER_QUERY
from app.schemas import AuditWorkbenchResponse, AuditWorkbenchListResponse

router = APIRouter(
    prefix="/api/audit/workbench",
    tags=["ECL Audit & Benchmarking Workbench API"]
)

@router.get(
    "/{no_rekening}",
    response_model=AuditWorkbenchResponse,
    summary="Detail Audit Transparansi per Rekening (JSON API)",
    description="Menampilkan perbandingan transparan per rekening antara metode bank (Excel) dengan metode aplikasi syariah (The Grand Master Engine)."
)
def get_audit_workbench_detail_api(no_rekening: str):
    """
    JSON API Endpoint: Menampilkan perbandingan transparan per rekening dari SQL Server.
    """
    conn = None
    try:
        conn = get_db_connection()
        db_kind = settings.DB_TYPE.lower()
        
        if db_kind == "sqlserver":
            query = DIRECT_AUDIT_ACCOUNT_DETAIL_SQLSERVER_QUERY
            df = pd.read_sql(query, conn, params=(no_rekening,))
        else:
            query = get_audit_query(db_kind)
            df = pd.read_sql(query, conn)
            df = df[df['no_rekening'].astype(str).str.strip() == str(no_rekening).strip()]
        
        if df.empty:
            raise HTTPException(
                status_code=404, 
                detail=f"Data audit rekening '{no_rekening}' tidak ditemukan di SQL Server."
            )
            
        row = df.iloc[0].to_dict()
        
        record = {
            "No Rekening": str(row["no_rekening"]),
            "Nama Nasabah": str(row["nama_debitur"]),
            "Baki Debet Kotor (Excel Bank)": float(row["baki_debet_kotor"] or 0),
            "EAD Bersih (Tanpa Margin Riba)": float(row["ead_bersih_syariah"] or 0),
            "CKPN Metode Sederhana (Rp)": float(row["ckpn_metode_bank"] or 0),
            "CKPN Grand Master Syariah (Rp)": float(row["ckpn_metode_aplikasi"] or 0),
            "Selisih Gap (Rp)": float(row["selisih_gap"] or 0),
            "Analisis Kepatuhan & Risiko": str(row["faktor_penyebab_gap"])
        }
        
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
    summary="Daftar Audit Transparansi Portofolio (JSON API)",
    description="Menampilkan seluruh daftar audit perbandingan portofolio rekening dalam format JSON dari SQL Server."
)
def get_audit_workbench_list_api(
    limit: int = Query(100, ge=1, le=5000, description="Jumlah baris data maksimal"),
    search: str = Query(None, description="Pencarian berdasarkan Nomor Rekening atau Nama Debitur")
):
    """
    JSON API Endpoint: Menampilkan tabel daftar perbandingan seluruh rekening dari SQL Server.
    """
    conn = None
    try:
        conn = get_db_connection()
        db_kind = settings.DB_TYPE.lower()
        query = get_audit_query(db_kind)
        
        df = pd.read_sql(query, conn)
        
        # Filter out invalid string header rows if any
        if 'no_rekening' in df.columns:
            df = df[df['no_rekening'].astype(str) != 'no_rekening']
        
        if search:
            search_str = str(search).lower()
            df = df[
                df['no_rekening'].astype(str).str.lower().str.contains(search_str) |
                df['nama_debitur'].astype(str).str.lower().str.contains(search_str)
            ]
            
        df = df.head(limit)
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
