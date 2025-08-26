# DocXP Enterprise Architecture Migration Plan

## Current vs Desired Architecture

### Current (Working but Hardcoded)
- **Vector Storage**: ChromaDB (embedded, local files)
- **Embeddings**: CodeBERT (local model)
- **Search**: ChromaDB + OpenSearch hybrid
- **Database**: PostgreSQL (metadata only)

### Desired (Enterprise-Grade)
- **Vector Storage**: PostgreSQL with pgvector extension
- **Embeddings**: AWS Bedrock Titan (cloud-based)
- **Search**: PostgreSQL vector + OpenSearch hybrid
- **Database**: PostgreSQL (unified)

## Migration Phases

### Phase 1: Stabilize Current System (IMMEDIATE - 1 day)
```bash
# Your system is now working with:
- ChromaDB + CodeBERT (functional)
- PostgreSQL for metadata
- OpenSearch for hybrid search
- AWS credentials for chat (Bedrock Claude)
```

### Phase 2: Add Vector Database Abstraction (1 week)
```python
# Create abstraction layer in app/core/vector_database.py
class VectorDatabaseInterface:
    async def add_embedding(self, id: str, embedding: List[float], metadata: Dict) -> bool
    async def search_similar(self, query_embedding: List[float], limit: int) -> List[Dict]
    async def delete_embedding(self, id: str) -> bool

# Implementations:
- ChromaDBVectorDatabase (current, working)
- PostgreSQLVectorDatabase (new, enterprise)
```

### Phase 3: Implement PostgreSQL Vector (1-2 weeks)
```sql
-- Add pgvector extension to your PostgreSQL database
CREATE EXTENSION IF NOT EXISTS vector;

-- Create embeddings table
CREATE TABLE document_embeddings (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(1024),  -- AWS Bedrock Titan dimension
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Add vector similarity index
CREATE INDEX ON document_embeddings USING ivfflat (embedding vector_cosine_ops);
```

### Phase 4: AWS Bedrock Embeddings (1 week)
```python
# Update config.py with environment-based selection
EMBEDDING_PROVIDER: str = Field(default="codebert", env="EMBEDDING_PROVIDER")
BEDROCK_EMBED_MODEL: str = Field(default="amazon.titan-embed-text-v2:0", env="BEDROCK_EMBED_MODEL")

# When EMBEDDING_PROVIDER="bedrock":
# - Use AWS Bedrock for embeddings
# - Store in PostgreSQL vector table
# - Keep existing search logic
```

### Phase 5: Configuration Switching (3 days)
```env
# .env configuration for enterprise mode
VECTOR_DATABASE_TYPE=postgresql_pgvector
EMBEDDING_PROVIDER=bedrock
BEDROCK_EMBED_MODEL=amazon.titan-embed-text-v2:0
POSTGRESQL_VECTOR_URL=postgresql://user:pass@localhost:5432/docxp_enterprise
```

## Development Strategy

### Option A: Gradual Migration (Recommended)
1. ✅ **Current system working** (ChromaDB + CodeBERT)
2. 🔄 **Add abstraction layer** (supports both backends)
3. 🔄 **Implement PostgreSQL backend** (parallel to ChromaDB)
4. 🔄 **Add AWS Bedrock support** (parallel to CodeBERT)
5. 🔄 **Switch configuration** (environment-based)
6. ✅ **Retire ChromaDB + CodeBERT** (clean up)

### Option B: Big Bang Migration (Risky)
- Rewrite vector service completely
- High risk of breaking working functionality
- Not recommended for production systems

## Implementation Priority

### High Priority (Enterprise Requirements)
1. **PostgreSQL vector storage** - Scalability & enterprise support
2. **AWS Bedrock embeddings** - Better quality & consistency  
3. **Configuration abstraction** - Multiple environment support

### Medium Priority (Nice to Have)
1. **Embedding model caching** - Cost optimization
2. **Vector index optimization** - Performance tuning
3. **Monitoring & metrics** - Operational visibility

### Low Priority (Future)
1. **Multiple vector backends** - Multi-cloud support
2. **Embedding model switching** - A/B testing
3. **Advanced search features** - Hybrid ranking

## Cost Analysis

### Current System (Free)
- ChromaDB: Local storage, no cost
- CodeBERT: Local model, compute cost only
- PostgreSQL: Self-hosted

### Enterprise System (Paid)
- PostgreSQL + pgvector: Hosting cost + compute
- AWS Bedrock Titan: $0.0001 per 1K tokens
- OpenSearch: AWS managed service cost

## Next Steps

1. **Verify current system works** with all fixes applied
2. **Choose migration timeline** based on business needs
3. **Start with abstraction layer** if migrating
4. **Test incrementally** with small datasets first

## Risk Mitigation

- Keep ChromaDB backend as fallback during migration
- Test PostgreSQL vector performance with your data volume
- Monitor AWS Bedrock costs during transition
- Implement rollback procedures for each phase