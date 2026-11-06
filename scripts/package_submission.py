"""
Submission Packaging Script for Apex Bank
Creates a clean, production-ready submission package and zip archive
excluding node_modules, virtualenvs, local databases, and runtime secrets.
"""

import os
import shutil
import zipfile
import re

ROOT_DIR = r"d:\grad prjt"
SUBMISSION_DIR = os.path.join(ROOT_DIR, "submission")
PACKAGE_DIR = os.path.join(SUBMISSION_DIR, "ApexBank_Submission")
ZIP_PATH = os.path.join(SUBMISSION_DIR, "ApexBank_Final_Submission.zip")

EXCLUDE_DIRS = {
    "node_modules", "venv", ".temp", ".npm_cache", ".pip_cache",
    ".pytest_cache", "__pycache__", "dist"
}

EXCLUDE_FILES = {
    ".env", "*.log", "package_submission.py"
}

def should_exclude(dir_name):
    return dir_name in EXCLUDE_DIRS

def clean_copy():
    print(f"Preparing clean submission directory: {PACKAGE_DIR}")
    if os.path.exists(SUBMISSION_DIR):
        shutil.rmtree(SUBMISSION_DIR)
    os.makedirs(PACKAGE_DIR, exist_ok=True)

    # 1. Copy backend
    backend_src = os.path.join(ROOT_DIR, "backend")
    backend_dst = os.path.join(PACKAGE_DIR, "backend")
    for root, dirs, files in os.walk(backend_src):
        dirs[:] = [d for d in dirs if not should_exclude(d)]
        rel_path = os.path.relpath(root, backend_src)
        target_dir = os.path.join(backend_dst, rel_path)
        os.makedirs(target_dir, exist_ok=True)
        for f in files:
            if f == ".env" or f.endswith((".pyc", ".pyo", ".log")):
                continue
            src_f = os.path.join(root, f)
            dst_f = os.path.join(target_dir, f)
            shutil.copy2(src_f, dst_f)

    # 2. Copy frontend
    frontend_src = os.path.join(ROOT_DIR, "frontend")
    frontend_dst = os.path.join(PACKAGE_DIR, "frontend")
    for root, dirs, files in os.walk(frontend_src):
        dirs[:] = [d for d in dirs if not should_exclude(d)]
        rel_path = os.path.relpath(root, frontend_src)
        target_dir = os.path.join(frontend_dst, rel_path)
        os.makedirs(target_dir, exist_ok=True)
        for f in files:
            if f == ".env" or f.endswith((".log", ".tmp")):
                continue
            src_f = os.path.join(root, f)
            dst_f = os.path.join(target_dir, f)
            shutil.copy2(src_f, dst_f)

    # 3. Copy docs
    docs_src = os.path.join(ROOT_DIR, "docs")
    docs_dst = os.path.join(PACKAGE_DIR, "docs")
    shutil.copytree(docs_src, docs_dst)

    # 4. Copy scripts
    scripts_src = os.path.join(ROOT_DIR, "scripts")
    scripts_dst = os.path.join(PACKAGE_DIR, "scripts")
    os.makedirs(scripts_dst, exist_ok=True)
    for s_file in os.listdir(scripts_src):
        if s_file.endswith(".py") and s_file != "package_submission.py":
            shutil.copy2(os.path.join(scripts_src, s_file), os.path.join(scripts_dst, s_file))

    # 5. Copy root files
    shutil.copy2(os.path.join(ROOT_DIR, "README.md"), os.path.join(PACKAGE_DIR, "README.md"))
    shutil.copy2(os.path.join(ROOT_DIR, ".gitignore"), os.path.join(PACKAGE_DIR, ".gitignore"))

    print("Clean copy completed successfully.")

def verify_and_zip():
    print(f"Creating ZIP archive: {ZIP_PATH}")
    file_count = 0
    total_uncompressed_bytes = 0

    with zipfile.ZipFile(ZIP_PATH, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(PACKAGE_DIR):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, SUBMISSION_DIR)
                zipf.write(full_path, rel_path)
                file_count += 1
                total_uncompressed_bytes += os.path.getsize(full_path)

    zip_size_bytes = os.path.getsize(ZIP_PATH)
    print("--- SUBMISSION PACKAGE GENERATED ---")
    print(f"  Exact ZIP Path       : {ZIP_PATH}")
    print(f"  Total Files Included : {file_count}")
    print(f"  Uncompressed Size    : {total_uncompressed_bytes / (1024*1024):.2f} MB")
    print(f"  Compressed ZIP Size  : {zip_size_bytes / (1024*1024):.2f} MB")

    # Final sanity check: ensure no .env or node_modules in zip
    with zipfile.ZipFile(ZIP_PATH, 'r') as zipf:
        namelist = zipf.namelist()
        for name in namelist:
            assert "node_modules" not in name, f"Forbidden node_modules found: {name}"
            assert "venv" not in name, f"Forbidden venv found: {name}"
            assert not name.endswith("/.env") and not name.endswith("\\.env"), f"Forbidden .env secret found: {name}"
            assert "data/db" not in name, f"Forbidden runtime database files found: {name}"

    print("[PASS] Verified archive excludes all virtualenvs, node_modules, database files, and .env secrets.")

if __name__ == "__main__":
    clean_copy()
    verify_and_zip()
