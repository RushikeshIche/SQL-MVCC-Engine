#!/usr/bin/env python3
"""
Setup script for SQL MVCC Engine
"""

import os
import sys
import subprocess
import importlib

def check_dependencies():
    """Check and install required dependencies"""
    required_packages = {
        'streamlit': 'streamlit',
        'pandas': 'pandas', 
        'plotly': 'plotly',
        'numpy': 'numpy',
        'prettytable': 'prettytable',
        'Pygments': 'pygments'
    }
    
    missing_packages = []
    
    for package, import_name in required_packages.items():
        try:
            importlib.import_module(import_name)
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    return missing_packages

def install_packages(packages):
    """Install missing packages"""
    if not packages:
        return True
        
    print(f"\nInstalling missing packages: {', '.join(packages)}")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + packages)
        print("✅ All packages installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install packages. Please install manually:")
        print(f"pip install {' '.join(packages)}")
        return False

def create_directories():
    """Create necessary directories"""
    directories = ['data', 'logs', 'exports']
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def setup_environment():
    """Setup the environment"""
    print("🔍 SQL MVCC Engine - Setup")
    print("=" * 40)
    
    print("\n1. Checking dependencies...")
    missing_packages = check_dependencies()
    
    if missing_packages:
        print("\n2. Installing missing packages...")
        if not install_packages(missing_packages):
            return False
    
    print("\n3. Creating directories...")
    create_directories()
    
    print("\n4. Setup complete! 🎉")
    print("\nTo start the application, run:")
    print("  streamlit run ui/enhanced_app.py")
    print("\nOr for the basic version:")
    print("  python main.py")
    
    return True

if __name__ == "__main__":
    success = setup_environment()
    sys.exit(0 if success else 1)