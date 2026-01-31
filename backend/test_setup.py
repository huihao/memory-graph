#!/usr/bin/env python3
"""
Simple test script to verify the backend setup
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    try:
        import fastapi
        print("✓ FastAPI imported successfully")
    except ImportError as e:
        print(f"✗ FastAPI import failed: {e}")
        return False
    
    try:
        import sqlalchemy
        print("✓ SQLAlchemy imported successfully")
    except ImportError as e:
        print(f"✗ SQLAlchemy import failed: {e}")
        return False
    
    try:
        import pydantic
        print("✓ Pydantic imported successfully")
    except ImportError as e:
        print(f"✗ Pydantic import failed: {e}")
        return False
    
    return True

def test_database():
    """Test database setup"""
    print("\nTesting database setup...")
    try:
        from database import init_db, Base, engine
        init_db()
        print("✓ Database initialized successfully")
        
        # Check tables were created
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"✓ Created tables: {', '.join(tables)}")
        return True
    except Exception as e:
        print(f"✗ Database setup failed: {e}")
        return False

def test_models():
    """Test that models can be imported"""
    print("\nTesting models...")
    try:
        from database import Article, Domain, KnowledgePoint
        print("✓ Models imported successfully")
        return True
    except Exception as e:
        print(f"✗ Models import failed: {e}")
        return False

def test_schemas():
    """Test that schemas can be imported"""
    print("\nTesting schemas...")
    try:
        from schemas import ArticleCreate, Article as ArticleSchema
        print("✓ Schemas imported successfully")
        return True
    except Exception as e:
        print(f"✗ Schemas import failed: {e}")
        return False

def test_services():
    """Test that services can be imported"""
    print("\nTesting services...")
    try:
        from services import LLMService, ContentExtractor
        print("✓ Services imported successfully")
        
        # Test instantiation
        llm = LLMService()
        extractor = ContentExtractor()
        print("✓ Services instantiated successfully")
        return True
    except Exception as e:
        print(f"✗ Services test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("Memory Graph Backend - Setup Verification")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Database", test_database()))
    results.append(("Models", test_models()))
    results.append(("Schemas", test_schemas()))
    results.append(("Services", test_services()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{name:20} {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n✓ All tests passed! Backend is ready to run.")
        print("\nTo start the server, run:")
        print("  python main.py")
        return 0
    else:
        print("\n✗ Some tests failed. Please install missing dependencies:")
        print("  pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())
