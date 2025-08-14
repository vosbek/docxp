"""
Cross-Technology Integration Analyzer

Analyzes integration patterns across different technologies to support enterprise legacy migration.
Maps data flows from frontend (Angular/JSP) through REST/Actions to backend services and databases.
"""

import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict
import xml.etree.ElementTree as ET

from app.core.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class HTTPCall:
    """Represents an HTTP client call from frontend code"""
    source_file: str
    line_number: int
    method: str  # GET, POST, PUT, DELETE
    url_pattern: str
    parameters: List[str]
    context_function: Optional[str] = None
    context_class: Optional[str] = None
    is_dynamic_url: bool = False

@dataclass
class RESTEndpoint:
    """Represents a REST endpoint definition"""
    source_file: str
    line_number: int
    method: str
    path: str
    handler_function: str
    handler_class: Optional[str] = None
    parameters: List[str]
    return_type: Optional[str] = None
    framework: str = "unknown"  # spring, struts, fastapi, etc.

@dataclass
class StrutsAction:
    """Represents a Struts action mapping"""
    name: str
    class_name: str
    method: str
    path: str
    result_pages: Dict[str, str]
    source_file: str
    line_number: int
    parameters: List[str]

@dataclass
class JSPComponent:
    """Represents a JSP/JSF component or form"""
    source_file: str
    line_number: int
    component_type: str  # form, link, button, etc.
    action_url: str
    parameters: List[str]
    target_action: Optional[str] = None

@dataclass
class IntegrationFlow:
    """Represents a complete integration flow across technologies"""
    flow_id: str
    description: str
    frontend_component: Optional[Any] = None
    http_call: Optional[HTTPCall] = None
    rest_endpoint: Optional[RESTEndpoint] = None
    struts_action: Optional[StrutsAction] = None
    backend_methods: List[str] = None
    database_queries: List[str] = None
    confidence_score: float = 0.0  # 0.0 to 1.0

