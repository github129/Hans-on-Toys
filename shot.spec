# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build config — run: python -m PyInstaller shot.spec"""

from PyInstaller.utils.hooks import collect_submodules

a = Analysis(
    ["hans_on_toys/__main__.py"],
    pathex=["."],
    binaries=[],
    datas=[],
    hiddenimports=[
        "pytesseract",              # OCR (PII masking)
    ] + collect_submodules("keyboard")   # global hotkey (all backends)
      + collect_submodules("pystray"),   # system tray (all backends)
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
