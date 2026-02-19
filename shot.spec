# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build config — run: python -m PyInstaller shot.spec"""

a = Analysis(
    ["hans_on_toys/__main__.py"],
    pathex=["."],
    binaries=[],
    datas=[],
    hiddenimports=[
        "pystray._win32",       # Windows tray icon backend
        "PIL._tkinter_finder",  # Pillow / tkinter bridge
    ],
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
