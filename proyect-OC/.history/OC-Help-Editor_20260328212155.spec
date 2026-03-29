# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ['tkinter', '_tkinter']
hiddenimports += collect_submodules('bitstring')


a = Analysis(
    ['app\\editor.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('images', 'images'),
        ('C:/Users/Alexxe/AppData/Local/Programs/Python/Python313/tcl/tcl8.6', '_tcl_data'),
        ('C:/Users/Alexxe/AppData/Local/Programs/Python/Python313/tcl/tk8.6', '_tk_data'),
    ],
    hiddenimports=hiddenimports,
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
    name='OC-Help-Editor',
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
)
