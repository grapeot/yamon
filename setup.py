"""Setup script with custom build command to build frontend before packaging"""

from setuptools import setup
from setuptools.command.build_py import build_py
from pathlib import Path
import subprocess
import sys
import shutil


class BuildPyWithFrontend(build_py):
    """Custom build command that builds frontend before packaging"""
    
    def run(self):
        """Build frontend before building Python package"""
        # Check if we're in a source distribution (sdist) or building from source
        # Only build frontend if frontend source exists
        project_root = Path(__file__).parent
        frontend_dir = project_root / "frontend"
        static_dir = project_root / "yamon" / "static"
        
        if frontend_dir.exists() and (frontend_dir / "package.json").exists():
            print("Building frontend...")
            try:
                # Build frontend
                # Run npm install (suppress output unless it fails)
                result = subprocess.run(
                    ["npm", "install"],
                    cwd=str(frontend_dir),
                    check=False,
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    print(f"npm install failed: {result.stderr}", file=sys.stderr)
                    raise subprocess.CalledProcessError(result.returncode, "npm install")
                
                # Run npm build
                result = subprocess.run(
                    ["npm", "run", "build"],
                    cwd=str(frontend_dir),
                    check=False,
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    print(f"npm run build failed: {result.stderr}", file=sys.stderr)
                    raise subprocess.CalledProcessError(result.returncode, "npm run build")
                
                # Copy built files to yamon/static
                dist_dir = frontend_dir / "dist"
                if dist_dir.exists():
                    if static_dir.exists():
                        shutil.rmtree(static_dir)
                    shutil.copytree(dist_dir, static_dir)
                    print(f"Frontend built and copied to {static_dir}")
                else:
                    print("Warning: frontend/dist not found after build")
            except subprocess.CalledProcessError as e:
                print(f"Warning: Failed to build frontend: {e}", file=sys.stderr)
                print("Continuing without frontend build...", file=sys.stderr)
            except FileNotFoundError:
                print("Warning: npm not found. Skipping frontend build.", file=sys.stderr)
                print("Make sure frontend is built before packaging.", file=sys.stderr)
        else:
            print("Frontend source not found, using existing static files if available")
        
        # Run the standard build_py command
        super().run()


# This file is only used when building the package
# The actual package metadata is in pyproject.toml
if __name__ == "__main__":
    setup(cmdclass={"build_py": BuildPyWithFrontend})

