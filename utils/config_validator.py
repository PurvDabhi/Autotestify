"""
Configuration validation utility for AutoTestify
Ensures all required configurations are properly set for stable operation
"""

import os
import logging
from typing import Dict, List, Tuple, Optional
import requests
from urllib.parse import urlparse

class ConfigValidator:
    """Validates application configuration for optimal stability"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.validation_results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'recommendations': []
        }
    
    def validate_all_configs(self) -> Dict:
        """Perform comprehensive configuration validation"""
        self.logger.info("Starting comprehensive configuration validation...")
        
        # Reset validation results
        self.validation_results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'recommendations': []
        }
        
        # Validate different configuration sections
        self._validate_environment_variables()
        self._validate_api_keys()
        self._validate_directories()
        self._validate_dependencies()
        self._validate_network_connectivity()
        self._validate_system_resources()
        
        # Set overall validity
        self.validation_results['valid'] = len(self.validation_results['errors']) == 0
        
        self.logger.info(f"Configuration validation completed. Valid: {self.validation_results['valid']}")
        return self.validation_results
    
    def _validate_environment_variables(self):
        """Validate required environment variables"""
        required_vars = [
            ('GEMINI_API_KEY', 'Gemini AI API key for code analysis'),
            ('SECRET_KEY', 'Flask secret key for session security')
        ]
        
        optional_vars = [
            ('GITHUB_TOKEN', 'GitHub API token for enhanced repository access'),
            ('MAILJET_API_KEY', 'Mailjet API key for email notifications'),
            ('MAILJET_API_SECRET', 'Mailjet API secret for email notifications'),
            ('MAILJET_SENDER_EMAIL', 'Verified sender email for notifications')
        ]
        
        # Check required variables
        for var_name, description in required_vars:
            value = os.environ.get(var_name)
            if not value:
                # Check if python-dotenv is actually available
                if var_name == 'SECRET_KEY':
                    # Generate a default secret key if missing
                    import secrets
                    os.environ['SECRET_KEY'] = secrets.token_hex(32)
                    self.validation_results['warnings'].append(
                        f"Generated default {var_name} - consider setting a permanent one"
                    )
                else:
                    self.validation_results['errors'].append(
                        f"Missing required environment variable: {var_name} ({description})"
                    )
            elif len(value.strip()) < 10:
                self.validation_results['warnings'].append(
                    f"Environment variable {var_name} seems too short, please verify"
                )
        
        # Check optional variables
        for var_name, description in optional_vars:
            value = os.environ.get(var_name)
            if not value:
                self.validation_results['recommendations'].append(
                    f"Consider setting {var_name} for enhanced functionality: {description}"
                )
    
    def _validate_api_keys(self):
        """Validate API key functionality"""
        # Validate Gemini API key
        gemini_key = os.environ.get('GEMINI_API_KEY')
        if gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=gemini_key)
                model = genai.GenerativeModel('gemini-2.0-flash')
                # Test with a simple prompt
                response = model.generate_content("Test connection")
                if response:
                    self.logger.info("Gemini API key validation successful")
                else:
                    self.validation_results['warnings'].append("Gemini API key may be invalid or rate limited")
            except Exception as e:
                self.validation_results['warnings'].append(f"Gemini API validation failed: {str(e)}")
        
        # Validate GitHub token
        github_token = os.environ.get('GITHUB_TOKEN')
        if github_token:
            try:
                headers = {'Authorization': f'token {github_token}'}
                response = requests.get('https://api.github.com/user', headers=headers, timeout=10)
                if response.status_code == 200:
                    self.logger.info("GitHub token validation successful")
                else:
                    self.validation_results['warnings'].append("GitHub token may be invalid or expired")
            except Exception as e:
                self.validation_results['warnings'].append(f"GitHub token validation failed: {str(e)}")
        
        # Validate Mailjet credentials
        mailjet_key = os.environ.get('MAILJET_API_KEY')
        mailjet_secret = os.environ.get('MAILJET_API_SECRET')
        if mailjet_key and mailjet_secret:
            try:
                response = requests.get(
                    'https://api.mailjet.com/v3/REST/contact',
                    auth=(mailjet_key, mailjet_secret),
                    timeout=10
                )
                if response.status_code == 200:
                    self.logger.info("Mailjet credentials validation successful")
                else:
                    self.validation_results['warnings'].append("Mailjet credentials may be invalid")
            except Exception as e:
                self.validation_results['warnings'].append(f"Mailjet validation failed: {str(e)}")
    
    def _validate_directories(self):
        """Validate required directories and permissions"""
        required_dirs = [
            'reports',
            'screenshots', 
            'static/charts',
            'templates',
            'services'
        ]
        
        for dir_path in required_dirs:
            abs_path = os.path.abspath(dir_path)
            
            # Check if directory exists
            if not os.path.exists(abs_path):
                try:
                    os.makedirs(abs_path, exist_ok=True)
                    self.logger.info(f"Created missing directory: {abs_path}")
                except Exception as e:
                    self.validation_results['errors'].append(
                        f"Cannot create required directory {abs_path}: {str(e)}"
                    )
                    continue
            
            # Check write permissions
            if not os.access(abs_path, os.W_OK):
                self.validation_results['errors'].append(
                    f"No write permission for directory: {abs_path}"
                )
    
    def _validate_dependencies(self):
        """Validate critical Python dependencies"""
        critical_deps = [
            ('flask', 'Flask web framework'),
            ('requests', 'HTTP library for API calls'),
            ('selenium', 'Web automation for UI testing'),
            ('plotly', 'Chart generation library'),
            ('pandas', 'Data analysis library'),
            ('jinja2', 'Template engine'),
            ('python-dotenv', 'Environment variable management')
        ]
        
        optional_deps = [
            ('google-generativeai', 'Gemini AI integration'),
            ('PyGithub', 'GitHub API integration'),
            ('matplotlib', 'Additional charting capabilities'),
            ('numpy', 'Numerical computing'),
            ('pdfkit', 'PDF export functionality')
        ]
        
        # Check critical dependencies
        for dep_name, description in critical_deps:
            try:
                if dep_name == 'python-dotenv':
                    import dotenv
                else:
                    __import__(dep_name.replace('-', '_'))
            except ImportError:
                self.validation_results['errors'].append(
                    f"Missing critical dependency: {dep_name} ({description})"
                )
        
        # Check optional dependencies
        for dep_name, description in optional_deps:
            try:
                if dep_name == 'google-generativeai':
                    import google.generativeai
                elif dep_name == 'PyGithub':
                    import github
                else:
                    __import__(dep_name.replace('-', '_'))
            except ImportError:
                self.validation_results['recommendations'].append(
                    f"Consider installing {dep_name} for enhanced functionality: {description}"
                )
    
    def _validate_network_connectivity(self):
        """Validate network connectivity to external services"""
        test_urls = [
            ('https://api.github.com', 'GitHub API'),
            ('https://generativelanguage.googleapis.com', 'Gemini AI API'),
            ('https://api.mailjet.com', 'Mailjet API'),
            ('https://httpbin.org/get', 'HTTP testing service')
        ]
        
        for url, service_name in test_urls:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code < 400:
                    self.logger.debug(f"Network connectivity to {service_name}: OK")
                else:
                    self.validation_results['warnings'].append(
                        f"Network connectivity issue with {service_name}: HTTP {response.status_code}"
                    )
            except requests.exceptions.Timeout:
                self.validation_results['warnings'].append(
                    f"Network timeout connecting to {service_name}"
                )
            except requests.exceptions.ConnectionError:
                self.validation_results['warnings'].append(
                    f"Cannot connect to {service_name} - check internet connection"
                )
            except Exception as e:
                self.validation_results['warnings'].append(
                    f"Network test failed for {service_name}: {str(e)}"
                )
    
    def _validate_system_resources(self):
        """Validate system resources for optimal performance"""
        try:
            import psutil
            
            # Check memory
            memory = psutil.virtual_memory()
            if memory.available < 512 * 1024 * 1024:  # 512MB
                self.validation_results['warnings'].append(
                    f"Low available memory: {memory.available / (1024*1024):.1f}MB"
                )
            
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 90:
                self.validation_results['warnings'].append(
                    f"High CPU usage: {cpu_percent}%"
                )
            
            # Check disk usage
            disk = psutil.disk_usage('.')
            if disk.free < 1024 * 1024 * 1024:  # 1GB
                self.validation_results['warnings'].append(
                    f"Low disk space: {disk.free / (1024*1024*1024):.1f}GB available"
                )
                
        except ImportError:
            self.validation_results['recommendations'].append(
                "Install psutil for system resource monitoring: pip install psutil"
            )
        except Exception as e:
            self.validation_results['warnings'].append(
                f"System resource check failed: {str(e)}"
            )
    
    def get_validation_summary(self) -> str:
        """Get a formatted summary of validation results"""
        results = self.validation_results
        
        summary = []
        summary.append("=== AutoTestify Configuration Validation Summary ===\n")
        
        if results['valid']:
            summary.append("[OK] Configuration is VALID - All critical requirements met\n")
        else:
            summary.append("[ERROR] Configuration has ERRORS - Please fix before proceeding\n")
        
        if results['errors']:
            summary.append("[ERRORS] (Must Fix):")
            for error in results['errors']:
                summary.append(f"  - {error}")
            summary.append("")
        
        if results['warnings']:
            summary.append("[WARNINGS] (Should Fix):")
            for warning in results['warnings']:
                summary.append(f"  - {warning}")
            summary.append("")
        
        if results['recommendations']:
            summary.append("[RECOMMENDATIONS] (Optional):")
            for rec in results['recommendations']:
                summary.append(f"  - {rec}")
            summary.append("")
        
        summary.append("=== End of Validation Summary ===")
        
        return "\n".join(summary)
    
    def fix_common_issues(self) -> List[str]:
        """Attempt to fix common configuration issues automatically"""
        fixes_applied = []
        
        # Create missing directories
        required_dirs = ['reports', 'screenshots', 'static/charts']
        for dir_path in required_dirs:
            if not os.path.exists(dir_path):
                try:
                    os.makedirs(dir_path, exist_ok=True)
                    fixes_applied.append(f"Created directory: {dir_path}")
                except Exception as e:
                    self.logger.error(f"Failed to create directory {dir_path}: {e}")
        
        # Set default SECRET_KEY if missing
        if not os.environ.get('SECRET_KEY'):
            import secrets
            default_key = secrets.token_hex(32)
            os.environ['SECRET_KEY'] = default_key
            fixes_applied.append("Generated default SECRET_KEY (consider setting a permanent one)")
        
        return fixes_applied

def validate_configuration() -> Dict:
    """Convenience function to validate configuration"""
    validator = ConfigValidator()
    return validator.validate_all_configs()

def print_validation_summary():
    """Print validation summary to console"""
    validator = ConfigValidator()
    results = validator.validate_all_configs()
    print(validator.get_validation_summary())
    return results

if __name__ == "__main__":
    # Run validation when script is executed directly
    print_validation_summary()