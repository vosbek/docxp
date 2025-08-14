"""
AI Service for AWS Bedrock integration
"""

import json
import logging
import sys
import time
import threading
import hashlib
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from app.core.config import settings
from app.models.schemas import BusinessRule, DocumentationDepth

logger = logging.getLogger(__name__)

class AIService:
    """Thread-safe singleton service for AI-powered analysis using AWS Bedrock"""
    
    _instance = None
    _lock = threading.Lock()
    _client = None
    _last_auth_check = 0
    _auth_cache_duration = 300  # 5 minutes
    _current_credentials_hash = None
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(AIService, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.client = None
            self._initialize_client()
            self._initialized = True
    
    def _get_credentials_hash(self):
        """Get hash of current credentials for change detection"""
        cred_string = f"{settings.AWS_PROFILE or ''}-{settings.AWS_ACCESS_KEY_ID or ''}-{settings.AWS_REGION}"
        return hashlib.md5(cred_string.encode()).hexdigest()
    
    def _should_reinitialize(self):
        """Check if client should be reinitialized"""
        current_time = time.time()
        current_creds_hash = self._get_credentials_hash()
        
        if (self._current_credentials_hash != current_creds_hash or 
            current_time - self._last_auth_check > self._auth_cache_duration or
            self.client is None):
            return True
        return False
    
    def _ensure_client_ready(self):
        """Ensure client is ready, reinitializing if needed"""
        if self._should_reinitialize():
            with self._lock:
                if self._should_reinitialize():  # Double-check locking
                    self._initialize_client()
        
        if not self.client:
            raise RuntimeError("AWS Bedrock client not initialized")
    
    def _invoke_model_sync(self, model_id: str, body_dict: Dict) -> Any:
        """Synchronous model invocation for use in thread pool"""
        self._ensure_client_ready()
        return self.client.invoke_model(
            modelId=model_id,
            body=json.dumps(body_dict)
        )
    
    def _create_session(self):
        """Create AWS session with current credentials"""
        session_kwargs = {
            'region_name': settings.AWS_REGION
        }
        
        # Method 1: Use AWS Profile if specified
        if settings.AWS_PROFILE:
            session_kwargs['profile_name'] = settings.AWS_PROFILE
        
        # Method 2: Use explicit credentials if provided
        elif settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            session_kwargs['aws_access_key_id'] = settings.AWS_ACCESS_KEY_ID
            session_kwargs['aws_secret_access_key'] = settings.AWS_SECRET_ACCESS_KEY
            
            # Include session token if provided
            if settings.AWS_SESSION_TOKEN:
                session_kwargs['aws_session_token'] = settings.AWS_SESSION_TOKEN
        
        return boto3.Session(**session_kwargs)
    
    def _initialize_client(self):
        """Initialize AWS Bedrock client with multiple auth methods"""
        logger.debug("Initializing AWS Bedrock client...")
        try:
            # Create session using centralized method
            session = self._create_session()
            
            # Log the auth method being used
            if settings.AWS_PROFILE:
                logger.debug(f"Using AWS Profile: {settings.AWS_PROFILE}")
            elif settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
                if settings.AWS_SESSION_TOKEN:
                    logger.debug("Using AWS credentials with session token")
                else:
                    logger.debug("Using AWS credentials without session token")
            else:
                logger.debug("Using default AWS credential chain")
            
            # Create bedrock-runtime client
            self.client = session.client('bedrock-runtime')
            
            # Test the connection
            self._test_connection()
            
            # Update cache info
            self._current_credentials_hash = self._get_credentials_hash()
            self._last_auth_check = time.time()
            
            logger.debug("AWS Bedrock client initialized and cached")
            
        except NoCredentialsError:
            error_msg = "No AWS credentials found. Please configure AWS_PROFILE or AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
                
        except Exception as e:
            error_msg = f"Failed to initialize Bedrock client: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def _test_connection(self):
        """Test AWS Bedrock connection"""
        try:
            # Create a separate bedrock client for listing models (not bedrock-runtime)
            session = self._create_session()
            bedrock_client = session.client('bedrock')
            
            # Try a simple API call to verify credentials
            response = bedrock_client.list_foundation_models()
            model_count = len(response.get('modelSummaries', []))
            logger.info(f"AWS Bedrock connection successful, found {model_count} models")
            
            return response.get('modelSummaries', [])
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDeniedException':
                raise Exception("AWS credentials do not have access to Bedrock. Please check IAM permissions.")
            elif error_code == 'UnauthorizedOperation':
                raise Exception("AWS credentials do not have permission to list Bedrock models. Please check IAM permissions.")
            else:
                raise Exception(f"AWS Bedrock connection test failed: {e}")
        except Exception as e:
            # If we can't create the bedrock client, try a simpler credential verification
            try:
                # Use simple STS call to verify credentials work at all
                session = self._create_session()
                sts = session.client('sts')
                identity = sts.get_caller_identity()
                logger.debug(f"AWS credentials verified for account {identity.get('Account')}, Bedrock client ready")
                return []
            except Exception as sts_error:
                raise Exception(f"AWS credential verification failed: {sts_error}")
    
    def get_current_model_info(self):
        """Get current model configuration info"""
        # Return current model from configuration - no discovery needed
        current_model_id = settings.BEDROCK_MODEL_ID
        
        # Map model IDs to display names
        model_info = {
            'us.anthropic.claude-3-5-sonnet-20241022-v2:0': {
                'id': current_model_id,
                'name': 'Claude 3.5 Sonnet v2',
                'provider': 'Anthropic',
                'description': 'Anthropic Claude 3.5 Sonnet v2 (Inference Profile)'
            },
            'us.anthropic.claude-3-7-sonnet-20250219-v1:0': {
                'id': current_model_id,
                'name': 'Claude 3.7 Sonnet',
                'provider': 'Anthropic',
                'description': 'Anthropic Claude 3.7 Sonnet (Inference Profile)'
            }
        }
        
        return model_info.get(current_model_id, {
            'id': current_model_id,
            'name': 'Custom Model',
            'provider': 'Anthropic',
            'description': f'Custom Model: {current_model_id}'
        })
    
    def get_current_model_id(self):
        """Get the current model ID from configuration"""
        return settings.BEDROCK_MODEL_ID
    
    async def extract_business_rules(
        self,
        code: str,
        entities: List[Dict],
        keywords: Optional[List[str]] = None
    ) -> List[BusinessRule]:
        """Extract business rules from code using AI"""
        
        self._ensure_client_ready()
        
        prompt = self._create_business_rule_prompt(code, entities, keywords)
        
        try:
            # Run the blocking boto3 call in a thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self._invoke_model_sync,
                settings.BEDROCK_MODEL_ID,
                {
                    "prompt": prompt,
                    "max_tokens_to_sample": 2000,
                    "temperature": 0.2,
                    "top_p": 0.9
                }
            )
            
            result = json.loads(response['body'].read())
            return self._parse_business_rules(result)
            
        except ClientError as e:
            logger.error(f"AWS Bedrock error: {e}")
            raise RuntimeError(f"Failed to extract business rules: {e}")
        except Exception as e:
            logger.error(f"Error extracting business rules: {e}")
            raise RuntimeError(f"AI service error: {e}")
    
    async def generate_overview(
        self,
        entities: List[Dict],
        business_rules: List[BusinessRule],
        depth: DocumentationDepth
    ) -> str:
        """Generate documentation overview using AI"""
        
        self._ensure_client_ready()
        
        prompt = self._create_overview_prompt(entities, business_rules, depth)
        
        try:
            # Run the blocking boto3 call in a thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self._invoke_model_sync,
                settings.BEDROCK_MODEL_ID,
                {
                    "prompt": prompt,
                    "max_tokens_to_sample": 3000,
                    "temperature": 0.3
                }
            )
            
            result = json.loads(response['body'].read())
            completion = result.get('completion', '')
            if not completion:
                raise RuntimeError("No completion received from AI model")
            return completion
            
        except Exception as e:
            logger.error(f"Error generating overview: {e}")
            raise RuntimeError(f"Failed to generate overview: {e}")
    
    async def generate_architecture_doc(
        self,
        entities: List[Dict],
        depth: DocumentationDepth
    ) -> str:
        """Generate architecture documentation using AI"""
        
        self._ensure_client_ready()
        
        prompt = self._create_architecture_prompt(entities, depth)
        
        try:
            # Run the blocking boto3 call in a thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self._invoke_model_sync,
                settings.BEDROCK_MODEL_ID,
                {
                    "prompt": prompt,
                    "max_tokens_to_sample": 4000,
                    "temperature": 0.3
                }
            )
            
            result = json.loads(response['body'].read())
            completion = result.get('completion', '')
            if not completion:
                raise RuntimeError("No completion received from AI model")
            return completion
            
        except Exception as e:
            logger.error(f"Error generating architecture doc: {e}")
            raise RuntimeError(f"Failed to generate architecture documentation: {e}")
    
    def _create_business_rule_prompt(
        self,
        code: str,
        entities: List[Dict],
        keywords: Optional[List[str]]
    ) -> str:
        """Create prompt for business rule extraction"""
        
        entities_summary = "\n".join([
            f"- {e.get('type')}: {e.get('name')}"
            for e in entities[:20]
        ])
        
        keywords_text = ""
        if keywords:
            keywords_text = f"\nFocus on these keywords: {', '.join(keywords)}"
        
        return f"""Analyze the following code and extract business rules.

Code Structure:
{entities_summary}

{keywords_text}

Code Sample (first 2000 characters):
{code[:2000]}

Extract business rules in the following categories:
1. Validation Rules (data validation, input checking)
2. Calculation Rules (formulas, computations)
3. Workflow Rules (process flow, state transitions)
4. Authorization Rules (permissions, access control)
5. Business Constraints (limits, thresholds)

For each rule provide:
- Unique ID
- Clear description
- Confidence score (0.0 to 1.0)
- Category
- Code reference
- Related entities

Format as JSON array.
"""
    
    def _create_overview_prompt(
        self,
        entities: List[Dict],
        business_rules: List[BusinessRule],
        depth: DocumentationDepth
    ) -> str:
        """Create prompt for overview generation"""
        
        depth_instruction = {
            DocumentationDepth.MINIMAL: "Brief 2-3 paragraph overview",
            DocumentationDepth.STANDARD: "Comprehensive 4-5 paragraph overview",
            DocumentationDepth.COMPREHENSIVE: "Detailed multi-section overview",
            DocumentationDepth.EXHAUSTIVE: "Complete technical overview with all details"
        }
        
        return f"""Generate a {depth_instruction[depth]} for a codebase with the following characteristics:

Statistics:
- Total entities: {len(entities)}
- Classes: {len([e for e in entities if e.get('type') == 'class'])}
- Functions: {len([e for e in entities if e.get('type') == 'function'])}
- Business rules: {len(business_rules)}

Top Components:
{self._summarize_entities(entities[:10])}

Include:
1. Purpose and functionality
2. Key architectural patterns
3. Technology stack
4. Main business domains
5. Critical dependencies

Write in clear, professional documentation style.
"""
    
    def _create_architecture_prompt(
        self,
        entities: List[Dict],
        depth: DocumentationDepth
    ) -> str:
        """Create prompt for architecture documentation"""
        
        return f"""Generate architecture documentation for a system with {len(entities)} components.

Document the following aspects:
1. System Architecture Overview
2. Component Organization
3. Data Flow Patterns
4. Integration Points
5. Design Patterns Used
6. Scalability Considerations
7. Security Architecture

Depth level: {depth.value}

Format with clear sections and subsections using Markdown.
"""
    
    def _summarize_entities(self, entities: List[Dict]) -> str:
        """Summarize entities for prompt"""
        summary = []
        for entity in entities:
            name = entity.get('name', 'Unknown')
            type_ = entity.get('type', 'unknown')
            file_ = entity.get('file_path', 'unknown')
            summary.append(f"- {type_}: {name} in {file_}")
        return "\n".join(summary)
    
    def _parse_business_rules(self, ai_response: Dict) -> List[BusinessRule]:
        """Parse AI response into BusinessRule objects with robust JSON extraction"""
        rules = []
        
        try:
            completion = ai_response.get('completion', '')
            if not completion:
                logger.warning("No completion text in AI response")
                return rules
            
            # Try multiple parsing strategies
            rules_data = self._extract_json_array(completion)
            
            if not rules_data:
                logger.warning("No valid JSON array found in AI response")
                return rules
            
            # Parse each rule
            for i, rule_data in enumerate(rules_data):
                try:
                    rule = BusinessRule(
                        id=rule_data.get('id', f"RULE-{len(rules)+1:03d}"),
                        description=rule_data.get('description', ''),
                        confidence_score=float(rule_data.get('confidence_score', 0.7)),
                        category=rule_data.get('category', 'General'),
                        code_reference=rule_data.get('code_reference', ''),
                        validation_logic=rule_data.get('validation_logic'),
                        related_entities=rule_data.get('related_entities', [])
                    )
                    rules.append(rule)
                except Exception as rule_error:
                    logger.warning(f"Failed to parse rule {i}: {rule_error}")
                    continue
                    
        except Exception as e:
            logger.warning(f"Failed to parse business rules: {e}")
        
        return rules
    
    def _extract_json_array(self, text: str) -> List[Dict]:
        """Extract JSON array from text using multiple strategies"""
        import re
        
        # Strategy 1: Look for JSON within code fences
        json_fence_match = re.search(r'```(?:json)?\s*\n?([\\s\\S]*?)\n?```', text, re.IGNORECASE)
        if json_fence_match:
            try:
                return json.loads(json_fence_match.group(1).strip())
            except json.JSONDecodeError:
                pass
        
        # Strategy 2: Find balanced brackets - more precise than greedy regex
        bracket_count = 0
        start_idx = -1
        
        for i, char in enumerate(text):
            if char == '[':
                if bracket_count == 0:
                    start_idx = i
                bracket_count += 1
            elif char == ']':
                bracket_count -= 1
                if bracket_count == 0 and start_idx != -1:
                    try:
                        json_str = text[start_idx:i+1]
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        continue
        
        # Strategy 3: Look for array patterns with line-by-line parsing
        lines = text.split('\n')
        json_lines = []
        in_array = False
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('['):
                in_array = True
                json_lines = [stripped]
            elif in_array:
                json_lines.append(stripped)
                if stripped.endswith(']') and not stripped.endswith(',]'):
                    try:
                        json_str = '\n'.join(json_lines)
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        in_array = False
                        json_lines = []
        
        # Strategy 4: Fallback - try the original greedy approach but with bounds
        json_match = re.search(r'\[([^\[\]]*|\[[^\]]*\])*\]', text)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        logger.warning("Could not extract valid JSON array from AI response")
        return []


# Create shared singleton instance
ai_service_instance = AIService()