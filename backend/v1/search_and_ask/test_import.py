import sys
sys.path.insert(0, '.')
try:
    from routes.qa_routes import router
    print("OK: qa_routes imported successfully")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
