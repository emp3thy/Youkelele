#!/bin/sh
# Makes a ukulele sheet from a YouTube link or an audio file on macOS or Linux:
#   ./run-youkelele.sh                (asks for a link)
#   ./run-youkelele.sh song.mp3
# Mirrors run-youkelele.cmd (the Windows script). Written to match it but untested
# here: the project is developed and checked on Windows. The sheet opens as a PDF
# and is kept in the runs folder beside this file, under the song's name.

# a file given as a relative path: make it absolute before moving
input=${1:-}
if [ -n "$input" ] && [ -f "$input" ]; then
    input="$(cd "$(dirname "$input")" && pwd)/$(basename "$input")"
fi

cd "$(dirname "$0")" || exit 1
here=$(pwd)
runs="$here/runs"

if ! command -v uv >/dev/null 2>&1 && [ -x "$HOME/.local/bin/uv" ]; then
    PATH="$HOME/.local/bin:$PATH"
    export PATH
fi

while [ -z "$input" ]; do
    printf '\nPaste a YouTube link and press Enter:\n> '
    IFS= read -r input || exit 1
    # a link pasted with quotes around it: drop them
    input=$(printf '%s' "$input" | tr -d "\"'")
done

# a marker older than anything this run writes, to tell its folder from earlier ones
mkdir -p "$runs"
marker=$(mktemp "$runs/.started.XXXXXX") || exit 1
trap 'rm -f "$marker"' EXIT

pause() {
    printf 'Press Enter to close.'
    read -r _ || true
}

echo ""
echo "Making the sheet. The first song takes longer while the models download."
echo ""
if uv run youkelele run "$input" --runs-dir "$runs"; then
    # the newest runs/*/08_render/sheet.pdf is the one this run wrote
    pdf=$(ls -t "$runs"/*/08_render/sheet.pdf 2>/dev/null | head -n 1)
    if [ -z "$pdf" ]; then
        echo ""
        echo "The run finished but no sheet.pdf was found in: $runs"
        echo "Send the text above to the person who gave you this tool."
        pause
        exit 1
    fi
    echo ""
    echo "The sheet is ready:"
    echo "  $pdf"
    if [ "$(uname)" = "Darwin" ]; then
        open "$pdf"
    else
        xdg-open "$pdf" >/dev/null 2>&1 &
    fi
    exit 0
fi

folder=$(find "$runs" -mindepth 2 -maxdepth 2 -name manifest.json -newer "$marker" 2>/dev/null | head -n 1)
echo ""
echo "Something went wrong. Send the text above to the person who gave you this tool."
if [ -n "$folder" ]; then
    echo "Send them this run's folder too, zipped:"
    echo "  $(dirname "$folder")"
else
    echo "No folder was made for this song. The runs are kept in:"
    echo "  $runs"
fi
pause
exit 1
