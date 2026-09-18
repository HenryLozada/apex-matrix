@echo off
title APEX MATRIX - DLSS Swapper & ShaderPurge
cd /d "%~dp0"
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Ocurrio un error al ejecutar ApexMatrix. Presiona una tecla para salir.
    pause >nul
)
