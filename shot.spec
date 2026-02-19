# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller ビルド設定 — python -m PyInstaller shot.spec でビルド"""

a = Analysis(
    ["hans_on_toys/__main__.py"],
    pathex=["."],
    binaries=[],
    datas=[],
    hiddenimports=[
        "pystray._win32",       # Windows トレイアイコン
        "PIL._tkinter_finder",  # Pillow / tkinter 連携
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
    console=False,   # コンソール画面を表示しない（pythonw 相当）
    icon=None,       # アイコンを指定したい場合: icon="path/to/icon.ico"
)
