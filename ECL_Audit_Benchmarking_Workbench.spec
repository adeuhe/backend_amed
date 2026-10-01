# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('static-audit-benchmarking-workbench', 'static-audit-benchmarking-workbench'), ('templates', 'templates'), ('.env', '.'), ('db_psak413_syariah.db', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['botocore', 'boto3', 's3transfer', 'pyarrow', 'polars', 'dask', 'distributed', 'tables', 'netCDF4', 'xarray', 'h5py', 'zarr', 'notebook', 'jupyter', 'IPython', 'ipykernel', 'jsonschema', 'jsonschema_specifications', 'nbformat', 'nbconvert', 'mistune', 'tinycss2', 'traitlets', 'tornado', 'zmq', 'matplotlib', 'scipy', 'sklearn', 'skimage', 'astropy', 'sympy', 'statsmodels', 'numba', 'cython', 'torch', 'tensorflow', 'transformers', 'langchain', 'langsmith', 'bokeh', 'altair', 'plotly', 'seaborn', 'panel', 'pyviz_comms', 'markdown', 'intake', 'xyzservices', 'mkl', 'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'tkinter', 'turtle', 'wx', 'nacl', 'psycopg2', 'lxml', 'PIL', 'Pillow', 'fitz', 'pdf2image', 'docutils', 'sphinx', 'graphviz', 'babel'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ECL_Audit_Benchmarking_Workbench',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
