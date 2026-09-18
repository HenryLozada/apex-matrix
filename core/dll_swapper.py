"""
Gestor de reemplazo seguro (swapping) y reversión de librerías DLL de escalado.
Asegura la preservación del archivo original mediante copias .bak inmutables
y verificación estricta de compatibilidad de familias de librerías (DLSS / FSR / XeSS).
"""

import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from core.dll_version import Win32VersionReader

class DllSwapper:
    def __init__(self, library_dir: Path | str = None):
        if library_dir:
            self.library_dir = Path(library_dir)
        else:
            self.library_dir = Path(__file__).resolve().parent.parent / "library"
        self.library_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def is_compatible_replacement(target_filename: str, vault_filename: str) -> bool:
        """
        Determina si una versión de la bóveda es compatible con la DLL objetivo del juego
        para evitar mezclar tecnologías incompatibles (ej. DLSS en FSR o FrameGen en Upscaler).
        """
        t = target_filename.lower()
        v = vault_filename.lower()

        # 1. NVIDIA DLSS Frame Generation
        if "dlssg" in t:
            return "dlssg" in v
        # 2. NVIDIA DLSS Ray Reconstruction
        if "dlssd" in t:
            return "dlssd" in v
        # 3. NVIDIA DLSS Super Resolution
        if "dlss" in t and "dlssg" not in t and "dlssd" not in t:
            return "dlss" in v and "dlssg" not in v and "dlssd" not in v
        # 4. Intel XeSS
        if "xess" in t:
            return "xess" in v
        # 5. AMD Frame Generation
        if "framegeneration" in t:
            return "framegeneration" in v
        # 6. AMD Upscaler
        if "upscaler" in t:
            return "upscaler" in v
        # 7. AMD FidelityFX genérico / DX12 loader
        if "fidelityfx" in t or "fsr" in t:
            return ("fidelityfx" in v or "fsr" in v) and "framegeneration" not in v and "upscaler" not in v

        return False

    def get_library_versions(self) -> List[Dict[str, Any]]:
        """
        Escanea la bóveda local de DLLs y lista todas las versiones disponibles para swapping.
        """
        results = []
        if not self.library_dir.exists():
            return results

        for p in self.library_dir.glob("*.dll"):
            meta = Win32VersionReader.get_dll_metadata(p)
            name_lower = p.name.lower()
            tech = "dlss_sr"
            if "dlssg" in name_lower:
                tech = "dlss_fg"
            elif "dlssd" in name_lower:
                tech = "dlss_rr"
            elif "xess" in name_lower:
                tech = "xess"
            elif "fidelityfx" in name_lower or "fsr" in name_lower:
                tech = "fsr"

            results.append({
                "filename": p.name,
                "tech_type": tech,
                "version": meta["version"],
                "size_str": meta["size_str"],
                "path": str(p),
                "modified": meta["modified"]
            })

        results.sort(key=lambda x: x["version"], reverse=True)
        return results

    def swap_dll(self, target_dll_path: str, replacement_dll_path: str) -> Dict[str, Any]:
        """
        Reemplaza la DLL en el juego seleccionado por la nueva versión,
        creando automáticamente una copia de seguridad original (.bak).
        """
        target = Path(target_dll_path).resolve()
        replacement = Path(replacement_dll_path).resolve()

        if not target.exists():
            return {"success": False, "error": f"No se encontró la DLL objetivo en {target}"}
        if not replacement.exists():
            return {"success": False, "error": f"No se encontró la DLL de reemplazo en {replacement}"}

        # Verificación de seguridad de compatibilidad
        if not self.is_compatible_replacement(target.name, replacement.name):
            return {
                "success": False,
                "error": f"Incompatibilidad detectada: No se puede reemplazar '{target.name}' con '{replacement.name}'. Las librerías deben pertenecer a la misma tecnología y familia."
            }

        try:
            # 1. Crear copia de respaldo inmutable .bak si aún no existe
            backup_file = target.with_suffix(".dll.bak")
            if not backup_file.exists():
                shutil.copy2(target, backup_file)

            # Metadata previa
            old_meta = Win32VersionReader.get_dll_metadata(target)

            # 2. Reemplazar archivo
            shutil.copy2(replacement, target)

            # Metadata nueva
            new_meta = Win32VersionReader.get_dll_metadata(target)

            return {
                "success": True,
                "message": f"DLL actualizada con éxito a v{new_meta['version']}",
                "old_version": old_meta["version"],
                "new_version": new_meta["version"],
                "target_path": str(target),
                "backup_path": str(backup_file)
            }
        except PermissionError:
            return {
                "success": False,
                "error": "Permiso denegado. Asegúrate de que el juego no se esté ejecutando en este momento."
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def restore_dll(self, target_dll_path: str) -> Dict[str, Any]:
        """
        Restaura la DLL original del juego desde su archivo .bak.
        """
        target = Path(target_dll_path).resolve()
        backup_file = target.with_suffix(".dll.bak")

        if not backup_file.exists():
            return {"success": False, "error": "No existe copia de seguridad (.bak) para este archivo."}

        try:
            shutil.copy2(backup_file, target)
            meta = Win32VersionReader.get_dll_metadata(target)

            return {
                "success": True,
                "message": f"DLL restaurada exitosamente a la versión original v{meta['version']}",
                "restored_version": meta["version"],
                "target_path": str(target)
            }
        except PermissionError:
            return {
                "success": False,
                "error": "Permiso denegado. Cierra el juego antes de revertir la DLL."
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def import_dll(self, source_path: str) -> Dict[str, Any]:
        """
        Importa una DLL descargada por el usuario hacia la bóveda library/ de la app.
        """
        src = Path(source_path).resolve()
        if not src.exists() or not src.is_file():
            return {"success": False, "error": "El archivo especificado no existe."}

        meta = Win32VersionReader.get_dll_metadata(src)
        dest = self.library_dir / src.name

        try:
            shutil.copy2(src, dest)
            return {
                "success": True,
                "message": f"Librería importada a la bóveda: {dest.name}",
                "version": meta["version"],
                "destination": str(dest)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def swap_all_in_game(self, game_install_path: str) -> Dict[str, Any]:
        """
        Actualiza todas las DLLs de escalado en el juego utilizando la versión más reciente
        compatible en la bóveda para cada familia de librería correspondiente.
        """
        from core.dll_detector import DllDetector
        from core.game_scanner import InstalledGameTarget

        root = Path(game_install_path).resolve()
        if not root.exists() or not root.is_dir():
            return {"success": False, "error": f"Directorio no encontrado: {root}"}

        vault_versions = self.get_library_versions()
        if not vault_versions:
            return {"success": False, "error": "No hay librerías en la bóveda. Descárgalas desde el CATÁLOGO primero."}

        game_target = InstalledGameTarget(name=root.name, platform="Custom", install_path=root)
        scan = DllDetector.scan_game_upscalers(game_target)
        dlls = scan.get("dlls", [])

        if not dlls:
            return {"success": False, "error": "No se encontraron DLLs de escalado en este juego."}

        updated_count = 0
        skipped_count = 0
        details = []

        for item in dlls:
            # Encontrar la mejor versión compatible en la bóveda para este archivo específico
            matching_vault = [
                v for v in vault_versions
                if self.is_compatible_replacement(item["filename"], v["filename"])
            ]
            if not matching_vault:
                skipped_count += 1
                details.append({
                    "filename": item["filename"],
                    "status": "omitido",
                    "reason": f"No hay versión compatible para '{item['filename']}' en la bóveda"
                })
                continue

            replacement_info = matching_vault[0]
            res = self.swap_dll(item["full_path"], replacement_info["path"])
            if res.get("success"):
                updated_count += 1
                details.append({
                    "filename": item["filename"],
                    "status": "actualizado",
                    "old_version": res.get("old_version"),
                    "new_version": res.get("new_version")
                })
            else:
                details.append({
                    "filename": item["filename"],
                    "status": "error",
                    "error": res.get("error")
                })

        return {
            "success": updated_count > 0,
            "updated_count": updated_count,
            "skipped_count": skipped_count,
            "details": details,
            "message": f"Actualización por lotes finalizada: {updated_count} archivo(s) actualizados."
        }

    def restore_all_in_game(self, game_install_path: str) -> Dict[str, Any]:
        """
        Restaura todas las copias de seguridad (.bak) encontradas en el juego a su estado original.
        """
        root = Path(game_install_path).resolve()
        if not root.exists() or not root.is_dir():
            return {"success": False, "error": f"Directorio no encontrado: {root}"}

        restored_count = 0
        details = []

        try:
            for bak in root.rglob("*.dll.bak"):
                target_dll = bak.parent / bak.name[:-4]
                res = self.restore_dll(str(target_dll))
                if res.get("success"):
                    restored_count += 1
                    details.append({
                        "filename": target_dll.name,
                        "status": "restaurado",
                        "version": res.get("restored_version")
                    })
                else:
                    details.append({
                        "filename": target_dll.name,
                        "status": "error",
                        "error": res.get("error")
                    })
        except Exception as e:
            return {"success": False, "error": str(e)}

        if restored_count == 0:
            return {"success": False, "error": "No se encontraron copias de seguridad (.bak) para revertir."}

        return {
            "success": True,
            "restored_count": restored_count,
            "details": details,
            "message": f"Reversión completada: {restored_count} archivo(s) restaurados al original."
        }

    def download_official_dlss(self) -> Dict[str, Any]:
        """
        Descarga automáticamente la última versión oficial de nvngx_dlss.dll
        directamente desde el repositorio oficial del SDK de NVIDIA en GitHub.
        """
        import urllib.request
        url = "https://raw.githubusercontent.com/NVIDIA/DLSS/main/lib/Windows_x86_64/rel/nvngx_dlss.dll"
        temp_dest = self.library_dir / "nvngx_dlss_downloading.tmp"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ApexMatrix-NVIDIA-Downloader/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp, open(temp_dest, "wb") as f:
                f.write(resp.read())

            meta = Win32VersionReader.get_dll_metadata(temp_dest)
            ver = meta.get("version", "latest")
            final_name = f"nvngx_dlss_v{ver}.dll"
            final_dest = self.library_dir / final_name

            if temp_dest.exists():
                if final_dest.exists():
                    final_dest.unlink()
                temp_dest.rename(final_dest)

            return {
                "success": True,
                "message": f"Última versión oficial de NVIDIA descargada: {final_name} (v{ver})",
                "version": ver,
                "filename": final_name,
                "path": str(final_dest)
            }
        except Exception as e:
            if temp_dest.exists():
                temp_dest.unlink()
            return {"success": False, "error": f"Error descargando desde NVIDIA: {str(e)}"}
