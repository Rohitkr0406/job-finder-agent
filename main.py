import sys
import asyncio
from dotenv import load_dotenv

# Ensure standard output/error use UTF-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# Load environment variables
load_dotenv()

from src.pipeline.pipeline import run_pipeline

if __name__ == "__main__":
    asyncio.run(run_pipeline())
