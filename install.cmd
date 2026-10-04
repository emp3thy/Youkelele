@echo off
rem Double-click to install youkelele. The work is done by install.ps1, run with the
rem execution policy bypassed for this one process only. The UTF-8 code page keeps the
rem tools' progress output readable in this window.
chcp 65001 >nul
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
set "YK_CODE=%errorlevel%"
pause
exit /b %YK_CODE%
