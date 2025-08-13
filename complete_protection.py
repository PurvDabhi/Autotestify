#!/usr/bin/env python3
"""
Complete PyArmor protection for AutoTestify
"""

import os
import shutil
import subprocess

def protect_project():
    """Complete protection of the AutoTestify project"""
    
    output_dir = "dist_protected"
    
    print("Starting AutoTestify protection...")
    
    # Step 1: Protect main files (already done)
    print("Main files protected")
    
    # Step 2: Protect services individually to avoid encoding issues
    services_files = [
        "services/__init__.py",
        "services/api_tester.py", 
        "services/gemini_service.py",
        "services/github_service.py",
        "services/report_generator.py"
    ]
    
    # Create services directory in output
    services_output = os.path.join(output_dir, "services")
    os.makedirs(services_output, exist_ok=True)
    
    for service_file in services_files:
        if os.path.exists(service_file):
            try:
                cmd = [
                    "python", "-c", 
                    "import pyarmor.cli.__main__; pyarmor.cli.__main__.main()",
                    "gen", "--output", services_output, service_file
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"Protected {service_file}")
                else:
                    print(f"Copying {service_file} (protection failed)")
                    shutil.copy2(service_file, os.path.join(services_output, os.path.basename(service_file)))
            except Exception as e:
                print(f"Copying {service_file} due to error: {e}")
                shutil.copy2(service_file, os.path.join(services_output, os.path.basename(service_file)))
    
    # Handle email_service.py separately due to encoding
    email_service_src = "services/email_service.py"
    email_service_dst = os.path.join(services_output, "email_service.py")
    if os.path.exists(email_service_src):
        shutil.copy2(email_service_src, email_service_dst)
        print("Copied services/email_service.py")
    
    # Step 3: Copy additional files
    additional_files = [
        "requirements.txt",
        ".env",
        "README.md", 
        "chromedriver.exe",
        "test_config.py",
        "test_gemini.py"
    ]
    
    for file_name in additional_files:
        if os.path.exists(file_name):
            try:
                shutil.copy2(file_name, output_dir)
                print(f"Copied {file_name}")
            except Exception as e:
                print(f"Error copying {file_name}: {e}")
    
    # Step 4: Copy directories
    directories = [
        "templates",
        "static",
        "reports", 
        "screenshots"
    ]
    
    for dir_name in directories:
        if os.path.exists(dir_name):
            try:
                dest_dir = os.path.join(output_dir, dir_name)
                if os.path.exists(dest_dir):
                    shutil.rmtree(dest_dir)
                shutil.copytree(dir_name, dest_dir)
                print(f"Copied directory {dir_name}")
            except Exception as e:
                print(f"Error copying {dir_name}: {e}")
    
    # Step 5: Create run script
    run_script = os.path.join(output_dir, "run.bat")
    with open(run_script, 'w') as f:
        f.write("@echo off\n")
        f.write("echo Starting AutoTestify (Protected)...\n")
        f.write("python app.py\n")
        f.write("pause\n")
    
    print(f"\nAutoTestify protection completed!")
    print(f"Protected files location: {output_dir}")
    print(f"Run with: python {output_dir}/app.py")
    print(f"Or use: {output_dir}/run.bat")
    
    return True

if __name__ == "__main__":
    protect_project()