#!/usr/bin/env python3
"""Run the Telegram bot with integrated scheduler for diabetes monitoring"""
import sys
from pathlib import Path

# Add project directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from bot.main import main

if __name__ == "__main__":
    print("Starting Diabetes Monitoring Bot with integrated scheduler...")
    main()