# APEX MATRIX // DLSS Swapper & ShaderPurge ⚡

Suite de optimización para PC con arquitectura de diseño **NVIDIA Power Green**, creada para:
1. **DLSS & AI Upscaling Matrix**: Detectar, diagnosticar, actualizar y reemplazar de forma segura (swapping) librerías DLL de **NVIDIA DLSS Super Resolution**, **Frame Generation**, **Ray Reconstruction**, **AMD FidelityFX FSR** e **Intel XeSS** en todos tus juegos instalados de Steam, Epic Games, EA App, GOG y Xbox Game Pass.
2. **ShaderPurge & Storage Reclaim**: Localizar y purgar gigabytes de caché de shaders de GPU (`NVIDIA DXCache`, `NVIDIA GLCache`, `DirectX D3DSCache`, `CrashDumps`), eliminando tirones (*stuttering*) provocados por shaders desactualizados y recuperando valioso espacio en discos SSD.
3. **GPU Hardware Telemetry**: Monitoreo de modelo de tarjeta gráfica, versión de controlador comercial de NVIDIA, estado de VRAM y contador histórico de espacio liberado.

---

## 🚀 Características Principales

### 1. Swapper de Tecnologías de Escalado por IA
- **Detección Automática Multi-Plataforma**: Localiza las librerías dinámicas dentro de las carpetas de instalación de tus juegos:
  - `nvngx_dlss.dll` (NVIDIA DLSS 2 / 3 Super Resolution)
  - `nvngx_dlssg.dll` (NVIDIA DLSS 3 Frame Generation)
  - `nvngx_dlssd.dll` (NVIDIA DLSS 3.5 Ray Reconstruction)
  - `libxess.dll` (Intel XeSS)
  - `amd_fidelityfx_*.dll` (AMD FSR 2/3)
- **Lector Nativo Win32**: Extrae la versión exacta de compilación (ej. `v3.7.10.0`) directamente desde los recursos PE sin herramientas externas.
- **Copias de Seguridad Inmutables (`.bak`)**: Antes de actualizar cualquier DLL, se genera automáticamente una copia `.bak` del archivo original.
- **Reversión en 1 Clic**: Restaura instantáneamente la versión oficial de fábrica si un juego experimenta incompatibilidad.
- **Bóveda Local de Versiones (`library/`)**: Almacén centralizado donde puedes importar y conservar versiones oficiales de DLLs para inyectar en cualquier juego.

### 2. Purgador Inteligente de Shaders (ShaderPurge)
- **Cachés Analizadas:**
  - `NVIDIA DirectX Cache` (`%LOCALAPPDATA%\NVIDIA\DXCache`)
  - `NVIDIA OpenGL/Vulkan Cache` (`%LOCALAPPDATA%\NVIDIA\GLCache`)
  - `DirectX D3DSCache` (`%LOCALAPPDATA%\D3DSCache`)
  - `DirectX Shader Temp` (`%LOCALAPPDATA%\Temp\DirectXShaderCache`)
  - `Windows Crash Dumps` (`%LOCALAPPDATA%\CrashDumps`)
- **Tolerancia a Bloqueos en Caliente**: Si un juego o proceso del sistema tiene un archivo de shader en uso, el limpiador lo omite con seguridad sin generar errores ni interrumpir la sesión gráfica.
- **Métricas Históricas**: Registra el volumen acumulado de almacenamiento recuperado.

---

## 🎨 Sistema de Diseño NVIDIA Power Green
- **Fondo:** Negro absoluto (`#000000`) y superficies oscuras (`#1a1a1a`).
- **Acentos:** Verde NVIDIA puro (`#76b900`) y verde neón (`#bff230`).
- **Geometría:** Esquinas afiladas de ingeniería (`border-radius: 2px`).
- **Iconografía:** Microchips de silicio vectorial y simbología de hardware.

---

## 💻 Ejecución y Compilación

### Requisitos:
- Windows 10 o Windows 11 (64-bit)
- Python 3.10+
- `pip install pywebview`

### Ejecución Directa:
Doble clic en **`Ejecutar_ApexMatrix.bat`** o en terminal:
```powershell
python main.py
```

### Ejecutar Pruebas Automatizadas:
```powershell
python -m unittest discover -s tests -v
```

### Compilar a Ejecutable (.exe):
```powershell
python build.py
```
El ejecutable compilado se generará en:
`dist/ApexMatrix/ApexMatrix.exe`

---

## 🛡️ Licencia
Distribuido bajo licencia MIT. Desarrollado con ❤️ para la comunidad de gaming en PC.
