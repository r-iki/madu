#!/usr/bin/env python
"""
Dependency verification script that checks if all required dependencies 
are properly installed and at the correct versions.
"""
import os
import sys
import importlib
import pkg_resources
from importlib.util import find_spec

def check_module(module_name, min_version=None):
    """
    Check if a module is installed and optionally check its version.
    
    Args:
        module_name (str): Name of the module
        min_version (str, optional): Minimum version required
        
    Returns:
        tuple: (is_installed, version)
    """
    try:
        spec = find_spec(module_name)
        if spec is None:
            return False, None
            
        # If we need to check version
        if min_version:
            try:
                version = pkg_resources.get_distribution(module_name).version
                return True, version
            except pkg_resources.DistributionNotFound:
                # This happens with some built-in modules
                return True, "unknown"
                
        return True, None
    except ImportError:
        return False, None

def parse_requirements_file(file_path):
    """Parse a requirements file and return a dictionary of package:version"""
    if not os.path.exists(file_path):
        print(f"Error: Requirements file {file_path} not found!")
        return {}
        
    packages = {}
    with open(file_path) as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
                
            # Handle packages with specific versions
            if '==' in line:
                name, version = line.split('==', 1)
                packages[name.strip()] = version.strip()
            else:
                packages[line] = None
                
    return packages

def main():
    """Check dependencies from requirements files"""
    # Get base path
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if __name__ == "__main__" else os.getcwd()
    
    # Check the main requirements
    requirements_path = os.path.join(base_dir, 'requirements.txt')
    ml_requirements_path = os.path.join(base_dir, 'ml-requirements.txt')
    
    print(f"Checking main requirements in {requirements_path}...")
    main_packages = parse_requirements_file(requirements_path)
    
    print(f"Checking ML requirements in {ml_requirements_path}...")
    ml_packages = parse_requirements_file(ml_requirements_path)
    
    # Combine both dictionaries
    all_packages = {**main_packages, **ml_packages}
    
    # Check critical packages
    critical_packages = [
        'django', 'channels', 'joblib', 'scikit-learn', 'boto3', 
        'numpy', 'pandas', 'gunicorn', 'whitenoise'
    ]
    
    missing = []
    outdated = []
    
    print("\nChecking critical packages:")
    for package in critical_packages:
        required_version = all_packages.get(package)
        installed, version = check_module(package.lower().replace('-', '_'), required_version)
        
        if not installed:
            missing.append(package)
            print(f"❌ {package}: Not installed")
        elif required_version and version != "unknown" and version != required_version:
            outdated.append((package, version, required_version))
            print(f"⚠️ {package}: Installed {version}, required {required_version}")
        else:
            print(f"✅ {package}: {version or 'Installed'}")
    
    # Check cloud storage requirements
    print("\nChecking cloud storage dependencies:")
    cloud_deps = ['boto3', 'botocore', 's3transfer']
    for dep in cloud_deps:
        installed, version = check_module(dep)
        if not installed:
            print(f"❌ {dep}: Not installed - Cloud storage will NOT work")
        else:
            print(f"✅ {dep}: {version or 'Installed'}")
    
    # Print summary
    print("\n=== Summary ===")
    if missing:
        print(f"❌ Missing {len(missing)} critical packages: {', '.join(missing)}")
    if outdated:
        print(f"⚠️ {len(outdated)} packages have version mismatches:")
        for pkg, installed_ver, required_ver in outdated:
            print(f"  - {pkg}: installed {installed_ver}, required {required_ver}")
    
    if not missing and not outdated:
        print("✅ All critical dependencies are properly installed!")
    
    return len(missing) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
