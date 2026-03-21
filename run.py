"""
SOP Reference App - Startup Script
Run: python run.py

Requirements: Python 3.10+ (no external packages needed)
"""
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

print("=" * 55)
print("  LOGISTICS SOP REFERENCE APP - Starting Up")
print("=" * 55)

# Initialize database and seed data
print("\n[1/2] Initializing database and seeding data...")
from seed_data import seed
seed()

# Start server
print("[2/2] Starting server...\n")
from app import run_server
run_server()
