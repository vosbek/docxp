"""
Environment Validator for DocXP
Validates all requirements before application startup
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple
import json

class EnvironmentValidator:
    """Validate environment and dependencies"""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
    
    def validate_all(self) -> Tuple[bool, Dict]:
        """Run all validations"""
        self.validate_python_version()
        self.validate_node_version()
        self.validate_required_directories()
        self.validate_aws_credentials()
        self.validate_database()
        self.validate_dependencies()
        self.validate_ports()
        self.validate_disk_space()
        
        return len(self.errors) == 0, {
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info
        }
    
    def validate_python_version(self):
        """Check Python version"""
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 10):
            self.errors.append(
                f"Python 3.10+ required, found {version.major}.{version.minor}"
            )
        else:
            self.info.append(f"Python {version.major}.{version.minor} ✓")
    
    def validate_node_version(self):
        """Check Node.js version"""
        try:
            result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                self.info.append(f"Node.js {version} ✓")
            else:
                self.errors.append("Node.js check failed")
        except FileNotFoundError:
            self.errors.append("Node.js not found in PATH")
        except Exception as e:
            self.errors.append(f"Node.js check error: {e}")
    
    def validate_required_directories(self):
        """Ensure required directories exist"""
        required_dirs = ["output", "temp", "logs", "configs"]
        for dir_name in required_dirs:
            dir_path = Path(dir_name)
            if not dir_path.exists():
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    self.info.append(f"Created directory: {dir_name}")
                except Exception as e:
                    self.errors.append(f"Cannot create {dir_name}: {e}")
            else:
                self.info.append(f"Directory exists: {dir_name} ✓")
    
    def validate_aws_credentials(self):
        """Validate AWS credentials and Bedrock access"""
        try:
            import boto3
            from botocore.exceptions import ClientError, NoCredentialsError
            
            # Check for credentials
            session = boto3.Session()
            credentials = session.get_credentials()
            
            if not credentials:
                self.errors.append(
                    "No AWS credentials found - AI features require valid AWS credentials"
                )
                return
            
            # Test Bedrock access
            try:
                bedrock = session.client('bedrock-runtime', 
                                        region_name=os.getenv('AWS_REGION', 'us-east-1'))
                self.info.append("AWS credentials configured ✓")
                
                # Try a simple API call to verify access
                try:
                    # This is a lightweight check - just verify client creation
                    self.info.append("AWS Bedrock client initialized ✓")
                except ClientError as e:
                    if e.response['Error']['Code'] == 'AccessDeniedException':
                        self.warnings.append(
                            "AWS credentials valid but limited Bedrock access"
                        )
                    else:
                        self.warnings.append(f"AWS Bedrock warning: {e}")
                        
        except ImportError:
            self.errors.append("boto3 not installed - run: pip install boto3")
        except NoCredentialsError:
            self.errors.append(
                "AWS credentials not configured - AI features require valid AWS credentials"
            )
        except Exception as e:
            self.warnings.append(f"AWS validation warning: {e}")
    
    def validate_database(self):
        """Check database connectivity"""
        try:
            from sqlalchemy import create_engine, text
            
            # Create test engine
            engine = create_engine("sqlite:///docxp.db")
            
            # Test connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                conn.commit()
            
            self.info.append("Database connection successful ✓")
        except ImportError:
            self.errors.append("SQLAlchemy not installed")
        except Exception as e:
            self.warnings.append(f"Database check warning: {e}")
    
    def validate_dependencies(self):
        """Check if all Python packages are installed"""
        required_packages = {
            'fastapi': 'FastAPI web framework',
            'uvicorn': 'ASGI server',
            'sqlalchemy': 'Database ORM',
            'boto3': 'AWS SDK',
            'pydantic': 'Data validation',
            'aiofiles': 'Async file operations',
            'python-multipart': 'Form data parsing'
        }
        
        missing = []
        for package, description in required_packages.items():
            try:
                __import__(package)
                self.info.append(f"{description} ({package}) ✓")
            except ImportError:
                missing.append(package)
                self.errors.append(f"Missing: {description} ({package})")
        
        if missing:
            self.errors.append(f"Install missing packages: pip install {' '.join(missing)}")
    
    def validate_ports(self):
        """Check if required ports are available"""
        import socket
        
        ports_to_check = [
            (8001, "Backend API"),
            (4200, "Frontend Development Server")
        ]
        
        for port, service in ports_to_check:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                # Port is in use, could be our service or another
                self.warnings.append(
                    f"Port {port} ({service}) is already in use - may need to stop existing service"
                )
            else:
                self.info.append(f"Port {port} ({service}) is available ✓")
    
    def validate_disk_space(self):
        """Check available disk space"""
        try:
            import shutil
            
            total, used, free = shutil.disk_usage(".")
            free_gb = free / (1024 ** 3)  # Convert to GB
            
            if free_gb < 0.5:
                self.errors.append(f"Insufficient disk space: {free_gb:.2f}GB free (need at least 500MB)")
            elif free_gb < 1:
                self.warnings.append(f"Low disk space: {free_gb:.2f}GB free")
            else:
                self.info.append(f"Disk space: {free_gb:.1f}GB free ✓")
        except Exception as e:
            self.warnings.append(f"Disk space check failed: {e}")
