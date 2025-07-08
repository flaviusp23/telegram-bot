#!/usr/bin/env python3
"""Run the data export for diabetes monitoring"""
import sys
from pathlib import Path

# Add project directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from scripts.data_export import main

if __name__ == "__main__":
    main()