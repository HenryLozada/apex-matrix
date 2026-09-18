"""
Detector y Purgador seguro de Cachés de Shaders de GPU y Volcados de Errores (ShaderPurge).
Libera almacenamiento SSD y resuelve tirones (stuttering) por shaders corruptos tras actualizar drivers.
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

class ShaderCleaner:
    def __init__(self, stats_file: Path | str = None):
        local_app = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        
        self.targets: Dict[str, Dict[str, Any]] = {
            "nvidia_dx": {
                "id": "nvidia_dx",
                "label": "NVIDIA DirectX Shader Cache",
                "path": local_app / "NVIDIA" / "DXCache",
                "category": "NVIDIA",
                "description": "Caché de compilación de shaders DirectX 11/12 para GPUs NVIDIA GeForce RTX/GTX."
            },
            "nvidia_gl": {
                "id": "nvidia_gl",
                "label": "NVIDIA OpenGL & Vulkan Cache",
                "path": local_app / "NVIDIA" / "GLCache",
                "category": "NVIDIA",
                "description": "Caché de shaders para juegos y emuladores que renderizan en Vulkan y OpenGL."
            },
            "d3ds_cache": {
                "id": "d3ds_cache",
                "label": "DirectX D3DSCache",
                "path": local_app / "D3DSCache",
                "category": "DirectX",
                "description": "Almacén general de shaders compilados del subsistema de gráficos de Windows."
            },
            "dx_temp_cache": {
                "id": "dx_temp_cache",
                "label": "DirectX Shader Temp",
                "path": local_app / "Temp" / "DirectXShaderCache",
                "category": "DirectX",
                "description": "Archivos temporales generados durante la compilación de shaders en tiempo real."
            },
            "crash_dumps": {
                "id": "crash_dumps",
                "label": "Windows Crash Dumps",
                "path": local_app / "CrashDumps",
                "category": "Crash Logs",
                "description": "Volcados pesados de memoria generados cuando un juego o app sufre un crash."
            }
        }

        # Archivo para almacenar estadísticas acumulativas
        if stats_file:
            self.stats_file = Path(stats_file)
        else:
            self.stats_file = Path(__file__).resolve().parent.parent / "library" / "purge_stats.json"
        self.stats_file.parent.mkdir(parents=True, exist_ok=True)

    def scan_all(self) -> Dict[str, Any]:
        """
        Escanea todos los directorios de shaders y calcula tamaños, cantidad de archivos y fechas.
        """
        categories = []
        total_bytes = 0
        total_files = 0

        for key, info in self.targets.items():
            target_path = info["path"]
            exists = target_path.exists()
            cat_bytes = 0
            cat_files = 0
            oldest_date = None
            newest_date = None

            if exists and target_path.is_dir():
                try:
                    for f in target_path.rglob("*"):
                        if f.is_file():
                            try:
                                sz = f.stat().st_size
                                mtime = f.stat().st_mtime
                                cat_bytes += sz
                                cat_files += 1
                                if oldest_date is None or mtime < oldest_date:
                                    oldest_date = mtime
                                if newest_date is None or mtime > newest_date:
                                    newest_date = mtime
                            except Exception:
                                pass
                except Exception:
                    pass

            total_bytes += cat_bytes
            total_files += cat_files

            oldest_str = datetime.fromtimestamp(oldest_date).strftime("%Y-%m-%d") if oldest_date else "N/A"
            newest_str = datetime.fromtimestamp(newest_date).strftime("%Y-%m-%d %H:%M") if newest_date else "N/A"

            categories.append({
                "id": info["id"],
                "label": info["label"],
                "category": info["category"],
                "path": str(target_path),
                "exists": exists,
                "file_count": cat_files,
                "size_bytes": cat_bytes,
                "size_str": self._format_size(cat_bytes),
                "oldest_file": oldest_str,
                "newest_file": newest_str,
                "description": info["description"]
            })

        return {
            "total_bytes": total_bytes,
            "total_files": total_files,
            "total_size_str": self._format_size(total_bytes),
            "categories": categories,
            "lifetime_reclaimed_str": self._format_size(self.get_lifetime_reclaimed_bytes())
        }

    def purge_targets(self, target_ids: Optional[List[str]] = None, older_than_days: int = 0) -> Dict[str, Any]:
        """
        Elimina los archivos de caché especificados con tolerancia a bloqueos en caliente.
        Si un juego está en ejecución y tiene un shader bloqueado, se omite con seguridad sin romper el proceso.
        """
        targets_to_clean = []
        if not target_ids or "all" in target_ids:
            targets_to_clean = list(self.targets.keys())
        else:
            targets_to_clean = [t for t in target_ids if t in self.targets]

        reclaimed_bytes = 0
        deleted_files = 0
        locked_files = 0
        errors = []

        cutoff_timestamp = None
        if older_than_days > 0:
            cutoff_timestamp = time.time() - (older_than_days * 86400)

        for tid in targets_to_clean:
            info = self.targets[tid]
            target_path = info["path"]
            if not target_path.exists() or not target_path.is_dir():
                continue

            for root, dirs, files in os.walk(str(target_path), topdown=False):
                for fname in files:
                    fpath = Path(root) / fname
                    try:
                        stat = fpath.stat()
                        # Filtrar por antigüedad si se indicó
                        if cutoff_timestamp and stat.st_mtime > cutoff_timestamp:
                            continue

                        sz = stat.st_size
                        fpath.unlink()
                        reclaimed_bytes += sz
                        deleted_files += 1
                    except (PermissionError, OSError):
                        locked_files += 1
                    except Exception as e:
                        errors.append(str(e))

                # Intentar eliminar carpetas vacías
                for dname in dirs:
                    dpath = Path(root) / dname
                    try:
                        dpath.rmdir()
                    except Exception:
                        pass

        # Registrar estadísticas históricas
        self._record_reclaimed_bytes(reclaimed_bytes)

        return {
            "success": True,
            "deleted_files": deleted_files,
            "reclaimed_bytes": reclaimed_bytes,
            "reclaimed_size_str": self._format_size(reclaimed_bytes),
            "locked_files": locked_files,
            "errors": errors[:5],
            "message": f"Purga completada: {self._format_size(reclaimed_bytes)} liberados ({deleted_files} archivos eliminados)."
        }

    def get_lifetime_reclaimed_bytes(self) -> int:
        if self.stats_file.exists():
            try:
                data = json.loads(self.stats_file.read_text(encoding="utf-8"))
                return data.get("total_reclaimed_bytes", 0)
            except Exception:
                return 0
        return 0

    def _record_reclaimed_bytes(self, num_bytes: int):
        current = self.get_lifetime_reclaimed_bytes()
        new_total = current + num_bytes
        try:
            self.stats_file.write_text(json.dumps({
                "total_reclaimed_bytes": new_total,
                "last_purge": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }, indent=2), encoding="utf-8")
        except Exception:
            pass

    @staticmethod
    def _format_size(bytes_val: int) -> str:
        if bytes_val < 1024:
            return f"{bytes_val} B"
        elif bytes_val < 1024 * 1024:
            return f"{bytes_val / 1024:.1f} KB"
        elif bytes_val < 1024 * 1024 * 1024:
            return f"{bytes_val / (1024 * 1024):.2f} MB"
        else:
            return f"{bytes_val / (1024 * 1024 * 1024):.2f} GB"
