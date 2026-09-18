"""
Telemetría de hardware de GPU, versiones de controlador y estado gráfico del sistema.
"""

import os
import json
import subprocess
from typing import Dict, Any, List

class GpuTelemetry:
    @classmethod
    def get_gpu_info(cls) -> Dict[str, Any]:
        """
        Obtiene información detallada sobre las tarjetas gráficas instaladas,
        priorizando GPUs dedicadas NVIDIA / AMD.
        """
        gpus = []
        try:
            cmd = [
                "powershell", "-NoProfile", "-Command",
                "Get-CimInstance Win32_VideoController | Select-Object Name, DriverVersion, AdapterRAM, VideoProcessor | ConvertTo-Json"
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout)
                if isinstance(data, dict):
                    data = [data]

                for item in data:
                    name = item.get("Name", "")
                    # Ignorar adaptadores virtuales o de streaming si hay GPUs físicas
                    if not name or "Virtual" in name or "RDP" in name:
                        continue

                    ram_bytes = item.get("AdapterRAM") or 0
                    vram_gb = round(ram_bytes / (1024 ** 3), 1) if ram_bytes > 0 else 0

                    driver_raw = item.get("DriverVersion", "")
                    # En NVIDIA el driver 32.0.15.8266 corresponde a la versión comercial 582.66
                    commercial_driver = driver_raw
                    if "NVIDIA" in name.upper() and "." in driver_raw:
                        parts = driver_raw.split(".")
                        if len(parts) >= 4:
                            last_two = parts[-2] + parts[-1]
                            if len(last_two) >= 5:
                                commercial_driver = f"{last_two[-5:-2]}.{last_two[-2:]}"

                    is_nvidia = "NVIDIA" in name.upper()
                    is_rtx = "RTX" in name.upper()
                    supports_dlss_sr = is_rtx or "GTX" in name.upper() # RTX para DLSS oficial, mods/FSR para GTX
                    supports_dlss_fg = is_rtx and ("40" in name or "50" in name) # DLSS 3 FG oficial en RTX 40/50

                    gpus.append({
                        "name": name,
                        "driver_version": driver_raw,
                        "commercial_driver": commercial_driver,
                        "vram_gb": vram_gb,
                        "is_nvidia": is_nvidia,
                        "is_rtx": is_rtx,
                        "supports_dlss_sr": supports_dlss_sr,
                        "supports_dlss_fg": supports_dlss_fg
                    })
        except Exception:
            pass

        # Ordenar para que la GPU dedicada NVIDIA quede primera
        gpus.sort(key=lambda x: (x["is_nvidia"], x["vram_gb"]), reverse=True)
        primary = gpus[0] if gpus else {
            "name": "GPU Genérica Direct3D",
            "driver_version": "N/A",
            "commercial_driver": "N/A",
            "vram_gb": 0,
            "is_nvidia": False,
            "is_rtx": False,
            "supports_dlss_sr": False,
            "supports_dlss_fg": False
        }

        return {
            "primary_gpu": primary,
            "all_gpus": gpus,
            "os": "Windows 11 / 10 64-bit",
            "has_dedicated_gpu": len(gpus) > 0
        }
