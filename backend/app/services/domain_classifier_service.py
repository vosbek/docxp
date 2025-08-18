"""
Domain Classification Service for DocXP Enterprise
AI-powered classification of code components into business domains using AWS Bedrock
"""

import asyncio
import logging
import json
import re
from typing import List, Dict, Any, Optional, Tuple, Set
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

import boto3
from botocore.exceptions import ClientError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_async_session
from app.models.business_domains import (
    DomainTaxonomy, DomainClassificationRule, DomainClassificationResult,
    BusinessSubdomain, DomainCategory, ENTERPRISE_DOMAIN_TAXONOMY,
    get_domain_keywords, get_domain_patterns, get_all_domain_ids
)
from app.models.business_rule_trace import BusinessRuleTrace, FlowStep

logger = logging.getLogger(__name__)

@dataclass
class ClassificationScore:
    """Classification result with confidence score"""
    domain_id: str
    confidence: float
    method: str
    evidence: List[str]

@dataclass
class ComponentContext:
    """Context information for component classification"""
    file_path: str
    component_name: str
    component_type: str  # class, method, jsp, action, etc.
    content: str
    repository_id: str
    commit_hash: str
    technology: str
    related_files: List[str] = None
    database_tables: List[str] = None
    business_logic: str = None

class DomainClassifierService:
    """
    Advanced domain classification service using multiple methods:
    1. Rule-based keyword matching
    2. Pattern-based file path analysis  
    3. AI-powered semantic analysis using AWS Bedrock
    4. Context-aware relationship analysis
    """
    
    def __init__(self):
        self.bedrock_client = None
        self.model_id = settings.BEDROCK_MODEL_ID
        self.region = settings.AWS_REGION
        self._initialize_bedrock()
        
        # Classification thresholds
        self.min_confidence_threshold = 0.6
        self.ai_analysis_threshold = 0.8  # When to use AI for complex cases
        
        # Cache for performance
        self._domain_cache = {}
        self._rules_cache = {}
    
    def _initialize_bedrock(self):
        """Initialize AWS Bedrock client"""
        try:
            self.bedrock_client = boto3.client(
                'bedrock-runtime',
                region_name=self.region
            )
            logger.info("Bedrock client initialized for domain classification")
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {e}")
            raise
    
    async def classify_component(
        self, 
        context: ComponentContext,
        use_ai: bool = True
    ) -> List[ClassificationScore]:
        """
        Classify a code component into business domains
        Returns ranked list of domain classifications with confidence scores
        """
        try:
            results = []
            
            # 1. Rule-based classification
            rule_scores = await self._classify_by_rules(context)
            results.extend(rule_scores)
            
            # 2. Pattern-based classification
            pattern_scores = await self._classify_by_patterns(context)
            results.extend(pattern_scores)
            
            # 3. Keyword-based classification
            keyword_scores = await self._classify_by_keywords(context)
            results.extend(keyword_scores)
            
            # 4. AI-powered semantic analysis (if confidence is low or requested)
            max_confidence = max([s.confidence for s in results], default=0.0)
            if use_ai and max_confidence < self.ai_analysis_threshold:
                ai_scores = await self._classify_by_ai_analysis(context)
                results.extend(ai_scores)
            
            # 5. Context-aware relationship analysis
            context_scores = await self._classify_by_context(context)
            results.extend(context_scores)
            
            # Combine and rank results
            final_scores = self._combine_classification_scores(results)
            
            # Filter by minimum confidence
            filtered_scores = [
                score for score in final_scores 
                if score.confidence >= self.min_confidence_threshold
            ]
            
            # Sort by confidence descending
            filtered_scores.sort(key=lambda x: x.confidence, reverse=True)
            
            logger.info(f"Classified {context.component_name}: {len(filtered_scores)} domains found")
            return filtered_scores[:5]  # Return top 5 classifications
            
        except Exception as e:
            logger.error(f"Error classifying component {context.component_name}: {e}")
            return []
    
    async def _classify_by_rules(self, context: ComponentContext) -> List[ClassificationScore]:
        """Apply rule-based classification"""
        try:
            # Load classification rules from database
            async with get_async_session() as session:
                result = await session.execute(
                    select(DomainClassificationRule).where(
                        DomainClassificationRule.is_active == True
                    ).order_by(DomainClassificationRule.priority)
                )
                rules = result.scalars().all()
            
            scores = []
            for rule in rules:
                confidence = await self._evaluate_rule(rule, context)
                if confidence > 0:
                    scores.append(ClassificationScore(
                        domain_id=rule.target_domain,
                        confidence=confidence * rule.confidence_weight,
                        method=f"rule:{rule.rule_type}",
                        evidence=[f"Rule: {rule.rule_name}"]
                    ))
            
            return scores
            
        except Exception as e:
            logger.error(f"Error in rule-based classification: {e}")
            return []
    
    async def _evaluate_rule(self, rule: DomainClassificationRule, context: ComponentContext) -> float:
        """Evaluate a single classification rule"""
        confidence = 0.0
        text_to_analyze = f"{context.file_path} {context.component_name} {context.content}"
        
        if rule.rule_type == "keyword":
            # Keyword matching
            if rule.keywords:
                matches = sum(1 for keyword in rule.keywords 
                            if keyword.lower() in text_to_analyze.lower())
                confidence = min(matches / len(rule.keywords), 1.0)
        
        elif rule.rule_type == "pattern":
            # File pattern matching
            if rule.file_patterns:
                for pattern in rule.file_patterns:
                    if self._match_pattern(pattern, context.file_path):
                        confidence = 0.8
                        break
        
        elif rule.rule_type == "code_pattern":
            # Code content pattern matching
            if rule.code_patterns:
                for pattern in rule.code_patterns:
                    if re.search(pattern, context.content, re.IGNORECASE):
                        confidence = 0.7
                        break
        
        return confidence
    
    def _match_pattern(self, pattern: str, file_path: str) -> bool:
        """Match file path against pattern (supports wildcards)"""
        import fnmatch
        return fnmatch.fnmatch(file_path.lower(), pattern.lower())
    
    async def _classify_by_patterns(self, context: ComponentContext) -> List[ClassificationScore]:
        """Classify based on file path patterns"""
        scores = []
        
        try:
            for domain_id in get_all_domain_ids():
                patterns = get_domain_patterns(domain_id)
                for pattern in patterns:
                    if self._match_pattern(pattern, context.file_path):
                        scores.append(ClassificationScore(
                            domain_id=domain_id,
                            confidence=0.7,
                            method="pattern_matching",
                            evidence=[f"File pattern: {pattern}"]
                        ))
                        break  # One match per domain
            
            return scores
            
        except Exception as e:
            logger.error(f"Error in pattern-based classification: {e}")
            return []
    
    async def _classify_by_keywords(self, context: ComponentContext) -> List[ClassificationScore]:
        """Classify based on keyword matching"""
        scores = []
        
        try:
            text_to_analyze = f"{context.file_path} {context.component_name} {context.business_logic or ''}"
            text_lower = text_to_analyze.lower()
            
            for domain_id in get_all_domain_ids():
                keywords = get_domain_keywords(domain_id)
                if not keywords:
                    continue
                
                matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
                if matches > 0:
                    confidence = min(matches / len(keywords), 1.0)
                    scores.append(ClassificationScore(
                        domain_id=domain_id,
                        confidence=confidence * 0.8,  # Weight keyword matching
                        method="keyword_matching",
                        evidence=[f"Keywords: {[k for k in keywords if k.lower() in text_lower]}"]
                    ))
            
            return scores
            
        except Exception as e:
            logger.error(f"Error in keyword-based classification: {e}")
            return []
    
    async def _classify_by_ai_analysis(self, context: ComponentContext) -> List[ClassificationScore]:
        """Use AI semantic analysis for complex classification"""
        try:
            # Prepare domain context for AI
            domain_descriptions = self._get_domain_descriptions()
            
            # Create AI analysis prompt
            prompt = self._create_ai_classification_prompt(context, domain_descriptions)
            
            # Call Bedrock AI
            response = await self._call_bedrock_for_classification(prompt)
            
            # Parse AI response
            scores = self._parse_ai_classification_response(response)
            
            return scores
            
        except Exception as e:
            logger.error(f"Error in AI-based classification: {e}")
            return []
    
    def _get_domain_descriptions(self) -> Dict[str, str]:
        """Get descriptions of all business domains for AI context"""
        descriptions = {}
        taxonomy = ENTERPRISE_DOMAIN_TAXONOMY
        
        def extract_descriptions(data: Dict[str, Any], prefix: str = ""):
            for key, value in data.items():
                if isinstance(value, dict):
                    if "description" in value:
                        descriptions[key] = value["description"]
                    if "business_purpose" in value:
                        descriptions[key] = f"{descriptions.get(key, '')} {value['business_purpose']}"
                    if "children" in value:
                        extract_descriptions(value["children"], f"{prefix}{key}.")
        
        extract_descriptions(taxonomy)
        return descriptions
    
    def _create_ai_classification_prompt(
        self, 
        context: ComponentContext, 
        domain_descriptions: Dict[str, str]
    ) -> str:
        """Create AI prompt for domain classification"""
        prompt = f"""
You are an expert enterprise software architect analyzing code components for business domain classification.

COMPONENT TO CLASSIFY:
- File Path: {context.file_path}
- Component Name: {context.component_name}
- Component Type: {context.component_type}
- Technology: {context.technology}
- Business Logic: {context.business_logic or 'N/A'}

CODE CONTENT (first 1000 chars):
{context.content[:1000]}

AVAILABLE BUSINESS DOMAINS:
"""
        
        for domain_id, description in domain_descriptions.items():
            prompt += f"- {domain_id}: {description}\n"
        
        prompt += """

ANALYSIS TASK:
Analyze the code component and classify it into the most appropriate business domain(s). Consider:
1. The business purpose and functionality
2. The data elements and operations
3. The file location and naming patterns
4. The technology stack context

RESPONSE FORMAT:
Return a JSON array of classifications, each with:
{
    "domain_id": "domain_identifier",
    "confidence": 0.0-1.0,
    "reasoning": "explanation of why this domain fits"
}

Provide up to 3 most relevant domains, ranked by confidence.
"""
        
        return prompt
    
    async def _call_bedrock_for_classification(self, prompt: str) -> str:
        """Call AWS Bedrock for AI classification"""
        try:
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            # Make async call to Bedrock
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.bedrock_client.invoke_model(
                    modelId=self.model_id,
                    body=json.dumps(body),
                    contentType='application/json',
                    accept='application/json'
                )
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']
            
        except Exception as e:
            logger.error(f"Error calling Bedrock for classification: {e}")
            return ""
    
    def _parse_ai_classification_response(self, response: str) -> List[ClassificationScore]:
        """Parse AI classification response"""
        try:
            # Extract JSON from response
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            
            if json_start == -1 or json_end == 0:
                return []
            
            json_str = response[json_start:json_end]
            classifications = json.loads(json_str)
            
            scores = []
            for classification in classifications:
                scores.append(ClassificationScore(
                    domain_id=classification['domain_id'],
                    confidence=float(classification['confidence']),
                    method="ai_semantic_analysis",
                    evidence=[classification.get('reasoning', 'AI analysis')]
                ))
            
            return scores
            
        except Exception as e:
            logger.error(f"Error parsing AI classification response: {e}")
            return []
    
    async def _classify_by_context(self, context: ComponentContext) -> List[ClassificationScore]:
        """Classify based on related components and context"""
        scores = []
        
        try:
            # Analyze related files in same directory
            if context.related_files:
                related_domains = await self._analyze_related_files(context.related_files)
                for domain_id, confidence in related_domains.items():
                    scores.append(ClassificationScore(
                        domain_id=domain_id,
                        confidence=confidence * 0.6,  # Lower weight for context
                        method="context_analysis",
                        evidence=[f"Related files indicate {domain_id}"]
                    ))
            
            # Analyze database table usage
            if context.database_tables:
                table_domains = await self._analyze_database_context(context.database_tables)
                for domain_id, confidence in table_domains.items():
                    scores.append(ClassificationScore(
                        domain_id=domain_id,
                        confidence=confidence * 0.7,
                        method="database_context",
                        evidence=[f"Database tables: {context.database_tables}"]
                    ))
            
            return scores
            
        except Exception as e:
            logger.error(f"Error in context-based classification: {e}")
            return []
    
    async def _analyze_related_files(self, related_files: List[str]) -> Dict[str, float]:
        """Analyze related files to infer domain context"""
        domain_votes = {}
        
        for file_path in related_files:
            # Simple heuristic based on file names
            for domain_id in get_all_domain_ids():
                keywords = get_domain_keywords(domain_id)
                for keyword in keywords:
                    if keyword.lower() in file_path.lower():
                        domain_votes[domain_id] = domain_votes.get(domain_id, 0) + 0.1
        
        # Normalize scores
        if domain_votes:
            max_score = max(domain_votes.values())
            return {k: v / max_score for k, v in domain_votes.items()}
        
        return {}
    
    async def _analyze_database_context(self, database_tables: List[str]) -> Dict[str, float]:
        """Analyze database table names to infer domain context"""
        domain_votes = {}
        
        for table_name in database_tables:
            table_lower = table_name.lower()
            
            # Map common table name patterns to domains
            table_domain_mapping = {
                'claims': 'claims_processing',
                'policy': 'policy_management', 
                'payment': 'payment_processing',
                'customer': 'customer_management',
                'user': 'authentication',
                'audit': 'audit_trail',
                'commission': 'commission_management',
                'workflow': 'workflow_management'
            }
            
            for pattern, domain_id in table_domain_mapping.items():
                if pattern in table_lower:
                    domain_votes[domain_id] = domain_votes.get(domain_id, 0) + 0.8
        
        return domain_votes
    
    def _combine_classification_scores(self, scores: List[ClassificationScore]) -> List[ClassificationScore]:
        """Combine multiple classification scores for same domain"""
        domain_scores = {}
        
        for score in scores:
            if score.domain_id not in domain_scores:
                domain_scores[score.domain_id] = {
                    'total_confidence': 0.0,
                    'method_count': 0,
                    'methods': [],
                    'evidence': []
                }
            
            domain_scores[score.domain_id]['total_confidence'] += score.confidence
            domain_scores[score.domain_id]['method_count'] += 1
            domain_scores[score.domain_id]['methods'].append(score.method)
            domain_scores[score.domain_id]['evidence'].extend(score.evidence)
        
        # Calculate final scores using weighted average
        final_scores = []
        for domain_id, data in domain_scores.items():
            # Weight by number of supporting methods
            method_weight = min(data['method_count'] * 0.2, 1.0)
            avg_confidence = data['total_confidence'] / data['method_count']
            final_confidence = avg_confidence * (1.0 + method_weight)
            
            final_scores.append(ClassificationScore(
                domain_id=domain_id,
                confidence=min(final_confidence, 1.0),
                method=f"combined({','.join(set(data['methods']))})",
                evidence=data['evidence']
            ))
        
        return final_scores
    
    async def store_classification_result(
        self,
        context: ComponentContext,
        classification: ClassificationScore,
        secondary_classifications: List[ClassificationScore] = None
    ) -> str:
        """Store classification result in database"""
        try:
            async with get_async_session() as session:
                # Prepare secondary domains data
                secondary_domains = {}
                if secondary_classifications:
                    secondary_domains = {
                        cls.domain_id: cls.confidence 
                        for cls in secondary_classifications
                    }
                
                # Create classification result record
                result = DomainClassificationResult(
                    repository_id=context.repository_id,
                    file_path=context.file_path,
                    component_name=context.component_name,
                    component_type=context.component_type,
                    primary_domain=classification.domain_id,
                    confidence_score=classification.confidence,
                    secondary_domains=secondary_domains,
                    classification_method=classification.method,
                    rules_applied=[],  # Could be enhanced to track specific rules
                    metadata={
                        'evidence': classification.evidence,
                        'technology': context.technology,
                        'commit_hash': context.commit_hash
                    }
                )
                
                session.add(result)
                await session.commit()
                
                logger.info(f"Stored classification result for {context.component_name}")
                return str(result.id)
                
        except Exception as e:
            logger.error(f"Error storing classification result: {e}")
            return ""

# Global service instance
_domain_classifier_service = None

async def get_domain_classifier_service() -> DomainClassifierService:
    """Get domain classifier service instance"""
    global _domain_classifier_service
    if _domain_classifier_service is None:
        _domain_classifier_service = DomainClassifierService()
    return _domain_classifier_service