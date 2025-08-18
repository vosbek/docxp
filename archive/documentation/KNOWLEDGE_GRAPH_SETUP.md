# DocXP Knowledge Graph Setup Guide

This guide covers the setup and deployment of DocXP's Neo4j-based Knowledge Graph system for enterprise code analysis.

## Overview

DocXP now includes a complete Knowledge Graph implementation using Neo4j that provides:

- **Cross-technology relationship mapping** across Java, Struts, JSP, CORBA, and other enterprise technologies
- **Business rule flow tracing** from UI entry points to data layer
- **Architectural pattern detection** and similarity analysis
- **Multi-repository dependency analysis**
- **Impact analysis** for code changes
- **Enterprise-grade scalability** with optimized indexes and constraints

## Prerequisites

- Docker and Docker Compose
- Python 3.8+
- 8GB+ RAM (recommended for Neo4j)
- 10GB+ disk space

## Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# Windows
start-knowledge-graph.bat

# Linux/Mac
./start-knowledge-graph.sh
```

### Option 2: Manual Setup

1. **Verify readiness:**
   ```bash
   cd backend
   python verify_docxp_ready.py
   ```

2. **Start Neo4j:**
   ```bash
   docker-compose up -d neo4j
   ```

3. **Initialize database:**
   ```bash
   python scripts/setup-neo4j.py
   ```

4. **Run integration tests:**
   ```bash
   python test_knowledge_graph_integration.py
   ```

5. **Start all services:**
   ```bash
   docker-compose up -d
   ```

## Architecture

### Components

- **Neo4j 5.15 Enterprise** - Graph database with APOC plugins
- **KnowledgeGraphService** - Core Python service for graph operations
- **GraphMigrationService** - Schema management and versioning
- **GraphSyncService** - Data synchronization across repositories

### Data Model

#### Node Types
- `CodeEntity` - Base class for all code elements
- `Repository` - Source code repositories
- `Class`, `Method`, `Interface` - Java code structures
- `JSPPage` - JSP/web pages
- `StrutsAction` - Struts framework actions
- `BusinessRule` - Business logic components
- `DatabaseTable` - Database schema elements

#### Relationship Types
- `CALLS` - Method/function invocations
- `DEPENDS_ON` - Dependencies between components
- `FLOWS_TO` - Business process flows
- `BELONGS_TO` - Organizational hierarchy
- `IMPLEMENTS`, `EXTENDS` - Inheritance relationships

## Configuration

### Environment Variables

```bash
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=docxp-neo4j-2024
NEO4J_DATABASE=neo4j

# Performance Tuning
NEO4J_MAX_CONNECTION_LIFETIME=300
NEO4J_MAX_CONNECTION_POOL_SIZE=50
NEO4J_CONNECTION_ACQUISITION_TIMEOUT=60
```

### Docker Compose Configuration

The `docker-compose.yml` includes:
- Neo4j Enterprise with APOC plugins
- Optimized memory settings (2GB heap, 1GB page cache)
- Health checks and dependency management
- Persistent volumes for data

## API Usage

### Basic Operations

```python
from app.services.knowledge_graph_service import get_knowledge_graph_service

# Get service instance
kg_service = await get_knowledge_graph_service()

# Create a repository node
repo_node = GraphNode(
    id="my_repo_001",
    node_type=NodeType.REPOSITORY,
    properties={
        "name": "legacy-banking-system",
        "language": "Java",
        "framework": "Struts"
    }
)
await kg_service.create_node(repo_node)

# Create relationships
relationship = GraphRelationship(
    source_id="class_AccountService",
    target_id="my_repo_001",
    relationship_type=RelationshipType.BELONGS_TO
)
await kg_service.create_relationship(relationship)
```

### Advanced Analysis

```python
# Find business rule paths
paths = await kg_service.find_business_rule_path(
    entry_point="jsp_account_details",
    max_depth=10
)

# Analyze impact of changes
impact = await kg_service.analyze_impact_of_change(
    entity_id="class_AccountService",
    change_type="method_signature_change"
)

# Find similar patterns
patterns = await kg_service.find_similar_patterns(
    pattern_type="service_class",
    repository_id="my_repo_001"
)
```

## Access Points

After startup, access:

- **Neo4j Browser**: http://localhost:7474
  - Username: `neo4j`
  - Password: `docxp-neo4j-2024`
- **DocXP Backend**: http://localhost:8000
- **DocXP Frontend**: http://localhost:80

## Performance Optimization

### Neo4j Tuning

The default configuration allocates:
- **Heap Size**: 2GB (for query processing)
- **Page Cache**: 1GB (for data caching)
- **Connection Pool**: 50 connections

For production, adjust based on your hardware:

```yaml
environment:
  - NEO4J_dbms_memory_heap_max__size=4G
  - NEO4J_dbms_memory_pagecache_size=2G
```

### Index Strategy

The system creates optimized indexes for:
- Entity ID lookups (unique constraints)
- Name-based searches
- Pattern type filtering
- Temporal queries (created_at, updated_at)
- Business domain categorization

## Monitoring

### Health Checks

```bash
# Check Neo4j status
curl http://localhost:7474/db/data/

# Check graph statistics
python -c "
import asyncio
from app.services.knowledge_graph_service import get_knowledge_graph_service

async def check():
    kg = await get_knowledge_graph_service()
    stats = await kg.get_graph_statistics()
    print(stats)

asyncio.run(check())
"
```

### Metrics

Monitor these key metrics:
- Node count by type
- Relationship count by type
- Query response times
- Memory usage
- Connection pool utilization

## Troubleshooting

### Common Issues

1. **Connection Refused**
   ```bash
   # Check if Neo4j is running
   docker ps | grep neo4j
   
   # Check logs
   docker logs docxp-neo4j
   ```

2. **Memory Issues**
   ```bash
   # Increase Docker memory allocation
   # In Docker Desktop: Settings > Resources > Memory > 8GB
   ```

3. **Permission Errors**
   ```bash
   # Ensure volumes have correct permissions
   docker-compose down -v
   docker-compose up -d
   ```

### Validation

Run the integration test suite:
```bash
cd backend
python test_knowledge_graph_integration.py
```

Expected output:
```
✅ Connection Test PASSED
✅ Schema Initialization PASSED
✅ Node Creation PASSED
✅ Relationship Creation PASSED
...
🎉 ALL TESTS PASSED - DocXP Knowledge Graph is ready!
```

## Integration with Existing Services

The Knowledge Graph integrates with:

- **Migration Service**: Manages schema evolution
- **Sync Service**: Keeps graph data current
- **AI Service**: Provides context for AI analysis
- **Documentation Service**: Enhances generated docs
- **Search Service**: Improves semantic search

## Next Steps

1. **Load Your Data**: Use the parsing services to populate the graph
2. **Configure Dashboards**: Set up monitoring and analytics
3. **Customize Queries**: Adapt the analysis queries for your specific use cases
4. **Scale Up**: Increase Neo4j resources for production workloads

## Support

For issues or questions:
- Check the integration test results
- Review Neo4j logs: `docker logs docxp-neo4j`
- Verify configuration with `verify_docxp_ready.py`
- Consult the [Neo4j documentation](https://neo4j.com/docs/)

---

**Status**: ✅ Ready for production deployment
**Version**: 1.0.0
**Last Updated**: 2025-08-18