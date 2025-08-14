#!/usr/bin/env python3
import json
import subprocess
import shutil
from pathlib import Path
import sys

def install_pyinstaller():
    """Install PyInstaller if not found."""
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

def clean_previous_builds(project_dir):
    """Remove old build artifacts."""
    for folder in ["build", "__pycache__"]:
        path = project_dir / folder
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

def main():
    # Load build configuration
    config_file = Path("program_File/app_resources/build_info.json")
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

    # Prepare environment
    install_pyinstaller()
    clean_previous_builds(project_dir)
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

    print("Build complete!")

if __name__ == "__main__":
    main()
