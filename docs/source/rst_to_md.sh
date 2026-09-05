#!/usr/bin/env bash
# Convert all .rst files in source/ to .md
set -e
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

if command -v pandoc &> /dev/null; then
    for f in *.rst; do
        base="${f%.rst}"
        pandoc "$f" -f rst -t markdown_strict -o "$base.md"
        echo "Converted $f -> $base.md"
    done
else
    echo "pandoc not found."
fi
