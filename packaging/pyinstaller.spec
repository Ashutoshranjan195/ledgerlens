# -*- mode: python ; coding: utf-8 -*-
# PyInstaller specification for single-binary native LedgerLens packaging

import sys
from pathlib import Path

block_cipher = None

added_files = [
    ('prompts', 'prompts'),
    ('models', 'models'),
    ('samples', 'samples'),
    ('evals/golden', 'evals/golden'),
    ('evals/baselines', 'evals/baselines'),
    ('app/models.yaml', 'app'),
    ('app/config.yaml', 'app'),
    ('app/store/migrations', 'app/store/migrations'),
    ('app/store/schema.sql', 'app/store'),
    ('app/update/manifest.schema.json', 'app/update'),
]

a = Analysis(
    ['app/main.py'],
    pathex=['.'],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'streamlit',
        'pydantic',
        'yaml',
        'pypdf',
        'PIL',
        'sqlite3',
        'cryptography'
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ledgerlens',
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
