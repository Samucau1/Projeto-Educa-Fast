@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0iniciar-educafast.ps1" %*
exit /b %ERRORLEVEL%
