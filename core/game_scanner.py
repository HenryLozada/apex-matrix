"""
Detector de bibliotecas y carpetas de instalación de juegos de PC.
Rastrea Steam, Epic Games, EA App, GOG Galaxy, Xbox y rutas comunes.
"""

import os
import re
import json
import winreg
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional, Any

@dataclass
class InstalledGameTarget:
    name: str
    platform: str
    install_path: Path
    app_id: Optional[str] = None

class GameScanner:
    def __init__(self):
        self._custom_paths: List[Path] = []

    def add_custom_path(self, path: Path | str):
        p = Path(path).resolve()
        if p.exists() and p not in self._custom_paths:
            self._custom_paths.append(p)

    def scan_all_games(self) -> List[InstalledGameTarget]:
        """Detecta todos los juegos instalados en el sistema."""
        games: List[InstalledGameTarget] = []
        games.extend(self.scan_steam_games())
        games.extend(self.scan_epic_games())
        games.extend(self.scan_gog_games())
        games.extend(self.scan_ea_games())
        games.extend(self.scan_xbox_games())
        games.extend(self.scan_common_game_folders())

        # Desduplicar por ruta de instalación canónica
        seen_paths = set()
        unique_games = []
        for g in games:
            norm_p = str(g.install_path.resolve()).lower()
            if norm_p not in seen_paths and g.install_path.exists():
                seen_paths.add(norm_p)
                unique_games.append(g)

        unique_games.sort(key=lambda x: x.name.lower())
        return unique_games

    def scan_steam_games(self) -> List[InstalledGameTarget]:
        games = []
        # Buscar Steam en el registro
        steam_path = None
        for hkey in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
            for subkey in [r"SOFTWARE\Valve\Steam", r"SOFTWARE\WOW6432Node\Valve\Steam"]:
                try:
                    with winreg.OpenKey(hkey, subkey) as key:
                        val, _ = winreg.QueryValueEx(key, "InstallPath")
                        if val and Path(val).exists():
                            steam_path = Path(val)
                            break
                except Exception:
                    pass
            if steam_path:
                break

        if not steam_path:
            for fallback in [Path(r"C:\Program Files (x86)\Steam"), Path(r"C:\Program Files\Steam")]:
                if fallback.exists():
                    steam_path = fallback
                    break

        if not steam_path:
            return games

        # Parsear libraryfolders.vdf
        vdf_path = steam_path / "steamapps" / "libraryfolders.vdf"
        lib_dirs = [steam_path / "steamapps"]
        if vdf_path.exists():
            try:
                content = vdf_path.read_text(encoding="utf-8", errors="ignore")
                for m in re.finditer(r'"path"\s+"([^"]+)"', content):
                    p = Path(m.group(1).replace(r"\\", "\\")) / "steamapps"
                    if p.exists() and p not in lib_dirs:
                        lib_dirs.append(p)
            except Exception:
                pass

        # Leer appmanifest_*.acf
        for lib in lib_dirs:
            if not lib.exists():
                continue
            for acf in lib.glob("appmanifest_*.acf"):
                try:
                    txt = acf.read_text(encoding="utf-8", errors="ignore")
                    name_match = re.search(r'"name"\s+"([^"]+)"', txt)
                    installdir_match = re.search(r'"installdir"\s+"([^"]+)"', txt)
                    appid_match = re.search(r'"appid"\s+"([^"]+)"', txt)
                    if name_match and installdir_match:
                        name = name_match.group(1).strip()
                        folder = installdir_match.group(1).strip()
                        game_dir = lib / "common" / folder
                        if game_dir.exists():
                            games.append(InstalledGameTarget(
                                name=name,
                                platform="Steam",
                                install_path=game_dir,
                                app_id=appid_match.group(1) if appid_match else None
                            ))
                except Exception:
                    pass
        return games

    def scan_epic_games(self) -> List[InstalledGameTarget]:
        games = []
        prog_data = os.environ.get("PROGRAMDATA", r"C:\ProgramData")
        manifests_dir = Path(prog_data) / "Epic" / "EpicGamesLauncher" / "Data" / "Manifests"
        if manifests_dir.exists():
            for item in manifests_dir.glob("*.item"):
                try:
                    data = json.loads(item.read_text(encoding="utf-8", errors="ignore"))
                    name = data.get("DisplayName", "").strip()
                    install_loc = data.get("InstallLocation", "").strip()
                    app_name = data.get("AppName", "")
                    if name and install_loc and Path(install_loc).exists():
                        games.append(InstalledGameTarget(
                            name=name,
                            platform="Epic Games",
                            install_path=Path(install_loc),
                            app_id=app_name
                        ))
                except Exception:
                    pass
        return games

    def scan_gog_games(self) -> List[InstalledGameTarget]:
        games = []
        reg_path = r"SOFTWARE\GOG.com\Games"
        for hkey in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
            try:
                with winreg.OpenKey(hkey, reg_path) as base_key:
                    num_subkeys = winreg.QueryInfoKey(base_key)[0]
                    for i in range(num_subkeys):
                        sub_name = winreg.EnumKey(base_key, i)
                        with winreg.OpenKey(base_key, sub_name) as sub_key:
                            try:
                                game_name, _ = winreg.QueryValueEx(sub_key, "gameName")
                                path_val, _ = winreg.QueryValueEx(sub_key, "path")
                                if game_name and path_val and Path(path_val).exists():
                                    games.append(InstalledGameTarget(
                                        name=str(game_name),
                                        platform="GOG Galaxy",
                                        install_path=Path(path_val),
                                        app_id=sub_name
                                    ))
                            except Exception:
                                pass
            except Exception:
                pass
        return games

    def scan_ea_games(self) -> List[InstalledGameTarget]:
        games = []
        prog_data = os.environ.get("PROGRAMDATA", r"C:\ProgramData")
        ea_data = Path(prog_data) / "EA Desktop" / "InstallData"
        if ea_data.exists():
            for p in ea_data.iterdir():
                if p.is_dir():
                    clean_name = p.name.replace("_", " ").title()
                    # Buscar en carpetas típicas de EA
                    for root in [Path(r"C:\Program Files\EA Games"), Path(r"C:\Program Files (x86)\Origin Games")]:
                        target = root / p.name
                        if target.exists():
                            games.append(InstalledGameTarget(
                                name=clean_name,
                                platform="EA App",
                                install_path=target
                            ))
        return games

    def scan_xbox_games(self) -> List[InstalledGameTarget]:
        games = []
        for drive in ["C", "D", "E", "F", "G"]:
            xbox_dir = Path(f"{drive}:\\XboxGames")
            if xbox_dir.exists():
                for item in xbox_dir.iterdir():
                    if item.is_dir() and not item.name.startswith("."):
                        clean_name = item.name.replace("-", " ")
                        games.append(InstalledGameTarget(
                            name=clean_name,
                            platform="Xbox Game Pass",
                            install_path=item
                        ))
        return games

    def scan_common_game_folders(self) -> List[InstalledGameTarget]:
        games = []
        check_dirs = [
            Path(r"C:\Games"),
            Path(r"D:\Games"),
            Path(r"E:\Games"),
            *self._custom_paths
        ]
        for cdir in check_dirs:
            if cdir.exists() and cdir.is_dir():
                for sub in cdir.iterdir():
                    if sub.is_dir():
                        games.append(InstalledGameTarget(
                            name=sub.name.replace("_", " "),
                            platform="PC / Custom",
                            install_path=sub
                        ))
        return games
