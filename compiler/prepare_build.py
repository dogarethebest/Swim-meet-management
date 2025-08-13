#!/usr/bin/env python3
import os
import stat
import json
from pathlib import Path
import shutil

# CONFIG
from pathlib import Path

# Get the directory where this script is located
script_dir = Path(__file__).parent.resolve()

# Paths relative to the script location
build_sh_path = (script_dir / "build.sh").resolve()
version_json_path = (script_dir / "../program_File/app_resources/build_info.json").resolve()
cleanup_config_file = (script_dir / "build_dirs.txt").resolve()

print(f"build.sh path: {build_sh_path}")
print(f"version JSON path: {version_json_path}")
print(f"cleanup config path: {cleanup_config_file}")
# STEP 1 — Make build.sh executable
if build_sh_path.exists():
    st = os.stat(build_sh_path)
    os.chmod(build_sh_path, st.st_mode | stat.S_IEXEC)
    print(f"{build_sh_path} is now executable.")
else:
    print(f"Error: {build_sh_path} does not exist.")

# STEP 2 — Load version JSON and increment build_id
if version_json_path.exists():
    with open(version_json_path, "r") as f:
        version_data = json.load(f)
else:
    print(f"Error: {version_json_path} does not exist.")
    version_data = {}

if "build_id" in version_data and isinstance(version_data["build_id"], int):
    version_data["build_id"] += 1
else:
    version_data["build_id"] = 1

version_data["build_ID."] = f"build_{version_data['build_id']}"

with open(version_json_path, "w") as f:
    json.dump(version_data, f, indent=4)

print(f"Updated version JSON: {version_json_path}")
print(json.dumps(version_data, indent=4))

# STEP 3 — Read cleanup paths from text file
if cleanup_config_file.exists():
    with open(cleanup_config_file, "r") as f:
        cleanup_paths = [line.strip() for line in f.readlines()
                         if line.strip() and not line.startswith("#")]
else:
    print(f"Error: {cleanup_config_file} does not exist.")
    cleanup_paths = []

# STEP 4 — Clean paths (files or directories)
for p in cleanup_paths:
    path = Path(p).resolve()  # Absolute path, handles ../
    if path.exists():
        if path.is_dir():
            shutil.rmtree(path)
            print(f"Deleted directory: {path}")
        elif path.is_file():
            path.unlink()
            print(f"Deleted file: {path}")
        else:
            print(f"Skipping unknown type: {path}")
    else:
        print(f"Path does not exist, skipping: {path}")

print("Pre-build cleanup complete.")

import subprocess
import sys
from pathlib import Path

# Path to build.sh (adjust if needed)
script_dir = Path(__file__).parent.resolve()
build_sh_path = script_dir / "build.sh"

# Make sure build.sh exists
if build_sh_path.exists():
    print(f"Running {build_sh_path}...")
    result = subprocess.run(["/bin/bash", str(build_sh_path)])
    if result.returncode != 0:
        print("build.sh failed!")
        sys.exit(result.returncode)
    print("build.sh finished successfully.")
else:
    print(f"{build_sh_path} not found. Skipping build.sh execution.")
