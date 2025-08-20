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
            # Do NOT initialize client during __init__ - defer until first use
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
    
    def _is_claude_3_plus_model(self, model_id: str) -> bool:
        """Check if the model is Claude 3+ and requires Messages API format"""
        claude_3_plus_patterns = [
            'claude-3',
            'claude-3-5',
            'claude-3-7',
            'us.anthropic.claude-3',
            'anthropic.claude-3'
        ]
        return any(pattern in model_id.lower() for pattern in claude_3_plus_patterns)
    
    def _format_request_body(self, prompt: str, model_id: str, **kwargs) -> Dict:
        """Format request body based on model type"""
        if self._is_claude_3_plus_model(model_id):
            # Claude 3+ uses Messages API
            body = {
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": kwargs.get("max_tokens_to_sample", 2000),
                "temperature": kwargs.get("temperature", 0.2),
                "top_p": kwargs.get("top_p", 0.9),
                "anthropic_version": "bedrock-2023-05-31"
            }
        else:
            # Legacy Claude models use Text Completions API
            body = {
                "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
                "max_tokens_to_sample": kwargs.get("max_tokens_to_sample", 2000),
                "temperature": kwargs.get("temperature", 0.2),
                "top_p": kwargs.get("top_p", 0.9)
            }
        
        return body
    
    def _parse_model_response(self, response_body: Dict, model_id: str) -> str:
        """Parse model response based on model type"""
        if self._is_claude_3_plus_model(model_id):
            # Claude 3+ response format
            content = response_body.get('content', [])
            if content and isinstance(content, list) and len(content) > 0:
                return content[0].get('text', '')
            return ''
        else:
            # Legacy Claude response format
            return response_body.get('completion', '')
    
    async def _create_session(self):
        """Create AWS session with current credentials using token manager"""
        from app.services.aws_token_manager import aws_token_manager
        
        # First try to get credentials from token manager
        try:
            credentials = await aws_token_manager.get_valid_credentials()
            if credentials:
                return boto3.Session(**credentials)
        except Exception as e:
            logger.debug(f"Token manager unavailable, falling back to traditional methods: {e}")
        
        # Fallback to traditional session creation
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
            # Create session using centralized method (now async-aware)
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                session = loop.run_until_complete(self._create_session())
            except RuntimeError:
                # No event loop running, create one
                session = asyncio.run(self._create_session())
            
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
            logger.warning("AWS credentials unavailable - service will operate in fallback mode")
            self.client = None
            # Don't raise error - allow graceful degradation
            return
                
        except Exception as e:
            error_msg = f"Failed to initialize Bedrock client: {e}"
            logger.error(error_msg)
            logger.warning("AWS Bedrock unavailable - service will operate in fallback mode")
            self.client = None
            # Don't raise error - allow graceful degradation
            return
    
    def _test_connection(self):
        """Test AWS Bedrock connection"""
        try:
            # Create a separate bedrock client for listing models (not bedrock-runtime)
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                session = loop.run_until_complete(self._create_session())
            except RuntimeError:
                session = asyncio.run(self._create_session())
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
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    session = loop.run_until_complete(self._create_session())
                except RuntimeError:
                    session = asyncio.run(self._create_session())
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
    
    def get_available_models(self):
        """Get available Bedrock models"""
        try:
            self._ensure_client_ready()
            
            # Create a separate bedrock client for listing models (not bedrock-runtime)
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                session = loop.run_until_complete(self._create_session())
            except RuntimeError:
                session = asyncio.run(self._create_session())
            bedrock_client = session.client('bedrock')
            
            # Get foundation models
            response = bedrock_client.list_foundation_models()
            model_summaries = response.get('modelSummaries', [])
            
            # Filter for supported models and format for UI
            supported_models = []
            for model in model_summaries:
                model_id = model.get('modelId', '')
                # Focus on Anthropic Claude models
                if 'anthropic.claude' in model_id:
                    supported_models.append({
                        'id': model_id,
                        'name': model.get('modelName', model_id),
                        'provider': model.get('providerName', 'Anthropic'),
                        'status': model.get('modelLifecycle', {}).get('status', 'ACTIVE')
                    })
            
            return supported_models
            
        except Exception as e:
            logger.error(f"Error fetching available models: {e}")
            # Return a fallback list of known models if API call fails
            return [
                {
                    'id': 'anthropic.claude-v2',
                    'name': 'Claude v2',
                    'provider': 'Anthropic',
                    'status': 'ACTIVE'
                },
                {
                    'id': 'us.anthropic.claude-3-5-sonnet-20241022-v2:0',
                    'name': 'Claude 3.5 Sonnet v2',
                    'provider': 'Anthropic',
                    'status': 'ACTIVE'
                }
            ]
    
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
            # Format request body based on model type
            body = self._format_request_body(
                prompt, 
                settings.BEDROCK_MODEL_ID,
                max_tokens_to_sample=2000,
                temperature=0.2,
                top_p=0.9
            )
            
            # Run the blocking boto3 call in a thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self._invoke_model_sync,
                settings.BEDROCK_MODEL_ID,
                body
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
            # Format request body based on model type
            body = self._format_request_body(
                prompt, 
                settings.BEDROCK_MODEL_ID,
                max_tokens_to_sample=3000,
                temperature=0.3
            )
            
            # Run the blocking boto3 call in a thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self._invoke_model_sync,
                settings.BEDROCK_MODEL_ID,
                body
            )
            
            result = json.loads(response['body'].read())
            completion = self._parse_model_response(result, settings.BEDROCK_MODEL_ID)
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
            # Format request body based on model type
            body = self._format_request_body(
                prompt, 
                settings.BEDROCK_MODEL_ID,
                max_tokens_to_sample=4000,
                temperature=0.3
            )
            
            # Run the blocking boto3 call in a thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self._invoke_model_sync,
                settings.BEDROCK_MODEL_ID,
                body
            )
            
            result = json.loads(response['body'].read())
            completion = self._parse_model_response(result, settings.BEDROCK_MODEL_ID)
            if not completion:
                raise RuntimeError("No completion received from AI model")
            return completion
            
        except Exception as e:
            logger.error(f"Error generating architecture doc: {e}")
            raise RuntimeError(f"Failed to generate architecture documentation: {e}")
    
    async def generate_content(
        self,
        prompt: str,
        max_tokens: int = 3000,
        temperature: float = 0.3
    ) -> str:
        """Generate content from a prompt using AI"""
        
        self._ensure_client_ready()
        
        try:
            # Format request body based on model type
            body = self._format_request_body(
                prompt, 
                settings.BEDROCK_MODEL_ID,
                max_tokens_to_sample=max_tokens,
                temperature=temperature
            )
            
            # Run the blocking boto3 call in a thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self._invoke_model_sync,
                settings.BEDROCK_MODEL_ID,
                body
            )
            
            result = json.loads(response['body'].read())
            completion = self._parse_model_response(result, settings.BEDROCK_MODEL_ID)
            if not completion:
                raise RuntimeError("No completion received from AI model")
            return completion
            
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            raise RuntimeError(f"Failed to generate content: {e}")
    
    def _create_business_rule_prompt(
        self,
        code: str,
        entities: List[Dict],
        keywords: Optional[List[str]]
    ) -> str:
        """Create enhanced prompt for business rule extraction using expert prompt engineering"""
        
        entities_summary = "\n".join([
            f"- {e.get('type')}: {e.get('name')} (File: {e.get('file_path', 'unknown')})"
            for e in entities[:25]  # Increased from 20 to provide more context
        ])
        
        keywords_text = ""
        if keywords:
            keywords_text = f"\n## 🎯 FOCUS KEYWORDS\nPay special attention to business logic involving: {', '.join(keywords)}"
        
        # Use more code context - increase from 2000 to 4000 chars
        code_sample = code[:4000] if len(code) > 4000 else code
        code_length_note = f" (showing first 4,000 of {len(code)} characters)" if len(code) > 4000 else " (complete code)"
        
        return f"""# 🔍 EXPERT BUSINESS RULES ANALYST

You are a senior business analyst and software architect specializing in extracting business rules from source code. Your task is to identify, categorize, and document business logic embedded in the codebase.

## 📋 DEFINITION
A **business rule** is any logic that represents:
- How the business operates (processes, workflows)
- What the business allows/prohibits (constraints, validations)
- How the business calculates values (formulas, algorithms)
- Who can do what (authorization, permissions)
- When things should happen (triggers, conditions)

## 🏗️ CODE STRUCTURE CONTEXT
{entities_summary}
{keywords_text}

## 💻 CODE TO ANALYZE{code_length_note}
```
{code_sample}
```

## 🎯 EXTRACTION METHODOLOGY

### Step 1: Scan for Business Logic Patterns
Look for these indicators:
- Conditional statements with business meaning (if/else, switch/case)
- Mathematical calculations and formulas
- Validation logic and constraints
- Workflow state transitions
- Permission checks and role-based logic
- Configuration values and business constants
- Error messages that reveal business rules

### Step 2: Categorize Each Rule
**📊 VALIDATION RULES**: Input validation, data integrity, format checking, required fields
**🧮 CALCULATION RULES**: Mathematical formulas, pricing logic, scoring algorithms, aggregations
**⚡ WORKFLOW RULES**: Process steps, state transitions, approval flows, business process logic
**🔐 AUTHORIZATION RULES**: Access control, role permissions, security constraints, user restrictions
**⚖️ BUSINESS CONSTRAINTS**: Limits, thresholds, quotas, business policy enforcement
**🔄 INTEGRATION RULES**: External system interactions, data transformation, API business logic

### Step 3: Score Confidence
- **0.9-1.0**: Explicit business rule clearly visible in code
- **0.7-0.8**: Strong indication of business rule with clear intent
- **0.5-0.6**: Likely business rule but some interpretation required
- **0.3-0.4**: Possible business rule but uncertain
- **0.1-0.2**: Weak indication, might be technical implementation

### Step 4: Provide Precise References
Include line numbers, method names, or specific code snippets that contain the rule.

## 📝 REQUIRED OUTPUT FORMAT

Return a JSON array with this exact structure:

```json
[
  {{
    "id": "BR-001",
    "description": "Clear, business-focused description of what the rule does",
    "confidence_score": 0.85,
    "category": "Validation Rules",
    "code_reference": "Method: validatePayment(), Line 45-52",
    "validation_logic": "Specific implementation details if applicable",
    "related_entities": ["PaymentService", "ValidationUtils"],
    "business_impact": "Brief explanation of why this rule matters to the business"
  }}
]
```

## ⚠️ QUALITY STANDARDS
- Write descriptions in business language, not technical jargon
- Each rule should be actionable and specific
- Avoid duplicating essentially the same rule
- Focus on business intent, not implementation details
- If uncertain about a rule, explain your reasoning in the description

## 🔍 EDGE CASE HANDLING
- If code is incomplete or unclear, note this in the description
- For complex nested logic, break into multiple rules if they serve different business purposes
- If no clear business rules are found, return an empty array
- For configuration-driven rules, focus on the business intent rather than the configuration mechanism

Now analyze the provided code and extract business rules following this methodology.
"""
    
    def _create_overview_prompt(
        self,
        entities: List[Dict],
        business_rules: List[BusinessRule],
        depth: DocumentationDepth
    ) -> str:
        """Create enhanced prompt for overview generation using expert prompt engineering"""
        
        # Enhanced depth instructions with specific guidance
        depth_specs = {
            DocumentationDepth.MINIMAL: {
                "length": "2-3 focused paragraphs (300-500 words)",
                "audience": "executives and stakeholders",
                "focus": "high-level business purpose and key capabilities",
                "technical_detail": "minimal technical details, focus on business value"
            },
            DocumentationDepth.STANDARD: {
                "length": "4-6 structured sections (800-1200 words)",
                "audience": "product managers and technical leads", 
                "focus": "balanced technical and business perspective",
                "technical_detail": "moderate technical depth with business context"
            },
            DocumentationDepth.COMPREHENSIVE: {
                "length": "8-10 detailed sections (1500-2500 words)",
                "audience": "architects and senior developers",
                "focus": "detailed technical architecture with business implications",
                "technical_detail": "significant technical depth with architectural insights"
            },
            DocumentationDepth.EXHAUSTIVE: {
                "length": "12-15 comprehensive sections (3000+ words)",
                "audience": "system architects and documentation specialists",
                "focus": "complete system analysis covering all aspects",
                "technical_detail": "full technical detail with implementation considerations"
            }
        }
        
        current_spec = depth_specs[depth]
        
        # Analyze entity distribution for better insights
        entity_stats = self._analyze_entity_distribution(entities)
        business_rule_insights = self._analyze_business_rules(business_rules)
        
        return f"""# 📚 EXPERT TECHNICAL DOCUMENTATION SPECIALIST

You are a senior technical writer and software architect specializing in creating compelling, accurate system overviews. Your audience includes {current_spec['audience']}, so tailor your language and depth accordingly.

## 🎯 DOCUMENTATION REQUIREMENTS

**Target Length**: {current_spec['length']}  
**Primary Focus**: {current_spec['focus']}  
**Technical Detail Level**: {current_spec['technical_detail']}  
**Writing Style**: Professional, clear, engaging, and structured

## 📊 SYSTEM ANALYSIS DATA

### Entity Distribution
{entity_stats}

### Business Logic Analysis  
{business_rule_insights}

### Key Components (Top 15)
{self._summarize_entities(entities[:15])}

## 📋 REQUIRED STRUCTURE

Based on the {depth.value} depth level, include these sections:

### 🎯 **System Purpose & Vision** (Required)
- Clear statement of what this system does and why it exists
- Primary business value and intended users
- Key problems it solves

### 🏗️ **Architecture Highlights** (Required)
- Overall architectural approach and patterns
- Major components and their relationships
- Technology choices and rationale

### 💼 **Business Domain & Rules** (Required) 
- Core business domains the system serves
- Critical business rules and constraints (leverage the {len(business_rules)} identified rules)
- Workflow and process insights

### 🔧 **Technical Foundation** (Required)
- Primary technologies and frameworks
- Integration patterns and external dependencies  
- Development and deployment approach

{self._get_additional_sections_by_depth(depth)}

## ⭐ QUALITY STANDARDS

### Content Quality
- Lead with business value, then explain technical implementation
- Use concrete examples from the codebase when possible
- Avoid generic statements - be specific to THIS system
- Balance technical accuracy with readability
- Connect technical decisions to business outcomes

### Writing Quality  
- Use active voice and clear, direct language
- Include relevant metrics and numbers from the analysis
- Structure with clear headings and logical flow
- End each section with key takeaways when appropriate

### Technical Accuracy
- Reference actual components and business rules found in the code
- Distinguish between what is implemented vs. what is intended
- Note any significant patterns or anti-patterns observed
- Highlight unique or noteworthy architectural decisions

## 🔍 ANALYSIS METHODOLOGY

1. **Start with Purpose**: Why does this system exist? What business problem does it solve?
2. **Identify Core Domains**: What business areas does the code serve? What are the main workflows?
3. **Map Technical Architecture**: How is the code organized? What patterns emerge?
4. **Connect Business to Technical**: How do technical decisions support business goals?
5. **Assess Maturity**: What does the code structure tell us about system evolution?

## 📝 OUTPUT FORMAT

Structure your response in clear markdown with:
- Descriptive section headings (use ##)
- Bullet points for key facts and lists
- Code component references where relevant
- Business rule references using the identified rules
- Clear transitions between sections

## ⚠️ IMPORTANT GUIDELINES
- Write for your target audience - adjust technical depth accordingly
- Reference specific components and business rules from the provided data
- If certain information isn't available in the data, note this rather than speculating
- Focus on what makes THIS system unique, not generic software patterns
- Ensure each section provides actionable insights for the intended readers

Now generate a comprehensive system overview following these specifications.
"""
    
    def _create_architecture_prompt(
        self,
        entities: List[Dict],
        depth: DocumentationDepth
    ) -> str:
        """Create enhanced prompt for architecture documentation using expert prompt engineering"""
        
        # Enhanced depth specifications for architecture docs
        arch_depth_specs = {
            DocumentationDepth.MINIMAL: {
                "sections": "4-5 core sections",
                "detail": "High-level architectural overview with key patterns",
                "audience": "architects and technical leads",
                "focus": "Major architectural decisions and component relationships"
            },
            DocumentationDepth.STANDARD: {
                "sections": "6-8 detailed sections", 
                "detail": "Comprehensive architecture with implementation insights",
                "audience": "senior developers and system architects",
                "focus": "Detailed component interaction and design rationale"
            },
            DocumentationDepth.COMPREHENSIVE: {
                "sections": "10-12 in-depth sections",
                "detail": "Complete architectural analysis with operational considerations",
                "audience": "platform engineers and solution architects", 
                "focus": "Full system design including non-functional requirements"
            },
            DocumentationDepth.EXHAUSTIVE: {
                "sections": "15+ comprehensive sections",
                "detail": "Enterprise-grade architectural documentation",
                "audience": "enterprise architects and system designers",
                "focus": "Complete architectural blueprint with all technical details"
            }
        }
        
        current_spec = arch_depth_specs[depth]
        
        # Analyze entity patterns for architecture insights
        entity_analysis = self._analyze_architectural_patterns(entities)
        
        return f"""# 🏗️ EXPERT SOFTWARE ARCHITECT

You are a principal software architect with deep expertise in system design, architectural patterns, and technical documentation. Your task is to create comprehensive architecture documentation that serves as a technical blueprint for {current_spec['audience']}.

## 🎯 DOCUMENTATION SPECIFICATIONS

**Target Audience**: {current_spec['audience']}  
**Section Count**: {current_spec['sections']}  
**Detail Level**: {current_spec['detail']}  
**Primary Focus**: {current_spec['focus']}  
**Output Format**: Well-structured Markdown with clear hierarchy

## 📊 ARCHITECTURAL ANALYSIS INPUT

### System Scale
- **Total Components**: {len(entities)}
- **Complexity Level**: {self._assess_complexity_level(entities)}

### Component Analysis
{entity_analysis}

### Key Components (Top 20)
{self._summarize_entities(entities[:20])}

## 🏛️ REQUIRED ARCHITECTURE SECTIONS

{self._get_architecture_sections_by_depth(depth)}

## 🎯 ARCHITECTURAL ANALYSIS METHODOLOGY

### 1. **System Decomposition**
- Identify major subsystems and bounded contexts
- Map component dependencies and relationships  
- Analyze layering and separation of concerns
- Detect architectural patterns and anti-patterns

### 2. **Quality Attribute Analysis**
- Assess scalability characteristics from code structure
- Evaluate maintainability through code organization
- Identify security patterns and potential vulnerabilities
- Analyze performance implications of architectural choices

### 3. **Integration & Interface Design**
- Map external system dependencies and integration points
- Document API patterns and communication mechanisms
- Identify data flow patterns and transformation points
- Assess coupling levels between components

### 4. **Operational Architecture**
- Infer deployment patterns from code structure
- Identify monitoring and observability approaches
- Assess error handling and resilience patterns
- Document configuration and environment management

## ⭐ QUALITY STANDARDS FOR ARCHITECTURE DOCUMENTATION

### Technical Accuracy
- Base all analysis on actual code evidence, not assumptions
- Distinguish between current implementation and architectural intent
- Identify gaps between intended and actual architecture
- Reference specific components and their interactions

### Clarity & Structure
- Use consistent architectural terminology throughout
- Provide clear diagrams in text form (ASCII or detailed descriptions)
- Structure information from high-level concepts to specific details
- Include both "what" and "why" for architectural decisions

### Actionable Insights
- Highlight significant architectural strengths and weaknesses
- Identify potential scalability bottlenecks or technical debt
- Suggest specific improvements or alternative approaches
- Connect architectural choices to business and operational outcomes

### Professional Standards
- Follow established architectural documentation patterns
- Use C4 model concepts (Context, Container, Component, Code) where applicable
- Include both functional and non-functional architecture aspects
- Provide clear section transitions and logical information flow

## 🔍 ARCHITECTURAL PATTERNS TO IDENTIFY

Look for evidence of these patterns in the codebase:
- **Layered Architecture**: Clear separation between presentation, business, and data layers
- **Microservices/Modular Monolith**: Service boundaries and communication patterns
- **Event-Driven Architecture**: Event sourcing, CQRS, or pub/sub patterns
- **Domain-Driven Design**: Bounded contexts, aggregates, and domain models
- **Clean Architecture**: Dependency inversion and clean boundaries
- **API Patterns**: RESTful design, GraphQL, RPC, or messaging patterns

## 📋 OUTPUT FORMATTING REQUIREMENTS

Structure your response using this hierarchy:
```
# System Architecture Documentation

## Executive Summary
[Brief architectural overview and key characteristics]

## [Core Sections based on depth level]
[Detailed sections as specified above]

## Architectural Decision Records (ADRs)
[Key architectural decisions with rationale]

## Recommendations & Future Considerations
[Specific improvement opportunities and evolution path]
```

## ⚠️ CRITICAL GUIDELINES

- **Evidence-Based Analysis**: Every architectural claim must be supported by code evidence
- **Avoid Generic Statements**: Focus on what makes THIS system's architecture unique
- **Balance Detail Levels**: Provide appropriate technical depth for the target audience
- **Include Trade-offs**: Discuss architectural trade-offs and their implications
- **Future-Focused**: Consider system evolution and scalability implications
- **Operational Reality**: Address how the architecture works in real-world deployment

Now generate comprehensive architecture documentation following these expert specifications and analyzing the provided component data.
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
    
    def _analyze_entity_distribution(self, entities: List[Dict]) -> str:
        """Analyze entity distribution for enhanced prompt context"""
        from collections import Counter
        
        if not entities:
            return "No entities found in the codebase."
            
        type_counts = Counter(e.get('type', 'unknown') for e in entities)
        total = len(entities)
        
        # Calculate percentages and create distribution summary
        distribution = []
        for entity_type, count in type_counts.most_common():
            percentage = (count / total) * 100
            distribution.append(f"- {entity_type.title()}: {count} ({percentage:.1f}%)")
        
        # Identify patterns
        patterns = []
        if type_counts.get('class', 0) > type_counts.get('function', 0):
            patterns.append("Object-oriented design emphasis")
        if type_counts.get('function', 0) > type_counts.get('class', 0) * 2:
            patterns.append("Functional programming patterns")
        if type_counts.get('interface', 0) > 0:
            patterns.append("Interface-driven architecture")
        if type_counts.get('enum', 0) > 0:
            patterns.append("Type-safe enumeration usage")
            
        pattern_text = "\n- " + "\n- ".join(patterns) if patterns else "\n- Mixed programming paradigms"
        
        return f"""**Total Components**: {total}
