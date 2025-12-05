# -*- mode: python ; coding: utf-8 -*-
import sys
import os

# Get the directory where this spec file is located
spec_root = os.path.abspath(SPECPATH)
icon_path = os.path.join(spec_root, 'icon.icns')

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'requests',
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
        'PyPDF2',  # You don't actually use this

        # Anthropic SDK extras
        'anthropic.lib.bedrock',
        'anthropic.lib.vertex',

        # Zeep (not used at all - remove from requirements.txt too!)
        'zeep',

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
    # REMOVED: a.binaries, a.zipfiles, a.datas from here (that made it onefile)
    [],
    exclude_binaries=True,  # KEY CHANGE: This makes it onedir
    name='PrintavoQuoteCreator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch='x86_64',
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

# Create macOS app bundle
app = BUNDLE(
    coll,
    name='PrintavoQuoteCreator.app',
    icon=icon_path if os.path.exists(icon_path) else None,
    bundle_identifier='com.yourcompany.printavoquotecreator',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': 'True',
        'CFBundleShortVersionString': '1.0.0',
        'LSMinimumSystemVersion': '10.13.0',
    },
)