import io
import math
import sqlite3
from datetime import datetime
import pandas as pd
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from app.database import get_db_connection
from app.config import settings
from app.sql_queries import (
    get_audit_query, 
    DIRECT_AUDIT_WORKBENCH_SUMMARY_SQLSERVER_QUERY, 
    DIRECT_AUDIT_ACCOUNT_DETAIL_SQLSERVER_QUERY,
    get_segment_options_query,
    build_audit_count_query,
    build_audit_list_query
)

from app.path_utils import get_resource_path

router = APIRouter(tags=["Workbench HTML Views (Jinja2)"])
templates = Jinja2Templates(directory=get_resource_path("templates"))

@router.get("/", summary="Halaman Utama Workbench (Jinja2 Template)")
def render_workbench_home(
    request: Request, 
    q: str = Query(None, description="Pencarian Nomor Rekening / Nama Debitur"),
    segmen: str = Query(None, description="Filter Segmen Portofolio"),
    page: int = Query(1, ge=1, description="Nomor Halaman Halaman (Pagination)"),
    limit: int = Query(25, ge=5, le=500, description="Jumlah data per halaman")
):
    """
    Renders the main Workbench Dashboard UI using Jinja2 templates.
    Executes direct SQL calculation query from SQL Server (ipsak413 database - 10.81.21.144).
    Supports dynamic Segment options from `select * from segment where KodeForm = 'ECL'`,
    ultra-fast server-side pagination (OFFSET-FETCH) and filter optimization.
    BR-AUD-01: Read-Only analysis mode.
    """
    if request.url.path == "/":
        query_str = f"?{request.url.query}" if request.url.query else ""
        return RedirectResponse(url=f"/ecl-audit-benchmarking-workbench{query_str}", status_code=307)

    conn = None
    try:
        conn = get_db_connection()
        db_kind = "sqlite" if isinstance(conn, sqlite3.Connection) else "sqlserver"
        
        # 1. Fetch Dynamic Segment Options from Database: select * from segment where KodeForm = 'ECL'
        segment_list = []
        try:
            seg_query = get_segment_options_query(db_kind)
            df_segments = pd.read_sql(seg_query, conn)
            if not df_segments.empty:
                segment_list = df_segments.to_dict(orient="records")
        except Exception:
            # Graceful fallback segment list if table segment unavailable
            segment_list = [
                {"id": 1, "name": "SEG_01_CORPORATE"},
                {"id": 2, "name": "SEG_02-COMMERCIAL"},
                {"id": 3, "name": "SEG_03_SME_MICRO"},
                {"id": 4, "name": "SEG_04_CONSUMER"}
            ]

        # 2. Fetch Fast Aggregate Portfolio Macro Summary
        if db_kind == "sqlserver":
            df_sum = pd.read_sql(DIRECT_AUDIT_WORKBENCH_SUMMARY_SQLSERVER_QUERY, conn)
            sum_row = df_sum.iloc[0].to_dict() if not df_sum.empty else {}
            total_accounts = int(sum_row.get("total_accounts", 0))
            total_ckpn_bank = float(sum_row.get("total_ckpn_bank", 0.0))
            total_ckpn_syariah = float(sum_row.get("total_ckpn_syariah", 0.0))
            total_gap = float(sum_row.get("total_gap", 0.0))
        else:
            query_test = get_audit_query("sqlite")
            df_test = pd.read_sql(query_test, conn)
            total_accounts = len(df_test)
            total_ckpn_bank = float(df_test['ckpn_metode_bank'].sum()) if not df_test.empty else 0.0
            total_ckpn_syariah = float(df_test['ckpn_metode_aplikasi'].sum()) if not df_test.empty else 0.0
            total_gap = float(df_test['selisih_gap'].sum()) if not df_test.empty else 0.0

        # 3. Fetch Total Matching Filtered Records & Paginated Data
        try:
            count_sql, count_params = build_audit_count_query(db_kind, search=q, segmen=segmen)
            df_count = pd.read_sql(count_sql, conn, params=count_params if count_params else None)
            total_filtered = int(df_count.iloc[0]["total_records"]) if not df_count.empty else 0
        except Exception:
            # Fallback if sqlite tables for count query differ
            query_test = get_audit_query(db_kind)
            df_all = pd.read_sql(query_test, conn)
            if q:
                search_str = str(q).lower()
                df_all = df_all[
                    df_all['no_rekening'].astype(str).str.lower().str.contains(search_str) |
                    df_all['nama_debitur'].astype(str).str.lower().str.contains(search_str)
                ]
            total_filtered = len(df_all)

        # Calculate Pagination Math
        total_pages = max(1, math.ceil(total_filtered / limit)) if total_filtered > 0 else 1
        page = min(max(1, page), total_pages)
        
        start_index = (page - 1) * limit + 1 if total_filtered > 0 else 0
        end_index = min(page * limit, total_filtered)
        
        has_prev = page > 1
        has_next = page < total_pages
        prev_page = page - 1
        next_page = page + 1

        # Compute page navigation buttons (range of 5 surrounding current page)
        start_p = max(1, page - 2)
        end_p = min(total_pages, start_p + 4)
        if end_p - start_p < 4:
            start_p = max(1, end_p - 4)
        page_numbers = list(range(start_p, end_p + 1))

        # 4. Fetch Paginated Display Table Data
        try:
            list_sql, list_params = build_audit_list_query(db_kind, search=q, segmen=segmen, page=page, limit=limit)
            df = pd.read_sql(list_sql, conn, params=list_params if list_params else None)
        except Exception:
            query_test = get_audit_query(db_kind)
            df_all = pd.read_sql(query_test, conn)
            if q:
                search_str = str(q).lower()
                df_all = df_all[
                    df_all['no_rekening'].astype(str).str.lower().str.contains(search_str) |
                    df_all['nama_debitur'].astype(str).str.lower().str.contains(search_str)
                ]
            start_offset = (page - 1) * limit
            df = df_all.iloc[start_offset:start_offset + limit]

        # Ensure correct numeric types
        for col in ['plafon', 'baki_debet_kotor', 'ead_bersih_syariah', 'ckpn_metode_bank', 'ckpn_metode_aplikasi', 'nil_final_buku_besar', 'selisih_gap', 'efek_unearned_margin', 'efek_sicr_kualitatif']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

        # Filter out header string rows if any
        if 'no_rekening' in df.columns:
            df = df[df['no_rekening'].astype(str) != 'no_rekening']

        items = df.to_dict(orient="records")

        return templates.TemplateResponse(
            request=request,
            name="workbench.html",
            context={
                "active_page": "workbench",
                "items": items,
                "segment_list": segment_list,
                "total_accounts": total_accounts,
                "total_filtered": total_filtered,
                "displayed_accounts": len(items),
                "total_ckpn_bank": total_ckpn_bank,
                "total_ckpn_syariah": total_ckpn_syariah,
                "total_gap": total_gap,
                "search_query": q,
                "selected_segmen": str(segmen) if segmen else "ALL",
                "page": page,
                "limit": limit,
                "total_pages": total_pages,
                "start_index": start_index,
                "end_index": end_index,
                "has_prev": has_prev,
                "has_next": has_next,
                "prev_page": prev_page,
                "next_page": next_page,
                "page_numbers": page_numbers
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database SQL Server Error: {str(e)}")
    finally:
        if conn is not None:
            conn.close()

@router.get("/export-excel", summary="Export Data Audit Workbench ke Format Excel (.xlsx)")
def export_excel_workbench(
    q: str = Query(None, description="Pencarian Nomor Rekening / Nama Debitur"),
    segmen: str = Query(None, description="Filter Segmen Portofolio"),
    limit: int = Query(5000, ge=1, le=50000, description="Maksimal data yang di-export")
):
    """
    Export paginated or filtered Workbench comparison data to formatted Excel (.xlsx) file.
    Supports active filters (search query & segment).
    """
    conn = None
    try:
        conn = get_db_connection()
        db_kind = "sqlite" if isinstance(conn, sqlite3.Connection) else "sqlserver"
        
        try:
            list_sql, list_params = build_audit_list_query(db_kind, search=q, segmen=segmen, page=1, limit=limit)
            df = pd.read_sql(list_sql, conn, params=list_params if list_params else None)
        except Exception:
            query_test = get_audit_query(db_kind)
            df = pd.read_sql(query_test, conn)
            if q:
                search_str = str(q).lower()
                df = df[
                    df['no_rekening'].astype(str).str.lower().str.contains(search_str) |
                    df['nama_debitur'].astype(str).str.lower().str.contains(search_str)
                ]
            df = df.head(limit)
            
        if 'no_rekening' in df.columns:
            df = df[df['no_rekening'].astype(str) != 'no_rekening']
            
        # Clean columns and rename for professional Excel output
        excel_df = pd.DataFrame()
        excel_df['No Rekening'] = df['no_rekening'].astype(str)
        excel_df['Nama Debitur'] = df['nama_debitur'].astype(str)
        excel_df['Jenis Akad'] = df['jenis_akad'].astype(str)
        excel_df['Segmen'] = df['segmen'].astype(str)
        excel_df['CIF'] = df['cif'].astype(str)
        excel_df['Plafon (Rp)'] = pd.to_numeric(df['plafon'], errors='coerce').fillna(0.0)
        excel_df['Baki Debet Kotor (Rp)'] = pd.to_numeric(df['baki_debet_kotor'], errors='coerce').fillna(0.0)
        excel_df['EAD Bersih Syariah (Rp)'] = pd.to_numeric(df['ead_bersih_syariah'], errors='coerce').fillna(0.0)
        excel_df['Hari Tunggakan (DPD)'] = pd.to_numeric(df['days_past_due'], errors='coerce').fillna(0)
        excel_df['1. CKPN Metode Bank (Rp)'] = pd.to_numeric(df['ckpn_metode_bank'], errors='coerce').fillna(0.0)
        excel_df['2. CKPN Metode Syariah (Rp)'] = pd.to_numeric(df['ckpn_metode_aplikasi'], errors='coerce').fillna(0.0)
        excel_df['3. Final Buku Besar (Rp)'] = pd.to_numeric(df['nil_final_buku_besar'], errors='coerce').fillna(0.0)
        excel_df['Selisih Gap Total (Rp)'] = pd.to_numeric(df['selisih_gap'], errors='coerce').fillna(0.0)
        excel_df['(a) Efek Unearned Margin (Rp)'] = pd.to_numeric(df['efek_unearned_margin'], errors='coerce').fillna(0.0)
        excel_df['(b) Efek SICR Kualitatif (Rp)'] = pd.to_numeric(df['efek_sicr_kualitatif'], errors='coerce').fillna(0.0)
        excel_df['Analisis Kepatuhan & Risiko'] = df['faktor_penyebab_gap'].astype(str)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            excel_df.to_excel(writer, sheet_name='Audit Workbench', index=False)
            workbook = writer.book
            worksheet = writer.sheets['Audit Workbench']
            
            # Auto-fit column widths
            for col in worksheet.columns:
                max_len = max(len(str(cell.value or '')) for cell in col)
                col_letter = col[0].column_letter
                worksheet.column_dimensions[col_letter].width = max(max_len + 3, 12)
                
        output.seek(0)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ECL_Audit_Workbench_Export_{timestamp}.xlsx"
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal mengeksport data Excel: {str(e)}")
    finally:
        if conn is not None:
            conn.close()

@router.get("/audit/{no_rekening}", summary="Halaman Detail Audit Transparansi Rekening")
def render_audit_detail(request: Request, no_rekening: str):
    """
    Renders the Detail Audit Transparency view for a specific account using Jinja2 templates.
    Displays 3 side-by-side components & Variance Breakdown (a: Unearned Margin, b: SICR).
    """
    conn = None
    try:
        conn = get_db_connection()
        db_kind = "sqlite" if isinstance(conn, sqlite3.Connection) else "sqlserver"
        
        if db_kind == "sqlserver":
            query = DIRECT_AUDIT_ACCOUNT_DETAIL_SQLSERVER_QUERY
            df = pd.read_sql(query, conn, params=(no_rekening,))
        else:
            query = get_audit_query("sqlite")
            df = pd.read_sql(query, conn)
            df = df[df['no_rekening'].astype(str).str.strip() == str(no_rekening).strip()]
        
        if df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Data audit untuk nomor rekening '{no_rekening}' tidak ditemukan di database."
            )
            
        record = df.iloc[0].to_dict()
        
        # Format numeric fields
        for col in ['plafon', 'baki_debet_kotor', 'ead_bersih_syariah', 'ckpn_metode_bank', 'ckpn_metode_aplikasi', 'nil_final_buku_besar', 'selisih_gap', 'efek_unearned_margin', 'efek_sicr_kualitatif']:
            if col in record:
                try:
                    record[col] = float(record[col])
                except (ValueError, TypeError):
                    record[col] = 0.0
        
        return templates.TemplateResponse(
            request=request,
            name="detail.html",
            context={
                "active_page": "detail",
                "record": record
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database SQL Server Error: {str(e)}")
    finally:
        if conn is not None:
            conn.close()

@router.get("/audit/{no_rekening}/export-excel", summary="Export Kertas Kerja Audit Rekening Individual (.xlsx)")
def export_single_account_excel(no_rekening: str):
    """
    Exports a detailed Working Paper Audit Transparansi (.xlsx) for a single account.
    Contains header metadata, 3-component comparison table, variance breakdown, and compliance notes.
    """
    conn = None
    try:
        conn = get_db_connection()
        db_kind = "sqlite" if isinstance(conn, sqlite3.Connection) else "sqlserver"
        
        if db_kind == "sqlserver":
            query = DIRECT_AUDIT_ACCOUNT_DETAIL_SQLSERVER_QUERY
            df = pd.read_sql(query, conn, params=(no_rekening,))
        else:
            query = get_audit_query("sqlite")
            df = pd.read_sql(query, conn)
            df = df[df['no_rekening'].astype(str).str.strip() == str(no_rekening).strip()]
            
        if df.empty:
            raise HTTPException(status_code=404, detail=f"Rekening '{no_rekening}' tidak ditemukan.")
            
        rec = df.iloc[0].to_dict()
        
        # Build structured Working Paper dataframe
        data_rows = [
            {"Kategori": "IDENTITAS REKENING", "Parameter Audit": "Nomor Rekening", "Nilai / Details": str(rec.get("no_rekening", ""))},
            {"Kategori": "IDENTITAS REKENING", "Parameter Audit": "Nama Debitur", "Nilai / Details": str(rec.get("nama_debitur", ""))},
            {"Kategori": "IDENTITAS REKENING", "Parameter Audit": "Jenis Akad Syariah", "Nilai / Details": str(rec.get("jenis_akad", ""))},
            {"Kategori": "IDENTITAS REKENING", "Parameter Audit": "Segmen Portofolio", "Nilai / Details": str(rec.get("segmen", ""))},
            {"Kategori": "IDENTITAS REKENING", "Parameter Audit": "Nomor CIF", "Nilai / Details": str(rec.get("cif", ""))},
            {"Kategori": "IDENTITAS REKENING", "Parameter Audit": "Plafon Pembiayaan", "Nilai / Details": float(rec.get("plafon", 0.0))},
            {"Kategori": "IDENTITAS REKENING", "Parameter Audit": "Hari Tunggakan (DPD)", "Nilai / Details": int(rec.get("days_past_due", 0))},
            
            {"Kategori": "1. METODE BANK / EXCEL", "Parameter Audit": "Baki Debet Kotor (Raw Exposure)", "Nilai / Details": float(rec.get("baki_debet_kotor", 0.0))},
            {"Kategori": "1. METODE BANK / EXCEL", "Parameter Audit": "CKPN Metode Sederhana Bank (DPD)", "Nilai / Details": float(rec.get("ckpn_metode_bank", 0.0))},
            
            {"Kategori": "2. METODE SYARIAH MURNI", "Parameter Audit": "EAD Bersih Margin (Tanpa Riba/Gharar)", "Nilai / Details": float(rec.get("ead_bersih_syariah", 0.0))},
            {"Kategori": "2. METODE SYARIAH MURNI", "Parameter Audit": "CKPN Grand Master Engine Syariah", "Nilai / Details": float(rec.get("ckpn_metode_aplikasi", 0.0))},
            
            {"Kategori": "3. FINAL BUKU BESAR", "Parameter Audit": "Nilai CKPN Buku Besar (General Ledger)", "Nilai / Details": float(rec.get("nil_final_buku_besar", 0.0))},
            
            {"Kategori": "RINGKASAN SELISIH GAP", "Parameter Audit": "Total Selisih (Syariah Engine - Bank Excel)", "Nilai / Details": float(rec.get("selisih_gap", 0.0))},
            
            {"Kategori": "VARIANCE BREAKDOWN", "Parameter Audit": "(a) Efek Pembuangan Unearned Margin (Kepatuhan Riba)", "Nilai / Details": float(rec.get("efek_unearned_margin", 0.0))},
            {"Kategori": "VARIANCE BREAKDOWN", "Parameter Audit": "(b) Efek Perhitungan Kualitatif (SICR Sektor Riil)", "Nilai / Details": float(rec.get("efek_sicr_kualitatif", 0.0))},
            
            {"Kategori": "ANALISIS KEPATUHAN & RISIKO", "Parameter Audit": "Keterangan Audit & Teologis (BR-AUD-02)", "Nilai / Details": str(rec.get("faktor_penyebab_gap", ""))}
        ]
        
        excel_df = pd.DataFrame(data_rows)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            excel_df.to_excel(writer, sheet_name='Kertas Kerja Audit', index=False)
            worksheet = writer.sheets['Kertas Kerja Audit']
            
            # Auto-fit columns
            for col in worksheet.columns:
                max_len = max(len(str(cell.value or '')) for cell in col)
                col_letter = col[0].column_letter
                worksheet.column_dimensions[col_letter].width = max(max_len + 3, 15)
                
        output.seek(0)
        clean_norek = str(rec.get("no_rekening", "account")).replace("/", "_")
        filename = f"Kertas_Kerja_Audit_ECL_{clean_norek}.xlsx"
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal mengeksport Kertas Kerja Audit Excel: {str(e)}")
    finally:
        if conn is not None:
            conn.close()