**Distribution**:
{chr(10).join(distribution)}
**Architectural Patterns**:{pattern_text}"""

    def _analyze_business_rules(self, business_rules: List[BusinessRule]) -> str:
        """Analyze business rules for enhanced prompt context"""
        if not business_rules:
            return "No business rules have been extracted yet (this analysis will run first)."
            
        from collections import Counter
        
        # Analyze rule categories
        categories = Counter(rule.category for rule in business_rules)
        confidence_avg = sum(rule.confidence_score for rule in business_rules) / len(business_rules)
        
        category_summary = []
        for category, count in categories.most_common():
            category_summary.append(f"- {category}: {count} rules")
            
        high_confidence_rules = [r for r in business_rules if r.confidence_score >= 0.8]
        
        return f"""**Total Business Rules**: {len(business_rules)}
**Average Confidence**: {confidence_avg:.2f}
**Category Breakdown**:
{chr(10).join(category_summary)}
**High-Confidence Rules**: {len(high_confidence_rules)} rules (≥0.8 confidence)"""

    def _get_additional_sections_by_depth(self, depth: DocumentationDepth) -> str:
        """Generate additional sections based on documentation depth"""
        sections = {
            DocumentationDepth.MINIMAL: "",
            DocumentationDepth.STANDARD: """
