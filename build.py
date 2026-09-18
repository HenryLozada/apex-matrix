"""
Script de compilación a ejecutable (.exe) para ApexMatrix mediante PyInstaller.
"""

import sys
import shutil
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def build():
    print("========================================================")
    print("   APEX MATRIX // BUILD ENGINE (NVIDIA POWER GREEN)     ")
    print("========================================================")

    # Comprobar si PyInstaller está instalado
    try:
        import PyInstaller
    except ImportError:
        print("[ERROR] PyInstaller no está instalado. Instalando...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    dist_dir = BASE_DIR / "dist"
    build_dir = BASE_DIR / "build"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name", "ApexMatrix",
        "--add-data", f"{BASE_DIR / 'gui'};gui",
        "--add-data", f"{BASE_DIR / 'library'};library",
        "--collect-all", "webview",
        str(BASE_DIR / "main.py")
    ]

    print(f"Ejecutando PyInstaller...")
    res = subprocess.run(cmd, cwd=str(BASE_DIR))

    if res.returncode == 0:
        exe_path = dist_dir / "ApexMatrix" / "ApexMatrix.exe"
        print("--------------------------------------------------------")
        print(f"[EXITO] Compilación completada con éxito.")
        print(f"Ejecutable generado en: {exe_path}")
        print("--------------------------------------------------------")
    else:
        print("[ERROR] La compilación falló.")

if __name__ == "__main__":
    build()
