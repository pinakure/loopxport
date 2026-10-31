# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['loopxport.py'],
    pathex=[],
    binaries=[],
    datas=[('m4geek.png', 'm4geek.png'), ('ocr.ttf', 'ocr.ttf'), ('lcd.ttf', 'lcd.ttf'), ('knob.png', 'knob.png'), ('deck.png', 'deck.png')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='loopxport',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['m4geek.png'],
)
