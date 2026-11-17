import os
import shutil
import zipfile
from pathlib import Path

def build_submission():
    root_dir = Path("d:/grad prjt")
    build_dir = Path("d:/grad prjt/.temp/Karpagavalli_Apex")
    zip_dest_d = Path("d:/Karpagavalli_Apex.zip")
    zip_dest_local = Path("d:/grad prjt/Karpagavalli_Apex.zip")

    # Clean previous build
    if build_dir.exists():
        shutil.rmtree(build_dir, ignore_errors=True)
    build_dir.mkdir(parents=True, exist_ok=True)

    print(">>> 1. Creating Clean Submission Folder: Karpagavalli_Apex...")

    # 1. Frontend
    fe_src = root_dir / "frontend"
    fe_dst = build_dir / "Frontend"
    fe_dst.mkdir(parents=True, exist_ok=True)
    
    # Copy frontend directories & files excluding node_modules, dist, etc.
    shutil.copytree(fe_src / "src", fe_dst / "src", dirs_exist_ok=True)
    if (fe_src / "public").exists():
        shutil.copytree(fe_src / "public", fe_dst / "public", dirs_exist_ok=True)
    
    for f in ["package.json", "package-lock.json", "vite.config.js", "index.html", "tailwind.config.js", "postcss.config.js"]:
        src_file = fe_src / f
        if src_file.exists():
            shutil.copy2(src_file, fe_dst / f)

    # 2. Backend
    be_src = root_dir / "backend"
    be_dst = build_dir / "Backend"
    be_dst.mkdir(parents=True, exist_ok=True)

    def ignore_backend_patterns(folder, files):
        ignored = []
        for f in files:
            if f in ["venv", ".env", "__pycache__", ".pytest_cache", ".coverage", "logs"]:
                ignored.append(f)
            elif f.endswith(".pyc") or f.endswith(".log"):
                ignored.append(f)
        return ignored

    shutil.copytree(be_src / "app", be_dst / "app", dirs_exist_ok=True, ignore=ignore_backend_patterns)
    if (be_src / "tests").exists():
        shutil.copytree(be_src / "tests", be_dst / "tests", dirs_exist_ok=True, ignore=ignore_backend_patterns)
    if (be_src / "ml").exists():
        shutil.copytree(be_src / "ml", be_dst / "ml", dirs_exist_ok=True, ignore=ignore_backend_patterns)

    for f in ["run.py", "requirements.txt", ".env.example"]:
        src_file = be_src / f
        if src_file.exists():
            shutil.copy2(src_file, be_dst / f)

    # 3. ML (Standalone Root Folder as requested)
    ml_src = root_dir / "backend" / "ml"
    ml_dst = build_dir / "ML"
    ml_dst.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ml_src, ml_dst, dirs_exist_ok=True, ignore=ignore_backend_patterns)

    # 4. Documentation (PDF + Word + Markdown)
    doc_src = root_dir / "docs"
    doc_dst = build_dir / "Documentation"
    doc_dst.mkdir(parents=True, exist_ok=True)
    shutil.copytree(doc_src, doc_dst, dirs_exist_ok=True)

    # 5. README.md & Root Files
    shutil.copy2(root_dir / "README.md", build_dir / "README.md")
    if (root_dir / ".gitignore").exists():
        shutil.copy2(root_dir / ".gitignore", build_dir / ".gitignore")

    # 6. Scripts (Seed users, admin init)
    scripts_src = root_dir / "scripts"
    scripts_dst = build_dir / "scripts"
    scripts_dst.mkdir(parents=True, exist_ok=True)
    for s in ["seed_demo_users.py", "init_admin.py", "phase6_system_audit.py"]:
        src_script = scripts_src / s
        if src_script.exists():
            shutil.copy2(src_script, scripts_dst / s)

    print(">>> 2. Verifying Folder Contents...")
    for item in sorted(build_dir.iterdir()):
        print(f"  • {item.name} ({'Dir' if item.is_dir() else 'File'})")

    print("\n>>> 3. Compressing into ZIP...")
    # Remove existing zip files if any
    if zip_dest_d.exists():
        zip_dest_d.unlink()
    if zip_dest_local.exists():
        zip_dest_local.unlink()

    # Create zip containing Karpagavalli_Apex folder
    with zipfile.ZipFile(zip_dest_d, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(build_dir.parent / "Karpagavalli_Apex"):
            # Exclude unwanted directories
            dirs[:] = [d for d in dirs if d not in ["__pycache__", "node_modules", "venv", ".pytest_cache", ".git"]]
            for file in files:
                if file.endswith(".pyc") or file == ".env":
                    continue
                file_path = Path(root) / file
                arcname = file_path.relative_to(build_dir.parent)
                zf.write(file_path, arcname)

    # Make local copy
    shutil.copy2(zip_dest_d, zip_dest_local)

    zip_size_mb = zip_dest_d.stat().st_size / (1024 * 1024)
    print(f"\n[SUCCESS] ZIP created at:\n  1. {zip_dest_d} ({zip_size_mb:.2f} MB)\n  2. {zip_dest_local} ({zip_size_mb:.2f} MB)")

if __name__ == "__main__":
    build_submission()
