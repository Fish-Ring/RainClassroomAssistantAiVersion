# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['RainClassroomAssistant.py'],
    pathex=[],
    binaries=[],
    datas=[('UI/Image/favicon.ico', 'UI/Image'), ('UI/Image/NoRainClassroom.jpg', 'UI/Image'), ('file_version_info.txt', '.')],
    hiddenimports=['PyQt5', 'PyQt5.QtWidgets', 'PyQt5.QtCore', 'PyQt5.QtGui', 'scai', 'openai', 'pyttsx3', 'requests', 'websocket', 'win32api'],
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
    name='RainClassroomAssistantAi',
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
    icon=['UI\\Image\\favicon.ico'],
)
