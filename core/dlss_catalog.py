"""
Catálogo de versiones oficiales y probadas de tecnologías de escalado (DLSS / FSR / XeSS).
Permite descargar versiones específicas desde fuentes oficiales (NVIDIA, Intel y AMD SDKs).
"""

import os
import zipfile
import io
import urllib.request
from pathlib import Path
from typing import Dict, Any, List, Optional
from core.dll_version import Win32VersionReader

# Catálogo curado de versiones de escalado por IA y Reconstrucción
CURATED_CATALOG: List[Dict[str, Any]] = [
    # --- NVIDIA DLSS ---
    {
        "id": "dlss_3_7_20",
        "tech_type": "dlss_sr",
        "vendor": "NVIDIA",
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
        "vendor": "NVIDIA",
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
        "vendor": "NVIDIA",
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
        "vendor": "NVIDIA",
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
        "vendor": "NVIDIA",
        "name": "NVIDIA DLSS 3.5 Ray Reconstruction",
        "version": "3.7.10.0",
        "category": "Ray Reconstruction",
        "tag": "DENOISING IA",
        "description": "Reemplaza los denoisers convencionales por una red neuronal para reflejos hiperrealistas.",
        "download_url": "https://raw.githubusercontent.com/NVIDIA/DLSS/main/lib/Windows_x86_64/rel/nvngx_dlssd.dll",
        "target_filename": "nvngx_dlssd_v3.7.10.0.dll"
    },

    # --- INTEL XeSS ---
    {
        "id": "xess_1_3_1",
        "tech_type": "xess",
        "vendor": "Intel",
        "name": "Intel XeSS v1.3.1 (Latest SDK)",
        "version": "1.3.1.0",
        "category": "Intel XeSS",
        "tag": "MULTI-GPU IA",
        "description": "Escalado por IA oficial de Intel con algoritmos XMX y DP4a. Compatible con GPUs Arc, RTX, GTX y Radeon.",
        "download_url": "https://raw.githubusercontent.com/intel/xess/master/bin/libxess.dll",
        "target_filename": "libxess_v1.3.1.0.dll"
    },
    {
        "id": "xess_1_3_0",
        "tech_type": "xess",
        "vendor": "Intel",
        "name": "Intel XeSS v1.3.0",
        "version": "1.3.0.0",
        "category": "Intel XeSS",
        "tag": "ULTRA QUALITY+",
        "description": "Versión que introduce nuevos perfiles Ultra Quality Plus y mejor retención de detalles finos.",
        "download_url": "https://raw.githubusercontent.com/intel/xess/v1.3.0/bin/libxess.dll",
        "target_filename": "libxess_v1.3.0.0.dll"
    },
    {
        "id": "xess_1_2_0",
        "tech_type": "xess",
        "vendor": "Intel",
        "name": "Intel XeSS v1.2.0",
        "version": "1.2.0.0",
        "category": "Intel XeSS",
        "tag": "ESTABLE",
        "description": "Versión clásica con amplio soporte para juegos con integración temprana de XeSS.",
        "download_url": "https://raw.githubusercontent.com/intel/xess/v1.2.0/bin/libxess.dll",
        "target_filename": "libxess_v1.2.0.0.dll"
    },

    # --- AMD FIDELITYFX (FSR) ---
    {
        "id": "amd_fsr_fg_dx12",
        "tech_type": "fsr",
        "vendor": "AMD",
        "name": "AMD FidelityFX Frame Generation DX12",
        "version": "3.1.0.0",
        "category": "AMD FSR",
        "tag": "FRAME GEN ABIERTO",
        "description": "Generación de fotogramas abierta de AMD para DirectX 12. Duplica los FPS sin requerir hardware exclusivo.",
        "download_url": "https://github.com/GPUOpen-LibrariesAndSDKs/FidelityFX-SDK/releases/download/v2.3.0/FidelityFX-Samples-v2.3.0-prebuilt.zip",
        "archive_member": "Samples/Upscalers/FidelityFX_FSR/dx12/x64/Release/amd_fidelityfx_framegeneration_dx12.dll",
        "target_filename": "amd_fidelityfx_framegeneration_dx12.dll"
    },
    {
        "id": "amd_fsr_upscaler_dx12",
        "tech_type": "fsr",
        "vendor": "AMD",
        "name": "AMD FidelityFX Upscaler DX12",
        "version": "3.1.0.0",
        "category": "AMD FSR",
        "tag": "ESCALADO TEMPORAL",
        "description": "Módulo de superresolución temporal de alta precisión de AMD para juegos DirectX 12.",
        "download_url": "https://github.com/GPUOpen-LibrariesAndSDKs/FidelityFX-SDK/releases/download/v2.3.0/FidelityFX-Samples-v2.3.0-prebuilt.zip",
        "archive_member": "Samples/Upscalers/FidelityFX_FSR/dx12/x64/Release/amd_fidelityfx_upscaler_dx12.dll",
        "target_filename": "amd_fidelityfx_upscaler_dx12.dll"
    },
    {
        "id": "amd_fsr_loader_dx12",
        "tech_type": "fsr",
        "vendor": "AMD",
        "name": "AMD FidelityFX Loader DX12",
        "version": "3.1.0.0",
        "category": "AMD FSR",
        "tag": "CARGADOR DX12",
        "description": "Cargador nativo de renderizado y orquestación de recursos de AMD FidelityFX.",
        "download_url": "https://github.com/GPUOpen-LibrariesAndSDKs/FidelityFX-SDK/releases/download/v2.3.0/FidelityFX-Samples-v2.3.0-prebuilt.zip",
        "archive_member": "Samples/Upscalers/FidelityFX_FSR/dx12/x64/Release/amd_fidelityfx_loader_dx12.dll",
        "target_filename": "amd_fidelityfx_loader_dx12.dll"
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
        Soporta descargas binarias directas y extracción de miembros en archivos ZIP.
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
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = resp.read()

            # Si es un ZIP con un miembro específico a extraer
            if matched.get("archive_member"):
                with zipfile.ZipFile(io.BytesIO(data)) as z:
                    member_data = z.read(matched["archive_member"])
                    with open(temp_path, "wb") as f:
                        f.write(member_data)
            else:
                with open(temp_path, "wb") as f:
                    f.write(data)

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
