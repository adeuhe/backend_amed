# =============================================================================
# ECL Audit & Benchmarking Workbench — Ultra-Lightweight PyInstaller Compiler
# =============================================================================

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host " Building Lightweight Windows Executable (.exe) dengan PyInstaller" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Cyan

# 1. Set Working Directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# 2. Check & Install PyInstaller & OpenPyXL
Write-Host "[1/4] Memeriksa modul PyInstaller & OpenPyXL..." -ForegroundColor Yellow
python -m pip install pyinstaller openpyxl --quiet

# 3. Clean up previous build/dist folders & temporary cache files
Write-Host "[2/4] Membersihkan proses berjalan, folder build lama, dan cache..." -ForegroundColor Yellow

# Force kill any running instances of executable to release Windows file locks
taskkill /F /IM ECL_Audit_Benchmarking_Workbench.exe 2>$null
taskkill /F /FI "WINDOWTITLE eq ECL Audit & Benchmarking Workbench*" 2>$null
Stop-Process -Name "ECL_Audit_Benchmarking_Workbench" -ErrorAction SilentlyContinue -Force
Start-Sleep -Seconds 1

if (Test-Path "dist") { cmd /c "rmdir /s /q dist" 2>$null }
if (Test-Path "build") { cmd /c "rmdir /s /q build" 2>$null }
if (Test-Path "extracted_doc_text.txt") { Remove-Item -Force "extracted_doc_text.txt" -ErrorAction SilentlyContinue }
if (Test-Path ".pytest_cache") { Remove-Item -Recurse -Force ".pytest_cache" -ErrorAction SilentlyContinue }
Get-ChildItem -Path . -Include "*.spec" -File | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path . -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# 4. Compile Project using PyInstaller
Write-Host "[3/4] Mengompilasi aplikasi..." -ForegroundColor Yellow

$PyInstallerArgs = @(
    "--noconfirm",
    "--clean",
    "--onefile",
    "--name=ECL_Audit_Benchmarking_Workbench",
    "--add-data=static-audit-benchmarking-workbench;static-audit-benchmarking-workbench",
    "--add-data=templates;templates",
    "--add-data=.env;.",
    "--add-data=db_psak413_syariah.db;.",
    # Heavy Cloud & Data Science Exclusions
    "--exclude-module=botocore",
    "--exclude-module=boto3",
    "--exclude-module=s3transfer",
    "--exclude-module=pyarrow",
    "--exclude-module=polars",
    "--exclude-module=dask",
    "--exclude-module=distributed",
    "--exclude-module=tables",
    "--exclude-module=netCDF4",
    "--exclude-module=xarray",
    "--exclude-module=h5py",
    "--exclude-module=zarr",
    # Jupyter, Notebook, JS Schema Exclusions
    "--exclude-module=notebook",
    "--exclude-module=jupyter",
    "--exclude-module=IPython",
    "--exclude-module=ipykernel",
    "--exclude-module=jsonschema",
    "--exclude-module=jsonschema_specifications",
    "--exclude-module=nbformat",
    "--exclude-module=nbconvert",
    "--exclude-module=mistune",
    "--exclude-module=tinycss2",
    "--exclude-module=traitlets",
    "--exclude-module=tornado",
    "--exclude-module=zmq",
    # Heavy AI, ML & Scientific Exclusions
    "--exclude-module=matplotlib",
    "--exclude-module=scipy",
    "--exclude-module=sklearn",
    "--exclude-module=skimage",
    "--exclude-module=astropy",
    "--exclude-module=sympy",
    "--exclude-module=statsmodels",
    "--exclude-module=numba",
    "--exclude-module=cython",
    "--exclude-module=torch",
    "--exclude-module=tensorflow",
    "--exclude-module=transformers",
    "--exclude-module=langchain",
    "--exclude-module=langsmith",
    # Heavy Visualization & Dashboard Exclusions
    "--exclude-module=bokeh",
    "--exclude-module=altair",
    "--exclude-module=plotly",
    "--exclude-module=seaborn",
    "--exclude-module=panel",
    "--exclude-module=pyviz_comms",
    "--exclude-module=markdown",
    "--exclude-module=intake",
    "--exclude-module=xyzservices",
    "--exclude-module=mkl",
    # Heavy GUI Framework Exclusions
    "--exclude-module=PyQt5",
    "--exclude-module=PyQt6",
    "--exclude-module=PySide2",
    "--exclude-module=PySide6",
    "--exclude-module=tkinter",
    "--exclude-module=turtle",
    "--exclude-module=wx",
    # Other Heavy Unused Packages
    "--exclude-module=nacl",
    "--exclude-module=psycopg2",
    "--exclude-module=lxml",
    "--exclude-module=PIL",
    "--exclude-module=Pillow",
    "--exclude-module=fitz",
    "--exclude-module=pdf2image",
    "--exclude-module=docutils",
    "--exclude-module=sphinx",
    "--exclude-module=graphviz",
    "--exclude-module=babel",
    "main.py"
)

python -m PyInstaller @PyInstallerArgs

if ($LASTEXITCODE -eq 0) {
    if (Test-Path ".env") {
        Copy-Item .env -Destination "dist\.env" -Force
    }
    Write-Host "`n=================================================================" -ForegroundColor Green
    Write-Host " COMPILATION SUCCESSFUL (SINGLE STANDALONE .EXE)!" -ForegroundColor Green
    Write-Host " Single Executable berlokasi di: " -ForegroundColor White
    Write-Host " $ScriptDir\dist\ECL_Audit_Benchmarking_Workbench.exe" -ForegroundColor Cyan
    Write-Host "=================================================================`n" -ForegroundColor Green
} else {
    Write-Host "`n[ERROR] Proses kompilasi ke .exe gagal. Periksa log error di atas." -ForegroundColor Red
}
