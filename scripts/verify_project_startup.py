"""
Startup and connectivity verification for MongoDB, Flask, and React Vite.
"""
import urllib.request
import json
from pymongo import MongoClient

print("=== 2. PROJECT STARTUP & CONNECTIVITY VERIFICATION ===")

# A. MongoDB Replica Set
try:
    mc = MongoClient("mongodb://127.0.0.1:27017/?replicaSet=rs0&directConnection=true", serverSelectionTimeoutMS=2000)
    hello = mc.admin.command("hello")
    print(f"[PASS] MongoDB Connected: Replica Set '{hello.get('setName')}', Primary={hello.get('isWritablePrimary')}")
except Exception as e:
    print(f"[FAIL] MongoDB connection error: {e}")

# B. Flask REST API
try:
    req = urllib.request.Request("http://127.0.0.1:5000/api/system/health")
    with urllib.request.urlopen(req, timeout=5) as resp:
        health = json.loads(resp.read().decode())
        print(f"[PASS] Flask API Health Check (HTTP {resp.status}): {health}")
except Exception as e:
    print(f"[FAIL] Flask API error: {e}")

# C. React Frontend Server
try:
    req_fe = urllib.request.Request("http://127.0.0.1:5173")
    with urllib.request.urlopen(req_fe, timeout=5) as resp_fe:
        html = resp_fe.read().decode()
        has_root = '<div id="root">' in html
        print(f"[PASS] Vite Frontend Dev Server (HTTP {resp_fe.status}): Found #root mount container: {has_root}")
except Exception as e:
    print(f"[FAIL] Frontend error: {e}")
