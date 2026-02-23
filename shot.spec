# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build config — run: python -m PyInstaller shot.spec"""

from PyInstaller.utils.hooks import collect_all

kb_datas,  kb_binaries,  kb_hidden  = collect_all("keyboard")
pst_datas, pst_binaries, pst_hidden = collect_all("pystray")

a = Analysis(
    ["hans_on_toys/__main__.py"],
    pathex=["."],
    binaries=kb_binaries + pst_binaries,
    datas=kb_datas + pst_datas,
    hiddenimports=[
        "mss",                      # screen capture
        "mss.windows",              # Windows backend
        "pytesseract",              # OCR (PII masking)
    ] + kb_hidden + pst_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="shot",
    debug=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,   # no console window (equivalent to pythonw)
    icon=None,       # set to "path/to/icon.ico" to embed an icon
)
