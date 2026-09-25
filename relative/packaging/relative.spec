# -*- mode: python -*-
# Настройки PyInstaller — общие для Windows и Linux.
# Результат: один исполняемый файл без установки (всё, включая папку assets, внутри).
#   Windows: dist/windows/Relative.exe      Linux: dist/linux/relative
# Запускается из scripts/build_windows.sh и scripts/build_linux.sh (или make).

import os
import sys

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
WINDOWS = sys.platform.startswith("win")

# То, что программе не нужно, но PyInstaller мог бы захватить "на всякий случай".
EXCLUDES = [
    "tkinter", "matplotlib", "PIL", "scipy", "pandas", "IPython", "pytest",
    "OpenGL", "pyqtgraph.opengl", "pyqtgraph.examples", "pyqtgraph.jupyter",
    "PyQt5.QtWebEngineWidgets", "PyQt5.QtWebEngineCore", "PyQt5.QtMultimedia",
    "PyQt5.QtQml", "PyQt5.QtQuick", "PyQt5.QtSql", "PyQt5.QtBluetooth",
]

a = Analysis(
    [os.path.join(ROOT, "main.py")],
    pathex=[ROOT],
    datas=[(os.path.join(ROOT, "assets"), "assets")],
    excludes=EXCLUDES,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name="Relative" if WINDOWS else "relative",
    console=False,  # без чёрного окна консоли
    upx=False,
    strip=not WINDOWS,
)
