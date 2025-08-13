#!/bin/bash

# CONFIG
ENTRY_POINT="main.py"           # Your main Python file
OUTPUT_DIR="dist"               # Base output folder
DATA_DIRS=("data" "config")     # Folders to keep unchanged

# STEP 1 — Increment build_id
echo "Incrementing build ID..."
python3 << 'EOF'
import re
from pathlib import Path

ver_file = Path("version.py")
text = ver_file.read_text()
new_text = re.sub(
    r"(build_id\s*=\s*)(\d+)",
    lambda m: f"{m.group(1)}{int(m.group(2))+1}",
    text
)
ver_file.write_text(new_text)
print("Updated:", ver_file.read_text().strip())
EOF

# STEP 2 — Clean old build
echo "Cleaning old build..."
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

# STEP 3 — Compile Debug Version
DEBUG_DIR="$OUTPUT_DIR/debug"
echo "Building debug version..."
mkdir -p "$DEBUG_DIR"
nuitka3 --standalone --follow-imports --debug \
    "$ENTRY_POINT" \
    $(for dir in "${DATA_DIRS[@]}"; do echo --include-data-dir="$dir=$dir"; done) \
    --output-dir="$DEBUG_DIR"

# STEP 4 — Compile Release Version
RELEASE_DIR="$OUTPUT_DIR/release"
echo "Building release version..."
mkdir -p "$RELEASE_DIR"
nuitka3 --standalone --follow-imports --lto --remove-output \
    "$ENTRY_POINT" \
    $(for dir in "${DATA_DIRS[@]}"; do echo --include-data-dir="$dir=$dir"; done) \
    --output-dir="$RELEASE_DIR"

# STEP 5 — Done
echo "Build complete!"
echo "Debug build in: $DEBUG_DIR"
echo "Release build in: $RELEASE_DIR"