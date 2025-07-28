#!/usr/bin/env python3
"""
Publishing script for PyPI
"""
import subprocess
import sys
import os


def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Error: {description} failed")
        print(f"Command: {cmd}")
        print(f"Error: {result.stderr}")
        return False

    print(f"✅ {description} completed successfully")
    if result.stdout.strip():
        print(result.stdout)
    return True


def main():
    """Main publishing workflow"""
    print("🚢 RethinkPort PyPI Publishing Script")
    print("=" * 40)

    # Check if we're in the right directory
    if not os.path.exists("pyproject.toml"):
        print(
            "❌ Error: pyproject.toml not found. Run this script from the project root."
        )
        sys.exit(1)

    # Clean previous builds
    if not run_command("rm -rf dist/ build/ *.egg-info/", "Cleaning previous builds"):
        sys.exit(1)

    # Install/upgrade build tools
    if not run_command(
        "pip install --upgrade build twine", "Installing/upgrading build tools"
    ):
        sys.exit(1)

    # Build the package
    if not run_command("python -m build", "Building package"):
        sys.exit(1)

    # Check the distribution
    if not run_command("python -m twine check dist/*", "Checking distribution"):
        sys.exit(1)

    print("\n🎉 Package built successfully!")
    print("\nNext steps:")
    print("1. Test upload to TestPyPI:")
    print("   python -m twine upload --repository testpypi dist/*")
    print("\n2. Upload to PyPI:")
    print("   python -m twine upload dist/*")
    print("\n3. Install and test:")
    print("   pip install rethinkport")


if __name__ == "__main__":
    main()
