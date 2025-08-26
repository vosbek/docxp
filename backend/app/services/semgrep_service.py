"""
Semgrep Static Analysis Service

Advanced static analysis integration for DocXP providing:
- Security vulnerability detection (OWASP Top 10)
- Code quality and anti-pattern analysis
- Custom enterprise rule enforcement
- Integration with indexing pipeline for enriched search results
"""

import asyncio
import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import hashlib

from app.core.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class SemgrepFinding:
    """Represents a Semgrep static analysis finding"""
    rule_id: str
    severity: str  # 'ERROR', 'WARNING', 'INFO'
    category: str  # 'security', 'correctness', 'performance', 'maintainability'
    message: str
    file_path: str
    start_line: int
    end_line: int
    start_column: int
    end_column: int
    code_snippet: str
    rule_source: str  # 'semgrep-rules', 'custom', 'enterprise'
    confidence: str  # 'HIGH', 'MEDIUM', 'LOW'
    cwe_ids: List[str]  # Common Weakness Enumeration IDs
    owasp_categories: List[str]  # OWASP Top 10 categories
    fix_suggestion: Optional[str] = None
    references: List[str] = None

@dataclass
class SemgrepAnalysisResult:
    """Results of Semgrep analysis on a repository"""
    repo_id: str
    commit_hash: str
    analysis_timestamp: datetime
    total_findings: int
    findings_by_severity: Dict[str, int]
    findings_by_category: Dict[str, int]
    critical_security_issues: int
    performance_issues: int
    maintainability_score: float  # 0-100, higher is better
    findings: List[SemgrepFinding]
    analysis_duration_seconds: float
    rules_used: List[str]

