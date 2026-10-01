import sqlite3
import os
import datetime
from app.config import settings

def seed_database():
    """
    Menyuntikkan tabel-tabel sumber (Source Tables) langsung tanpa tabel ETL:
    1. CLTB_ACCOUNT_APPS_MASTER (Master Rekening)
    2. Source_CLVS_ACC_COMP_BALANCES_Temp (Baki Debet / Saldo Kotor)
    3. TEMP_DPD_VMID (Data DPD Hari Tunggakan)
    4. fact_ultimate_ead_cons (Ultimate EAD Bersih Syariah)
    5. fact_psak413_ckpn_final_detail (Hasil CKPN Grand Master Syariah Engine)
    6. dim_fasilitas (Dimensi Nasabah)
    """
    db_path = os.path.abspath(settings.DB_FILE)
    print(f"Menyuntikkan tabel-tabel sumber ke database SQLite local: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Master Account Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS CLTB_ACCOUNT_APPS_MASTER (
        ACCOUNT_NUMBER TEXT PRIMARY KEY
    );
    """)
    
    # 2. Balances Table (Baki Debet Kotor)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Source_CLVS_ACC_COMP_BALANCES_Temp (
        ACCOUNT_NUMBER TEXT PRIMARY KEY,
        OS_POKOK REAL NOT NULL
    );
    """)
    
    # 3. DPD Table (Days Past Due)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS TEMP_DPD_VMID (
        ACCOUNT_NUMBER TEXT PRIMARY KEY,
        days_past_due INTEGER NOT NULL
    );
    """)
    
    # 4. Ultimate EAD Table (EAD Bersih Syariah)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fact_ultimate_ead_cons (
        no_rekening TEXT PRIMARY KEY,
        total_ultimate REAL NOT NULL
    );
    """)
    
    # 5. Final CKPN Syariah Detail Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fact_psak413_ckpn_final_detail (
        no_rekening TEXT PRIMARY KEY,
        total_nominal_ckpn REAL NOT NULL
    );
    """)
    
    # 6. Dimensi Fasilitas Nasabah
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dim_fasilitas (
        no_rekening TEXT PRIMARY KEY,
        nama_debitur TEXT NOT NULL,
        cif TEXT NULL,
        jenis_akad TEXT NULL,
        plafon REAL NULL
    );
    """)
    
    # Clear existing source tables
    cursor.execute("DELETE FROM CLTB_ACCOUNT_APPS_MASTER;")
    cursor.execute("DELETE FROM Source_CLVS_ACC_COMP_BALANCES_Temp;")
    cursor.execute("DELETE FROM TEMP_DPD_VMID;")
    cursor.execute("DELETE FROM fact_ultimate_ead_cons;")
    cursor.execute("DELETE FROM fact_psak413_ckpn_final_detail;")
    cursor.execute("DELETE FROM dim_fasilitas;")
    
    # Sample Accounts
    accounts = [
        '10000000012',
        '10000000015',
        '10000000088',
        '10000000099',
        '10000000105',
        '10000000210'
    ]
    cursor.executemany("INSERT INTO CLTB_ACCOUNT_APPS_MASTER VALUES (?);", [(a,) for a in accounts])
    
    # Sample Balances (Baki Debet Kotor)
    balances = [
        ('10000000012', 1500000000.00),
        ('10000000015', 3000000000.00),
        ('10000000088', 500000000.00),
        ('10000000099', 4500000000.00),
        ('10000000105', 2200000000.00),
        ('10000000210', 8000000000.00)
    ]
    cursor.executemany("INSERT INTO Source_CLVS_ACC_COMP_BALANCES_Temp VALUES (?,?);", balances)
    
    # Sample DPD (Days Past Due)
    dpd_data = [
        ('10000000012', 0),   # DPD 0 tapi proyek mangkrak (GAP POSITIF)
        ('10000000015', 95),  # DPD 95 (>90 -> Bank 50% = 1.5M, Syariah 1.25M steril margin)
        ('10000000088', 15),  # DPD 15
        ('10000000099', 45),  # DPD 45
        ('10000000105', 120), # DPD 120
        ('10000000210', 0)    # DPD 0
    ]
    cursor.executemany("INSERT INTO TEMP_DPD_VMID VALUES (?,?);", dpd_data)
    
    # Sample Ultimate EAD (EAD Bersih Syariah)
    ead_data = [
        ('10000000012', 1200000000.00),
        ('10000000015', 2500000000.00),
        ('10000000088', 450000000.00),
        ('10000000099', 4000000000.00),
        ('10000000105', 1800000000.00),
        ('10000000210', 7000000000.00)
    ]
    cursor.executemany("INSERT INTO fact_ultimate_ead_cons VALUES (?,?);", ead_data)
    
    # Sample Final CKPN Syariah Results
    ckpn_syariah = [
        ('10000000012', 75000000.00),  # Bank: 15M (1%), Syariah: 75M (Safety Margin SICR)
        ('10000000015', 1250000000.00),# Bank: 1.5B (50%), Syariah: 1.25B (Sterilisasi Margin)
        ('10000000088', 5000000.00),   # Selaras 5M
        ('10000000099', 200000000.00), # Bank: 45M, Syariah: 200M (Penurunan yield)
        ('10000000105', 900000000.00), # Bank: 1.1B, Syariah: 900M
        ('10000000210', 80000000.00)   # Bank: 80M, Syariah: 80M
    ]
    cursor.executemany("INSERT INTO fact_psak413_ckpn_final_detail VALUES (?,?);", ckpn_syariah)
    
    # Sample Dimensi Fasilitas Nasabah
    dim_data = [
        ('10000000012', 'PT Barakah Nusantara Sektor Riil', 'CIF-0012', 'Mudharabah', 2000000000.0),
        ('10000000015', 'PT Mudharabah Sejahtera Properti', 'CIF-0015', 'Musyarakah', 3500000000.0),
        ('10000000088', 'CV Syariah Karya Mandiri', 'CIF-0088', 'Murabahah', 600000000.0),
        ('10000000099', 'PT Industri Syariah Indonesia', 'CIF-0099', 'Istishna', 5000000000.0),
        ('10000000105', 'PT Transaksi Utama Syariah', 'CIF-0105', 'Mudharabah', 2500000000.0),
        ('10000000210', 'PT Mega Konstruksi Syariah', 'CIF-0210', 'Musyarakah', 10000000000.0)
    ]
    cursor.executemany("INSERT INTO dim_fasilitas VALUES (?,?,?,?,?);", dim_data)
    
    conn.commit()
    conn.close()
    print("Seed database tabel-tabel sumber (Source Tables) berhasil disuntikkan!")

if __name__ == "__main__":
    seed_database()
