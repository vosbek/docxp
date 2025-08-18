# jQAssistant Integration Guide for DocXP

## Overview

This guide provides comprehensive documentation for the jQAssistant integration in DocXP, which adds enterprise-grade Java architecture analysis capabilities to the existing V1 indexing pipeline.

## Table of Contents

1. [Features](#features)
2. [Architecture](#architecture)
3. [Installation & Setup](#installation--setup)
4. [Quick Start](#quick-start)
5. [API Reference](#api-reference)
6. [Frontend Components](#frontend-components)
7. [Configuration](#configuration)
8. [Integration Examples](#integration-examples)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)

## Features

### Core Analysis Capabilities

- **Package Dependency Analysis**: Complete dependency mapping between Java packages
- **Architectural Layer Compliance**: Validation of layered architecture patterns
- **Cyclic Dependency Detection**: Identification and visualization of dependency cycles
- **Dead Code Identification**: Detection of unused classes, methods, and fields
- **Design Pattern Recognition**: Automatic identification of common design patterns
- **Code Quality Metrics**: Comprehensive metrics for complexity, coupling, and cohesion

### Enterprise Features

- **Batch Processing**: Support for large codebases (100k+ files)
- **Fault Tolerance**: Checkpoint/resume capability for long-running analyses
- **Progress Tracking**: Real-time progress monitoring with SSE
- **Neo4j Integration**: Graph database for advanced architectural queries
- **V1 Pipeline Integration**: Seamless integration with existing indexing
- **Interactive Visualization**: D3.js-powered dependency graphs

## Architecture

### Service Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Layer                           │
├─────────────────┬─────────────────┬─────────────────────────┤
│ Architecture    │ Dependency      │ Compliance              │
│ Analysis        │ Graph           │ Dashboard               │
│ Component       │ Component       │ Component               │
└─────────────────┴─────────────────┴─────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────┐
│                    API Layer                                │
├─────────────────┬─────────────────┬─────────────────────────┤
│ jQAssistant     │ Enhanced        │ V1 Indexing             │
│ API             │ Indexing API    │ API                     │
└─────────────────┴─────────────────┴─────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────┐
│                  Service Layer                              │
├─────────────────┬─────────────────┬─────────────────────────┤
│ jQAssistant     │ jQAssistant     │ Enhanced V1             │
│ Service         │ Batch Service   │ Indexing Service        │
└─────────────────┴─────────────────┴─────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────┐
│                 Integration Layer                           │
├─────────────────┬─────────────────┬─────────────────────────┤
│ Neo4j           │ V1 Indexing     │ Code Entity             │
│ Graph DB        │ Pipeline        │ Enrichment              │
└─────────────────┴─────────────────┴─────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────┐
│                 Data Layer                                  │
├─────────────────┬─────────────────┬─────────────────────────┤
│ PostgreSQL      │ OpenSearch      │ Redis                   │
│ (Analysis       │ (Search Index)  │ (Cache & Queue)         │
│ Results)        │                 │                         │
└─────────────────┴─────────────────┴─────────────────────────┘
```

### Database Models

The integration extends the existing database schema with comprehensive architectural analysis models:

- **ArchitecturalAnalysisJob**: Main job tracking
- **PackageDependency**: Dependency relationships
- **ArchitecturalViolation**: Constraint violations
- **DesignPattern**: Detected patterns
- **DeadCodeElement**: Unused code elements
- **CodeMetrics**: Quality metrics
- **ArchitecturalInsight**: High-level recommendations

## Installation & Setup

### Prerequisites

1. **jQAssistant CLI**: Install jQAssistant command-line interface
2. **Neo4j Database**: For graph-based analysis (optional but recommended)
3. **Java Runtime**: JRE 11+ for jQAssistant execution

### jQAssistant Installation

#### Option 1: Package Manager (Recommended)

```bash
# Ubuntu/Debian
sudo apt-get install jqassistant

# macOS with Homebrew
brew install jqassistant

# CentOS/RHEL
sudo yum install jqassistant
```

#### Option 2: Manual Installation

```bash
# Download and extract jQAssistant
wget https://repo1.maven.org/maven2/com/buschmais/jqassistant/jqassistant-commandline-distribution/2.0.0/jqassistant-commandline-distribution-2.0.0-bin.zip
unzip jqassistant-commandline-distribution-2.0.0-bin.zip
sudo mv jqassistant-commandline-distribution-2.0.0 /opt/jqassistant
sudo ln -s /opt/jqassistant/bin/jqassistant.sh /usr/local/bin/jqassistant
```

### Neo4j Setup (Optional)

```bash
# Install Neo4j
sudo apt-get install neo4j

# Configure Neo4j
sudo systemctl enable neo4j
sudo systemctl start neo4j

# Set initial password
neo4j-admin set-initial-password your-password
```

### DocXP Configuration

Add to your `backend/app/core/config.py`:

```python
# jQAssistant Configuration
JQA_NEO4J_URL = "bolt://localhost:7687"
JQA_NEO4J_USER = "neo4j"
JQA_NEO4J_PASSWORD = "your-password"
JQA_MAX_CONCURRENT_ANALYSES = 2
JQA_ANALYSIS_TIMEOUT_HOURS = 4
JQA_MAX_MEMORY_GB = 8
JQA_MAX_REPO_SIZE_GB = 5
```

### Database Migration

Run the database migration to create jQAssistant tables:

```bash
cd backend
python -m alembic revision --autogenerate -m "Add jQAssistant models"
python -m alembic upgrade head
```

## Quick Start

### 1. Basic Repository Analysis

```python
# Python API Example
import requests

# Start enhanced indexing with architectural analysis
response = requests.post('http://localhost:8000/api/enhanced-indexing/start', json={
    "repository_path": "/path/to/java/repository",
    "repository_id": "my-java-project",
    "job_type": "full",
    "enable_architectural_analysis": True
})

job_info = response.json()
indexing_job_id = job_info["indexing_job_id"]
architectural_job_id = job_info["architectural_analysis_job_id"]
```

### 2. Monitor Progress

```python
# Poll for status updates
import time

def monitor_progress(job_id):
    while True:
        response = requests.get(f'http://localhost:8000/api/enhanced-indexing/status/{job_id}')
        status = response.json()
        
        print(f"Overall Status: {status['overall_status']}")
        print(f"Progress: {status['overall_progress']:.1f}%")
        
        if status['overall_status'] in ['completed', 'failed']:
            break
        
        time.sleep(5)

monitor_progress(indexing_job_id)
```

### 3. Retrieve Results

```python
# Get architectural analysis results
response = requests.get(f'http://localhost:8000/api/jqassistant/analyze/results/{architectural_job_id}')
results = response.json()

print(f"Quality Score: {results['overall_quality_score']}")
print(f"Violations: {results['architectural_violations_count']}")
print(f"Cyclic Dependencies: {results['cyclic_dependencies_count']}")
```

### 4. Get Repository Health Score

```python
# Get comprehensive health assessment
response = requests.get('http://localhost:8000/api/enhanced-indexing/health-score', params={
    'repository_path': '/path/to/java/repository'
})

health = response.json()
print(f"Health Grade: {health['health_grade']} ({health['health_score']:.1f})")
print("Recommendations:")
for rec in health['recommendations']:
    print(f"  - {rec}")
```

## API Reference

### Enhanced Indexing Endpoints

#### Start Enhanced Indexing
```http
POST /api/enhanced-indexing/start
Content-Type: application/json

{
  "repository_path": "/path/to/repository",
  "repository_id": "project-name",
  "job_type": "full",
  "enable_architectural_analysis": true,
  "custom_architectural_layers": [
    {
      "name": "Controller",
      "pattern": ".*\\.controller\\..*",
      "description": "Web controllers",
      "allowed_dependencies": ["Service"],
      "forbidden_dependencies": ["Repository"]
    }
  ]
}
```

#### Get Job Status
```http
GET /api/enhanced-indexing/status/{job_id}
```

#### Get Repository Health
```http
GET /api/enhanced-indexing/health-score?repository_path=/path/to/repo
```

### jQAssistant Analysis Endpoints

#### Get Analysis Results
```http
GET /api/jqassistant/analyze/results/{job_id}
```

#### Get Dependency Graph
```http
GET /api/jqassistant/dependencies/graph/{job_id}?format=json&include_cycles=true
```

#### Get Architectural Violations
```http
GET /api/jqassistant/violations/{job_id}?severity=HIGH&violation_type=LAYER_VIOLATION
```

#### Get Architectural Insights
```http
GET /api/jqassistant/insights/{job_id}?priority=HIGH&category=STRUCTURE
```

## Frontend Components

### Architecture Analysis Component

Add the component to your Angular module:

```typescript
import { ArchitectureAnalysisComponent } from './components/architecture-analysis/architecture-analysis.component';
import { DependencyGraphComponent } from './components/dependency-graph/dependency-graph.component';

@NgModule({
  declarations: [
    ArchitectureAnalysisComponent,
    DependencyGraphComponent
  ],
  // ...
})
export class AppModule { }
```

Use in templates:

```html
<!-- Main architecture analysis interface -->
<app-architecture-analysis></app-architecture-analysis>

<!-- Standalone dependency graph -->
<app-dependency-graph [jobId]="analysisJobId" [height]="600"></app-dependency-graph>
```

### Service Integration

```typescript
import { JQAssistantService } from './services/jqassistant.service';

@Component({
  // ...
})
export class MyComponent {
  constructor(private jqAssistantService: JQAssistantService) {}

  async analyzeRepository() {
    const request = {
      repository_path: '/path/to/repo',
      repository_id: 'my-project',
      commit_hash: 'HEAD'
    };

    const response = await this.jqAssistantService.analyzeRepository(request).toPromise();
    
    // Monitor progress
    this.jqAssistantService.pollAnalysisStatus(response.job_id)
      .subscribe(status => {
        console.log('Analysis progress:', status);
      });
  }
}
```

## Configuration

### Architectural Layers

Define custom architectural layers for your organization:

```json
{
  "layers": [
    {
      "name": "API",
      "pattern": ".*\\.api\\..*",
      "description": "REST API endpoints",
      "allowed_dependencies": ["Service", "DTO"],
      "forbidden_dependencies": ["Repository", "Entity"],
      "severity_level": "HIGH"
    },
    {
      "name": "Service",
      "pattern": ".*\\.service\\..*",
      "description": "Business logic layer",
      "allowed_dependencies": ["Repository", "Entity", "DTO"],
      "forbidden_dependencies": ["API"],
      "severity_level": "HIGH"
    }
  ]
}
```

### Custom Constraints

Add organization-specific constraints:

```xml
<constraint id="custom:NamingConvention" severity="MEDIUM">
    <description>Service classes must end with 'Service'</description>
    <cypher><![CDATA[
        MATCH (t:Type)
        WHERE t.fqn =~ '.*\\.service\\..*'
        AND NOT t.name =~ '.*Service$'
        RETURN t.fqn as violating_class
    ]]></cypher>
</constraint>
```

### Performance Tuning

Configure for large repositories:

```python
# In config.py
JQA_MAX_MEMORY_GB = 16  # Increase for large codebases
JQA_MAX_CONCURRENT_ANALYSES = 1  # Reduce for memory constraints
JQA_ANALYSIS_TIMEOUT_HOURS = 8  # Increase for very large repos
INDEXING_MAX_FILES_PER_CHUNK = 25  # Reduce for memory efficiency
```

## Integration Examples

### 1. CI/CD Pipeline Integration

```yaml
# .github/workflows/architecture-analysis.yml
name: Architecture Analysis

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  architecture-analysis:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup jQAssistant
      run: |
        wget https://repo1.maven.org/maven2/com/buschmais/jqassistant/jqassistant-commandline-distribution/2.0.0/jqassistant-commandline-distribution-2.0.0-bin.zip
        unzip jqassistant-commandline-distribution-2.0.0-bin.zip
        export PATH=$PATH:$(pwd)/jqassistant-commandline-distribution-2.0.0/bin
    
    - name: Run Architecture Analysis
      run: |
        curl -X POST "${{ secrets.DOCXP_URL }}/api/enhanced-indexing/start" \
          -H "Content-Type: application/json" \
          -d '{
            "repository_path": "${{ github.workspace }}",
            "repository_id": "${{ github.repository }}",
            "job_type": "full",
            "enable_architectural_analysis": true
          }' > job_response.json
        
        JOB_ID=$(jq -r '.indexing_job_id' job_response.json)
        
        # Monitor until completion
        while true; do
          STATUS=$(curl -s "${{ secrets.DOCXP_URL }}/api/enhanced-indexing/status/$JOB_ID" | jq -r '.overall_status')
          if [[ "$STATUS" == "completed" ]]; then
            break
          elif [[ "$STATUS" == "failed" ]]; then
            echo "Analysis failed"
            exit 1
          fi
          sleep 30
        done
    
    - name: Check Quality Gates
      run: |
        HEALTH=$(curl -s "${{ secrets.DOCXP_URL }}/api/enhanced-indexing/health-score?repository_path=${{ github.workspace }}")
        SCORE=$(echo $HEALTH | jq -r '.health_score')
        
        if (( $(echo "$SCORE < 70" | bc -l) )); then
          echo "Quality gate failed: Score $SCORE is below threshold 70"
          exit 1
        fi
```

### 2. Scheduled Health Monitoring

```python
# scheduled_health_check.py
import asyncio
import logging
from datetime import datetime
from typing import List
import smtplib
from email.mime.text import MIMEText

from app.services.enhanced_v1_indexing_service import get_enhanced_v1_indexing_service

class ArchitecturalHealthMonitor:
    def __init__(self):
        self.repositories = [
            "/path/to/core-services",
            "/path/to/web-portal", 
            "/path/to/data-processor"
        ]
        self.health_threshold = 75.0
        self.notification_email = "architecture-team@company.com"
    
    async def run_health_checks(self):
        """Run health checks on all monitored repositories"""
        service = await get_enhanced_v1_indexing_service()
        health_reports = []
        
        for repo_path in self.repositories:
            try:
                health = await service.get_repository_health_score(repo_path)
                health_reports.append({
                    'repository': repo_path,
                    'health': health
                })
                
                # Trigger analysis if no recent data
                if health['status'] == 'no_analysis':
                    await self.trigger_analysis(repo_path)
                    
            except Exception as e:
                logging.error(f"Health check failed for {repo_path}: {e}")
        
        await self.process_health_reports(health_reports)
    
    async def trigger_analysis(self, repo_path: str):
        """Trigger analysis for repository with no recent data"""
        service = await get_enhanced_v1_indexing_service()
        
        result = await service.start_enhanced_indexing_job(
            repository_path=repo_path,
            repository_id=repo_path.split('/')[-1],
            job_type='full',
            enable_architectural_analysis=True
        )
        
        logging.info(f"Triggered analysis for {repo_path}: {result['indexing_job_id']}")
    
    async def process_health_reports(self, reports: List[dict]):
        """Process health reports and send notifications"""
        unhealthy_repos = []
        
        for report in reports:
            health = report['health']
            if health.get('health_score', 0) < self.health_threshold:
                unhealthy_repos.append(report)
        
        if unhealthy_repos:
            await self.send_health_alert(unhealthy_repos)
    
    async def send_health_alert(self, unhealthy_repos: List[dict]):
        """Send email alert for unhealthy repositories"""
        subject = f"Architecture Health Alert - {len(unhealthy_repos)} repositories below threshold"
        
        message_body = "The following repositories have architectural health scores below the threshold:\n\n"
        
        for repo in unhealthy_repos:
            health = repo['health']
            message_body += f"Repository: {repo['repository']}\n"
            message_body += f"Health Score: {health.get('health_score', 'N/A')}\n"
            message_body += f"Health Grade: {health.get('health_grade', 'N/A')}\n"
            
            if health.get('recommendations'):
                message_body += "Recommendations:\n"
                for rec in health['recommendations']:
                    message_body += f"  - {rec}\n"
            message_body += "\n"
        
        # Send email notification
        msg = MIMEText(message_body)
        msg['Subject'] = subject
        msg['From'] = 'docxp-monitor@company.com'
        msg['To'] = self.notification_email
        
        # Configure SMTP and send
        # Implementation depends on your email setup

# Run as scheduled task
if __name__ == "__main__":
    monitor = ArchitecturalHealthMonitor()
    asyncio.run(monitor.run_health_checks())
```

### 3. Custom Analysis Rules

```python
# custom_analysis_rules.py
from app.services.jqassistant_service import ArchitecturalLayer

class EnterpriseArchitecturalRules:
    """Custom architectural rules for enterprise applications"""
    
    @staticmethod
    def get_microservices_layers():
        """Architectural layers for microservices architecture"""
        return [
            ArchitecturalLayer(
                name="API Gateway",
                pattern=r".*\.gateway\..*",
                description="API Gateway and routing layer",
                allowed_dependencies=["Service Discovery", "Security"],
                forbidden_dependencies=["Database", "Message Queue"],
                severity_level="CRITICAL"
            ),
            ArchitecturalLayer(
                name="Service Layer",
                pattern=r".*\.service\..*",
                description="Business service implementations",
                allowed_dependencies=["Repository", "Message Queue", "External API"],
                forbidden_dependencies=["API Gateway"],
                severity_level="HIGH"
            ),
            ArchitecturalLayer(
                name="Repository",
                pattern=r".*\.repository\..*",
                description="Data access layer",
                allowed_dependencies=["Database", "Cache"],
                forbidden_dependencies=["Service Layer", "API Gateway"],
                severity_level="HIGH"
            )
        ]
    
    @staticmethod
    def get_spring_boot_constraints():
        """Custom constraints for Spring Boot applications"""
        return [
            "custom:ControllerRestAnnotation",
            "custom:ServiceTransactional", 
            "custom:RepositoryInterface",
            "custom:ConfigurationProperties"
        ]

# Usage in analysis
async def analyze_with_enterprise_rules(repo_path: str):
    from app.services.jqassistant_batch_service import get_jqassistant_batch_service
    
    service = await get_jqassistant_batch_service()
    rules = EnterpriseArchitecturalRules()
    
    job_id = await service.start_architectural_analysis(
        repository_path=repo_path,
        repository_id="enterprise-app",
        commit_hash="HEAD",
        custom_layers=[asdict(layer) for layer in rules.get_microservices_layers()],
        custom_constraints=rules.get_spring_boot_constraints()
    )
    
    return job_id
```

## Troubleshooting

### Common Issues

#### 1. jQAssistant Not Found
```bash
# Check if jQAssistant is in PATH
which jqassistant
# or
jqassistant --version

# If not found, verify installation
ls -la /usr/local/bin/jqassistant
ls -la /opt/jqassistant/bin/jqassistant.sh
```

#### 2. Neo4j Connection Issues
```bash
# Check Neo4j status
sudo systemctl status neo4j

# Test connection
echo "RETURN 'Hello World'" | cypher-shell -u neo4j -p your-password

# Check configuration
cat /etc/neo4j/neo4j.conf | grep bolt
```

#### 3. Memory Issues with Large Repositories
```python
# Reduce memory usage in config.py
JQA_MAX_MEMORY_GB = 4
INDEXING_MAX_FILES_PER_CHUNK = 25
JQA_MAX_CONCURRENT_ANALYSES = 1

# Enable incremental analysis
enable_architectural_analysis = False  # For initial indexing
# Then trigger separately for smaller batches
```

#### 4. Analysis Timeout
```python
# Increase timeout for large repositories
JQA_ANALYSIS_TIMEOUT_HOURS = 8

# Use selective analysis for specific packages
file_patterns = ["**/com/yourcompany/core/**/*.java"]
exclude_patterns = ["**/test/**", "**/target/**"]
```

### Log Analysis

Check logs for detailed error information:

```bash
# DocXP backend logs
tail -f backend/logs/docxp.log | grep -i jqassistant

# jQAssistant specific logs
tail -f backend/logs/jqassistant-analysis.log

# Database migration logs
tail -f backend/logs/alembic.log
```

### Performance Monitoring

```python
# Monitor analysis performance
import psutil
import time

def monitor_analysis_resources(job_id: str):
    while True:
        # Monitor CPU and memory usage
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        print(f"CPU: {cpu_percent}%, Memory: {memory.percent}%")
        
        # Check job status
        status = get_job_status(job_id)
        if status['overall_status'] in ['completed', 'failed']:
            break
        
        time.sleep(10)
```

## Best Practices

### 1. Repository Preparation

- **Clean Build**: Ensure repositories are compiled before analysis
- **Dependency Resolution**: Run `mvn dependency:resolve` or `gradle build`
- **Exclude Test Code**: For production analysis, exclude test directories
- **Size Management**: Split very large repositories into modules

### 2. Analysis Strategy

- **Incremental Analysis**: Use incremental mode for regular monitoring
- **Batch Processing**: Process multiple repositories during off-peak hours
- **Custom Rules**: Develop organization-specific architectural rules
- **Quality Gates**: Implement quality thresholds in CI/CD pipelines

### 3. Performance Optimization

```python
# Optimal configuration for different repository sizes
SMALL_REPO_CONFIG = {
    'max_memory_gb': 2,
    'max_files_per_chunk': 50,
    'concurrent_analyses': 3
}

MEDIUM_REPO_CONFIG = {
    'max_memory_gb': 4,
    'max_files_per_chunk': 25,
    'concurrent_analyses': 2
}

LARGE_REPO_CONFIG = {
    'max_memory_gb': 8,
    'max_files_per_chunk': 10,
    'concurrent_analyses': 1
}
```

### 4. Monitoring and Alerting

- **Health Score Tracking**: Monitor repository health scores over time
- **Violation Trends**: Track architectural violation trends
- **Performance Metrics**: Monitor analysis duration and resource usage
- **Automated Reporting**: Generate regular architectural health reports

### 5. Team Integration

- **Architectural Reviews**: Use insights for code review processes
- **Training Material**: Use violation examples for developer training
- **Documentation**: Maintain architectural decision records (ADRs)
- **Governance**: Establish architectural governance processes

## Conclusion

The jQAssistant integration provides comprehensive architectural analysis capabilities for Java codebases within the DocXP ecosystem. By following this guide, you can leverage enterprise-grade architectural analysis to improve code quality, maintain architectural integrity, and support informed decision-making in your software development lifecycle.

For additional support or questions, please refer to the DocXP documentation or contact the development team.