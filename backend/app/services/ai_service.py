"""
AI Service for AWS Bedrock integration
"""

import json
import logging
import sys
from typing import List, Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from app.core.config import settings
from app.models.schemas import BusinessRule, DocumentationDepth

logger = logging.getLogger(__name__)

class AIService:
    """Service for AI-powered analysis using AWS Bedrock"""
    
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize AWS Bedrock client with multiple auth methods"""
        try:
            # Build session with appropriate auth method
            session_kwargs = {
                'region_name': settings.AWS_REGION
            }
            
            # Method 1: Use AWS Profile if specified
            if settings.AWS_PROFILE:
                session_kwargs['profile_name'] = settings.AWS_PROFILE
                logger.info(f"Using AWS Profile: {settings.AWS_PROFILE}")
            
            # Method 2: Use explicit credentials if provided
            elif settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
                session_kwargs['aws_access_key_id'] = settings.AWS_ACCESS_KEY_ID
                session_kwargs['aws_secret_access_key'] = settings.AWS_SECRET_ACCESS_KEY
                
                # Include session token if provided
                if settings.AWS_SESSION_TOKEN:
                    session_kwargs['aws_session_token'] = settings.AWS_SESSION_TOKEN
                    logger.info("Using AWS credentials with session token")
                else:
                    logger.info("Using AWS credentials without session token")
            
            # Method 3: Use default credential chain (IAM role, etc.)
            else:
                logger.info("Using default AWS credential chain")
            
            # Create session and client
            session = boto3.Session(**session_kwargs)
            self.client = session.client('bedrock-runtime')
            
            # Test the connection
            self._test_connection()
            logger.info("Successfully initialized AWS Bedrock client")
            
        except NoCredentialsError:
            error_msg = "No AWS credentials found. Please configure AWS_PROFILE or AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY"
            logger.error(error_msg)
            
            if settings.REQUIRE_AWS_CREDENTIALS:
                logger.error("Exiting: AWS credentials are required")
                sys.exit(1)
            else:
                logger.warning("Continuing without AWS Bedrock (mock mode)")
                self.client = None
                
        except Exception as e:
            error_msg = f"Failed to initialize Bedrock client: {e}"
            logger.error(error_msg)
            
            if settings.REQUIRE_AWS_CREDENTIALS:
                logger.error("Exiting: AWS Bedrock initialization failed")
                sys.exit(1)
            else:
                logger.warning("Continuing without AWS Bedrock (mock mode)")
                self.client = None
    
    def _test_connection(self):
        """Test AWS Bedrock connection"""
        try:
            # Try a simple API call to verify credentials
            # This is a lightweight call to check connectivity
            response = self.client.list_foundation_models()
            logger.info(f"AWS Bedrock connection successful, found {len(response.get('modelSummaries', []))} models")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDeniedException':
                raise Exception("AWS credentials do not have access to Bedrock. Please check IAM permissions.")
            else:
                raise Exception(f"AWS Bedrock connection test failed: {e}")
    
    async def extract_business_rules(
        self,
        code: str,
        entities: List[Dict],
        keywords: Optional[List[str]] = None
    ) -> List[BusinessRule]:
        """Extract business rules from code using AI"""
        
        if not self.client:
            # Return mock data for development
            return self._mock_business_rules()
        
        prompt = self._create_business_rule_prompt(code, entities, keywords)
        
        try:
            response = self.client.invoke_model(
                modelId=settings.BEDROCK_MODEL_ID,
                body=json.dumps({
                    "prompt": prompt,
                    "max_tokens_to_sample": 2000,
                    "temperature": 0.2,
                    "top_p": 0.9
                })
            )
            
            result = json.loads(response['body'].read())
            return self._parse_business_rules(result)
            
        except ClientError as e:
            logger.error(f"AWS Bedrock error: {e}")
            return self._mock_business_rules()
        except Exception as e:
            logger.error(f"Error extracting business rules: {e}")
            return []
    
    async def generate_overview(
        self,
        entities: List[Dict],
        business_rules: List[BusinessRule],
        depth: DocumentationDepth
    ) -> str:
        """Generate documentation overview using AI"""
        
        if not self.client:
            return self._mock_overview()
        
        prompt = self._create_overview_prompt(entities, business_rules, depth)
        
        try:
            response = self.client.invoke_model(
                modelId=settings.BEDROCK_MODEL_ID,
                body=json.dumps({
                    "prompt": prompt,
                    "max_tokens_to_sample": 3000,
                    "temperature": 0.3
                })
            )
            
            result = json.loads(response['body'].read())
            return result.get('completion', self._mock_overview())
            
        except Exception as e:
            logger.error(f"Error generating overview: {e}")
            return self._mock_overview()
    
    async def generate_architecture_doc(
        self,
        entities: List[Dict],
        depth: DocumentationDepth
    ) -> str:
        """Generate architecture documentation using AI"""
        
        if not self.client:
            return self._mock_architecture_doc()
        
        prompt = self._create_architecture_prompt(entities, depth)
        
        try:
            response = self.client.invoke_model(
                modelId=settings.BEDROCK_MODEL_ID,
                body=json.dumps({
                    "prompt": prompt,
                    "max_tokens_to_sample": 4000,
                    "temperature": 0.3
                })
            )
            
            result = json.loads(response['body'].read())
            return result.get('completion', self._mock_architecture_doc())
            
        except Exception as e:
            logger.error(f"Error generating architecture doc: {e}")
            return self._mock_architecture_doc()
    
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
        """Parse AI response into BusinessRule objects"""
        rules = []
        
        try:
            # Try to parse JSON from completion
            completion = ai_response.get('completion', '')
            
            # Find JSON array in response
            import re
            json_match = re.search(r'\[.*\]', completion, re.DOTALL)
            if json_match:
                rules_data = json.loads(json_match.group())
                
                for rule_data in rules_data:
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
        except Exception as e:
            logger.warning(f"Failed to parse business rules: {e}")
        
        return rules
    
    def _mock_business_rules(self) -> List[BusinessRule]:
        """Return mock business rules for development"""
        return [
            BusinessRule(
                id="RULE-001",
                description="Validate payment amount must be greater than zero",
                confidence_score=0.95,
                category="Validation Rules",
                code_reference="payment_service.py:45",
                validation_logic="if amount <= 0: raise ValueError('Invalid amount')",
                related_entities=["PaymentProcessor", "validate_amount"]
            ),
            BusinessRule(
                id="RULE-002",
                description="Calculate insurance premium based on risk factors",
                confidence_score=0.88,
                category="Calculation Rules",
                code_reference="premium_calculator.py:120",
                validation_logic=None,
                related_entities=["PremiumCalculator", "calculate_premium"]
            ),
            BusinessRule(
                id="RULE-003",
                description="Require manager approval for claims over $10,000",
                confidence_score=0.92,
                category="Workflow Rules",
                code_reference="claims_workflow.py:78",
                validation_logic="if claim_amount > 10000: require_approval()",
                related_entities=["ClaimsProcessor", "ApprovalWorkflow"]
            )
        ]
    
    def _mock_overview(self) -> str:
        """Return mock overview for development"""
        return """This repository contains a comprehensive insurance processing system designed to handle various aspects of insurance operations including claims processing, premium calculations, and customer management.

