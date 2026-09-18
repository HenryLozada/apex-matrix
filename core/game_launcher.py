"""
Módulo de lanzamiento directo de juegos y generación de portadas/banners visuales.
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

# Nombres de ejecutables comunes que NO son el juego principal
EXCLUDED_EXE_PATTERNS = {
    "crash", "unins", "setup", "vcredist", "dxsetup", "update", "patch",
    "launcher", "config", "editor", "easyanticheat", "battleye", "reporter"
}

class GameLauncher:
    @staticmethod
    def get_game_cover(game_name: str, app_id: Optional[str] = None, platform: str = "") -> str:
        """
        Devuelve la URL de la portada oficial (Steam CDN) o genera un banner procedural NVIDIA Green.
        """
        if app_id and "steam" in platform.lower():
            return f"https://shared.cloudflare.steamstatic.com/store_item_assets/steam/apps/{app_id}/header.jpg"

        # Generar banner procedural SVG en base a los colores del sistema de diseño
        clean_name = game_name.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        initials = "".join(w[0] for w in clean_name.split() if w)[:3].upper()

        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 460 120" width="100%" height="100%">
          <defs>
            <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#050505"/>
              <stop offset="50%" stop-color="#111111"/>
              <stop offset="100%" stop-color="#000000"/>
            </linearGradient>
            <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
              <path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(118, 185, 0, 0.06)" stroke-width="1"/>
            </pattern>
          </defs>
          <rect width="460" height="120" fill="url(#g)"/>
          <rect width="460" height="120" fill="url(#grid)"/>
          <rect x="0" y="0" width="460" height="2" fill="#76b900"/>
          <text x="430" y="85" text-anchor="end" font-family="system-ui, sans-serif" font-size="64" font-weight="900" fill="rgba(118, 185, 0, 0.08)">{initials}</text>
          <text x="24" y="52" font-family="'JetBrains Mono', monospace" font-size="9" font-weight="700" fill="#76b900" letter-spacing="1.5">// {platform.upper() or 'CUSTOM GAME'}</text>
          <text x="24" y="80" font-family="'Inter', system-ui, sans-serif" font-size="16" font-weight="800" fill="#ffffff" letter-spacing="0.5">{clean_name[:28]}</text>
        </svg>"""

        import urllib.parse
        encoded_svg = urllib.parse.quote(svg)
        return f"data:image/svg+xml;utf8,{encoded_svg}"

    @classmethod
    def launch_game(cls, install_path_str: str, app_id: Optional[str] = None, platform: str = "") -> Dict[str, Any]:
        """
        Lanza el juego de forma segura sin bloquear la aplicación.
        """
        # 1. Si es Steam con AppID, usar el protocolo oficial de Steam
        if app_id and "steam" in platform.lower():
            try:
                subprocess.Popen(f'explorer "steam://run/{app_id}"', shell=True)
                return {"success": True, "message": f"Iniciando juego a través de Steam (AppID: {app_id})..."}
            except Exception as e:
                return {"success": False, "error": f"Fallo al abrir Steam: {str(e)}"}

        # 2. Si es una ruta local, buscar el ejecutable principal
        root = Path(install_path_str).resolve()
        if not root.exists():
            return {"success": False, "error": f"La carpeta no existe: {root}"}

        target_exe = cls._find_primary_executable(root)
        if not target_exe:
            return {
                "success": False,
                "error": "No se encontró un archivo ejecutable (.exe) principal en la carpeta del juego."
            }

        try:
            # Ejecutar en segundo plano desacoplado
            subprocess.Popen([str(target_exe)], cwd=str(target_exe.parent))
            return {
                "success": True,
                "message": f"Juego iniciado: {target_exe.name}",
                "exe_path": str(target_exe)
            }
        except Exception as e:
            return {"success": False, "error": f"Error al ejecutar {target_exe.name}: {str(e)}"}

    @classmethod
    def _find_primary_executable(cls, root: Path) -> Optional[Path]:
        """
        Localiza el .exe más probable del juego en la raíz o subcarpetas Binaries/Win64.
        """
        candidates = []
        try:
            # Prioridad 1: Ejecutables en carpetas Binaries/Win64 o x64
            for sub in [root / "Binaries" / "Win64", root / "bin" / "x64", root / "bin"]:
                if sub.exists():
                    for exe in sub.glob("*.exe"):
                        if not any(ex in exe.name.lower() for ex in EXCLUDED_EXE_PATTERNS):
                            candidates.append(exe)

            # Prioridad 2: Ejecutables en la raíz del juego
            for exe in root.glob("*.exe"):
                if not any(ex in exe.name.lower() for ex in EXCLUDED_EXE_PATTERNS):
                    candidates.append(exe)

            if candidates:
                # Elegir el de mayor tamaño (típicamente el binario del juego real)
                candidates.sort(key=lambda x: x.stat().st_size if x.exists() else 0, reverse=True)
                return candidates[0]
        except Exception:
            pass
        return None
