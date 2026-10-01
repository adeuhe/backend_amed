from fastapi.testclient import TestClient
from main import app
from seed_data import seed_database
from app.config import settings

# Seed local database for fallback
settings.DB_TYPE = "sqlite"
seed_database()


client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "ECL Audit & Benchmarking Workbench" in data["app_name"]

def test_render_workbench_home_html():
    """Test Jinja2 HTML rendering for home page"""
    response = client.get("/ecl-audit-benchmarking-workbench")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "ECL Audit & Benchmarking Workbench" in response.text or "Matrix Uji Banding" in response.text

def test_root_redirect_to_workbench():
    """Test redirect from bare root / to /ecl-audit-benchmarking-workbench"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert "/ecl-audit-benchmarking-workbench" in response.headers["location"]

def test_offline_swagger_docs():
    """Test offline Swagger UI docs rendering with preset JS script"""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "swagger-ui-bundle.js" in response.text
    assert "swagger-ui-standalone-preset.js" in response.text


def test_get_audit_workbench_list_api():
    """Test JSON API for account list"""
    response = client.get("/api/audit/workbench")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["total_records"] > 0

def test_get_audit_workbench_detail_api_success():
    """Test JSON API for account detail dynamically from loaded list"""
    list_res = client.get("/api/audit/workbench")
    assert list_res.status_code == 200
    accounts = list_res.json()["data"]
    assert len(accounts) > 0
    
    account_no = accounts[0]["no_rekening"]
    response = client.get(f"/api/audit/workbench/{account_no}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "detail_perbandingan" in data

def test_render_audit_detail_html_success():
    """Test Jinja2 HTML rendering for detail page dynamically"""
    list_res = client.get("/api/audit/workbench")
    accounts = list_res.json()["data"]
    account_no = accounts[0]["no_rekening"]
    
    response = client.get(f"/audit/{account_no}")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_api_layar_workbench_prefixed_endpoints():
    """Test endpoints with /api-layar-workbench prefix"""
    res1 = client.get("/api-layar-workbench/health")
    assert res1.status_code == 200
    assert res1.json()["port"] == 5154

    res2 = client.get("/ecl-audit-benchmarking-workbench")
    assert res2.status_code == 200
    assert "text/html" in res2.headers["content-type"]

def test_export_excel_workbench():
    """Test exporting comparison data to Excel (.xlsx) file"""
    response = client.get("/ecl-audit-benchmarking-workbench/export-excel")
    assert response.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in response.headers["content-type"]
    assert "Content-Disposition" in response.headers
    assert "filename=" in response.headers["Content-Disposition"]
    assert len(response.content) > 0

def test_export_single_account_excel():
    """Test exporting single account working paper to Excel (.xlsx) file"""
    list_res = client.get("/api/audit/workbench")
    accounts = list_res.json()["data"]
    account_no = accounts[0]["no_rekening"]
    
    response = client.get(f"/ecl-audit-benchmarking-workbench/audit/{account_no}/export-excel")
    assert response.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in response.headers["content-type"]
    assert "Content-Disposition" in response.headers
    assert f"Kertas_Kerja_Audit_ECL_{account_no}" in response.headers["Content-Disposition"]
    assert len(response.content) > 0




