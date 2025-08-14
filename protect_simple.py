#!/usr/bin/env python3
"""
Simple PyArmor protection for AutoTestify
"""

import os
import shutil
import sys

def protect_project():
    """Protect the project using PyArmor gen command"""
    
    output_dir = "dist_protected"
    
    # Remove existing directory
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
        print(f"Removed existing {output_dir}")
    
    # Files and directories to protect
    items_to_protect = [
        "app.py",
        "config.py", 
        "services"
    ]
    
    print("Starting PyArmor protection...")
    
    # Use os.system to run pyarmor command
    cmd_parts = ["python", "-c", "\"import pyarmor.cli.__main__; pyarmor.cli.__main__.main()\"", "gen", "--output", output_dir]
    cmd_parts.extend(items_to_protect)
    
    cmd = " ".join(cmd_parts)
    print(f"Running: {cmd}")
    
    result = os.system(cmd)
    
    if result == 0:
        print("Protection completed!")
        
        # Copy additional files
        additional_files = [
            "requirements.txt",
            ".env", 
            "README.md",
            "chromedriver.exe"
        ]
        
        additional_dirs = [
            "templates",
            "static", 
            "reports",
            "screenshots"
        ]
        
        # Copy files
        for file_name in additional_files:
            if os.path.exists(file_name):
                try:
                    shutil.copy2(file_name, output_dir)
                    print(f"Copied {file_name}")
                except Exception as e:
                    print(f"Error copying {file_name}: {e}")
        
        # Copy directories
        for dir_name in additional_dirs:
            if os.path.exists(dir_name):
                try:
                    dest_dir = os.path.join(output_dir, dir_name)
                    if os.path.exists(dest_dir):
                        shutil.rmtree(dest_dir)
                    shutil.copytree(dir_name, dest_dir)
                    print(f"Copied directory {dir_name}")
                except Exception as e:
                    print(f"Error copying {dir_name}: {e}")
        
        print(f"\nProject protected in: {output_dir}")
        print(f"Run with: python {output_dir}/app.py")
        
    else:
        print("Protection failed!")
        return False
    
    return True

if __name__ == "__main__":
    protect_project()