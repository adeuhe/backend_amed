import sys
import uvicorn
import webbrowser
import threading
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from app.config import settings
from app.path_utils import get_resource_path
from app.routers import web_views, api_workbench

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "ECL Transparency & Audit Workbench — Program FastAPI + Jinja2 UI.\n"
        "Menyajikan rincian audit perbandingan transparan per rekening antara metode bank (Excel/DPD) "
        "dan Grand Master Engine (PSAK 413 Syariah) langsung dari query kalkulasi SQL Server (pymssql)."
    ),
    version="1.0.0",
    docs_url=None,   # Disable default online docs to serve 100% offline local docs
    redoc_url=None
)

# Mount Static Files (CSS / JS / Assets / Offline Swagger UI) via get_resource_path
app.mount("/static-audit-benchmarking-workbench", StaticFiles(directory=get_resource_path("static-audit-benchmarking-workbench")), name="static-audit-benchmarking-workbench")
app.mount("/static", StaticFiles(directory=get_resource_path("static-audit-benchmarking-workbench")), name="static")

# Configuration CORS untuk integrasi frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root Routers
app.include_router(web_views.router)       # Direct HTML UI: / and /audit/{no_rekening}
app.include_router(api_workbench.router)   # JSON API: /api/audit/workbench

# Prefixes requested by user
PREFIXES = [
    "/ecl-audit-benchmarking-workbench",
    "/ecl-audit-and-benchmarking-workbench",
    "/ecl-audit-workbench",
    "/api-layar-workbench",
    "/api/layar-workbench"
]

for prefix in PREFIXES:
    app.include_router(web_views.router, prefix=prefix)
    app.include_router(api_workbench.router, prefix=prefix)

# Custom 100% Offline Swagger UI Docs Route
@app.get("/docs", include_in_schema=False)
@app.get("/ecl-audit-benchmarking-workbench/docs", include_in_schema=False)
@app.get("/ecl-audit-and-benchmarking-workbench/docs", include_in_schema=False)
@app.get("/ecl-audit-workbench/docs", include_in_schema=False)
@app.get("/api-layar-workbench/docs", include_in_schema=False)
@app.get("/api/layar-workbench/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """
    100% Offline Air-Gapped Swagger UI Docs Endpoint.
    Loads BOTH swagger-ui-bundle.js AND swagger-ui-standalone-preset.js from local /static-audit-benchmarking-workbench/swagger/
    to prevent JavaScript ReferenceErrors when SwaggerUIStandalonePreset is initialized.
    """
    html_content = f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{settings.APP_NAME} — Offline Swagger API Docs</title>
    <link rel="stylesheet" type="text/css" href="/static-audit-benchmarking-workbench/swagger/swagger-ui.css" />
    <link rel="icon" type="image/png" href="/static-audit-benchmarking-workbench/swagger/favicon.png" />
    <style>
        html {{ box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }}
        *, *:before, *:after {{ box-sizing: inherit; }}
        body {{ margin: 0; background: #fafafa; }}
        .swagger-ui .topbar {{ display: none; }}
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="/static-audit-benchmarking-workbench/swagger/swagger-ui-bundle.js"></script>
    <script src="/static-audit-benchmarking-workbench/swagger/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {{
            window.ui = SwaggerUIBundle({{
                url: "/openapi.json",
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout"
            }});
        }};
    </script>
</body>
</html>"""
    return HTMLResponse(content=html_content)

@app.get("/health", tags=["Health Check"])
@app.get("/ecl-audit-benchmarking-workbench/health", tags=["Health Check"])
@app.get("/ecl-audit-and-benchmarking-workbench/health", tags=["Health Check"])
@app.get("/ecl-audit-workbench/health", tags=["Health Check"])
@app.get("/api-layar-workbench/health", tags=["Health Check"])
@app.get("/api/layar-workbench/health", tags=["Health Check"])
def health_check():
    return {
        "status": "online",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "database_type": settings.DB_TYPE,
        "database_driver": settings.DB_DRIVER,
        "port": settings.APP_PORT,
        "swagger_docs": "/docs",
        "primary_workbench_endpoint": "/ecl-audit-benchmarking-workbench",
        "available_endpoint_prefixes": PREFIXES
    }

if __name__ == "__main__":
    try:
        is_frozen = getattr(sys, 'frozen', False)
        
        # Auto open default browser after server starts
        def open_browser():
            import time
            time.sleep(1.5)
            try:
                webbrowser.open(f"http://localhost:{settings.APP_PORT}/ecl-audit-benchmarking-workbench")
            except Exception:
                pass
            
        threading.Thread(target=open_browser, daemon=True).start()

        # Pass 'app' object directly for PyInstaller compatibility
        uvicorn.run(app, host="0.0.0.0", port=settings.APP_PORT, reload=False if is_frozen else False)
    except Exception as e:
        print(f"\n[ERROR CRITICAL] Server gagal dimulai: {e}")
        import traceback
        traceback.print_exc()
        input("\nTekan ENTER untuk keluar...")


