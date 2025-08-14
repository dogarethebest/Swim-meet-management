#!/usr/bin/env python3
import json
import subprocess
import shutil
from pathlib import Path
import sys
import tempfile
import psutil

def install_pyinstaller():
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

def clean_previous_builds(build_paths):
    """Remove old build artifacts."""
    for path in build_paths:
        if path.exists():
            print(f"Cleaning {path}...")
            shutil.rmtree(path, ignore_errors=True)

def collect_assets(project_dir):
    """Collect all non-Python files as assets."""
    assets = []
    for file in project_dir.rglob("*"):
        if file.is_file() and file.suffix != ".py":
            relative_path = file.relative_to(project_dir)
            dest = relative_path.parent or Path(".")
            assets.append(f"{file}:{dest}")
    return assets

def estimate_ram_required(project_dir):
    """Estimate RAM needed to compile project."""
    total_size = sum(f.stat().st_size for f in project_dir.rglob("*") if f.is_file())
    safety_multiplier = 2  # double the project size as buffer
    return total_size * safety_multiplier

def main():
    # Load build configuration
    script_dir = Path(__file__).parent.resolve()
    config_file = script_dir.parent / "program_File" / "app_resources" / "build_info.json"

    if not config_file.exists():
        print(f"Missing build configuration: {config_file}")
        sys.exit(1)

    with open(config_file) as f:
        config = json.load(f)

    # Paths
    project_dir = Path(config.get("project_dir", ".")).resolve()
    build_dir = Path(config.get("build_dir", "dist")).resolve()
    binary_name = config.get("binary_name", "app")
    main_script = project_dir / config.get("main_script", "entry.py")

    if not main_script.exists():
        print(f"Main script {main_script} not found!")
        sys.exit(1)

    build_dir.mkdir(parents=True, exist_ok=True)

    # Install PyInstaller
    install_pyinstaller()

    # Estimate RAM usage
    required_ram = estimate_ram_required(project_dir)
    available_ram = psutil.virtual_memory().available
    print(f"Estimated RAM needed: {required_ram / (1024**2):.1f} MB")
    print(f"Available RAM: {available_ram / (1024**2):.1f} MB")

    if available_ram > required_ram:
        # Use RAM disk if enough RAM
        print("Sufficient RAM detected. Using RAM disk for build...")
        temp_build_dir = Path(tempfile.mkdtemp(prefix="build_ram_"))
        temp_project_dir = temp_build_dir / "project"
        shutil.copytree(project_dir, temp_project_dir)
        project_dir = temp_project_dir
        main_script = project_dir / config.get("main_script", "main.py")
    else:
        temp_build_dir = None

    # Clean previous builds
    clean_previous_builds([project_dir / "build", project_dir / "__pycache__"])

    # Collect assets
    assets = collect_assets(project_dir)

    # Build PyInstaller command
    pyinstaller_cmd = [
        "pyinstaller",
        "--onefile",
        f"--name={binary_name}",
        f"--distpath={build_dir}"
    ]

    for asset in assets:
        pyinstaller_cmd.append(f"--add-data={asset}")

    pyinstaller_cmd.append(str(main_script))

    # Run compilation
    print("Running PyInstaller...")
    subprocess.run(pyinstaller_cmd, check=True)

    # Optional packaging
    if config.get("package", False):
        package_path = build_dir / f"{binary_name}.tar.gz"
        shutil.make_archive(str(package_path.with_suffix('')), 'gztar', root_dir=build_dir)
        print(f"Packaged binary as {package_path}")

    # Clean temporary RAM build
    if temp_build_dir and temp_build_dir.exists():
        shutil.rmtree(temp_build_dir)
        print("Cleaned RAM build directory.")

    # Clean local build artifacts
    clean_previous_builds([project_dir / "build", project_dir / "__pycache__"])

    print("Build complete!")

if __name__ == "__main__":
    main()