class SemgrepService:
    """
    Semgrep integration service for advanced static analysis
    
    Provides comprehensive code analysis including:
    - Security vulnerability detection
    - Code quality assessment
    - Custom enterprise rule enforcement
    - Integration with search and indexing pipeline
    """
    
    def __init__(self):
        self.semgrep_binary = self._find_semgrep_binary()
        self.rules_cache = {}
        self.analysis_cache = {}
        self.custom_rules_path = Path("config/semgrep/custom_rules")
        self.enterprise_rules_path = Path("config/semgrep/enterprise_rules")
        
        # Rule sets configuration
        self.rule_sets = {
            'security': [
                'p/security-audit',
                'p/owasp-top-ten', 
                'p/cwe-top-25',
                'p/secrets'
            ],
            'quality': [
                'p/code-quality',
                'p/correctness',
                'p/performance'
            ],
            'enterprise': [
                'custom/legacy-patterns',
                'custom/architecture-compliance',
                'custom/naming-conventions'
            ]
        }
        
        # Language-specific configurations
        self.language_configs = {
            'java': {
                'rules': ['p/java', 'p/spring', 'p/struts'],
                'extensions': ['.java', '.jsp'],
                'custom_rules': ['java-security', 'java-performance', 'struts-security']
            },
            'javascript': {
                'rules': ['p/javascript', 'p/typescript', 'p/nodejs'],
                'extensions': ['.js', '.ts', '.jsx', '.tsx'],
                'custom_rules': ['js-security', 'angular-patterns']
            },
            'python': {
                'rules': ['p/python', 'p/flask', 'p/django'],
                'extensions': ['.py'],
                'custom_rules': ['python-security', 'fastapi-patterns']
            },
            'sql': {
                'rules': ['p/sql'],
                'extensions': ['.sql'],
                'custom_rules': ['sql-injection', 'oracle-patterns']
            }
        }
        
    def _find_semgrep_binary(self) -> str:
        """Find Semgrep binary in system PATH"""
        try:
            result = subprocess.run(['which', 'semgrep'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
            
        # Try common locations
        common_paths = [
            '/usr/local/bin/semgrep',
            '/usr/bin/semgrep',
            '~/.local/bin/semgrep',
            'semgrep'  # Assume in PATH
        ]
        
        for path in common_paths:
            try:
                expanded_path = Path(path).expanduser()
                if expanded_path.exists():
                    return str(expanded_path)
            except:
                continue
                
        return 'semgrep'  # Default fallback
    
    async def analyze_repository(
        self, 
        repo_path: Path, 
        repo_id: str,
        commit_hash: str,
        rule_sets: Optional[List[str]] = None,
        custom_rules: Optional[List[str]] = None
    ) -> SemgrepAnalysisResult:
        """
        Perform comprehensive Semgrep analysis on a repository
        
        Args:
            repo_path: Path to repository
            repo_id: Repository identifier
            commit_hash: Git commit hash
            rule_sets: Specific rule sets to use
            custom_rules: Additional custom rules
            
        Returns:
            Complete analysis results with findings and metrics
        """
        start_time = datetime.now()
        
        logger.info(f"🔍 Starting Semgrep analysis for {repo_id}@{commit_hash[:8]}")
        
        # Check cache first
        cache_key = self._generate_cache_key(repo_path, commit_hash, rule_sets, custom_rules)
        if cache_key in self.analysis_cache:
            logger.info(f"📋 Using cached Semgrep analysis for {repo_id}")
            return self.analysis_cache[cache_key]
        
        try:
            # Determine languages present in repository
            languages = await self._detect_languages(repo_path)
            logger.info(f"🔧 Detected languages: {', '.join(languages)}")
            
            # Build rule configuration
            rules_config = self._build_rules_config(languages, rule_sets, custom_rules)
            
            # Run Semgrep analysis
            findings = await self._run_semgrep_analysis(repo_path, rules_config)
            
            # Process and enrich findings
            enriched_findings = await self._enrich_findings(findings, repo_path)
            
            # Calculate metrics
            analysis_duration = (datetime.now() - start_time).total_seconds()
            
            result = SemgrepAnalysisResult(
                repo_id=repo_id,
                commit_hash=commit_hash,
                analysis_timestamp=start_time,
                total_findings=len(enriched_findings),
                findings_by_severity=self._count_by_severity(enriched_findings),
                findings_by_category=self._count_by_category(enriched_findings),
                critical_security_issues=self._count_critical_security(enriched_findings),
                performance_issues=self._count_performance_issues(enriched_findings),
                maintainability_score=self._calculate_maintainability_score(enriched_findings),
                findings=enriched_findings,
                analysis_duration_seconds=analysis_duration,
                rules_used=rules_config['rules_used']
            )
            
            # Cache results
            self.analysis_cache[cache_key] = result
            
            logger.info(f"✅ Semgrep analysis complete: {result.total_findings} findings in {analysis_duration:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Semgrep analysis failed for {repo_id}: {e}")
            raise
    
    async def analyze_file(
        self, 
        file_path: Path, 
        content: Optional[str] = None
    ) -> List[SemgrepFinding]:
        """
        Analyze a single file with Semgrep
        
        Args:
            file_path: Path to file
            content: Optional file content (if not reading from disk)
            
        Returns:
            List of findings for the file
        """
        try:
            # Determine language
            language = self._detect_file_language(file_path)
            if not language:
                return []
            
            # Build rules for this language
            rules_config = self._build_rules_config([language])
            
            # Create temporary file if content provided
            if content:
                with tempfile.NamedTemporaryFile(mode='w', suffix=file_path.suffix, delete=False) as tmp_file:
                    tmp_file.write(content)
                    analysis_path = Path(tmp_file.name)
            else:
                analysis_path = file_path
            
            try:
                # Run analysis
                findings = await self._run_semgrep_analysis(analysis_path, rules_config)
                
                # Enrich findings
                enriched_findings = await self._enrich_findings(findings, analysis_path.parent)
                
                return enriched_findings
                
            finally:
                # Clean up temporary file
                if content and analysis_path.exists():
                    analysis_path.unlink()
                    
        except Exception as e:
            logger.warning(f"Failed to analyze file {file_path}: {e}")
            return []
    
    async def get_security_summary(self, analysis_result: SemgrepAnalysisResult) -> Dict[str, Any]:
        """
        Generate security-focused summary of analysis results
        
        Args:
            analysis_result: Semgrep analysis results
            
        Returns:
            Security summary with risk assessment
        """
        security_findings = [
            f for f in analysis_result.findings 
            if f.category == 'security'
        ]
        
        # Group by OWASP categories
        owasp_issues = {}
        for finding in security_findings:
            for owasp_cat in finding.owasp_categories:
                if owasp_cat not in owasp_issues:
                    owasp_issues[owasp_cat] = []
                owasp_issues[owasp_cat].append(finding)
        
        # Group by CWE
        cwe_issues = {}
        for finding in security_findings:
            for cwe_id in finding.cwe_ids:
                if cwe_id not in cwe_issues:
                    cwe_issues[cwe_id] = []
                cwe_issues[cwe_id].append(finding)
        
        # Calculate risk score
        risk_score = self._calculate_security_risk_score(security_findings)
        
        return {
            'total_security_findings': len(security_findings),
            'critical_vulnerabilities': len([f for f in security_findings if f.severity == 'ERROR']),
            'risk_score': risk_score,
            'risk_level': self._determine_risk_level(risk_score),
            'owasp_top_10_issues': owasp_issues,
            'cwe_categories': cwe_issues,
            'most_critical_findings': sorted(
                security_findings, 
                key=lambda f: (f.severity == 'ERROR', f.confidence == 'HIGH'),
                reverse=True
            )[:10],
            'remediation_priority': self._generate_remediation_priorities(security_findings)
        }
    
    async def _detect_languages(self, repo_path: Path) -> List[str]:
        """Detect programming languages in repository"""
        languages = set()
        
        for file_path in repo_path.rglob('*'):
            if file_path.is_file():
                lang = self._detect_file_language(file_path)
                if lang:
                    languages.add(lang)
        
        return list(languages)
    
    def _detect_file_language(self, file_path: Path) -> Optional[str]:
        """Detect programming language of a file"""
        suffix = file_path.suffix.lower()
        
        language_map = {
            '.java': 'java',
            '.jsp': 'java',  # JSP files use Java rules
            '.js': 'javascript',
            '.ts': 'javascript',
            '.jsx': 'javascript',
            '.tsx': 'javascript',
            '.py': 'python',
            '.sql': 'sql',
            '.xml': 'xml',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.json': 'json'
        }
        
        return language_map.get(suffix)
    
    def _build_rules_config(
        self, 
        languages: List[str], 
        rule_sets: Optional[List[str]] = None,
        custom_rules: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Build Semgrep rules configuration"""
        rules = []
        rules_used = []
        
        # Add default rule sets
        if not rule_sets:
            rule_sets = ['security', 'quality']
        
        for rule_set in rule_sets:
            if rule_set in self.rule_sets:
                rules.extend(self.rule_sets[rule_set])
                rules_used.extend(self.rule_sets[rule_set])
        
        # Add language-specific rules
        for language in languages:
            if language in self.language_configs:
                lang_rules = self.language_configs[language]['rules']
                rules.extend(lang_rules)
                rules_used.extend(lang_rules)
        
        # Add custom rules
        if custom_rules:
            rules.extend(custom_rules)
            rules_used.extend(custom_rules)
        
        return {
            'rules': list(set(rules)),  # Remove duplicates
            'rules_used': rules_used
        }
    
    async def _run_semgrep_analysis(
        self, 
        target_path: Path, 
        rules_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Run Semgrep analysis and return raw findings"""
        try:
            # Build Semgrep command
            cmd = [
                self.semgrep_binary,
                '--json',
                '--no-git-ignore',
                '--disable-version-check',
                '--quiet'
            ]
            
            # Add rules
            for rule in rules_config['rules']:
                cmd.extend(['--config', rule])
            
            # Add target
            cmd.append(str(target_path))
            
            logger.debug(f"Running Semgrep command: {' '.join(cmd)}")
            
            # Execute Semgrep
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0 and process.returncode != 1:  # 1 is findings found
                logger.warning(f"Semgrep execution warning: {stderr.decode()}")
            
            # Parse JSON output
            if stdout:
                result = json.loads(stdout.decode())
                return result.get('results', [])
            else:
                return []
                
        except Exception as e:
            logger.error(f"Failed to run Semgrep: {e}")
            return []
    
    async def _enrich_findings(
        self, 
        raw_findings: List[Dict[str, Any]], 
        repo_path: Path
    ) -> List[SemgrepFinding]:
        """Enrich raw Semgrep findings with additional context"""
        enriched_findings = []
        
        for raw_finding in raw_findings:
            try:
                # Extract basic information
                check_id = raw_finding.get('check_id', '')
                message = raw_finding.get('message', '')
                severity = raw_finding.get('extra', {}).get('severity', 'INFO').upper()
                
                # Extract location information
                start = raw_finding.get('start', {})
                end = raw_finding.get('end', {})
                file_path = raw_finding.get('path', '')
                
                # Extract code snippet
                lines = raw_finding.get('extra', {}).get('lines', '')
                
                # Determine category
                category = self._determine_category(check_id, message)
                
                # Extract security metadata
                metadata = raw_finding.get('extra', {}).get('metadata', {})
                cwe_ids = metadata.get('cwe', [])
                owasp_categories = metadata.get('owasp', [])
                confidence = metadata.get('confidence', 'MEDIUM').upper()
                
                # Generate fix suggestion
                fix_suggestion = self._generate_fix_suggestion(check_id, message)
                
                # Extract references
                references = metadata.get('references', [])
                
                finding = SemgrepFinding(
                    rule_id=check_id,
                    severity=severity,
                    category=category,
                    message=message,
                    file_path=file_path,
                    start_line=start.get('line', 0),
                    end_line=end.get('line', 0),
                    start_column=start.get('col', 0),
                    end_column=end.get('col', 0),
                    code_snippet=lines,
                    rule_source=self._determine_rule_source(check_id),
                    confidence=confidence,
                    cwe_ids=cwe_ids if isinstance(cwe_ids, list) else [cwe_ids],
                    owasp_categories=owasp_categories if isinstance(owasp_categories, list) else [owasp_categories],
                    fix_suggestion=fix_suggestion,
                    references=references if isinstance(references, list) else [references]
                )
                
                enriched_findings.append(finding)
                
            except Exception as e:
                logger.warning(f"Failed to enrich finding: {e}")
                continue
        
        return enriched_findings
    
    def _determine_category(self, rule_id: str, message: str) -> str:
        """Determine finding category based on rule ID and message"""
        rule_id_lower = rule_id.lower()
        message_lower = message.lower()
        
        if any(keyword in rule_id_lower for keyword in ['security', 'injection', 'xss', 'csrf', 'auth']):
            return 'security'
        elif any(keyword in rule_id_lower for keyword in ['performance', 'slow', 'memory', 'cpu']):
            return 'performance'
        elif any(keyword in rule_id_lower for keyword in ['correctness', 'bug', 'error', 'null']):
            return 'correctness'
        elif any(keyword in rule_id_lower for keyword in ['style', 'naming', 'format', 'convention']):
            return 'maintainability'
        else:
            return 'code-quality'
    
    def _determine_rule_source(self, rule_id: str) -> str:
        """Determine the source of a rule"""
        if rule_id.startswith('custom/'):
            return 'custom'
        elif rule_id.startswith('enterprise/'):
            return 'enterprise'
        else:
            return 'semgrep-rules'
    
    def _generate_fix_suggestion(self, rule_id: str, message: str) -> Optional[str]:
        """Generate fix suggestions for common issues"""
        fix_suggestions = {
            'sql-injection': 'Use parameterized queries or prepared statements instead of string concatenation',
            'xss': 'Sanitize user input and use proper output encoding',
            'hardcoded-secret': 'Move secrets to environment variables or secure key management',
            'weak-crypto': 'Use strong cryptographic algorithms and proper key sizes',
            'path-traversal': 'Validate and sanitize file paths, use allow-lists',
            'command-injection': 'Avoid system calls with user input, use safe alternatives',
            'unsafe-reflection': 'Avoid dynamic code execution, use static alternatives'
        }
        
        rule_id_lower = rule_id.lower()
        for pattern, suggestion in fix_suggestions.items():
            if pattern in rule_id_lower:
                return suggestion
        
        return None
    
    def _count_by_severity(self, findings: List[SemgrepFinding]) -> Dict[str, int]:
        """Count findings by severity"""
        counts = {'ERROR': 0, 'WARNING': 0, 'INFO': 0}
        for finding in findings:
            counts[finding.severity] = counts.get(finding.severity, 0) + 1
        return counts
    
    def _count_by_category(self, findings: List[SemgrepFinding]) -> Dict[str, int]:
        """Count findings by category"""
        counts = {}
        for finding in findings:
            counts[finding.category] = counts.get(finding.category, 0) + 1
        return counts
    
    def _count_critical_security(self, findings: List[SemgrepFinding]) -> int:
        """Count critical security issues"""
        return len([
            f for f in findings 
            if f.category == 'security' and f.severity == 'ERROR'
        ])
    
    def _count_performance_issues(self, findings: List[SemgrepFinding]) -> int:
        """Count performance-related issues"""
        return len([
            f for f in findings 
            if f.category == 'performance'
        ])
    
    def _calculate_maintainability_score(self, findings: List[SemgrepFinding]) -> float:
        """Calculate maintainability score (0-100)"""
        if not findings:
            return 100.0
        
        # Weight different types of issues
        weights = {
            'ERROR': 10,
            'WARNING': 5,
            'INFO': 1
        }
        
        total_weight = sum(weights.get(f.severity, 1) for f in findings)
        
        # Start with 100 and subtract based on issues
        score = max(0, 100 - (total_weight * 2))
        
        return round(score, 1)
    
    def _calculate_security_risk_score(self, security_findings: List[SemgrepFinding]) -> float:
        """Calculate security risk score (0-100)"""
        if not security_findings:
            return 0.0
        
        # Weight by severity and confidence
        total_risk = 0
        for finding in security_findings:
            severity_weight = {'ERROR': 10, 'WARNING': 5, 'INFO': 1}[finding.severity]
            confidence_weight = {'HIGH': 1.0, 'MEDIUM': 0.7, 'LOW': 0.4}[finding.confidence]
            total_risk += severity_weight * confidence_weight
        
        # Normalize to 0-100 scale
        risk_score = min(100, total_risk * 2)
        
        return round(risk_score, 1)
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine risk level from score"""
        if risk_score >= 80:
            return 'CRITICAL'
        elif risk_score >= 60:
            return 'HIGH'
        elif risk_score >= 40:
            return 'MEDIUM'
        elif risk_score >= 20:
            return 'LOW'
        else:
            return 'MINIMAL'
    
    def _generate_remediation_priorities(self, security_findings: List[SemgrepFinding]) -> List[Dict[str, Any]]:
        """Generate prioritized remediation recommendations"""
        priorities = []
        
        # Group by rule ID
        rule_groups = {}
        for finding in security_findings:
            if finding.rule_id not in rule_groups:
                rule_groups[finding.rule_id] = []
            rule_groups[finding.rule_id].append(finding)
        
        # Create priority entries
        for rule_id, findings in rule_groups.items():
            critical_count = len([f for f in findings if f.severity == 'ERROR'])
            total_count = len(findings)
            
            priority = {
                'rule_id': rule_id,
                'total_occurrences': total_count,
                'critical_occurrences': critical_count,
                'priority_score': critical_count * 10 + total_count,
                'category': findings[0].category,
                'fix_suggestion': findings[0].fix_suggestion,
                'affected_files': list(set(f.file_path for f in findings))
            }
            
            priorities.append(priority)
        
        # Sort by priority score
        priorities.sort(key=lambda p: p['priority_score'], reverse=True)
        
        return priorities[:10]  # Top 10 priorities
    
    def _generate_cache_key(
        self, 
        repo_path: Path, 
        commit_hash: str,
        rule_sets: Optional[List[str]],
        custom_rules: Optional[List[str]]
    ) -> str:
        """Generate cache key for analysis results"""
        key_data = f"{repo_path}_{commit_hash}_{rule_sets}_{custom_rules}"
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    async def install_custom_rules(self, rules_directory: Path) -> bool:
        """Install custom Semgrep rules"""
        try:
            if not rules_directory.exists():
                rules_directory.mkdir(parents=True)
                logger.info(f"Created custom rules directory: {rules_directory}")
            
            # Copy custom rules if they don't exist
            # This would typically copy from a rules repository
            logger.info(f"Custom rules directory ready: {rules_directory}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to install custom rules: {e}")
            return False
    
    async def validate_installation(self) -> Dict[str, Any]:
        """Validate Semgrep installation and configuration"""
        validation = {
            'semgrep_installed': False,
            'version': None,
            'rules_available': False,
            'custom_rules_ready': False,
            'errors': []
        }
        
        try:
            # Check Semgrep installation
            process = await asyncio.create_subprocess_exec(
                self.semgrep_binary, '--version',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                validation['semgrep_installed'] = True
                validation['version'] = stdout.decode().strip()
            else:
                validation['errors'].append(f"Semgrep not found: {stderr.decode()}")
            
            # Check if rules can be loaded
            if validation['semgrep_installed']:
                test_process = await asyncio.create_subprocess_exec(
                    self.semgrep_binary, '--config', 'p/security-audit', '--dryrun',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                _, test_stderr = await test_process.communicate()
                
                if test_process.returncode == 0:
                    validation['rules_available'] = True
                else:
                    validation['errors'].append(f"Rules not available: {test_stderr.decode()}")
            
            # Check custom rules
            if self.custom_rules_path.exists():
                validation['custom_rules_ready'] = True
            
        except Exception as e:
            validation['errors'].append(f"Validation failed: {e}")
        
        return validation