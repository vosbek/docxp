"""
Enhanced Context Manager for Single-Agent Tool Integration

Manages conversation context, tool results, and knowledge graph integration
to maintain coherent state across complex multi-tool analysis workflows.

Part of Week 5 implementation.
"""

import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import asyncio
from collections import defaultdict

from app.core.database import AsyncSessionLocal
from app.services.knowledge_graph_service import KnowledgeGraphService
from app.models.business_rule_trace import BusinessRuleTrace, FlowStep
from app.models.architectural_insight import ArchitecturalInsight
from app.models.tool_workflows import ToolSequence, ToolStep, WorkflowExecution

logger = logging.getLogger(__name__)


@dataclass
class ContextualData:
    """Structured container for contextual data from tools"""
    data_type: str  # "business_rule_trace", "architectural_insight", "repository_analysis", etc.
    data: Dict[str, Any]
    source_tool: str
    confidence: float
    timestamp: datetime
    relevance_score: float = 0.0
    expires_at: Optional[datetime] = None
    
    def is_expired(self) -> bool:
        """Check if this contextual data has expired"""
        return self.expires_at is not None and datetime.utcnow() > self.expires_at


@dataclass
class ConversationMemory:
    """Long-term conversation memory with intelligent retrieval"""
    session_id: str
    memories: List[Dict[str, Any]] = field(default_factory=list)
    semantic_index: Dict[str, List[int]] = field(default_factory=dict)  # keyword -> memory indices
    importance_scores: List[float] = field(default_factory=list)
    last_accessed: List[datetime] = field(default_factory=list)
    
    def add_memory(self, memory: Dict[str, Any], importance: float = 0.5):
        """Add a memory with importance scoring"""
        self.memories.append(memory)
        self.importance_scores.append(importance)
        self.last_accessed.append(datetime.utcnow())
        
        # Update semantic index
        memory_idx = len(self.memories) - 1
        content = str(memory).lower()
        for word in content.split():
            if len(word) > 3:  # Only index meaningful words
                if word not in self.semantic_index:
                    self.semantic_index[word] = []
                self.semantic_index[word].append(memory_idx)
    
    def retrieve_relevant_memories(self, query: str, max_memories: int = 5) -> List[Dict[str, Any]]:
        """Retrieve memories relevant to a query"""
        query_words = [word.lower() for word in query.split() if len(word) > 3]
        memory_scores = defaultdict(float)
        
        # Score memories based on keyword overlap
        for word in query_words:
            if word in self.semantic_index:
                for memory_idx in self.semantic_index[word]:
                    memory_scores[memory_idx] += self.importance_scores[memory_idx]
        
        # Sort by score and recency
        scored_memories = []
        for memory_idx, score in memory_scores.items():
            recency_bonus = 1.0 / (1 + (datetime.utcnow() - self.last_accessed[memory_idx]).days)
            total_score = score + recency_bonus
            scored_memories.append((memory_idx, total_score))
        
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        
        # Return top memories
        relevant_memories = []
        for memory_idx, _ in scored_memories[:max_memories]:
            relevant_memories.append(self.memories[memory_idx])
            self.last_accessed[memory_idx] = datetime.utcnow()  # Update access time
        
        return relevant_memories


