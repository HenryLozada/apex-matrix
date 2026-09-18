"""
Detector de librerías de escalado por IA en juegos de PC.
Rastrea NVIDIA DLSS, Frame Generation, Ray Reconstruction, AMD FSR e Intel XeSS.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from core.dll_version import Win32VersionReader
from core.game_scanner import InstalledGameTarget

# Nombres conocidos de librerías de escalado
DLSS_SR_NAMES = {"nvngx_dlss.dll"}
DLSS_FG_NAMES = {"nvngx_dlssg.dll"}
DLSS_RR_NAMES = {"nvngx_dlssd.dll"}
XESS_NAMES = {"libxess.dll"}
FSR_PATTERNS = {"fidelityfx", "amd_fidelityfx", "ffx_fsr"}

class DllDetector:
    @staticmethod
    def scan_game_upscalers(game: InstalledGameTarget) -> Dict[str, Any]:
        """
        Escanea de forma recursiva (limitada a 4 niveles de profundidad para velocidad)
        la carpeta de instalación de un juego en busca de DLLs de escalado.
        """
        root = game.install_path
        detected_dlls: List[Dict[str, Any]] = []

        if not root.exists() or not root.is_dir():
            return {
                "game_name": game.name,
                "platform": game.platform,
                "install_path": str(root),
                "has_upscaling": False,
                "dlls": []
            }

        # Búsqueda selectiva en subcarpetas (ej. Binaries/Win64, Binaries, etc.)
        try:
            for p in root.rglob("*.dll"):
                # Limitar profundidad para evitar bucles o lentitud
                try:
                    rel_depth = len(p.relative_to(root).parts)
                    if rel_depth > 5:
                        continue
                except ValueError:
                    continue

                name_lower = p.name.lower()
                tech_type = None
                tech_label = None

                if name_lower in DLSS_SR_NAMES:
                    tech_type = "dlss_sr"
                    tech_label = "NVIDIA DLSS (Super Resolution)"
                elif name_lower in DLSS_FG_NAMES:
                    tech_type = "dlss_fg"
                    tech_label = "NVIDIA DLSS 3 (Frame Generation)"
                elif name_lower in DLSS_RR_NAMES:
                    tech_type = "dlss_rr"
                    tech_label = "NVIDIA DLSS 3.5 (Ray Reconstruction)"
                elif name_lower in XESS_NAMES:
                    tech_type = "xess"
                    tech_label = "Intel XeSS"
                elif any(pat in name_lower for pat in FSR_PATTERNS):
                    tech_type = "fsr"
                    tech_label = "AMD FidelityFX FSR"

                if tech_type:
                    meta = Win32VersionReader.get_dll_metadata(p)
                    # Comprobar si existe respaldo previo
                    bak_file = p.with_suffix(".dll.bak")
                    has_backup = bak_file.exists()

                    detected_dlls.append({
                        "tech_type": tech_type,
                        "tech_label": tech_label,
                        "filename": p.name,
                        "rel_path": str(p.relative_to(root)),
                        "full_path": str(p),
                        "version": meta["version"],
                        "size_str": meta["size_str"],
                        "size_bytes": meta["size_bytes"],
                        "modified": meta["modified"],
                        "has_backup": has_backup,
                        "backup_path": str(bak_file) if has_backup else None
                    })
        except Exception:
            pass

        return {
            "game_name": game.name,
            "platform": game.platform,
            "install_path": str(root),
            "app_id": game.app_id,
            "has_upscaling": len(detected_dlls) > 0,
            "dll_count": len(detected_dlls),
            "dlls": detected_dlls
        }

    @classmethod
    def scan_all_games_upscalers(cls, games: List[InstalledGameTarget]) -> List[Dict[str, Any]]:
        results = []
        for g in games:
            info = cls.scan_game_upscalers(g)
            if info["has_upscaling"]:
                results.append(info)
        return results
