"""
Lector nativo de versiones y metadatos de archivos ejecutables y DLLs en Windows.
Utiliza ctypes y la API Win32 version.dll sin dependencias externas.
"""

import ctypes
from ctypes import wintypes
from pathlib import Path
from typing import Optional, Dict, Any

class Win32VersionReader:
    @staticmethod
    def get_file_version(filepath: Path | str) -> Optional[str]:
        """
        Obtiene la versión numérica del archivo (ej: 3.7.10.0) desde el bloque VS_FIXEDFILEINFO.
        """
        path = str(filepath)
        try:
            size = ctypes.windll.version.GetFileVersionInfoSizeW(path, None)
            if size == 0:
                return None

            buffer = ctypes.create_string_buffer(size)
            if not ctypes.windll.version.GetFileVersionInfoW(path, 0, size, buffer):
                return None

            p_info = ctypes.c_void_p()
            p_len = wintypes.UINT()
            if not ctypes.windll.version.VerQueryValueW(buffer, "\\", ctypes.byref(p_info), ctypes.byref(p_len)):
                return None

            class VS_FIXEDFILEINFO(ctypes.Structure):
                _fields_ = [
                    ("dwSignature", wintypes.DWORD),
                    ("dwStrucVersion", wintypes.DWORD),
                    ("dwFileVersionMS", wintypes.DWORD),
                    ("dwFileVersionLS", wintypes.DWORD),
                    ("dwProductVersionMS", wintypes.DWORD),
                    ("dwProductVersionLS", wintypes.DWORD),
                    ("dwFileFlagsMask", wintypes.DWORD),
                    ("dwFileFlags", wintypes.DWORD),
                    ("dwFileOS", wintypes.DWORD),
                    ("dwFileType", wintypes.DWORD),
                    ("dwFileSubtype", wintypes.DWORD),
                    ("dwFileDateMS", wintypes.DWORD),
                    ("dwFileDateLS", wintypes.DWORD),
                ]

            fixed_info = ctypes.cast(p_info, ctypes.POINTER(VS_FIXEDFILEINFO)).contents
            ms = fixed_info.dwFileVersionMS
            ls = fixed_info.dwFileVersionLS

            major = (ms >> 16) & 0xFFFF
            minor = ms & 0xFFFF
            build = (ls >> 16) & 0xFFFF
            revision = ls & 0xFFFF

            # Normalización inteligente para ejecutables o mods que empaquetan subversiones en el número mayor (ej. 310 -> 3.1.0)
            if major == 310:
                return f"3.1.0.{minor}"
            elif major == 31:
                return f"3.1.{minor}.{build}"
            elif major > 100 and str(major).startswith("3"):
                s = str(major)
                return f"{s[0]}.{s[1]}.{s[2:]}.{minor}"

            return f"{major}.{minor}.{build}.{revision}"
        except Exception:
            return None

    @classmethod
    def get_dll_metadata(cls, filepath: Path | str) -> Dict[str, Any]:
        """
        Devuelve información enriquecida sobre el archivo DLL (tamaño, fecha, versión Win32).
        """
        p = Path(filepath)
        if not p.exists() or not p.is_file():
            return {
                "exists": False,
                "version": "N/A",
                "size_bytes": 0,
                "size_str": "0 B",
                "modified": ""
            }

        stat = p.stat()
        version = cls.get_file_version(p) or "Desconocida"

        # Formatear tamaño
        bytes_val = stat.st_size
        if bytes_val < 1024:
            size_str = f"{bytes_val} B"
        elif bytes_val < 1024 * 1024:
            size_str = f"{bytes_val / 1024:.1f} KB"
        else:
            size_str = f"{bytes_val / (1024 * 1024):.2f} MB"

        from datetime import datetime
        mod_date = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")

        return {
            "exists": True,
            "filename": p.name,
            "path": str(p),
            "version": version,
            "size_bytes": bytes_val,
            "size_str": size_str,
            "modified": mod_date
        }
