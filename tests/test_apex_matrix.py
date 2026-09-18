"""
Banco de pruebas automatizadas (Unit & Integration Tests) para ApexMatrix.
Verifica escaneo de DLLs de escalado, swapping seguro, lectura de versión Win32,
limpieza de shaders y telemetría de hardware de GPU.
"""

import os
import sys
import shutil
import tempfile
import unittest
from pathlib import Path

# Agregar directorio raíz
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.dll_version import Win32VersionReader
from core.game_scanner import GameScanner, InstalledGameTarget
from core.dll_detector import DllDetector
from core.dll_swapper import DllSwapper
from core.shader_cleaner import ShaderCleaner
from core.gpu_telemetry import GpuTelemetry
from main import ApexMatrixApi


class TestWin32VersionReader(unittest.TestCase):
    def test_read_real_binary_version(self):
        """Verifica que el lector Win32 extraiga correctamente la versión de un binario real del sistema."""
        python_exe = Path(sys.executable)
        ver = Win32VersionReader.get_file_version(python_exe)
        self.assertIsNotNone(ver)
        self.assertTrue("." in ver)

    def test_read_nonexistent_file(self):
        """Verifica que manejar un archivo inexistente retorne None sin excepciones."""
        res = Win32VersionReader.get_file_version("C:\\nonexistent_fake_path_123.dll")
        self.assertIsNone(res)

    def test_dll_metadata(self):
        """Verifica el diccionario enriquecido de metadatos."""
        python_exe = Path(sys.executable)
        meta = Win32VersionReader.get_dll_metadata(python_exe)
        self.assertTrue(meta["exists"])
        self.assertIn("version", meta)
        self.assertIn("size_str", meta)


class TestGameScanner(unittest.TestCase):
    def setUp(self):
        self.scanner = GameScanner()

    def test_scan_all_games_returns_valid_list(self):
        """Verifica que el escáner recorra Steam, Epic, GOG, EA, Xbox sin generar excepciones."""
        games = self.scanner.scan_all_games()
        self.assertIsInstance(games, list)
        for g in games:
            self.assertIsInstance(g, InstalledGameTarget)
            self.assertTrue(g.install_path.exists())


