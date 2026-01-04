import os
import sys
import subprocess

ENTRY = "dhax.py"
OUT = "build"

IGNORE_DIRS = {
    "__pycache__", ".git", ".vscode",
    "build", "dist",
    "main.build", "main.dist", "main.onefile-build"
}

def scan_packages():
    args = []
    for d in os.listdir("."):
        if os.path.isdir(d) and d not in IGNORE_DIRS:
            args.append(f"--include-package={d}")
    return args

cmd = [
    sys.executable, "-m", "nuitka",
    ENTRY,

    # MODE
    "--standalone",
    "--onefile",
    "--follow-imports",

    # WINDOWS
    "--windows-uac-admin",

    # OPTIMIZATION (SAFE)
    "--python-flag=no_docstrings",
    "--lto=yes",

    # OUTPUT
    f"--output-dir={OUT}",
]

# auto include all packages
cmd += scan_packages()

print("[+] Starting Nuitka build...")
print(" ".join(cmd))
subprocess.run(cmd, check=True)
print("[✓] Build finished successfully")
print(f"[i] Output located in ./{OUT}/")