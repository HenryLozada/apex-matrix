"""
Gestor de reemplazo seguro (swapping) y reversión de librerías DLL de escalado.
Asegura la preservación del archivo original mediante copias .bak inmutables.
"""

import shutil
from pathlib import Path
from typing import Dict, Any, List
from core.dll_version import Win32VersionReader

class DllSwapper:
    def __init__(self, library_dir: Path | str = None):
        if library_dir:
            self.library_dir = Path(library_dir)
        else:
            self.library_dir = Path(__file__).resolve().parent.parent / "library"
        self.library_dir.mkdir(parents=True, exist_ok=True)

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
            # Restaurar el archivo original
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
        dest_name = f"{src.stem}_{meta['version']}.dll" if meta["version"] != "Desconocida" else src.name
        dest = self.library_dir / dest_name

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
