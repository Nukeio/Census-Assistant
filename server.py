"""
Census Assistant - Application Server Runner
"""

import os
import sys

# Ensure current directory is in sys.path
sys.path.insert(0, os.path.dirname(__file__))

from backend.main import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Census Assistant on http://localhost:{port}", flush=True)
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False, threaded=True)
