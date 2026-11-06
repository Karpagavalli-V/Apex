"""
Verify ZIP archive integrity, contents, and extraction.
"""
import os
import zipfile
import shutil

zip_path = r"d:\grad prjt\submission\ApexBank_Final_Submission.zip"
extract_test_dir = r"d:\grad prjt\.temp\zip_test_extract"

print("=== 1. ZIP ARCHIVE INSPECTION ===")
assert os.path.exists(zip_path), f"ZIP archive missing at {zip_path}"
zip_size = os.path.getsize(zip_path)
print(f"Archive Path: {zip_path}")
print(f"Archive Size: {zip_size} bytes ({zip_size / (1024*1024):.2f} MB)")

with zipfile.ZipFile(zip_path, "r") as zf:
    names = zf.namelist()
    print(f"Total Entries in ZIP: {len(names)}")

    # Categorical verification
    has_frontend = any("frontend/src/App.jsx" in n or "frontend/package.json" in n for n in names)
    has_backend = any("backend/app/__init__.py" in n for n in names) and any("backend/run.py" in n for n in names)
    has_tests = any("backend/tests/test_banking_api.py" in n for n in names)
    has_ml_dataset = any("backend/ml/data/synthetic_transactions.csv" in n for n in names)
    has_ml_model = any("backend/ml/artifacts/fraud_detector.joblib" in n for n in names)
    has_ml_notebook = any("backend/ml/notebooks/fraud_detection_training.ipynb" in n for n in names)
    has_docs = any("docs/SYSTEM_DESIGN.md" in n for n in names)
    has_readme = any("README.md" in n for n in names)

    print("Checking mandatory assets:")
    print(f"  Frontend Source     : {'YES' if has_frontend else 'NO'}")
    print(f"  Backend Source      : {'YES' if has_backend else 'NO'}")
    print(f"  Backend Tests       : {'YES' if has_tests else 'NO'}")
    print(f"  ML Dataset          : {'YES' if has_ml_dataset else 'NO'}")
    print(f"  ML Trained Model    : {'YES' if has_ml_model else 'NO'}")
    print(f"  ML Notebook         : {'YES' if has_ml_notebook else 'NO'}")
    print(f"  Documentation Files : {'YES' if has_docs else 'NO'}")
    print(f"  Root README.md      : {'YES' if has_readme else 'NO'}")

    assert has_frontend and has_backend and has_tests and has_ml_dataset and has_ml_model and has_ml_notebook and has_docs and has_readme

    # Exclusion checks
    forbidden = []
    for n in names:
        if "node_modules" in n:
            forbidden.append(("node_modules", n))
        if "venv/" in n or "venv\\" in n:
            forbidden.append(("venv", n))
        if n.endswith("/.env") or n.endswith("\\.env") or n == ".env":
            forbidden.append((".env", n))
        if "data/db" in n or "data\\db" in n:
            forbidden.append(("database_runtime", n))
        if ".temp" in n:
            forbidden.append((".temp", n))

    print(f"Forbidden items found: {len(forbidden)}")
    assert len(forbidden) == 0, f"Forbidden items found in zip: {forbidden}"

    # Test extraction
    if os.path.exists(extract_test_dir):
        shutil.rmtree(extract_test_dir)
    os.makedirs(extract_test_dir, exist_ok=True)
    
    print("Testing archive extraction to temp directory...")
    zf.extractall(extract_test_dir)
    extracted_count = sum(len(files) for _, _, files in os.walk(extract_test_dir))
    print(f"[PASS] Archive extracted cleanly. Extracted files count: {extracted_count}")

shutil.rmtree(extract_test_dir)
print("[PASS] Temporary extraction directory cleaned up.")
