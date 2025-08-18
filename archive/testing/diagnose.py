#!/usr/bin/env python3
"""
DocXP Diagnostic Tool
Run this to diagnose and troubleshoot common issues
"""

import sys
import os
import json
import subprocess
from pathlib import Path
from datetime import datetime
import socket
import shutil

class DocXPDiagnostic:
    """Comprehensive diagnostic tool for DocXP"""
    
    def __init__(self):
        self.issues = []
        self.fixes = []
        self.warnings = []
        self.info = []
        
    def run_all_checks(self):
        """Run all diagnostic checks"""
        print("\n" + "="*60)
        print("          DocXP Diagnostic Tool")
        print("="*60)
        print("\n🔍 Running comprehensive diagnostics...\n")
        
        # Run all checks
        self.check_python_version()
        self.check_node_version()
        self.check_python_packages()
        self.check_node_modules()
        self.check_aws_config()
        self.check_database()
        self.check_file_permissions()
        self.check_ports()
        self.check_logs_for_errors()
        self.check_disk_space()
        self.check_api_endpoints()
        
        # Print results
        self.print_results()
        
    def check_python_version(self):
        """Check Python version"""
        try:
            version = sys.version_info
            if version.major >= 3 and version.minor >= 10:
                self.info.append(f"Python {version.major}.{version.minor}.{version.micro} ✓")
            else:
                self.issues.append(f"Python 3.10+ required, found {version.major}.{version.minor}")
                self.fixes.append("Install Python 3.10 or higher")
        except Exception as e:
            self.issues.append(f"Python check failed: {e}")
            
    def check_node_version(self):
        """Check Node.js version"""
        try:
            result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                self.info.append(f"Node.js {result.stdout.strip()} ✓")
            else:
                self.issues.append("Node.js not working properly")
                self.fixes.append("Reinstall Node.js")
        except FileNotFoundError:
            self.issues.append("Node.js not found")
            self.fixes.append("Install Node.js 18+ from https://nodejs.org")
        except Exception as e:
            self.issues.append(f"Node.js check failed: {e}")
            
    def check_python_packages(self):
        """Check if all required Python packages are installed"""
        try:
            import pkg_resources
            
            required = [
                'fastapi', 'uvicorn', 'sqlalchemy', 'boto3',
                'pydantic', 'aiofiles', 'python-multipart', 'psutil'
            ]
            
            installed = {pkg.key for pkg in pkg_resources.working_set}
            missing = [pkg for pkg in required if pkg not in installed]
            
            if missing:
                self.issues.append(f"Missing Python packages: {', '.join(missing)}")
                self.fixes.append(f"Run: pip install {' '.join(missing)}")
            else:
                self.info.append("All Python packages installed ✓")
        except Exception as e:
            self.issues.append(f"Package check failed: {e}")
            
    def check_node_modules(self):
        """Check if frontend dependencies are installed"""
        frontend_path = Path("../frontend/node_modules")
        if not frontend_path.exists():
            self.issues.append("Frontend dependencies not installed")
            self.fixes.append("cd ../frontend && npm install")
        else:
            # Count modules
            module_count = len(list(frontend_path.iterdir()))
            self.info.append(f"Frontend modules installed ({module_count} packages) ✓")
            
    def check_aws_config(self):
        """Check AWS configuration"""
        aws_configured = False
        
        # Check environment variables
        if os.getenv('AWS_ACCESS_KEY_ID'):
            aws_configured = True
            self.info.append("AWS credentials in environment ✓")
        
        # Check .env file
        env_file = Path(".env")
        if env_file.exists():
            with open(env_file) as f:
                content = f.read()
                if 'AWS_ACCESS_KEY_ID' in content:
                    aws_configured = True
                    self.info.append("AWS credentials in .env file ✓")
        
        if not aws_configured:
            self.warnings.append("AWS credentials not configured")
            self.fixes.append("Copy .env.template to .env and add AWS credentials (optional for AI features)")
            
    def check_database(self):
        """Check database file and status"""
        db_file = Path("docxp.db")
        if not db_file.exists():
            self.warnings.append("Database file not found (will be created on first run)")
            self.fixes.append("Run the application to auto-create database")
        else:
            # Check file size and permissions
            size_mb = db_file.stat().st_size / (1024 * 1024)
            self.info.append(f"Database exists ({size_mb:.2f} MB) ✓")
            
            if not os.access(db_file, os.W_OK):
                self.issues.append("Database file not writable")
                self.fixes.append(f"Fix permissions: chmod 664 {db_file}")
                
    def check_file_permissions(self):
        """Check critical directory permissions"""
        dirs_to_check = ['output', 'temp', 'logs', 'configs']
        
        for dir_name in dirs_to_check:
            dir_path = Path(dir_name)
            if not dir_path.exists():
                self.warnings.append(f"Directory missing: {dir_name} (will be created)")
            elif not os.access(dir_path, os.W_OK):
                self.issues.append(f"Directory not writable: {dir_name}")
                self.fixes.append(f"Fix permissions: chmod 755 {dir_name}")
            else:
                self.info.append(f"Directory {dir_name} ✓")
                
    def check_ports(self):
        """Check if required ports are available or in use by our services"""
        ports_to_check = [
            (8001, "Backend API"),
            (4200, "Frontend")
        ]
        
        for port, service in ports_to_check:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                # Port is in use, check if it's our service
                try:
                    import requests
                    if port == 8001:
                        response = requests.get(f"http://localhost:{port}/health", timeout=1)
                        if response.status_code == 200:
                            self.info.append(f"Port {port} ({service}) - DocXP running ✓")
                        else:
                            self.warnings.append(f"Port {port} in use but not DocXP")
                    else:
                        self.warnings.append(f"Port {port} ({service}) in use")
                except:
                    self.warnings.append(f"Port {port} ({service}) in use by another process")
                    self.fixes.append(f"Stop process on port {port} or change DocXP port")
            else:
                self.info.append(f"Port {port} ({service}) available ✓")
                
    def check_logs_for_errors(self):
        """Scan logs for recent errors"""
        log_file = Path("logs/docxp.log")
        error_log = Path("logs/errors.log")
        
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    # Read last 100 lines
                    lines = f.readlines()[-100:]
                    
                error_count = sum(1 for line in lines if 'ERROR' in line)
                warning_count = sum(1 for line in lines if 'WARNING' in line)
                
                if error_count > 10:
                    self.issues.append(f"High error rate: {error_count} errors in recent logs")
                    self.fixes.append("Check logs/docxp.log for details")
                elif error_count > 0:
                    self.warnings.append(f"Found {error_count} errors in recent logs")
                else:
                    self.info.append("No recent errors in logs ✓")
                    
                if warning_count > 20:
                    self.warnings.append(f"High warning rate: {warning_count} warnings")
                    
            except Exception as e:
                self.warnings.append(f"Could not read log file: {e}")
        else:
            self.info.append("No log files yet (normal for fresh install)")
            
    def check_disk_space(self):
        """Check available disk space"""
        try:
            total, used, free = shutil.disk_usage(".")
            free_gb = free / (1024**3)
            used_percent = (used / total) * 100
            
            if free_gb < 0.5:
                self.issues.append(f"Critical: Only {free_gb:.2f}GB free disk space")
                self.fixes.append("Free up disk space (minimum 500MB required)")
            elif free_gb < 1:
                self.warnings.append(f"Low disk space: {free_gb:.2f}GB free")
            else:
                self.info.append(f"Disk space: {free_gb:.1f}GB free ({100-used_percent:.1f}% available) ✓")
        except Exception as e:
            self.warnings.append(f"Disk space check failed: {e}")
            
    def check_api_endpoints(self):
        """Test API endpoints if running"""
        try:
            import requests
            
            # Test health endpoint
            response = requests.get("http://localhost:8001/health", timeout=2)
            if response.status_code == 200:
                self.info.append("API health endpoint responding ✓")
                
                # Test detailed health
                response = requests.get("http://localhost:8001/health/detailed", timeout=2)
                if response.status_code == 200:
                    health_data = response.json()
                    if health_data.get('status') == 'healthy':
                        self.info.append("All services healthy ✓")
                    elif health_data.get('status') == 'degraded':
                        self.warnings.append("Some services degraded")
                    else:
                        self.issues.append("Services unhealthy")
                        
        except requests.exceptions.ConnectionError:
            self.info.append("API not running (normal if not started)")
        except Exception as e:
            self.warnings.append(f"API check error: {e}")
            
    def print_results(self):
        """Print diagnostic results"""
        print("\n" + "="*60)
        print("           DIAGNOSTIC RESULTS")
        print("="*60)
        
        # Print info
        if self.info:
            print("\n✅ HEALTHY COMPONENTS:")
            for item in self.info:
                print(f"  ✓ {item}")
                
        # Print warnings
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  ⚠ {warning}")
                
        # Print issues and fixes
        if self.issues:
            print("\n❌ ISSUES FOUND:")
            for issue, fix in zip(self.issues, self.fixes):
                print(f"  ✗ {issue}")
                print(f"    → FIX: {fix}")
                
        # Summary
        print("\n" + "="*60)
        if not self.issues:
            print("✅ DIAGNOSTIC PASSED - No critical issues found!")
            if self.warnings:
                print(f"   ({len(self.warnings)} warnings - review above)")
        else:
            print(f"❌ DIAGNOSTIC FAILED - {len(self.issues)} issue(s) need attention")
            print("   Please fix the issues above and run again")
            
        # Save report
        self.save_report()
        
    def save_report(self):
        """Save diagnostic report to file"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "issues": len(self.issues),
                "warnings": len(self.warnings),
                "healthy": len(self.info)
            },
            "issues": self.issues,
            "fixes": self.fixes,
            "warnings": self.warnings,
            "info": self.info
        }
        
        report_file = Path("diagnostic_report.json")
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
            
        print(f"\n📄 Full report saved to: {report_file}")
        print("="*60)

if __name__ == "__main__":
    try:
        diagnostic = DocXPDiagnostic()
        diagnostic.run_all_checks()
        
        # Exit with appropriate code
        sys.exit(0 if not diagnostic.issues else 1)
        
    except KeyboardInterrupt:
        print("\n\nDiagnostic cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Diagnostic tool error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