class ContextManager:
    """
    Enhanced context manager for maintaining rich conversational context
    across complex multi-tool analysis workflows
    """
    
    def __init__(self):
        self.knowledge_graph: Optional[KnowledgeGraphService] = None
        self.active_contexts: Dict[str, Dict[str, Any]] = {}  # session_id -> context
        self.contextual_data: Dict[str, List[ContextualData]] = {}  # session_id -> data list
        self.conversation_memories: Dict[str, ConversationMemory] = {}  # session_id -> memory
        self.tool_result_cache: Dict[str, Dict[str, Any]] = {}  # cache_key -> result
        
        # Context management settings
        self.max_context_age_hours = 24
        self.max_contextual_data_items = 50
        self.context_relevance_threshold = 0.3
        
    async def initialize(self):
        """Initialize the context manager with required services"""
        try:
            self.knowledge_graph = KnowledgeGraphService()
            logger.info("ContextManager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ContextManager: {e}")
    
    def get_or_create_context(self, session_id: str) -> Dict[str, Any]:
        """Get existing context or create new one for a session"""
        if session_id not in self.active_contexts:
            self.active_contexts[session_id] = {
                "session_id": session_id,
                "created_at": datetime.utcnow(),
                "last_activity": datetime.utcnow(),
                "current_workflow": None,
                "active_repositories": [],
                "business_rule_traces": [],
                "architectural_insights": [],
                "analysis_focus": None,
                "user_preferences": {},
                "conversation_state": "active",
                "tool_results_summary": {},
                "knowledge_graph_entities": [],
                "context_embeddings": [],
                "conversation_tags": []
            }
            
            # Initialize conversation memory
            self.conversation_memories[session_id] = ConversationMemory(session_id=session_id)
            self.contextual_data[session_id] = []
        
        return self.active_contexts[session_id]
    
    def add_contextual_data(self, session_id: str, data_type: str, data: Dict[str, Any], 
                          source_tool: str, confidence: float = 1.0, 
                          ttl_hours: Optional[int] = None) -> None:
        """Add structured contextual data from tool results"""
        context = self.get_or_create_context(session_id)
        
        # Calculate relevance score based on current conversation focus
        relevance_score = self._calculate_relevance_score(context, data_type, data)
        
        # Set expiration if TTL specified
        expires_at = None
        if ttl_hours:
            expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
        
        contextual_data = ContextualData(
            data_type=data_type,
            data=data,
            source_tool=source_tool,
            confidence=confidence,
            timestamp=datetime.utcnow(),
            relevance_score=relevance_score,
            expires_at=expires_at
        )
        
        self.contextual_data[session_id].append(contextual_data)
        
        # Update main context based on data type
        self._update_context_with_data(context, data_type, data)
        
        # Prune old/low-relevance data
        self._prune_contextual_data(session_id)
        
        # Add to conversation memory if important
        if relevance_score > 0.7:
            memory_entry = {
                "type": "tool_result",
                "tool": source_tool,
                "data_type": data_type,
                "summary": self._summarize_data(data),
                "timestamp": datetime.utcnow().isoformat(),
                "confidence": confidence
            }
            self.conversation_memories[session_id].add_memory(memory_entry, importance=relevance_score)
    
    def get_relevant_context(self, session_id: str, query: str, max_items: int = 10) -> Dict[str, Any]:
        """Get contextual data relevant to a specific query"""
        if session_id not in self.contextual_data:
            return {}
        
        query_lower = query.lower()
        relevant_data = []
        
        # Score contextual data based on query relevance
        for data in self.contextual_data[session_id]:
            if data.is_expired():
                continue
                
            relevance = self._calculate_query_relevance(query_lower, data)
            if relevance > self.context_relevance_threshold:
                relevant_data.append((data, relevance))
        
        # Sort by relevance and recency
        relevant_data.sort(key=lambda x: (x[1], x[0].timestamp), reverse=True)
        
        # Structure the response
        context_summary = {
            "session_id": session_id,
            "query": query,
            "relevant_data": [],
            "business_rule_traces": [],
            "architectural_insights": [],
            "repository_analyses": [],
            "conversation_memories": []
        }
        
        # Add top relevant data
        for data, relevance in relevant_data[:max_items]:
            context_item = {
                "data_type": data.data_type,
                "source_tool": data.source_tool,
                "confidence": data.confidence,
                "relevance": relevance,
                "timestamp": data.timestamp.isoformat(),
                "summary": self._summarize_data(data.data)
            }
            
            context_summary["relevant_data"].append(context_item)
            
            # Categorize by type
            if data.data_type == "business_rule_trace":
                context_summary["business_rule_traces"].append(data.data)
            elif data.data_type == "architectural_insight":
                context_summary["architectural_insights"].append(data.data)
            elif data.data_type == "repository_analysis":
                context_summary["repository_analyses"].append(data.data)
        
        # Add relevant conversation memories
        relevant_memories = self.conversation_memories[session_id].retrieve_relevant_memories(query, max_memories=5)
        context_summary["conversation_memories"] = relevant_memories
        
        return context_summary
    
    def update_workflow_state(self, session_id: str, workflow: ToolSequence, tool_results: Dict[str, Any]) -> None:
        """Update context with workflow execution state and results"""
        context = self.get_or_create_context(session_id)
        
        # Update workflow state
        context["current_workflow"] = {
            "sequence_id": workflow.sequence_id,
            "name": workflow.name,
            "status": workflow.status.value,
            "progress": self._calculate_workflow_progress(workflow),
            "started_at": workflow.started_at.isoformat() if workflow.started_at else None
        }
        
        # Process tool results
        for tool_name, result in tool_results.items():
            if result and isinstance(result, dict):
                # Add tool result as contextual data
                self.add_contextual_data(
                    session_id=session_id,
                    data_type=f"tool_result_{tool_name}",
                    data=result,
                    source_tool=tool_name,
                    confidence=result.get("confidence", 0.8)
                )
        
        # Update context summary
        context["tool_results_summary"] = {
            tool_name: self._summarize_data(result) 
            for tool_name, result in tool_results.items() 
            if result
        }
        
        context["last_activity"] = datetime.utcnow()
    
    async def enrich_context_from_knowledge_graph(self, session_id: str, entities: List[str]) -> Dict[str, Any]:
        """Enrich context using knowledge graph queries"""
        if not self.knowledge_graph or not entities:
            return {}
        
        enriched_context = {}
        
        try:
            for entity in entities:
                # Query knowledge graph for entity relationships
                relationships = await self.knowledge_graph.query_entity_relationships(entity)
                if relationships:
                    enriched_context[entity] = relationships
                    
                    # Add as contextual data
                    self.add_contextual_data(
                        session_id=session_id,
                        data_type="knowledge_graph_entity",
                        data={"entity": entity, "relationships": relationships},
                        source_tool="knowledge_graph",
                        confidence=0.9
                    )
            
        except Exception as e:
            logger.error(f"Error enriching context from knowledge graph: {e}")
        
        return enriched_context
    
    def prune_old_contexts(self) -> None:
        """Remove old, inactive contexts to free memory"""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.max_context_age_hours)
        
        sessions_to_remove = []
        for session_id, context in self.active_contexts.items():
            if context["last_activity"] < cutoff_time:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.active_contexts[session_id]
            if session_id in self.contextual_data:
                del self.contextual_data[session_id]
            if session_id in self.conversation_memories:
                del self.conversation_memories[session_id]
        
        logger.info(f"Pruned {len(sessions_to_remove)} old conversation contexts")
    
    def get_context_summary(self, session_id: str) -> Dict[str, Any]:
        """Get a summary of current context for the session"""
        if session_id not in self.active_contexts:
            return {}
        
        context = self.active_contexts[session_id]
        data_items = self.contextual_data.get(session_id, [])
        
        # Calculate context statistics
        data_by_type = defaultdict(int)
        avg_confidence = 0
        recent_activities = []
        
        for data in data_items[-10:]:  # Last 10 items
            if not data.is_expired():
                data_by_type[data.data_type] += 1
                avg_confidence += data.confidence
                recent_activities.append({
                    "tool": data.source_tool,
                    "type": data.data_type,
                    "timestamp": data.timestamp.isoformat()
                })
        
        if data_items:
            avg_confidence /= len([d for d in data_items if not d.is_expired()])
        
        return {
            "session_id": session_id,
            "created_at": context["created_at"].isoformat(),
            "last_activity": context["last_activity"].isoformat(),
            "current_workflow": context.get("current_workflow"),
            "active_repositories": context.get("active_repositories", []),
            "analysis_focus": context.get("analysis_focus"),
            "total_contextual_items": len([d for d in data_items if not d.is_expired()]),
            "data_by_type": dict(data_by_type),
            "average_confidence": round(avg_confidence, 2),
            "recent_activities": recent_activities[-5:],  # Last 5 activities
            "conversation_memories_count": len(self.conversation_memories.get(session_id, ConversationMemory("")).memories)
        }
    
    def _calculate_relevance_score(self, context: Dict[str, Any], data_type: str, data: Dict[str, Any]) -> float:
        """Calculate relevance score for new contextual data"""
        base_score = 0.5
        
        # Boost score if matches current analysis focus
        if context.get("analysis_focus") and context["analysis_focus"] in data_type:
            base_score += 0.3
        
        # Boost score if high confidence
        if isinstance(data, dict) and data.get("confidence", 0) > 0.8:
            base_score += 0.2
        
        # Boost score for business rule traces and architectural insights
        if data_type in ["business_rule_trace", "architectural_insight"]:
            base_score += 0.2
        
        return min(base_score, 1.0)
    
    def _update_context_with_data(self, context: Dict[str, Any], data_type: str, data: Dict[str, Any]) -> None:
        """Update main context structure with new data"""
        if data_type == "business_rule_trace":
            context["business_rule_traces"].append(data)
        elif data_type == "architectural_insight":
            context["architectural_insights"].append(data)
        elif data_type == "repository_analysis":
            if "active_repositories" not in context:
                context["active_repositories"] = []
            if "repository_path" in data:
                context["active_repositories"].append(data["repository_path"])
    
    def _prune_contextual_data(self, session_id: str) -> None:
        """Remove expired and low-relevance contextual data"""
        if session_id not in self.contextual_data:
            return
        
        current_time = datetime.utcnow()
        data_list = self.contextual_data[session_id]
        
        # Remove expired data
        data_list = [data for data in data_list if not data.is_expired()]
        
        # If still too many items, remove lowest relevance scores
        if len(data_list) > self.max_contextual_data_items:
            data_list.sort(key=lambda x: (x.relevance_score, x.timestamp), reverse=True)
            data_list = data_list[:self.max_contextual_data_items]
        
        self.contextual_data[session_id] = data_list
    
    def _summarize_data(self, data: Dict[str, Any]) -> str:
        """Generate a brief summary of data for context"""
        if isinstance(data, dict):
            # Try common summary fields
            for field in ["summary", "description", "name", "title"]:
                if field in data:
                    return str(data[field])[:200]
            
            # Generate summary from key fields
            key_info = []
            for key, value in data.items():
                if key in ["type", "status", "confidence", "result_count"] and value:
                    key_info.append(f"{key}: {value}")
            
            return "; ".join(key_info[:3]) if key_info else "Data summary unavailable"
        
        return str(data)[:200]
    
    def _calculate_query_relevance(self, query: str, data: ContextualData) -> float:
        """Calculate how relevant contextual data is to a query"""
        relevance = 0.0
        
        # Check query keywords against data content
        data_str = json.dumps(data.data).lower()
        query_words = query.split()
        
        for word in query_words:
            if len(word) > 3 and word in data_str:
                relevance += 0.2
        
        # Boost for recent data
        age_hours = (datetime.utcnow() - data.timestamp).total_seconds() / 3600
        recency_boost = max(0, 1.0 - (age_hours / 24))  # Decay over 24 hours
        relevance += recency_boost * 0.3
        
        # Factor in original relevance score and confidence
        relevance += data.relevance_score * 0.3
        relevance += data.confidence * 0.2
        
        return min(relevance, 1.0)
    
    def _calculate_workflow_progress(self, workflow: ToolSequence) -> float:
        """Calculate workflow completion progress"""
        if not workflow.tools:
            return 0.0
        
        completed_tools = sum(1 for tool in workflow.tools if tool.status.value == "completed")
        return completed_tools / len(workflow.tools)


# Global context manager instance
_context_manager: Optional[ContextManager] = None

async def get_context_manager() -> ContextManager:
    """Get the global context manager instance"""
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
        await _context_manager.initialize()
    return _context_manager