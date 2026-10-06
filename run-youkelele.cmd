@echo off
rem Double-click to make a ukulele sheet from a YouTube link, or drop an audio file
rem on this file. The sheet opens as a PDF when it is done and is kept in the runs
rem folder beside this file, under the song's name.
setlocal

rem A dropped file arrives as the first argument: make its path absolute before moving.
rem Anything else is a link, taken from the whole argument line because cmd splits an
rem argument at = (watch?v=...); quotes around it are dropped as for a pasted link.
set "YK_SOURCE="
if "%~1"=="" goto source_done
if exist "%~1" goto source_file
set YK_ARGS=%*
set "YK_SOURCE=%YK_ARGS:"=%"
goto source_done
:source_file
set "YK_SOURCE=%~f1"
:source_done

cd /d "%~dp0"
set "YK_RUNS=%~dp0runs"

set "YK_UV=uv"
where uv >nul 2>nul
if errorlevel 1 set "YK_UV=%USERPROFILE%\.local\bin\uv.exe"
if "%YK_UV%"=="uv" goto have_uv
if exist "%YK_UV%" goto have_uv
echo.
echo uv was not found. Run install.cmd first.
pause
exit /b 1
:have_uv

if defined YK_SOURCE goto have_source
:ask
echo.
echo Paste a YouTube link and press Enter:
set "YK_SOURCE="
set /p "YK_SOURCE=> "
if not defined YK_SOURCE goto ask
rem a link pasted with quotes around it: drop them (links may hold & so stay quoted)
set "YK_SOURCE=%YK_SOURCE:"=%"
if not defined YK_SOURCE goto ask
:have_source

rem the time before the run, to tell this run's folder from earlier ones
for /f "usebackq delims=" %%t in (`powershell -NoProfile -Command "[DateTime]::UtcNow.Ticks"`) do set "YK_SINCE=%%t"

echo.
echo Making the sheet. The first song takes longer while the models download.
echo.
"%YK_UV%" run youkelele run "%YK_SOURCE%" --runs-dir "%YK_RUNS%"
if errorlevel 1 goto failed

rem the newest runs\*\08_render\sheet.pdf written since the run began is this run's
set "YK_PDF="
for /f "usebackq delims=" %%p in (`powershell -NoProfile -Command "Get-ChildItem -LiteralPath $env:YK_RUNS -Directory -ErrorAction SilentlyContinue | ForEach-Object { Get-Item -LiteralPath (Join-Path $_.FullName '08_render\sheet.pdf') -ErrorAction SilentlyContinue } | Where-Object { $_.LastWriteTimeUtc.Ticks -ge [long]$env:YK_SINCE } | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1 -ExpandProperty FullName"`) do set "YK_PDF=%%p"
if not defined YK_PDF goto no_pdf
echo.
echo The sheet is ready:
echo   "%YK_PDF%"
start "" "%YK_PDF%"
exit /b 0

:no_pdf
echo.
echo The run finished but no sheet.pdf was found in:
echo   "%YK_RUNS%"
echo Send the text above to the person who gave you this tool.
pause
exit /b 1

:failed
set "YK_FOLDER="
for /f "usebackq delims=" %%d in (`powershell -NoProfile -Command "Get-ChildItem -LiteralPath $env:YK_RUNS -Directory -ErrorAction SilentlyContinue | ForEach-Object { Get-Item -LiteralPath (Join-Path $_.FullName 'manifest.json') -ErrorAction SilentlyContinue } | Where-Object { $_.LastWriteTimeUtc.Ticks -ge [long]$env:YK_SINCE } | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1 -ExpandProperty DirectoryName"`) do set "YK_FOLDER=%%d"
echo.
echo Something went wrong. Send the text above to the person who gave you this tool.
if defined YK_FOLDER (
    echo Send them this run's folder too, zipped:
    echo   "%YK_FOLDER%"
) else (
    echo No folder was made for this song. The runs are kept in:
    echo   "%YK_RUNS%"
)
pause
exit /b 1
