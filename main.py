"""
ApexMatrix // DLSS Swapper & ShaderPurge
Suite de optimización de GPU, escalado por IA y purga de caché de shaders.
Diseño de alto rendimiento NVIDIA Power Green Architecture.
"""

import os
import sys
import subprocess
import webview
from pathlib import Path

# Configurar directorio base
BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
sys.path.insert(0, str(BASE_DIR))

from core.game_scanner import GameScanner
from core.dll_detector import DllDetector
from core.dll_swapper import DllSwapper
from core.shader_cleaner import ShaderCleaner
from core.gpu_telemetry import GpuTelemetry

class ApexMatrixApi:
    def __init__(self):
        self.scanner = GameScanner()
        self.swapper = DllSwapper(BASE_DIR / "library")
        self.cleaner = ShaderCleaner(BASE_DIR / "library" / "purge_stats.json")
        self._window = None

    def set_window(self, window):
        self._window = window

    # 1. Escaneo de Juegos y Librerías de Escalado (DLSS / FSR / XeSS)
    def scan_games_and_upscalers(self):
        """Escanea todos los juegos instalados y localiza sus DLLs de escalado."""
        try:
            games = self.scanner.scan_all_games()
            results = DllDetector.scan_all_games_upscalers(games)
            return {
                "success": True,
                "total_installed_games": len(games),
                "games_with_upscaling": len(results),
                "games": results
            }
        except Exception as e:
            return {"success": False, "error": str(e), "games": []}

    def get_library_versions(self):
        """Obtiene las versiones de DLL disponibles en la bóveda local para swapping."""
        try:
            return self.swapper.get_library_versions()
        except Exception:
            return []

    def swap_dll(self, target_path: str, replacement_path: str):
        """Actualiza la DLL del juego con respaldo automático del original."""
        try:
            return self.swapper.swap_dll(target_path, replacement_path)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def restore_dll(self, target_path: str):
        """Restaura la DLL original (.bak) del juego."""
        try:
            return self.swapper.restore_dll(target_path)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def swap_all_in_game(self, game_install_path: str):
        """Actualiza todas las DLLs de escalado en el juego por lote."""
        try:
            return self.swapper.swap_all_in_game(game_install_path)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def restore_all_in_game(self, game_install_path: str):
        """Restaura todas las copias de seguridad (.bak) del juego por lote."""
        try:
            return self.swapper.restore_all_in_game(game_install_path)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def download_official_dlss(self):
        """Descarga la última versión oficial de DLSS desde el repositorio de NVIDIA."""
        try:
            return self.swapper.download_official_dlss()
        except Exception as e:
            return {"success": False, "error": str(e)}

    def import_custom_dll(self):
        """Abre un diálogo nativo de Windows para importar una DLL descargada."""
        if not self._window:
            return {"success": False, "error": "Ventana no inicializada"}
        try:
            file_types = ("Archivos de Librería Dinámica (*.dll)", "Todos los archivos (*.*)")
            res = self._window.create_file_dialog(
                webview.OPEN_DIALOG,
                allow_multiple=False,
                file_types=file_types
            )
            if res and len(res) > 0:
                return self.swapper.import_dll(res[0])
            return {"success": False, "cancelled": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # 2. ShaderPurge & Limpiador de Caché de GPU
    def scan_shader_caches(self):
        """Escanea el tamaño de cachés de shaders NVIDIA, DirectX y crash dumps."""
        try:
            return self.cleaner.scan_all()
        except Exception as e:
            return {"error": str(e), "total_bytes": 0, "categories": []}

    def purge_caches(self, target_ids=None, older_than_days=0):
        """Ejecuta la purga de cachés de shaders liberando almacenamiento SSD."""
        try:
            return self.cleaner.purge_targets(target_ids, older_than_days)
        except Exception as e:
            return {"success": False, "error": str(e)}

    # 3. Telemetría y Explorador
    def get_system_telemetry(self):
        """Obtiene datos de la GPU principal, versión de driver y almacenamiento recuperado."""
        try:
            gpu_data = GpuTelemetry.get_gpu_info()
            reclaimed_bytes = self.cleaner.get_lifetime_reclaimed_bytes()
            gpu_data["lifetime_reclaimed_str"] = self.cleaner._format_size(reclaimed_bytes)
            return gpu_data
        except Exception as e:
            return {"error": str(e)}

    def open_folder(self, folder_path: str):
        """Abre la carpeta en el Explorador de Windows."""
        try:
            p = Path(folder_path).resolve()
            if p.is_file():
                subprocess.Popen(f'explorer /select,"{p}"')
            else:
                p.mkdir(parents=True, exist_ok=True)
                subprocess.Popen(f'explorer "{p}"')
            return True
        except Exception:
            return False

def main():
    api = ApexMatrixApi()
    gui_dir = BASE_DIR / "gui"
    html_path = gui_dir / "index.html"

    window = webview.create_window(
        title="APEX MATRIX // DLSS Swapper & ShaderPurge — NVIDIA Power Green Architecture",
        url=str(html_path.resolve()),
        js_api=api,
        width=1320,
        height=880,
        min_size=(1000, 680),
        background_color="#000000"
    )
    api.set_window(window)

    webview.start(debug=False)

if __name__ == "__main__":
    main()
