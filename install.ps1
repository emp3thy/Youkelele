# Installs everything youkelele needs, for someone who does not code.
# Run it through install.cmd (a double-click). Safe to run again: each step
# checks first and installs only what is missing.
#
# Nothing is assumed to be installed except Windows 10 or 11 and an internet
# connection: uv brings its own Python 3.12, setup fetches the chord model as a
# zip (no git) and ffmpeg, and Playwright fetches Chromium for the PDF.

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

# The tools print UTF-8; read it as such (install.cmd also sets the code page), and keep
# uv's progress bars out of the window, where each redraw would print as a new line.
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }
$env:UV_NO_PROGRESS = "1"
$env:NO_COLOR = "1"

$script:Step = "starting"
$UvBin = Join-Path $env:USERPROFILE ".local\bin"

function Stop-WithHelp([string[]]$Lines) {
    Write-Host ""
    Write-Host "Something went wrong at step: $script:Step"
    if ($Lines -and $Lines.Count -gt 0) {
        Write-Host "The last lines it printed were:"
        $Lines | Select-Object -Last 20 | ForEach-Object { Write-Host "    $_" }
    }
    Write-Host ""
    Write-Host "Send the text above to the person who gave you this tool"
    exit 1
}

# Runs a native command (in a script block whose command merges stderr with 2>&1),
# showing its output as it goes unless -Silent and keeping it in $script:Output for
# the failure message. Returns its exit code; -1 if it never ran.
function Invoke-Native([scriptblock]$Command, [switch]$Silent) {
    $script:Output = New-Object System.Collections.Generic.List[string]
    # native programs write progress to stderr; under "Stop" PowerShell 5.1 would
    # treat the first such line as a fatal error
    $ErrorActionPreference = "Continue"
    $global:LASTEXITCODE = -1
    & $Command | ForEach-Object {
        # colour codes (when FORCE_COLOR is set) would print as stray characters here
        $line = "$_" -replace "\x1b\[[0-9;]*[A-Za-z]", ""
        if (-not $Silent) { Write-Host "    $line" }
        $script:Output.Add($line)
    }
    $code = $global:LASTEXITCODE
    $ErrorActionPreference = "Stop"
    return $code
}

function Invoke-Step([scriptblock]$Command) {
    $code = Invoke-Native $Command
    if ($code -ne 0) {
        $script:Output.Add("(exit code $code)")
        Stop-WithHelp $script:Output
    }
}

# True when the check command succeeds; its output is not shown.
function Test-Present([scriptblock]$Command) {
    return ((Invoke-Native $Command -Silent) -eq 0)
}

try {
    $script:Step = "[1/4] Installing uv"
    Write-Host $script:Step
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        Write-Host "    already present"
    } elseif (Test-Path -LiteralPath (Join-Path $UvBin "uv.exe")) {
        $env:Path = "$UvBin;$env:Path"
        Write-Host "    already present"
    } else {
        # the official installer, in its own process so its own exit cannot end this script;
        # TLS 1.2 is switched on for older Windows 10 builds
        Invoke-Step { powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor 3072; irm https://astral.sh/uv/install.ps1 | iex" 2>&1 }
        $env:Path = "$UvBin;$env:Path"
        if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
            Stop-WithHelp @("uv was installed but cannot be found in $UvBin")
        }
        Write-Host "    done"
    }

    $script:Step = "[2/4] Installing the tool"
    Write-Host $script:Step
    # always run: it is quick when everything is already there, and it brings Python 3.12
    Invoke-Step { uv sync 2>&1 }
    Write-Host "    done"

    $script:Step = "[3/4] Fetching the models"
    Write-Host $script:Step
    if (Test-Present { uv run python -c "import sys; from youkelele.preflight import default_probes; p = default_probes(); sys.exit(0 if p.ffmpeg_dir() and p.chord_model_present() else 1)" 2>&1 }) {
        Write-Host "    already present"
    } else {
        Invoke-Step { uv run youkelele setup 2>&1 }
        Write-Host "    done"
    }

    $script:Step = "[4/4] Installing the PDF printer"
    Write-Host $script:Step
    if (Test-Present { uv run python -c "import sys; from youkelele.preflight import default_probes; sys.exit(0 if default_probes().chromium_state() == 'present' else 1)" 2>&1 }) {
        Write-Host "    already present"
    } else {
        Invoke-Step { uv run playwright install chromium 2>&1 }
        Write-Host "    done"
    }
} catch {
    Stop-WithHelp @("$_")
}

Write-Host ""
Write-Host "Ready. Double-click run-youkelele.cmd to make a sheet."
exit 0
