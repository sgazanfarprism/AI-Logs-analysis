"""
Simple wrapper to run orchestrator from project root
This ensures Python can find all modules correctly
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run orchestrator
from orchestrator.orchestrator import main

if __name__ == "__main__":
    main()
