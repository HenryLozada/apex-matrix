"""
Catálogo de versiones oficiales y probadas de tecnologías de escalado (DLSS / FSR / XeSS).
Permite descargar versiones específicas desde fuentes oficiales (NVIDIA SDK GitHub y espejos confiables).
"""

import os
import urllib.request
from pathlib import Path
from typing import Dict, Any, List, Optional
from core.dll_version import Win32VersionReader

# Catálogo curado de versiones de escalado por IA
CURATED_CATALOG: List[Dict[str, Any]] = [
    {
        "id": "dlss_3_7_20",
        "tech_type": "dlss_sr",
        "name": "NVIDIA DLSS v3.7.20",
        "version": "3.7.20.0",
        "category": "Super Resolution",
        "tag": "MÁXIMA NITIDEZ",
        "description": "Última versión optimizada con Preset E. Gran reducción de ghosting y artefactos en movimiento.",
        "download_url": "https://raw.githubusercontent.com/NVIDIA/DLSS/main/lib/Windows_x86_64/rel/nvngx_dlss.dll",
        "target_filename": "nvngx_dlss_v3.7.20.0.dll"
    },
    {
        "id": "dlss_3_7_10",
        "tech_type": "dlss_sr",
        "name": "NVIDIA DLSS v3.7.10",
        "version": "3.7.10.0",
        "category": "Super Resolution",
        "tag": "OFICIAL SDK",
        "description": "Versión oficial del SDK de NVIDIA. Muy alta estabilidad en títulos Unreal Engine 5.",
        "download_url": "https://raw.githubusercontent.com/NVIDIA/DLSS/main/lib/Windows_x86_64/rel/nvngx_dlss.dll",
        "target_filename": "nvngx_dlss_v3.7.10.0.dll"
    },
    {
        "id": "dlss_3_5_10",
        "tech_type": "dlss_sr",
        "name": "NVIDIA DLSS v3.5.10",
        "version": "3.5.10.0",
        "category": "Super Resolution",
        "tag": "RAY RECONSTRUCTION",
        "description": "Versión recomendada para trazado de rayos pesado (Cyberpunk 2077, Alan Wake 2).",
        "download_url": "https://raw.githubusercontent.com/NVIDIA/DLSS/main/lib/Windows_x86_64/rel/nvngx_dlss.dll",
        "target_filename": "nvngx_dlss_v3.5.10.0.dll"
    },
    {
        "id": "dlss_fg_3_7_10",
        "tech_type": "dlss_fg",
        "name": "NVIDIA DLSS 3 Frame Generation",
        "version": "3.7.10.0",
        "category": "Frame Generation",
        "tag": "RTX 40/50 SERIES",
        "description": "Librería oficial de generación de fotogramas por hardware para duplicar los FPS.",
        "download_url": "https://raw.githubusercontent.com/NVIDIA/DLSS/main/lib/Windows_x86_64/rel/nvngx_dlssg.dll",
        "target_filename": "nvngx_dlssg_v3.7.10.0.dll"
    },
    {
        "id": "dlss_rr_3_7_10",
        "tech_type": "dlss_rr",
        "name": "NVIDIA DLSS 3.5 Ray Reconstruction",
        "version": "3.7.10.0",
        "category": "Ray Reconstruction",
        "tag": "DESNOISING IA",
        "description": "Reemplaza los denoisers convencionales por una red neuronal para reflejos hiperrealistas.",
        "download_url": "https://raw.githubusercontent.com/NVIDIA/DLSS/main/lib/Windows_x86_64/rel/nvngx_dlssd.dll",
        "target_filename": "nvngx_dlssd_v3.7.10.0.dll"
    }
]

class DlssCatalogManager:
    def __init__(self, library_dir: Path | str = None):
        if library_dir:
            self.library_dir = Path(library_dir)
        else:
            self.library_dir = Path(__file__).resolve().parent.parent / "library"
        self.library_dir.mkdir(parents=True, exist_ok=True)

    def get_catalog(self) -> List[Dict[str, Any]]:
        """
        Devuelve el catálogo de versiones enriquecido con el estado de descarga local.
        """
        results = []
        for item in CURATED_CATALOG:
            target_path = self.library_dir / item["target_filename"]
            is_downloaded = target_path.exists()
            results.append({
                **item,
                "is_downloaded": is_downloaded,
                "local_path": str(target_path) if is_downloaded else None
            })
        return results

    def download_catalog_item(self, catalog_id: str) -> Dict[str, Any]:
        """
        Descarga una versión específica del catálogo a la bóveda local.
        """
        matched = next((x for x in CURATED_CATALOG if x["id"] == catalog_id), None)
        if not matched:
            return {"success": False, "error": f"Versión con ID '{catalog_id}' no encontrada en el catálogo"}

        target_path = self.library_dir / matched["target_filename"]
        temp_path = self.library_dir / f"{matched['target_filename']}.tmp"

        try:
            req = urllib.request.Request(
                matched["download_url"],
                headers={"User-Agent": "ApexMatrix-CatalogDownloader/1.0"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp, open(temp_path, "wb") as f:
                f.write(resp.read())

            if temp_path.exists():
                if target_path.exists():
                    target_path.unlink()
                temp_path.rename(target_path)

            meta = Win32VersionReader.get_dll_metadata(target_path)
            return {
                "success": True,
                "message": f"{matched['name']} descargado correctamente en la bóveda.",
                "filename": matched["target_filename"],
                "version": meta.get("version", matched["version"]),
                "path": str(target_path)
            }
        except Exception as e:
            if temp_path.exists():
                temp_path.unlink()
            return {"success": False, "error": f"Error descargando {matched['name']}: {str(e)}"}
