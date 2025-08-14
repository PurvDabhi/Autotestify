#!/usr/bin/env python3
"""
PyArmor protection script for AutoTestify project
"""

import os
import shutil
import subprocess

def protect_project():
    """Protect the AutoTestify project using PyArmor"""
    
    # Define output directory
    output_dir = "dist_protected"
    
    # Remove existing protected directory
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Python files to protect
    python_files = [
        "app.py",
        "config.py",
        "test_config.py",
        "test_gemini.py",
        "services"
    ]
    
    print("Protecting Python files with PyArmor...")
    
    # Use PyArmor command line to protect files
    try:
        cmd = ["pyarmor", "gen", "--output", output_dir] + python_files
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Files protected successfully!")
        else:
            print(f"PyArmor error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Error running PyArmor: {e}")
        return False
    
    # Copy non-Python files
    copy_files = [
        "requirements.txt",
        ".env",
        ".gitignore",
        "README.md",
        "chromedriver.exe"
    ]
    
    copy_dirs = [
        "templates",
        "static",
        "reports",
        "screenshots"
    ]
    
    # Copy individual files
    for file_name in copy_files:
        if os.path.exists(file_name):
            shutil.copy2(file_name, output_dir)
            print(f"Copied {file_name}")
    
    # Copy directories
    for dir_name in copy_dirs:
        if os.path.exists(dir_name):
            dest_dir = os.path.join(output_dir, dir_name)
            if os.path.exists(dest_dir):
                shutil.rmtree(dest_dir)
            shutil.copytree(dir_name, dest_dir)
            print(f"Copied directory {dir_name}")
    
    print(f"\nProject protected successfully!")
    print(f"Protected files are in: {output_dir}")
    print(f"Run the protected app with: python {output_dir}/app.py")

if __name__ == "__main__":
    protect_project()