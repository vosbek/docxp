"""
AWS Bedrock Embedding Service
Provides enterprise-grade embeddings using Amazon Titan Text v2
"""

import asyncio
import logging
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

import boto3
from botocore.exceptions import ClientError, BotoCoreError
import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)

class BedrockEmbeddingService:
    """AWS Bedrock embedding service using Titan Text v2 model"""
    
    def __init__(self):
        self.client = None
        self.model_id = settings.BEDROCK_EMBED_MODEL_ID
        self.dimensions = settings.BEDROCK_EMBEDDING_DIMENSIONS
        self.region = settings.AWS_REGION
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize AWS Bedrock client"""
        try:
            self.client = boto3.client(
                'bedrock-runtime',
                region_name=self.region
            )
            logger.info(f"Bedrock client initialized for region: {self.region}")
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {e}")
            raise
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for a single text using AWS Bedrock Titan"""
        try:
            # Prepare the request body for Titan Text v2
            body = {
                "inputText": text,
                "dimensions": self.dimensions,
                "normalize": True  # Normalize embeddings for better similarity search
            }
            
            # Make the API call
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.invoke_model(
                    modelId=self.model_id,
                    body=json.dumps(body),
                    contentType='application/json',
                    accept='application/json'
                )
            )
            
            # Parse the response
            response_body = json.loads(response['body'].read())
            embedding = response_body.get('embedding')
            
            if not embedding:
                logger.error(f"No embedding returned from Bedrock for text: {text[:100]}...")
                return None
            
            return embedding
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Bedrock API error ({error_code}): {error_message}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error generating embedding: {e}")
            return None
    
    async def generate_embeddings_batch(self, texts: List[str], batch_size: int = 25) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts in batches"""
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            logger.info(f"Processing embedding batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")
            
            # Process batch concurrently
            batch_tasks = [self.generate_embedding(text) for text in batch]
            batch_embeddings = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Handle exceptions in batch results
            processed_batch = []
            for j, result in enumerate(batch_embeddings):
                if isinstance(result, Exception):
                    logger.error(f"Error in batch item {i + j}: {result}")
                    processed_batch.append(None)
                else:
                    processed_batch.append(result)
            
            all_embeddings.extend(processed_batch)
            
            # Rate limiting - Bedrock has quotas
            if i + batch_size < len(texts):
                await asyncio.sleep(0.1)  # Small delay between batches
        
        return all_embeddings
    
    async def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    async def get_embedding_stats(self) -> Dict[str, Any]:
        """Get embedding service statistics"""
        return {
            'service': 'AWS Bedrock Titan Text v2',
            'model_id': self.model_id,
            'dimensions': self.dimensions,
            'region': self.region,
            'normalized': True,
            'max_input_tokens': 8192,  # Titan Text v2 limit
            'cost_per_1k_tokens': 0.0001  # USD
        }
    
    async def validate_service(self) -> bool:
        """Validate that the Bedrock service is accessible"""
        try:
            # Test with a simple text
            test_embedding = await self.generate_embedding("test")
            return test_embedding is not None and len(test_embedding) == self.dimensions
        except Exception as e:
            logger.error(f"Bedrock service validation failed: {e}")
            return False


class CodeBERTEmbeddingService:
    """Local CodeBERT embedding service (fallback)"""
    
    def __init__(self):
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
            self.dimensions = 768  # CodeBERT dimension
            logger.info(f"CodeBERT model loaded: {settings.EMBEDDING_MODEL}")
        except Exception as e:
            logger.error(f"Failed to load CodeBERT model: {e}")
            raise
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding using local CodeBERT model"""
        try:
            # Run model inference in thread pool to avoid blocking
            embedding = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.model.encode(text, convert_to_numpy=True)
            )
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating CodeBERT embedding: {e}")
            return None
    
    async def generate_embeddings_batch(self, texts: List[str], batch_size: int = 32) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts"""
        try:
            # Process in batches to manage memory
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                # Run batch inference
                batch_embeddings = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.model.encode(batch, convert_to_numpy=True)
                )
                
                # Convert to list format
                for embedding in batch_embeddings:
                    all_embeddings.append(embedding.tolist())
            
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Error generating CodeBERT batch embeddings: {e}")
            return [None] * len(texts)
    
    async def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(dot_product / (norm1 * norm2))
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    async def get_embedding_stats(self) -> Dict[str, Any]:
        """Get embedding service statistics"""
        return {
            'service': 'CodeBERT Local',
            'model': settings.EMBEDDING_MODEL,
            'dimensions': self.dimensions,
            'local': True,
            'cost': 'Free (local compute)'
        }
    
    async def validate_service(self) -> bool:
        """Validate that the CodeBERT service is working"""
        try:
            test_embedding = await self.generate_embedding("test code")
            return test_embedding is not None and len(test_embedding) == self.dimensions
        except Exception as e:
            logger.error(f"CodeBERT service validation failed: {e}")
            return False


class EmbeddingServiceFactory:
    """Factory for creating embedding service instances"""
    
    @staticmethod
    def create_service():
        """Create embedding service based on configuration"""
        provider = settings.EMBEDDING_PROVIDER.lower()
        
        if provider == "bedrock":
            try:
                return BedrockEmbeddingService()
            except Exception as e:
                logger.warning(f"Failed to initialize Bedrock service: {e}, falling back to CodeBERT")
                return CodeBERTEmbeddingService()
        elif provider == "codebert":
            return CodeBERTEmbeddingService()
        else:
            logger.warning(f"Unknown embedding provider: {provider}, using CodeBERT")
            return CodeBERTEmbeddingService()


# Global instance
_embedding_service_instance = None

def get_embedding_service():
    """Get the configured embedding service instance"""
    global _embedding_service_instance
    if _embedding_service_instance is None:
        _embedding_service_instance = EmbeddingServiceFactory.create_service()
    return _embedding_service_instance