### 📈 **Development & Operations** (Standard+)
- Development workflow and tooling
- Testing approach and coverage
- Deployment and environment management""",
            DocumentationDepth.COMPREHENSIVE: """
### 📈 **Development & Operations** (Comprehensive+)  
- Development workflow and tooling
- Testing strategy and coverage analysis
- Deployment pipeline and environment management
- Performance characteristics and optimization

### 🔒 **Security & Compliance** (Comprehensive+)
- Security architecture and controls
- Data protection and privacy measures  
- Compliance requirements and implementation
- Authentication and authorization patterns""",
            DocumentationDepth.EXHAUSTIVE: """
### 📈 **Development & Operations** (Exhaustive)
- Complete development workflow and tooling ecosystem
- Comprehensive testing strategy and coverage analysis
- Detailed deployment pipeline and environment management
- Performance characteristics, monitoring, and optimization strategies

### 🔒 **Security & Compliance** (Exhaustive)
- Comprehensive security architecture and controls
- Data protection, privacy, and encryption strategies
- Compliance requirements and detailed implementation
- Authentication, authorization, and audit patterns

### 🔧 **Implementation Details** (Exhaustive)
- Code organization and module structure  
- Design patterns and architectural decisions
- Data models and persistence strategies
- Error handling and logging approaches

