#!/usr/bin/env python
"""
This script checks for duplicate packages in requirements files and
ensures that all dependencies are properly organized.
"""
import os
import sys
import re
from collections import defaultdict

def parse_requirements(file_path):
    """Parse a requirements file and return a dictionary of package details"""
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found")
        return {}
        
    packages = {}
    current_section = "Unknown"
    
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
                
            # Track sections by comments
            if line.startswith('#'):
                # Extract section name from comment
                if re.match(r'^# [A-Z]', line):  # Section comments start with "# Name"
                    current_section = line.lstrip('# ')
                continue
                
            # Handle package with version specified
            if '==' in line:
                name, version = line.split('==', 1)
                name = name.strip()
                packages[name] = {
                    "version": version.strip(),
                    "section": current_section
                }
            else:
                # Package without version
                packages[line] = {
                    "version": None,
                    "section": current_section
                }
                
    return packages

def main():
    """Check for duplicates and organization in requirements files"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Load requirements files
    main_req_path = os.path.join(base_dir, 'requirements.txt')
    ml_req_path = os.path.join(base_dir, 'ml-requirements.txt')
    
    main_packages = parse_requirements(main_req_path)
    ml_packages = parse_requirements(ml_req_path)
    
    # Check for duplicates between files
    duplicates = {}
    for pkg in ml_packages:
        if pkg in main_packages:
            main_ver = main_packages[pkg].get("version")
            ml_ver = ml_packages[pkg].get("version")
            
            if main_ver != ml_ver:
                duplicates[pkg] = {
                    "requirements.txt": main_ver, 
                    "ml-requirements.txt": ml_ver
                }
            else:
                duplicates[pkg] = {"version": main_ver}
    
    # Print results
    print(f"Found {len(main_packages)} packages in requirements.txt")
    print(f"Found {len(ml_packages)} packages in ml-requirements.txt")
    
    # Check for duplicates
    if duplicates:
        print("\n⚠️ Found duplicates across files:")
        for pkg, details in duplicates.items():
            if "version" in details:
                print(f"  - {pkg}=={details['version']} (identical versions in both files)")
            else:
                print(f"  - {pkg}: requirements.txt=={details['requirements.txt']}, " +
                      f"ml-requirements.txt=={details['ml-requirements.txt']}")
        
        print("\nRecommendation: Remove duplicates and keep them in only one file")
    else:
        print("\n✅ No duplicate packages found across files")
    
    # Basic organization check
    sections = defaultdict(list)
    for pkg, details in main_packages.items():
        sections[details["section"]].append(pkg)
    
    print("\nPackage organization in requirements.txt:")
    for section, packages in sections.items():
        print(f"  • {section}: {len(packages)} packages")
    
    return len(duplicates) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