class TestDllDetectorAndSwapper(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.mock_game_root = Path(self.temp_dir.name) / "MockGame"
        self.mock_binaries = self.mock_game_root / "Binaries" / "Win64"
        self.mock_binaries.mkdir(parents=True, exist_ok=True)

        # Crear DLL simulada de DLSS copiando un binario real con cabeceras PE válidas (python.exe)
        self.mock_dlss = self.mock_binaries / "nvngx_dlss.dll"
        shutil.copy2(sys.executable, self.mock_dlss)

        # Crear biblioteca de versiones
        self.mock_library = Path(self.temp_dir.name) / "Library"
        self.mock_library.mkdir(parents=True, exist_ok=True)
        self.swapper = DllSwapper(self.mock_library)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_detect_upscaling_dlls(self):
        """Verifica que DllDetector localice e identifique nvngx_dlss.dll en la estructura del juego."""
        game = InstalledGameTarget(name="Mock Title", platform="Steam", install_path=self.mock_game_root)
        report = DllDetector.scan_game_upscalers(game)
        self.assertTrue(report["has_upscaling"])
        self.assertEqual(len(report["dlls"]), 1)
        self.assertEqual(report["dlls"][0]["tech_type"], "dlss_sr")

    def test_swap_dll_with_backup_and_restore(self):
        """Verifica el flujo completo: creación de .bak inmutable, reemplazo y reversión."""
        # 1. Crear una nueva versión de reemplazo
        replacement_dll = self.mock_library / "nvngx_dlss_v3.7.0.dll"
        replacement_dll.write_bytes(b"NEW_DLSS_VERSION_MOCK_PAYLOAD")

        # 2. Ejecutar swap
        swap_res = self.swapper.swap_dll(str(self.mock_dlss), str(replacement_dll))
        self.assertTrue(swap_res["success"], f"Error en swap: {swap_res}")

        # Comprobar que existe el archivo .bak original
        backup_file = self.mock_dlss.with_suffix(".dll.bak")
        self.assertTrue(backup_file.exists())
        # Comprobar que el archivo actual tiene el nuevo contenido
        self.assertEqual(self.mock_dlss.read_bytes(), b"NEW_DLSS_VERSION_MOCK_PAYLOAD")

        # 3. Revertir
        restore_res = self.swapper.restore_dll(str(self.mock_dlss))
        self.assertTrue(restore_res["success"], f"Error al revertir: {restore_res}")
        # Comprobar que el archivo volvió a ser el original (el ejecutable de python)
        self.assertEqual(self.mock_dlss.stat().st_size, Path(sys.executable).stat().st_size)


class TestShaderCleaner(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cleaner = ShaderCleaner(Path(self.temp_dir.name) / "stats.json")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_scan_all_shader_caches(self):
        """Verifica que el escaneo de cachés de GPU y volcados calcule tamaños y no falle."""
        res = self.cleaner.scan_all()
        self.assertIn("total_bytes", res)
        self.assertIn("total_size_str", res)
        self.assertIn("categories", res)
        self.assertGreaterEqual(len(res["categories"]), 3)

    def test_format_size_utility(self):
        """Verifica la conversión de bytes a unidades legibles."""
        self.assertEqual(self.cleaner._format_size(500), "500 B")
        self.assertEqual(self.cleaner._format_size(2048), "2.0 KB")
        self.assertEqual(self.cleaner._format_size(1048576 * 5), "5.00 MB")
        self.assertEqual(self.cleaner._format_size(1073741824 * 3), "3.00 GB")

    def test_purge_mock_target(self):
        """Verifica la eliminación segura de archivos y la acumulación de estadísticas."""
        mock_cache_dir = Path(self.temp_dir.name) / "MockCache"
        mock_cache_dir.mkdir(parents=True, exist_ok=True)
        (mock_cache_dir / "shader1.bin").write_bytes(b"SHADER_DATA_1" * 100)
        (mock_cache_dir / "shader2.bin").write_bytes(b"SHADER_DATA_2" * 100)

        # Inyectar target simulado
        self.cleaner.targets["mock_target"] = {
            "id": "mock_target",
            "label": "Mock Cache",
            "path": mock_cache_dir,
            "category": "Test",
            "description": "Test"
        }

        purge_res = self.cleaner.purge_targets(["mock_target"])
        self.assertTrue(purge_res["success"])
        self.assertEqual(purge_res["deleted_files"], 2)
        self.assertGreater(purge_res["reclaimed_bytes"], 0)
        self.assertEqual(self.cleaner.get_lifetime_reclaimed_bytes(), purge_res["reclaimed_bytes"])


class TestGpuTelemetry(unittest.TestCase):
    def test_get_gpu_info(self):
        """Verifica que la detección de GPU devuelva la información estructurada sin errores."""
        info = GpuTelemetry.get_gpu_info()
        self.assertIn("primary_gpu", info)
        self.assertIn("all_gpus", info)
        primary = info["primary_gpu"]
        self.assertIn("name", primary)
        self.assertIn("driver_version", primary)


class TestApexMatrixApi(unittest.TestCase):
    def setUp(self):
        self.api = ApexMatrixApi()

    def test_api_headless_endpoints(self):
        """Verifica que todos los métodos consumidos por JavaScript respondan sin excepciones no controladas."""
        games_res = self.api.scan_games_and_upscalers()
        self.assertTrue(games_res["success"])
        self.assertIsInstance(games_res["games"], list)

        lib = self.api.get_library_versions()
        self.assertIsInstance(lib, list)

        caches = self.api.scan_shader_caches()
        self.assertIn("total_bytes", caches)

        telem = self.api.get_system_telemetry()
        self.assertIn("primary_gpu", telem)


if __name__ == "__main__":
    unittest.main()