### 🚀 **Scalability & Future Considerations** (Exhaustive)
- Current scalability limitations and bottlenecks
- Performance optimization opportunities
- Technical debt assessment and remediation
- Future enhancement recommendations and roadmap considerations"""
        }
        
        return sections.get(depth, "")

    def _analyze_architectural_patterns(self, entities: List[Dict]) -> str:
        """Analyze entities for architectural patterns and insights"""
        if not entities:
            return "No entities available for architectural analysis."
            
        from collections import Counter, defaultdict
        
        # Analyze file organization patterns
        file_paths = [e.get('file_path', '') for e in entities if e.get('file_path')]
        directory_structure = defaultdict(int)
        
        for path in file_paths:
            if '/' in path or '\\' in path:
                # Extract directory patterns
                parts = path.replace('\\', '/').split('/')
                if len(parts) > 1:
                    directory_structure[parts[0]] += 1
                    if len(parts) > 2:
                        directory_structure[f"{parts[0]}/{parts[1]}"] += 1
        
        # Analyze naming patterns
        entity_names = [e.get('name', '') for e in entities if e.get('name')]
        naming_patterns = []
        
        # Check for common patterns
        if any('Service' in name for name in entity_names):
            naming_patterns.append("Service layer pattern detected")
        if any('Controller' in name for name in entity_names):
            naming_patterns.append("Controller pattern (MVC/Web API)")
        if any('Repository' in name or 'Dao' in name for name in entity_names):
            naming_patterns.append("Repository/DAO pattern")
        if any('Factory' in name for name in entity_names):
            naming_patterns.append("Factory pattern usage")
        if any('Manager' in name for name in entity_names):
            naming_patterns.append("Manager/Coordinator pattern")
        if any('Handler' in name for name in entity_names):
            naming_patterns.append("Handler/Command pattern")
        
        # Analyze entity type distribution
        type_counts = Counter(e.get('type', 'unknown') for e in entities)
        
        # Build analysis result
        analysis_parts = []
        
        if directory_structure:
            top_dirs = sorted(directory_structure.items(), key=lambda x: x[1], reverse=True)[:5]
            dir_analysis = "**Directory Organization**:\n" + "\n".join([f"- {dir}: {count} components" for dir, count in top_dirs])
            analysis_parts.append(dir_analysis)
        
        if naming_patterns:
            pattern_analysis = "**Detected Patterns**:\n" + "\n".join([f"- {pattern}" for pattern in naming_patterns])
            analysis_parts.append(pattern_analysis)
        
        type_analysis = "**Component Types**:\n" + "\n".join([f"- {type_}: {count}" for type_, count in type_counts.most_common()])
        analysis_parts.append(type_analysis)
        
        return "\n\n".join(analysis_parts)
    
    def _assess_complexity_level(self, entities: List[Dict]) -> str:
        """Assess system complexity based on entity count and patterns"""
        total_entities = len(entities)
        
        if total_entities < 20:
            return "Low (Simple system)"
        elif total_entities < 100:
            return "Medium (Moderate complexity)"
        elif total_entities < 500:
            return "High (Complex system)"
        else:
            return "Very High (Enterprise-scale system)"
    
    def _get_architecture_sections_by_depth(self, depth: DocumentationDepth) -> str:
        """Generate architecture-specific sections based on documentation depth"""
        sections = {
            DocumentationDepth.MINIMAL: """
