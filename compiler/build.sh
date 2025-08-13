#!/bin/bash

# -------------------------------
# Dynamically find script & app root
# -------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ROOT="$SCRIPT_DIR/.."    # One level above the script

# -------------------------------
# Configuration
# -------------------------------
ENTRY_POINT="$APP_ROOT/main.py"
DATA_DIR="$APP_ROOT/data"       # Folder(s) to include in the build
OUTPUT_DIR="$APP_ROOT/dist"     # Build output directory

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
nuitka3 --standalone --follow-imports --debug \
    "$ENTRY_POINT" \
    --include-data-dir="$DATA_DIR=data" \
    --output-dir="$DEBUG_DIR"

# -------------------------------
# Build Release Version
# -------------------------------
RELEASE_DIR="$OUTPUT_DIR/release"
mkdir -p "$RELEASE_DIR"
echo "Building release version..."
nuitka3 --standalone --follow-imports --lto --remove-output \
    "$ENTRY_POINT" \
    --include-data-dir="$DATA_DIR=data" \
    --output-dir="$RELEASE_DIR"

# -------------------------------
# Done
# -------------------------------
echo "Build complete!"
echo "Debug build in: $DEBUG_DIR"
echo "Release build in: $RELEASE_DIR"