The system follows a microservices architecture pattern with separate services for different business domains. Each service is independently deployable and communicates through well-defined APIs. The codebase demonstrates strong separation of concerns with clear boundaries between business logic, data access, and presentation layers.

Key technologies include Python for backend services, with extensive use of object-oriented design patterns. The system integrates with multiple external services for payment processing, document management, and regulatory compliance checking. Database operations are abstracted through a repository pattern, allowing for flexibility in data storage solutions.

The codebase shows evidence of iterative development with multiple refactoring cycles visible in the git history. There's a strong emphasis on validation and business rule enforcement throughout the system, with centralized rule engines for complex decision-making processes."""
    
    def _mock_architecture_doc(self) -> str:
        """Return mock architecture documentation for development"""
        return """# System Architecture

## Overview
The system follows a layered architecture with clear separation between presentation, business logic, and data access layers.

## Component Organization
- **Core Services**: Central business logic and rule engines
- **API Layer**: RESTful endpoints for external communication
- **Data Access Layer**: Repository pattern for database operations
- **Integration Layer**: External service connectors and adapters

## Design Patterns
- Repository Pattern for data access
- Factory Pattern for object creation
- Observer Pattern for event handling
- Strategy Pattern for algorithm selection

## Scalability Considerations
The system is designed for horizontal scaling with stateless services and distributed caching mechanisms.

## Security Architecture
- Authentication via OAuth 2.0
- Role-based access control (RBAC)
- Data encryption at rest and in transit
- Audit logging for all critical operations"""