### 🎯 **System Context & Overview** (Required)
- System purpose and primary capabilities
- High-level architecture style and approach
- Major component relationships

### 🏗️ **Core Architecture Patterns** (Required)
- Primary architectural patterns in use
- Component organization and layering
- Key design principles and constraints

### 🔗 **Integration Architecture** (Required)
- External system dependencies
- API design and communication patterns
- Data flow and transformation points

### ⚡ **Key Quality Attributes** (Required)
- Scalability and performance characteristics
- Security and reliability patterns
- Operational considerations""",

            DocumentationDepth.STANDARD: """
### 🎯 **System Context & Overview** (Required)
- System purpose and primary capabilities  
- High-level architecture style and approach
- Major component relationships and boundaries

### 🏗️ **Component Architecture** (Required)
- Detailed component organization and responsibilities
- Inter-component communication patterns
- Layering strategy and separation of concerns

### 🔗 **Integration & Interface Design** (Required)
- External system dependencies and integration points
- API design patterns and communication protocols
- Data flow, transformation, and persistence patterns

### ⚡ **Quality Attributes & Cross-Cutting Concerns** (Required)
- Scalability and performance architecture
- Security architecture and access control
- Error handling and resilience patterns

### 🚀 **Deployment & Operational Architecture** (Standard+)
- Deployment patterns and environment strategy
- Monitoring, logging, and observability
- Configuration management approach

