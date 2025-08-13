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
            raise RuntimeError(error_msg)
                
        except Exception as e:
            error_msg = f"Failed to initialize Bedrock client: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def _test_connection(self):
        """Test AWS Bedrock connection"""
        try:
            # Create a separate bedrock client for listing models (not bedrock-runtime)
            # Use the same session configuration as the bedrock-runtime client
            session_kwargs = {}
            
            if settings.AWS_PROFILE:
                session_kwargs['profile_name'] = settings.AWS_PROFILE
            elif settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
                session_kwargs['aws_access_key_id'] = settings.AWS_ACCESS_KEY_ID
                session_kwargs['aws_secret_access_key'] = settings.AWS_SECRET_ACCESS_KEY
                if settings.AWS_SESSION_TOKEN:
                    session_kwargs['aws_session_token'] = settings.AWS_SESSION_TOKEN
            
            session_kwargs['region_name'] = settings.AWS_REGION
            session = boto3.Session(**session_kwargs)
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
                session = boto3.Session(**session_kwargs) if 'session_kwargs' in locals() else boto3.Session()
                sts = session.client('sts')
                identity = sts.get_caller_identity()
                logger.info(f"AWS credentials verified for account {identity.get('Account')}, Bedrock client ready")
                return []
            except Exception as sts_error:
                raise Exception(f"AWS credential verification failed: {sts_error}")
    
    def get_available_models(self):
        """Get list of available Bedrock models"""
        try:
            models = self._test_connection()
            # Filter for text generation models that we can use
            text_models = []
            for model in models:
                model_id = model.get('modelId', '')
                if any(provider in model_id.lower() for provider in ['anthropic', 'amazon', 'ai21', 'cohere']):
                    text_models.append({
                        'id': model_id,
                        'name': model.get('modelName', model_id),
                        'provider': model.get('providerName', 'Unknown'),
                        'description': f"{model.get('providerName', 'Unknown')} - {model.get('modelName', model_id)}"
                    })
            
            logger.info(f"Found {len(text_models)} compatible text generation models")
            return text_models
            
        except Exception as e:
            logger.warning(f"Could not fetch Bedrock models: {e}")
            # Return default models if we can't fetch the list
            return [
                {
                    'id': 'anthropic.claude-v2',
                    'name': 'Claude v2',
                    'provider': 'Anthropic',
                    'description': 'Anthropic - Claude v2 (Default)'
                },
                {
                    'id': 'anthropic.claude-instant-v1',
                    'name': 'Claude Instant',
                    'provider': 'Anthropic',
                    'description': 'Anthropic - Claude Instant v1'
                }
            ]
    
    def set_model_id(self, model_id: str):
        """Set the model ID to use for AI operations"""
        # Validate the model ID exists in available models
        available_models = self.get_available_models()
        model_ids = [model['id'] for model in available_models]
        
        if model_id in model_ids:
            # Update the settings temporarily for this instance
            settings.BEDROCK_MODEL_ID = model_id
            logger.info(f"Model ID set to: {model_id}")
        else:
            logger.warning(f"Model ID {model_id} not found in available models. Using default: {settings.BEDROCK_MODEL_ID}")
    
    def get_current_model_id(self):
        """Get the current model ID being used"""
        return settings.BEDROCK_MODEL_ID
    
    async def extract_business_rules(
        self,
        code: str,
        entities: List[Dict],
        keywords: Optional[List[str]] = None
    ) -> List[BusinessRule]:
        """Extract business rules from code using AI"""
        
        if not self.client:
            raise RuntimeError("AWS Bedrock client not available. Please check your AWS credentials and configuration.")
        
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
        
        if not self.client:
            raise RuntimeError("AWS Bedrock client not available. Please check your AWS credentials and configuration.")
        
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
        
        if not self.client:
            raise RuntimeError("AWS Bedrock client not available. Please check your AWS credentials and configuration.")
        
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
