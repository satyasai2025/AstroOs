import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from apps.api.main import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001, reload=False)