### 📐 **Design Decisions & Trade-offs** (Standard+)
- Key architectural decisions and rationale
- Trade-offs made and alternatives considered
- Technical debt and architectural evolution""",

            DocumentationDepth.COMPREHENSIVE: """
### 🎯 **System Context & Overview** (Required)
- Comprehensive system purpose and capabilities
- Detailed architecture style analysis and rationale
- Complete component landscape and relationship mapping

### 🏗️ **Component Architecture & Design** (Required)
- In-depth component organization and responsibilities
- Detailed inter-component communication and dependencies
- Advanced layering strategy and domain boundaries

### 🔗 **Integration & Interface Architecture** (Required)
- Complete external system dependency analysis
- Comprehensive API design patterns and protocols
- Advanced data flow, transformation, and persistence strategies

### ⚡ **Quality Attributes & Non-Functional Requirements** (Required)
- Detailed scalability and performance architecture
- Comprehensive security architecture and compliance
- Advanced error handling, resilience, and fault tolerance

### 🚀 **Deployment & Operational Excellence** (Comprehensive+)
- Advanced deployment patterns and infrastructure strategy
- Comprehensive monitoring, observability, and alerting
- Configuration management and environment orchestration

### 📐 **Architectural Decisions & Governance** (Comprehensive+)
- Complete architectural decision records (ADRs)
- Trade-off analysis and alternative architecture evaluation
- Technical debt assessment and evolution roadmap

