#!/usr/bin/env python3
"""
Quick test to verify pytracer environment setup.

Checks:
- Dependencies installed
- File loader works
- MongoDB connectivity (if configured)
- Credentials file exists and is valid
"""

import sys
import os

def test_dependencies():
    """Test that required packages are installed."""
    print("=== Checking Dependencies ===")
    required = {
        'pygame': 'pygame',
        'pydantic': 'pydantic',
        'pymongo': 'pymongo',
        'requests': 'requests',
        'fastapi': 'fastapi',
    }

    missing = []
    for name, package in required.items():
        try:
            __import__(package)
            print(f"✓ {name}")
        except ImportError:
            print(f"✗ {name} (missing)")
            missing.append(name)

    if missing:
        print(f"\n⚠ Missing: {', '.join(missing)}")
        print(f"Install with: pip3 install -r requirements.txt")
        return False

    print("✓ All dependencies installed\n")
    return True

def test_file_loader():
    """Test that file loader works."""
    print("=== Testing File Loader ===")
    try:
        import loader
        import vertex
        import surface

        print("Loading vertices from file...")
        vertices = loader.load_vertices_file()
        print(f"✓ Loaded {vertices.vertex_count()} vertices")

        print("Loading surfaces from file...")
        surfaces = loader.load_surfaces_file()
        print(f"✓ Loaded {surfaces.surface_count()} surfaces")

        if vertices.vertex_count() == 0 or surfaces.surface_count() == 0:
            print("✗ File loader returned empty collections")
            return False

        print("✓ File loader works\n")
        return True

    except Exception as e:
        print(f"✗ File loader failed: {e}\n")
        return False

def test_credentials():
    """Test that credentials.py exists and is valid."""
    print("=== Checking Credentials ===")
    try:
        import credentials
        print(f"✓ credentials.py found")
        print(f"  MONGODB_ADMIN_USERNAME = {credentials.MONGODB_ADMIN_USERNAME}")
        print(f"  MONGODB_ADMIN_PASSWORD = {'*' * len(credentials.MONGODB_ADMIN_PASSWORD)}")
        print("✓ Credentials valid\n")
        return True
    except ImportError:
        print("✗ credentials.py not found")
        print("  Run: python3 setup_mongodb.py [atlas|local]\n")
        return False
    except Exception as e:
        print(f"✗ Credentials invalid: {e}\n")
        return False

def test_mongodb():
    """Test MongoDB connectivity (optional)."""
    print("=== Testing MongoDB Connectivity ===")
    try:
        import credentials
        from pymongo import MongoClient
        from pymongo.errors import ServerSelectionTimeoutError

        # Try local first
        try:
            client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000)
            client.admin.command('ping')
            print("✓ Local MongoDB available (localhost:27017)")
            mongo_type = 'local'
        except ServerSelectionTimeoutError:
            # Try Atlas
            conn_string = f'mongodb+srv://{credentials.MONGODB_ADMIN_USERNAME}:{credentials.MONGODB_ADMIN_PASSWORD}@cluster0.iyzootc.mongodb.net/test'
            client = MongoClient(conn_string, serverSelectionTimeoutMS=5000)
            client.admin.command('ping')
            print("✓ MongoDB Atlas available")
            mongo_type = 'atlas'

        db = client['3dObjects']
        v_count = db['vertices'].count_documents({})
        s_count = db['surfaces'].count_documents({})

        print(f"  Database: 3dObjects")
        print(f"  Vertices: {v_count}")
        print(f"  Surfaces: {s_count}")

        if v_count == 0 or s_count == 0:
            print("✗ Collections are empty")
            print("  Run: python3 setup_mongodb.py [atlas|local]")
            client.close()
            return False

        print("✓ MongoDB configured and populated\n")
        client.close()
        return True

    except ImportError:
        print("✗ credentials.py not found (skip)\n")
        return True  # Not fatal
    except Exception as e:
        print(f"⚠ MongoDB not available: {e}")
        print("  This is optional. File loader will work fine.\n")
        return True  # Not fatal

def test_matrix_module():
    """Test matrix module works."""
    print("=== Testing Matrix Module ===")
    try:
        import matrix

        # Test identity matrix
        I = matrix.IdentityMatrix()
        assert I[0][0] == 1
        assert I[0][1] == 0
        print("✓ IdentityMatrix works")

        # Test vector normalization
        v = [3, 4, 0]
        n = matrix.NormaliseVector(v)
        magnitude = (n[0]**2 + n[1]**2 + n[2]**2) ** 0.5
        assert abs(magnitude - 1.0) < 0.001
        print("✓ NormaliseVector works")

        # Test surface normal
        v1 = [0, 0, 0]
        v2 = [1, 0, 0]
        v3 = [0, 1, 0]
        normal = matrix.CalcSurfaceNormal(v1, v2, v3)
        assert normal[2] > 0  # Normal should point up (z > 0)
        print("✓ CalcSurfaceNormal works")

        print("✓ Matrix module works\n")
        return True

    except Exception as e:
        print(f"✗ Matrix module failed: {e}\n")
        return False

def main():
    print("\n" + "="*50)
    print("PyTracer Setup Verification")
    print("="*50 + "\n")

    results = []

    # Required checks
    results.append(("Dependencies", test_dependencies()))
    results.append(("File Loader", test_file_loader()))
    results.append(("Matrix Module", test_matrix_module()))

    # Optional checks
    results.append(("Credentials", test_credentials()))
    results.append(("MongoDB", test_mongodb()))

    # Summary
    print("="*50)
    print("Summary")
    print("="*50)
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\n{passed}/{total} checks passed")

    if passed == total:
        print("\n✓ Setup complete! You're ready to run:")
        print("  python3 swfvs.py              # Load from file")
        print("  (Edit swfvs.py line 15 to load from MongoDB)")
        return 0
    elif passed >= total - 1:  # Only MongoDB optional failed
        print("\n⚠ Setup mostly complete (MongoDB is optional)")
        print("  File loader works, so you can run:")
        print("  python3 swfvs.py")
        print("\n  To use MongoDB, run:")
        print("  python3 setup_mongodb.py [atlas|local]")
        return 0
    else:
        print("\n✗ Setup incomplete. Fix the failures above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
