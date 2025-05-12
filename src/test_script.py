#!/usr/bin/env python
"""
Simple test script to verify Python execution.
"""
import sys
import os

def main():
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {os.getcwd()}")
    print("Test script executed successfully!")
    
    # Print the parent directory structure
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"Parent directory: {parent_dir}")
    
    req_file = os.path.join(parent_dir, "requirements.txt")
    if os.path.exists(req_file):
        print(f"requirements.txt exists at: {req_file}")
        with open(req_file, 'r') as f:
            first_line = f.readline().strip()
            print(f"First line: {first_line}")
    else:
        print(f"requirements.txt not found at: {req_file}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