### 🔧 **Implementation Patterns & Best Practices** (Comprehensive+)
- Code organization and module structure patterns
- Design pattern usage and anti-pattern identification
- Development standards and architectural guidelines

### 📊 **Performance & Optimization Architecture** (Comprehensive+)
- Performance characteristics and optimization strategies
- Caching patterns and data access optimization
- Resource utilization and capacity planning""",

            DocumentationDepth.EXHAUSTIVE: """
### 🎯 **System Context & Strategic Overview** (Required)
- Complete system purpose, capabilities, and business context
- Comprehensive architecture style analysis with industry benchmarking
- Full component ecosystem mapping with external dependencies

### 🏗️ **Component Architecture & Domain Design** (Required)
- Enterprise-level component organization and domain modeling
- Complete inter-component communication with protocol analysis
- Advanced domain-driven design and bounded context implementation

### 🔗 **Integration & Interface Excellence** (Required)
- Complete integration architecture with pattern analysis
- Enterprise API design standards and governance
- Advanced data architecture with consistency and sync strategies

### ⚡ **Quality Attributes & Enterprise Requirements** (Required)
- Enterprise scalability and performance architecture
- Complete security architecture with compliance frameworks
- Advanced resilience patterns and disaster recovery design

### 🚀 **Deployment & Operational Excellence** (Exhaustive)
- Enterprise deployment patterns and infrastructure as code
- Complete observability stack with SRE practices
- Advanced configuration management and GitOps workflows

