#!/usr/bin/env python
"""
Test script to verify Phase 1 setup is complete and working.
This tests imports and structure without requiring a database connection.
"""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test all imports work correctly"""
    print("Testing imports...")

    try:
        from app.core.config import settings
        print("✓ Config imports successfully")
        print(f"  - App Name: {settings.APP_NAME}")
        print(f"  - App Version: {settings.APP_VERSION}")
        print(f"  - Debug Mode: {settings.DEBUG}")
    except Exception as e:
        print(f"✗ Config import failed: {e}")
        return False

    try:
        from app.database import Base, engine, get_db, init_db
        print("✓ Database module imports successfully")
        print(f"  - Engine created: {engine is not None}")
    except Exception as e:
        print(f"✗ Database import failed: {e}")
        return False

    try:
        from app.schemas import TestModel
        print("✓ Schemas import successfully")
        print(f"  - TestModel table: {TestModel.__tablename__}")
    except Exception as e:
        print(f"✗ Schemas import failed: {e}")
        return False

    try:
        from app.main import app
        print("✓ FastAPI app imports successfully")
        print(f"  - App title: {app.title}")
        print(f"  - App version: {app.version}")
    except Exception as e:
        print(f"✗ FastAPI app import failed: {e}")
        return False

    return True


def test_structure():
    """Verify directory structure is correct"""
    print("\nVerifying project structure...")

    required_files = [
        "app/__init__.py",
        "app/main.py",
        "app/database.py",
        "app/core/__init__.py",
        "app/core/config.py",
        "app/models/__init__.py",
        "app/schemas/__init__.py",
        "tests/__init__.py",
        "requirements.txt",
        ".env.example",
        ".env",
        "README.md",
    ]

    base_path = Path(__file__).parent
    all_exist = True

    for file_path in required_files:
        full_path = base_path / file_path
        if full_path.exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} - MISSING")
            all_exist = False

    return all_exist


def test_app_routes():
    """Test that app routes are defined"""
    print("\nChecking FastAPI routes...")

    try:
        from app.main import app
        routes = [route.path for route in app.routes]

        expected_routes = ["/", "/health"]
        for route in expected_routes:
            if route in routes:
                print(f"✓ Route {route} is defined")
            else:
                print(f"✗ Route {route} is missing")
                return False

        return True
    except Exception as e:
        print(f"✗ Error checking routes: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Phase 1: FastAPI Foundation - Setup Verification")
    print("=" * 60)
    print()

    results = []

    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Structure", test_structure()))
    results.append(("Routes", test_app_routes()))

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    all_passed = all(result[1] for result in results)

    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {test_name}")

    print()
    if all_passed:
        print("🎉 All Phase 1 checks passed!")
        print("\nNext steps:")
        print("1. Ensure PostgreSQL is running")
        print("2. Create database: createdb mybotarmy")
        print("3. Run: uvicorn app.main:app --reload")
        print("4. Test health check: curl http://localhost:8000/health")
        sys.exit(0)
    else:
        print("❌ Some checks failed. Please review the output above.")
        sys.exit(1)
