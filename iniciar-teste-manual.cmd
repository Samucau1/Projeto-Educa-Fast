@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0iniciar-educafast.ps1" %*
set "manual_result=%ERRORLEVEL%"
echo.
if not "%manual_result%"=="0" echo O teste manual nao iniciou. Confira a mensagem acima.
pause
exit /b %manual_result%
