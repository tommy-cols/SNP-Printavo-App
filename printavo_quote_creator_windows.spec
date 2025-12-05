# -*- mode: python ; coding: utf-8 -*-
# Windows build spec file

import os
spec_root = os.path.abspath(SPECPATH)
icon_path = os.path.join(spec_root, 'icon.ico')

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'requests',
        'anthropic',
        'anthropic.resources',
        'anthropic.types',
        'openpyxl',
        'openpyxl.cell',
        'openpyxl.styles',
        'zeep',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # PyQt5 modules you don't use
        'PyQt5.QtBluetooth',
        'PyQt5.QtDBus',
        'PyQt5.QtDesigner',
        'PyQt5.QtHelp',
        'PyQt5.QtLocation',
        'PyQt5.QtMultimedia',
        'PyQt5.QtMultimediaWidgets',
        'PyQt5.QtNetwork',
        'PyQt5.QtNfc',
        'PyQt5.QtOpenGL',
        'PyQt5.QtPositioning',
        'PyQt5.QtPrintSupport',
        'PyQt5.QtQml',
        'PyQt5.QtQuick',
        'PyQt5.QtQuickWidgets',
        'PyQt5.QtSensors',
        'PyQt5.QtSerialPort',
        'PyQt5.QtSql',
        'PyQt5.QtSvg',
        'PyQt5.QtTest',
        'PyQt5.QtWebChannel',
        'PyQt5.QtWebEngine',
        'PyQt5.QtWebEngineCore',
        'PyQt5.QtWebEngineWidgets',
        'PyQt5.QtWebSockets',
        'PyQt5.QtXml',
        'PyQt5.QtXmlPatterns',

        # Common heavy packages you don't use
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'PIL',
        'Pillow',
        'tkinter',

        # Anthropic SDK extras
        'anthropic.lib.bedrock',
        'anthropic.lib.vertex',

        # Zeep extras (you only use sync SOAP)
        'zeep.asyncio',
        'zeep.tornado',

        # Requests extras
        'urllib3.contrib.pyopenssl',
        'urllib3.contrib.socks',
        'chardet',

        # Openpyxl extras (you only read, don't create charts/images)
        'openpyxl.chart',
        'openpyxl.drawing',
        'openpyxl.styles.differential',

        # Testing/dev packages
        'pytest',
        'unittest',
        'test',
        'tests',
        '_pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    # REMOVED: a.binaries, a.zipfiles, a.datas from here
    [],
    exclude_binaries=True,  # KEY CHANGE: This makes it onedir
    name='PrintavoQuoteCreator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path if os.path.exists(icon_path) else None,
)

# COLLECT bundles everything into a folder
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PrintavoQuoteCreator',
)