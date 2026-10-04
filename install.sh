#!/bin/sh
# Installs everything youkelele needs on macOS or Linux, for someone who does not code.
# Mirrors install.ps1 (the Windows script). Written to match it but untested here:
# the project is developed and checked on Windows. Safe to run again: each step
# checks first and installs only what is missing.
#
# On Linux, Chromium may also need system libraries; if the PDF step fails, run
#   uv run playwright install-deps chromium
# (it asks for your password).

cd "$(dirname "$0")" || exit 1

UV_BIN="$HOME/.local/bin"
LOG=$(mktemp) || exit 1
CODE=$(mktemp) || exit 1
trap 'rm -f "$LOG" "$CODE"' EXIT
STEP="starting"

fail() {
    echo ""
    echo "Something went wrong at step: $STEP"
    if [ -s "$LOG" ]; then
        echo "The last lines it printed were:"
        tail -n 20 "$LOG" | sed 's/^/    /'
    fi
    echo ""
    echo "Send the text above to the person who gave you this tool"
    exit 1
}

# run a command, showing its output and keeping it for the failure message
run_step() {
    { "$@" 2>&1; echo $? >"$CODE"; } | tee "$LOG" | sed 's/^/    /'
    [ "$(cat "$CODE")" = "0" ] || fail
}

# true when the check command succeeds; its output is not shown
present() {
    "$@" >/dev/null 2>&1
}

STEP="[1/4] Installing uv"
echo "$STEP"
if command -v uv >/dev/null 2>&1; then
    echo "    already present"
elif [ -x "$UV_BIN/uv" ]; then
    PATH="$UV_BIN:$PATH"
    export PATH
    echo "    already present"
else
    command -v curl >/dev/null 2>&1 || { echo "curl is needed to install uv" >"$LOG"; fail; }
    run_step sh -c 'curl -LsSf https://astral.sh/uv/install.sh | sh'
    PATH="$UV_BIN:$PATH"
    export PATH
    command -v uv >/dev/null 2>&1 || { echo "uv was installed but cannot be found in $UV_BIN" >"$LOG"; fail; }
    echo "    done"
fi

STEP="[2/4] Installing the tool"
echo "$STEP"
# always run: it is quick when everything is already there, and it brings Python 3.12
run_step uv sync
echo "    done"

STEP="[3/4] Fetching the models"
echo "$STEP"
# always run: setup checks what it has and downloads only what is missing (the
# Windows script's ffmpeg check looks for .exe names, so it is not reused here)
run_step uv run youkelele setup
echo "    done"

STEP="[4/4] Installing the PDF printer"
echo "$STEP"
if present uv run python -c "import sys; from youkelele.preflight import default_probes; sys.exit(0 if default_probes().chromium_state() == 'present' else 1)"; then
    echo "    already present"
else
    run_step uv run playwright install chromium
    echo "    done"
fi

echo ""
echo "Ready. Run ./run-youkelele.sh to make a sheet."
