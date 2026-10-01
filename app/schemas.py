from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class AuditDetailRecord(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    no_rekening: str = Field(..., alias="No Rekening")
    nama_nasabah: str = Field(..., alias="Nama Nasabah")
    baki_debet_kotor: float = Field(..., alias="Baki Debet Kotor (Excel Bank)")
    ead_bersih_syariah: float = Field(..., alias="EAD Bersih (Tanpa Margin Riba)")
    ckpn_metode_bank: float = Field(..., alias="CKPN Metode Sederhana (Rp)")
    ckpn_metode_aplikasi: float = Field(..., alias="CKPN Grand Master Syariah (Rp)")
    selisih_gap: float = Field(..., alias="Selisih Gap (Rp)")
    faktor_penyebab_gap: str = Field(..., alias="Analisis Kepatuhan & Risiko")


class AuditWorkbenchResponse(BaseModel):
    status: str = "success"
    keterangan_audit: str = "Fitur ini membuktikan transparansi mutlak perhitungan sistem terhadap metode konvensional bank."
    detail_perbandingan: Dict[str, Any]

class AuditWorkbenchListResponse(BaseModel):
    status: str = "success"
    total_records: int
    data: List[Dict[str, Any]]