### 📐 **Architectural Governance & Standards** (Exhaustive)
- Complete architectural decision records with impact analysis
- Enterprise architecture governance and review processes
- Comprehensive technical debt management and evolution strategy

### 🔧 **Implementation Excellence & Standards** (Exhaustive)
- Enterprise code organization and modular architecture
- Complete design pattern catalog and anti-pattern prevention
- Development excellence standards and architectural guidelines

### 📊 **Performance & Optimization Excellence** (Exhaustive)
- Complete performance architecture with benchmarking
- Advanced caching strategies and data optimization
- Resource optimization and capacity planning models

### 🔐 **Security & Compliance Architecture** (Exhaustive)
- Enterprise security architecture with threat modeling
- Complete compliance framework implementation
- Advanced authentication, authorization, and audit patterns

### 🌐 **Scalability & Future Architecture** (Exhaustive)
- Enterprise scalability patterns and cloud-native design
- Complete migration and evolution strategies
- Future architecture roadmap with technology assessment"""
        }
        
        return sections.get(depth, "")
    
    def _parse_business_rules(self, ai_response: Dict) -> List[BusinessRule]:
        """Parse AI response into BusinessRule objects with robust JSON extraction"""
        rules = []
        
        try:
            completion = self._parse_model_response(ai_response, settings.BEDROCK_MODEL_ID)
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


# Global AI service instance - lazily initialized
_ai_service_instance = None

def get_ai_service_instance():
    """Get or create the AI service instance"""
    global _ai_service_instance
    if _ai_service_instance is None:
        try:
            _ai_service_instance = AIService()
        except Exception as e:
            logger.error(f"Failed to initialize AI service: {e}")
            return None
    return _ai_service_instance

class _AIServiceProxy:
    """Proxy class for backward compatibility"""
    def __getattr__(self, name):
        service = get_ai_service_instance()
        if service is None:
            raise RuntimeError("AI service is not available")
        return getattr(service, name)

# Backward compatibility - will be removed in future versions
ai_service_instance = _AIServiceProxy()