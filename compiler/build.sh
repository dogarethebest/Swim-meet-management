#!/bin/bash

# -------------------------------
# Dynamically find script & app root
# -------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ROOT="$SCRIPT_DIR/.."    # Adjust if main app folder is one level above

# -------------------------------
# Configuration
# -------------------------------
ENTRY_POINT="$APP_ROOT/main.py"
DATA_DIR="$APP_ROOT/data"       # Folder(s) to include in the build
OUTPUT_DIR="$APP_ROOT/dist"     # Build output directory

# -------------------------------
# Check prerequisites
# -------------------------------
if ! command -v nuitka &> /dev/null; then
    echo "Error: 'nuitka' command not found. Make sure Nuitka is installed and in PATH."
    exit 1
fi

if [ ! -f "$ENTRY_POINT" ]; then
    echo "Error: Entry point $ENTRY_POINT does not exist."
    exit 1
fi

echo "Script Directory: $SCRIPT_DIR"
echo "App Root: $APP_ROOT"
echo "Entry Point: $ENTRY_POINT"
echo "Data Directory: $DATA_DIR"
echo "Output Directory: $OUTPUT_DIR"

# -------------------------------
# Clean old builds
# -------------------------------
echo "Cleaning old build directories..."
rm -rf "$OUTPUT_DIR/debug"
rm -rf "$OUTPUT_DIR/release"

# -------------------------------
# Build Debug Version
# -------------------------------
DEBUG_DIR="$OUTPUT_DIR/debug"
mkdir -p "$DEBUG_DIR"
echo "Building debug version..."
nuitka --standalone --follow-imports --debug \
    "$ENTRY_POINT" \
    --include-data-dir="$DATA_DIR=data" \
    --output-dir="$DEBUG_DIR" &> "$DEBUG_DIR/build.log"

if [ $? -ne 0 ]; then
    echo "Debug build failed. Check $DEBUG_DIR/build.log"
    exit 1
fi

# -------------------------------
# Build Release Version
# -------------------------------
RELEASE_DIR="$OUTPUT_DIR/release"
mkdir -p "$RELEASE_DIR"
echo "Building release version..."
nuitka --standalone --follow-imports --lto --remove-output \
    "$ENTRY_POINT" \
    --include-data-dir="$DATA_DIR=data" \
    --output-dir="$RELEASE_DIR" &> "$RELEASE_DIR/build.log"

if [ $? -ne 0 ]; then
    echo "Release build failed. Check $RELEASE_DIR/build.log"
    exit 1
fi

# -------------------------------
# Done
# -------------------------------
echo "Build complete!"
echo "Debug build in: $DEBUG_DIR"
echo "Release build in: $RELEASE_DIR"