class IntegrationAnalyzer:
    """Analyzes cross-technology integration patterns for migration insights"""
    
    def __init__(self):
        self.http_patterns = self._compile_http_patterns()
        self.rest_patterns = self._compile_rest_patterns()
        self.struts_patterns = self._compile_struts_patterns()
        self.jsp_patterns = self._compile_jsp_patterns()
        
    def _compile_http_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for HTTP client calls"""
        return {
            # Angular HTTP client patterns
            'angular_http': re.compile(r'this\.http\.(get|post|put|delete|patch)\s*\(\s*[\'"`]([^\'"`]*)[\'"`]', re.IGNORECASE),
            'angular_httpclient': re.compile(r'(?:httpClient|http)\.(get|post|put|delete|patch)\s*\(\s*[\'"`]([^\'"`]*)[\'"`]', re.IGNORECASE),
            
            # jQuery/JavaScript AJAX patterns  
            'jquery_ajax': re.compile(r'\$\.(?:ajax|get|post)\s*\(\s*[{\'"`].*?url\s*:\s*[\'"`]([^\'"`]*)[\'"`].*?type\s*:\s*[\'"`]([^\'"`]*)[\'"`]', re.IGNORECASE | re.DOTALL),
            'fetch_api': re.compile(r'fetch\s*\(\s*[\'"`]([^\'"`]*)[\'"`].*?method\s*:\s*[\'"`]([^\'"`]*)[\'"`]', re.IGNORECASE | re.DOTALL),
            
            # Java HTTP client patterns
            'java_okhttp': re.compile(r'\.url\s*\(\s*[\'"`]([^\'"`]*)[\'"`].*?\.(?:get|post|put|delete)\s*\(', re.IGNORECASE | re.DOTALL),
            'java_httpclient': re.compile(r'HttpRequest\.newBuilder\s*\(\s*\).*?\.uri\s*\(\s*URI\.create\s*\(\s*[\'"`]([^\'"`]*)[\'"`]', re.IGNORECASE | re.DOTALL),
        }
    
    def _compile_rest_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for REST endpoint definitions"""
        return {
            # Spring Boot patterns
            'spring_requestmapping': re.compile(r'@RequestMapping\s*\(\s*value\s*=\s*[\'"`]([^\'"`]*)[\'"`].*?method\s*=\s*RequestMethod\.(\w+)', re.IGNORECASE | re.DOTALL),
            'spring_getmapping': re.compile(r'@GetMapping\s*\(\s*[\'"`]([^\'"`]*)[\'"`]\s*\).*?public.*?(\w+)\s*\(', re.IGNORECASE | re.DOTALL),
            'spring_postmapping': re.compile(r'@PostMapping\s*\(\s*[\'"`]([^\'"`]*)[\'"`]\s*\).*?public.*?(\w+)\s*\(', re.IGNORECASE | re.DOTALL),
            'spring_putmapping': re.compile(r'@PutMapping\s*\(\s*[\'"`]([^\'"`]*)[\'"`]\s*\).*?public.*?(\w+)\s*\(', re.IGNORECASE | re.DOTALL),
            'spring_deletemapping': re.compile(r'@DeleteMapping\s*\(\s*[\'"`]([^\'"`]*)[\'"`]\s*\).*?public.*?(\w+)\s*\(', re.IGNORECASE | re.DOTALL),
            
            # FastAPI patterns  
            'fastapi_get': re.compile(r'@app\.get\s*\(\s*[\'"`]([^\'"`]*)[\'"`]\s*\).*?def\s+(\w+)', re.IGNORECASE | re.DOTALL),
            'fastapi_post': re.compile(r'@app\.post\s*\(\s*[\'"`]([^\'"`]*)[\'"`]\s*\).*?def\s+(\w+)', re.IGNORECASE | re.DOTALL),
            
            # JAX-RS patterns
            'jaxrs_path': re.compile(r'@Path\s*\(\s*[\'"`]([^\'"`]*)[\'"`]\s*\).*?@(?:GET|POST|PUT|DELETE).*?public.*?(\w+)\s*\(', re.IGNORECASE | re.DOTALL),
        }
    
    def _compile_struts_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for Struts action patterns"""
        return {
            'action_class': re.compile(r'class\s+(\w+)\s+extends\s+(?:Action|ActionSupport)', re.IGNORECASE),
            'struts2_action': re.compile(r'@Action\s*\(\s*value\s*=\s*[\'"`]([^\'"`]*)[\'"`]', re.IGNORECASE),
            'struts2_result': re.compile(r'@Result\s*\(\s*location\s*=\s*[\'"`]([^\'"`]*)[\'"`]', re.IGNORECASE),
        }
    
    def _compile_jsp_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for JSP/JSF component patterns"""
        return {
            'jsp_form': re.compile(r'<form[^>]*action\s*=\s*[\'"`]([^\'"`]*)[\'"`][^>]*>', re.IGNORECASE),
            'jsp_link': re.compile(r'<a[^>]*href\s*=\s*[\'"`]([^\'"`]*)[\'"`][^>]*>', re.IGNORECASE),
            'struts_form': re.compile(r'<s:form[^>]*action\s*=\s*[\'"`]([^\'"`]*)[\'"`][^>]*>', re.IGNORECASE),
            'struts_link': re.compile(r'<s:url[^>]*action\s*=\s*[\'"`]([^\'"`]*)[\'"`][^>]*>', re.IGNORECASE),
            'jsf_form': re.compile(r'<h:form[^>]*>', re.IGNORECASE),
            'jsf_command': re.compile(r'<h:commandButton[^>]*action\s*=\s*[\'"`]([^\'"`]*)[\'"`][^>]*>', re.IGNORECASE),
        }
    
    async def analyze_integration_flows(self, file_paths: List[Path]) -> Dict[str, Any]:
        """
        Main analysis method - discovers integration flows across all technologies
        """
        logger.info(f"Starting cross-technology integration analysis of {len(file_paths)} files")
        
        # Separate files by technology
        categorized_files = self._categorize_files(file_paths)
        
        # Extract integration points from each technology
        http_calls = await self._extract_http_calls(categorized_files['frontend'])
        rest_endpoints = await self._extract_rest_endpoints(categorized_files['backend'])
        struts_actions = await self._extract_struts_actions(categorized_files['struts'])
        jsp_components = await self._extract_jsp_components(categorized_files['jsp'])
        
        # Build integration flows by matching patterns
        integration_flows = await self._build_integration_flows(
            http_calls, rest_endpoints, struts_actions, jsp_components
        )
        
        # Analyze flow patterns and generate insights
        flow_analysis = self._analyze_flow_patterns(integration_flows)
        
        results = {
            'integration_flows': [self._flow_to_dict(flow) for flow in integration_flows],
            'flow_analysis': flow_analysis,
            'technology_breakdown': {
                'http_calls': len(http_calls),
                'rest_endpoints': len(rest_endpoints),
                'struts_actions': len(struts_actions),
                'jsp_components': len(jsp_components),
                'integration_flows': len(integration_flows)
            },
            'migration_insights': self._generate_migration_insights(integration_flows, flow_analysis)
        }
        
        logger.info(f"Integration analysis completed: {len(integration_flows)} flows discovered")
        return results
    
    def _categorize_files(self, file_paths: List[Path]) -> Dict[str, List[Path]]:
        """Categorize files by technology type"""
        categories = {
            'frontend': [],
            'backend': [],
            'struts': [],
            'jsp': [],
            'config': []
        }
        
        for file_path in file_paths:
            ext = file_path.suffix.lower()
            name = file_path.name.lower()
            
            if ext in ['.ts', '.js', '.html'] and 'angular' in str(file_path).lower():
                categories['frontend'].append(file_path)
            elif ext in ['.java'] and any(keyword in str(file_path).lower() for keyword in ['controller', 'rest', 'api', 'endpoint']):
                categories['backend'].append(file_path)
            elif ext in ['.java'] and 'action' in str(file_path).lower():
                categories['struts'].append(file_path)
            elif ext in ['.jsp', '.jsf', '.jspx']:
                categories['jsp'].append(file_path)
            elif name in ['struts.xml', 'struts-config.xml', 'web.xml']:
                categories['config'].append(file_path)
            elif ext in ['.java', '.py']:
                categories['backend'].append(file_path)
        
        return categories
    
    async def _extract_http_calls(self, frontend_files: List[Path]) -> List[HTTPCall]:
        """Extract HTTP client calls from frontend files"""
        http_calls = []
        
        for file_path in frontend_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    lines = content.split('\n')
                
                # Search for HTTP call patterns
                for pattern_name, pattern in self.http_patterns.items():
                    for match in pattern.finditer(content):
                        line_number = content[:match.start()].count('\n') + 1
                        
                        if pattern_name.startswith('angular'):
                            method = match.group(1).upper()
                            url = match.group(2)
                        elif 'ajax' in pattern_name:
                            url = match.group(1)
                            method = match.group(2).upper()
                        else:
                            continue
                        
                        # Extract context (function/class containing this call)
                        context_function = self._find_containing_function(content, match.start(), lines)
                        context_class = self._find_containing_class(content, match.start(), lines)
                        
                        http_call = HTTPCall(
                            source_file=str(file_path),
                            line_number=line_number,
                            method=method,
                            url_pattern=url,
                            parameters=self._extract_url_parameters(url),
                            context_function=context_function,
                            context_class=context_class,
                            is_dynamic_url='{' in url or '${' in url or ':' in url
                        )
                        http_calls.append(http_call)
                        
            except Exception as e:
                logger.warning(f"Error extracting HTTP calls from {file_path}: {e}")
        
        return http_calls
    
    async def _extract_rest_endpoints(self, backend_files: List[Path]) -> List[RESTEndpoint]:
        """Extract REST endpoint definitions from backend files"""
        rest_endpoints = []
        
        for file_path in backend_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Detect framework
                framework = self._detect_rest_framework(content)
                
                # Search for REST endpoint patterns
                for pattern_name, pattern in self.rest_patterns.items():
                    for match in pattern.finditer(content):
                        line_number = content[:match.start()].count('\n') + 1
                        
                        if 'spring' in pattern_name:
                            if 'requestmapping' in pattern_name:
                                path = match.group(1)
                                method = match.group(2).upper()
                                handler_function = self._find_next_function(content, match.end())
                            else:
                                path = match.group(1)
                                method = pattern_name.split('_')[1].upper()  # get, post, etc.
                                handler_function = match.group(2) if match.lastindex >= 2 else self._find_next_function(content, match.end())
                        elif 'fastapi' in pattern_name:
                            path = match.group(1)
                            method = pattern_name.split('_')[1].upper()
                            handler_function = match.group(2)
                        else:
                            continue
                        
                        # Extract class context
                        context_class = self._find_containing_class(content, match.start(), content.split('\n'))
                        
                        rest_endpoint = RESTEndpoint(
                            source_file=str(file_path),
                            line_number=line_number,
                            method=method,
                            path=path,
                            handler_function=handler_function,
                            handler_class=context_class,
                            parameters=self._extract_rest_parameters(content, match.start()),
                            framework=framework
                        )
                        rest_endpoints.append(rest_endpoint)
                        
            except Exception as e:
                logger.warning(f"Error extracting REST endpoints from {file_path}: {e}")
        
        return rest_endpoints
    
    async def _extract_struts_actions(self, struts_files: List[Path]) -> List[StrutsAction]:
        """Extract Struts action definitions from configuration and Java files"""
        struts_actions = []
        
        # First, parse struts.xml configuration files
        config_actions = await self._parse_struts_config(struts_files)
        struts_actions.extend(config_actions)
        
        # Then, parse Struts action classes
        for file_path in struts_files:
            if file_path.suffix == '.java':
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Look for Struts action class patterns
                    class_match = self.struts_patterns['action_class'].search(content)
                    if class_match:
                        class_name = class_match.group(1)
                        
                        # Look for @Action annotations (Struts2)
                        for action_match in self.struts_patterns['struts2_action'].finditer(content):
                            line_number = content[:action_match.start()].count('\n') + 1
                            action_name = action_match.group(1)
                            
                            # Find associated method
                            method_name = self._find_next_function(content, action_match.end())
                            
                            # Look for @Result annotations
                            result_pages = {}
                            result_start = action_match.end()
                            method_end = self._find_method_end(content, result_start)
                            method_content = content[result_start:method_end]
                            
                            for result_match in self.struts_patterns['struts2_result'].finditer(method_content):
                                result_pages['success'] = result_match.group(1)
                            
                            struts_action = StrutsAction(
                                name=action_name,
                                class_name=class_name,
                                method=method_name or 'execute',
                                path=f"/{action_name}",
                                result_pages=result_pages,
                                source_file=str(file_path),
                                line_number=line_number,
                                parameters=[]
                            )
                            struts_actions.append(struts_action)
                            
                except Exception as e:
                    logger.warning(f"Error extracting Struts actions from {file_path}: {e}")
        
        return struts_actions
    
    async def _extract_jsp_components(self, jsp_files: List[Path]) -> List[JSPComponent]:
        """Extract JSP/JSF components that make backend calls"""
        jsp_components = []
        
        for file_path in jsp_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Search for JSP/JSF component patterns
                for pattern_name, pattern in self.jsp_patterns.items():
                    for match in pattern.finditer(content):
                        line_number = content[:match.start()].count('\n') + 1
                        
                        if pattern_name in ['jsp_form', 'struts_form']:
                            component_type = 'form'
                            action_url = match.group(1)
                        elif pattern_name in ['jsp_link', 'struts_link']:
                            component_type = 'link'
                            action_url = match.group(1)
                        elif pattern_name == 'jsf_command':
                            component_type = 'button'
                            action_url = match.group(1)
                        else:
                            continue
                        
                        jsp_component = JSPComponent(
                            source_file=str(file_path),
                            line_number=line_number,
                            component_type=component_type,
                            action_url=action_url,
                            parameters=self._extract_jsp_parameters(content, match.start()),
                            target_action=self._normalize_action_url(action_url)
                        )
                        jsp_components.append(jsp_component)
                        
            except Exception as e:
                logger.warning(f"Error extracting JSP components from {file_path}: {e}")
        
        return jsp_components
    
    async def _build_integration_flows(self, http_calls: List[HTTPCall], rest_endpoints: List[RESTEndpoint], 
                                     struts_actions: List[StrutsAction], jsp_components: List[JSPComponent]) -> List[IntegrationFlow]:
        """Build complete integration flows by matching components across technologies"""
        flows = []
        flow_id_counter = 1
        
        # Match HTTP calls to REST endpoints
        for http_call in http_calls:
            matching_endpoints = self._find_matching_endpoints(http_call, rest_endpoints)
            for endpoint in matching_endpoints:
                flow = IntegrationFlow(
                    flow_id=f"flow_{flow_id_counter}",
                    description=f"{http_call.method} {http_call.url_pattern} → {endpoint.handler_function}",
                    http_call=http_call,
                    rest_endpoint=endpoint,
                    confidence_score=self._calculate_match_confidence(http_call.url_pattern, endpoint.path)
                )
                flows.append(flow)
                flow_id_counter += 1
        
        # Match JSP components to Struts actions
        for jsp_component in jsp_components:
            matching_actions = self._find_matching_struts_actions(jsp_component, struts_actions)
            for action in matching_actions:
                flow = IntegrationFlow(
                    flow_id=f"flow_{flow_id_counter}",
                    description=f"JSP {jsp_component.component_type} → {action.name}",
                    frontend_component=jsp_component,
                    struts_action=action,
                    confidence_score=self._calculate_struts_match_confidence(jsp_component.target_action, action.name)
                )
                flows.append(flow)
                flow_id_counter += 1
        
        return flows
    
    # Helper methods for pattern matching and analysis
    def _find_containing_function(self, content: str, position: int, lines: List[str]) -> Optional[str]:
        """Find the function containing the given position"""
        line_num = content[:position].count('\n')
        
        # Look backwards for function definition
        for i in range(line_num, -1, -1):
            if i < len(lines):
                line = lines[i].strip()
                # Look for function patterns in different languages
                func_patterns = [
                    r'function\s+(\w+)',  # JavaScript
                    r'(\w+)\s*\(\s*\)\s*{',  # TypeScript method
                    r'public\s+\w+\s+(\w+)\s*\(',  # Java method
                    r'def\s+(\w+)\s*\(',  # Python
                ]
                
                for pattern in func_patterns:
                    match = re.search(pattern, line)
                    if match:
                        return match.group(1)
        return None
    
    def _find_containing_class(self, content: str, position: int, lines: List[str]) -> Optional[str]:
        """Find the class containing the given position"""
        line_num = content[:position].count('\n')
        
        # Look backwards for class definition
        for i in range(line_num, -1, -1):
            if i < len(lines):
                line = lines[i].strip()
                class_patterns = [
                    r'class\s+(\w+)',  # General class pattern
                    r'export\s+class\s+(\w+)',  # TypeScript export class
                ]
                
                for pattern in class_patterns:
                    match = re.search(pattern, line)
                    if match:
                        return match.group(1)
        return None
    
    def _extract_url_parameters(self, url: str) -> List[str]:
        """Extract parameter placeholders from URL"""
        # Extract path parameters like {id}, :id, ${id}
        patterns = [
            r'\{(\w+)\}',  # {param}
            r':(\w+)',     # :param
            r'\$\{(\w+)\}' # ${param}
        ]
        
        params = []
        for pattern in patterns:
            matches = re.findall(pattern, url)
            params.extend(matches)
        
        return params
    
    def _detect_rest_framework(self, content: str) -> str:
        """Detect the REST framework being used"""
        if '@RestController' in content or '@RequestMapping' in content:
            return 'Spring Boot'
        elif '@app.get' in content or '@app.post' in content:
            return 'FastAPI'
        elif '@Path' in content and '@GET' in content:
            return 'JAX-RS'
        elif 'extends Action' in content:
            return 'Struts'
        else:
            return 'Unknown'
    
    def _find_next_function(self, content: str, start_pos: int) -> Optional[str]:
        """Find the next function definition after the given position"""
        remaining_content = content[start_pos:]
        
        func_patterns = [
            r'public\s+\w+\s+(\w+)\s*\(',  # Java method
            r'def\s+(\w+)\s*\(',           # Python function
            r'function\s+(\w+)',           # JavaScript function
        ]
        
        for pattern in func_patterns:
            match = re.search(pattern, remaining_content)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_rest_parameters(self, content: str, position: int) -> List[str]:
        """Extract REST endpoint parameters"""
        # Look for @RequestParam, @PathVariable, @RequestBody annotations
        param_patterns = [
            r'@RequestParam\s*\(\s*[\'"](\w+)[\'"]',
            r'@PathVariable\s*\(\s*[\'"](\w+)[\'"]',
            r'@RequestBody\s+\w+\s+(\w+)',
        ]
        
        params = []
        # Look in a window around the position
        start = max(0, position - 500)
        end = min(len(content), position + 500)
        window = content[start:end]
        
        for pattern in param_patterns:
            matches = re.findall(pattern, window)
            params.extend(matches)
        
        return params
    
    async def _parse_struts_config(self, struts_files: List[Path]) -> List[StrutsAction]:
        """Parse struts.xml configuration files"""
        struts_actions = []
        
        for file_path in struts_files:
            if file_path.name.endswith('.xml'):
                try:
                    tree = ET.parse(file_path)
                    root = tree.getroot()
                    
                    # Parse action mappings
                    for action in root.findall('.//action'):
                        name = action.get('name')
                        class_name = action.get('class')
                        method = action.get('method', 'execute')
                        
                        if name and class_name:
                            # Find result pages
                            result_pages = {}
                            for result in action.findall('result'):
                                result_name = result.get('name', 'success')
                                result_location = result.text or result.get('location', '')
                                result_pages[result_name] = result_location
                            
                            struts_action = StrutsAction(
                                name=name,
                                class_name=class_name,
                                method=method,
                                path=f"/{name}",
                                result_pages=result_pages,
                                source_file=str(file_path),
                                line_number=0,  # XML line numbers are harder to extract
                                parameters=[]
                            )
                            struts_actions.append(struts_action)
                            
                except Exception as e:
                    logger.warning(f"Error parsing Struts config {file_path}: {e}")
        
        return struts_actions
    
    def _find_method_end(self, content: str, start: int) -> int:
        """Find the end of a method definition"""
        # Simple brace matching to find method end
        brace_count = 0
        in_method = False
        
        for i, char in enumerate(content[start:], start):
            if char == '{':
                in_method = True
                brace_count += 1
            elif char == '}' and in_method:
                brace_count -= 1
                if brace_count == 0:
                    return i
        
        return len(content)
    
    def _extract_jsp_parameters(self, content: str, position: int) -> List[str]:
        """Extract parameters from JSP forms and components"""
        params = []
        
        # Look for input fields in forms
        input_pattern = r'<input[^>]*name\s*=\s*[\'"]([^\'\"]*)[\'"][^>]*>'
        
        # Search in a window around the position
        start = max(0, position - 1000)
        end = min(len(content), position + 1000)
        window = content[start:end]
        
        matches = re.findall(input_pattern, window, re.IGNORECASE)
        params.extend(matches)
        
        return params
    
    def _normalize_action_url(self, url: str) -> str:
        """Normalize action URL for matching"""
        # Remove common prefixes and suffixes
        url = url.strip()
        if url.startswith('/'):
            url = url[1:]
        if url.endswith('.action'):
            url = url[:-7]
        return url
    
    def _find_matching_endpoints(self, http_call: HTTPCall, endpoints: List[RESTEndpoint]) -> List[RESTEndpoint]:
        """Find REST endpoints that match an HTTP call"""
        matches = []
        
        for endpoint in endpoints:
            if http_call.method.upper() == endpoint.method.upper():
                # Check URL pattern matching
                if self._urls_match(http_call.url_pattern, endpoint.path):
                    matches.append(endpoint)
        
        return matches
    
    def _find_matching_struts_actions(self, jsp_component: JSPComponent, actions: List[StrutsAction]) -> List[StrutsAction]:
        """Find Struts actions that match a JSP component"""
        matches = []
        
        target = jsp_component.target_action
        if not target:
            return matches
        
        for action in actions:
            if target == action.name or target in action.path:
                matches.append(action)
        
        return matches
    
    def _urls_match(self, pattern1: str, pattern2: str) -> bool:
        """Check if two URL patterns match (considering parameters)"""
        # Normalize URLs
        p1 = pattern1.strip('/')
        p2 = pattern2.strip('/')
        
        # Simple exact match first
        if p1 == p2:
            return True
        
        # Parameter-aware matching
        # Replace parameters with wildcards for matching
        p1_normalized = re.sub(r'\{[^}]+\}|:\w+|\$\{[^}]+\}', '*', p1)
        p2_normalized = re.sub(r'\{[^}]+\}|:\w+|\$\{[^}]+\}', '*', p2)
        
        return p1_normalized == p2_normalized
    
    def _calculate_match_confidence(self, url1: str, url2: str) -> float:
        """Calculate confidence score for URL matching"""
        if url1 == url2:
            return 1.0
        elif self._urls_match(url1, url2):
            return 0.8
        elif url1 in url2 or url2 in url1:
            return 0.6
        else:
            return 0.3
    
    def _calculate_struts_match_confidence(self, jsp_action: Optional[str], struts_name: str) -> float:
        """Calculate confidence score for Struts action matching"""
        if not jsp_action:
            return 0.3
        if jsp_action == struts_name:
            return 1.0
        elif jsp_action in struts_name or struts_name in jsp_action:
            return 0.7
        else:
            return 0.4
    
    def _analyze_flow_patterns(self, flows: List[IntegrationFlow]) -> Dict[str, Any]:
        """Analyze patterns in integration flows"""
        analysis = {
            'total_flows': len(flows),
            'high_confidence_flows': len([f for f in flows if f.confidence_score > 0.7]),
            'technology_pairs': defaultdict(int),
            'most_common_endpoints': defaultdict(int),
            'complex_flows': []
        }
        
        for flow in flows:
            # Track technology pairs
            if flow.http_call and flow.rest_endpoint:
                analysis['technology_pairs']['Angular→REST'] += 1
            elif flow.frontend_component and flow.struts_action:
                analysis['technology_pairs']['JSP→Struts'] += 1
            
            # Track endpoint usage
            if flow.rest_endpoint:
                analysis['most_common_endpoints'][flow.rest_endpoint.path] += 1
            elif flow.struts_action:
                analysis['most_common_endpoints'][flow.struts_action.name] += 1
        
        # Find most common endpoints
        analysis['most_common_endpoints'] = dict(
            sorted(analysis['most_common_endpoints'].items(), 
                  key=lambda x: x[1], reverse=True)[:10]
        )
        
        return analysis
    
    def _generate_migration_insights(self, flows: List[IntegrationFlow], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate migration-specific insights from integration flows"""
        insights = {
            'modernization_opportunities': [],
            'risk_assessments': [],
            'technology_dependencies': {},
            'migration_complexity': 'Medium'
        }
        
        # Analyze technology dependencies
        if analysis['technology_pairs'].get('JSP→Struts', 0) > 0:
            insights['risk_assessments'].append({
                'type': 'Legacy Framework Dependency',
                'description': f"Found {analysis['technology_pairs']['JSP→Struts']} JSP→Struts integrations",
                'risk_level': 'High',
                'recommendation': 'Consider migrating to modern REST APIs'
            })
        
        if analysis['technology_pairs'].get('Angular→REST', 0) > 0:
            insights['modernization_opportunities'].append({
                'type': 'Modern API Integration',
                'description': f"Found {analysis['technology_pairs']['Angular→REST']} Angular→REST integrations",
                'opportunity': 'Well-positioned for microservices migration'
            })
        
        # Determine migration complexity
        total_legacy_flows = analysis['technology_pairs'].get('JSP→Struts', 0)
        total_modern_flows = analysis['technology_pairs'].get('Angular→REST', 0)
        
        if total_legacy_flows > total_modern_flows * 2:
            insights['migration_complexity'] = 'High'
        elif total_modern_flows > total_legacy_flows:
            insights['migration_complexity'] = 'Low'
        
        return insights
    
    def _flow_to_dict(self, flow: IntegrationFlow) -> Dict[str, Any]:
        """Convert IntegrationFlow to dictionary for JSON serialization"""
        return {
            'flow_id': flow.flow_id,
            'description': flow.description,
            'confidence_score': flow.confidence_score,
            'frontend_component': self._component_to_dict(flow.frontend_component) if flow.frontend_component else None,
            'http_call': self._http_call_to_dict(flow.http_call) if flow.http_call else None,
            'rest_endpoint': self._rest_endpoint_to_dict(flow.rest_endpoint) if flow.rest_endpoint else None,
            'struts_action': self._struts_action_to_dict(flow.struts_action) if flow.struts_action else None,
            'backend_methods': flow.backend_methods or [],
            'database_queries': flow.database_queries or []
        }
    
    def _http_call_to_dict(self, http_call: HTTPCall) -> Dict[str, Any]:
        """Convert HTTPCall to dictionary"""
        return {
            'source_file': http_call.source_file,
            'line_number': http_call.line_number,
            'method': http_call.method,
            'url_pattern': http_call.url_pattern,
            'parameters': http_call.parameters,
            'context_function': http_call.context_function,
            'context_class': http_call.context_class,
            'is_dynamic_url': http_call.is_dynamic_url
        }
    
    def _rest_endpoint_to_dict(self, endpoint: RESTEndpoint) -> Dict[str, Any]:
        """Convert RESTEndpoint to dictionary"""
        return {
            'source_file': endpoint.source_file,
            'line_number': endpoint.line_number,
            'method': endpoint.method,
            'path': endpoint.path,
            'handler_function': endpoint.handler_function,
            'handler_class': endpoint.handler_class,
            'parameters': endpoint.parameters,
            'framework': endpoint.framework
        }
    
    def _struts_action_to_dict(self, action: StrutsAction) -> Dict[str, Any]:
        """Convert StrutsAction to dictionary"""
        return {
            'name': action.name,
            'class_name': action.class_name,
            'method': action.method,
            'path': action.path,
            'result_pages': action.result_pages,
            'source_file': action.source_file,
            'line_number': action.line_number,
            'parameters': action.parameters
        }
    
    def _component_to_dict(self, component) -> Dict[str, Any]:
        """Convert JSPComponent to dictionary"""
        if isinstance(component, JSPComponent):
            return {
                'source_file': component.source_file,
                'line_number': component.line_number,
                'component_type': component.component_type,
                'action_url': component.action_url,
                'parameters': component.parameters,
                'target_action': component.target_action
            }
        return {}

# Singleton instance
integration_analyzer = IntegrationAnalyzer()