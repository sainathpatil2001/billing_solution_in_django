# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['run_django.py'],
    pathex=[],
    binaries=[],
    datas=[('genrate_bill/templates', 'genrate_bill/templates'), ('inventory/templates', 'inventory/templates'), ('static', 'static'), ('media', 'media'), ('initial_db.sqlite3', '.')],
    hiddenimports=['genrate_bill.apps', 'inventory.apps', 'genrate_bill.urls', 'inventory.urls', 'bill_maker.urls', 'django.contrib.admin.apps', 'django.contrib.auth.apps', 'django.contrib.contenttypes.apps', 'django.contrib.messages.apps', 'django.contrib.sessions.apps', 'django.contrib.staticfiles.apps'],
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
    [],
    exclude_binaries=True,
    name='django_app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='django_app',
)
