import traceback
import sys

try:
    import app.main
    print("IMPORT_OK")
except Exception:
    traceback.print_exc()
    sys.exit(1)
