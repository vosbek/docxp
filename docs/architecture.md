# DocXP Enterprise Architecture Documentation

## Enterprise Stack Architecture Overview

```mermaid
architecture-beta
    group frontend(cloud)[Frontend Layer]
    group api(server)[API Gateway Layer] 
    group services(database)[Service Layer]
    group processing(disk)[Processing Layer]
    group data(database)[Data Layer]
    group external(internet)[External Services]

    service angular(cloud)[Angular SPA] in frontend
    service nginx(cloud)[Nginx Proxy] in frontend

    service fastapi(server)[FastAPI Gateway] in api
    service middleware(server)[Security & CORS] in api
    service health(server)[Health Checks] in api
    service swagger(server)[API Docs] in api

    service orchestration(database)[Project Coordinator] in services
    service knowledge(database)[Knowledge Graph Service] in services
    service discovery(database)[Cross-Repo Discovery] in services
    service strands(database)[Strands Agent Service] in services
    service bedrock_svc(database)[Bedrock Embedding Service] in services
    service graph_sync(database)[Graph Sync Service] in services

    service indexing(disk)[V1 Indexing Engine] in processing
    service parsers(disk)[Parser Factory] in processing
    service flow_tracer(disk)[Flow Tracers] in processing
    service domain_classifier(disk)[Domain Classifier] in processing
    service migration_svc(disk)[Graph Migration] in processing

    service postgres(database)[PostgreSQL + pgvector] in data
    service neo4j(database)[Neo4j Enterprise] in data
    service opensearch(database)[OpenSearch Engine] in data
    service redis(database)[Redis Cache & Queue] in data
    service minio(database)[MinIO Storage] in data

    service bedrock(internet)[AWS Bedrock] in external
    service aws_s3(internet)[AWS S3] in external

    angular:B -- T:fastapi
    nginx:B -- T:angular
    
    fastapi:R -- L:middleware
    fastapi:B -- T:health
    fastapi:B -- T:swagger
    
    fastapi:B -- T:orchestration
    fastapi:B -- T:strands
    
    orchestration:R -- L:knowledge
    orchestration:R -- L:discovery
    orchestration:R -- L:bedrock_svc
    orchestration:B -- T:graph_sync
    
    strands:T -- B:bedrock
    bedrock_svc:T -- B:bedrock
    
    knowledge:B -- T:indexing
    discovery:B -- T:parsers
    
    indexing:R -- L:flow_tracer
    indexing:R -- L:domain_classifier
    parsers:B -- T:migration_svc
    
    orchestration:B -- T:postgres
    knowledge:B -- T:neo4j
    discovery:B -- T:opensearch
    strands:B -- T:redis
    
    graph_sync:T -- B:neo4j
    migration_svc:T -- B:postgres
    
    bedrock_svc:T -- B:minio
    indexing:T -- B:aws_s3
```

## Enterprise Service Interaction Map

```mermaid
graph TB
    subgraph "Client Layer"
        UI["Angular Frontend<br/>Port 4200"]
        BROWSER["Web Browser<br/>User Interface"]
    end
    
    subgraph "API Gateway Layer"
        API["FastAPI Gateway<br/>Port 8001"]
        CORS["CORS Middleware"]
        AUTH["Authentication"]
        HEALTH["Health Checks"]
    end
    
    subgraph "Core Services Layer"
        PROJECT["Project Coordinator<br/>Multi-repo orchestration"]
        KNOWLEDGE["Knowledge Graph Service<br/>Relationship mapping"]
        STRANDS["Strands Agent Service<br/>AI orchestration"]
        BEDROCK_SVC["Bedrock Embedding Service<br/>Vector generation"]
        DISCOVERY["Cross-Repo Discovery<br/>Dependency analysis"]
        DOMAIN["Domain Classifier<br/>Business logic identification"]
    end
    
    subgraph "Processing Engine Layer"
        INDEXING["V1 Indexing Engine<br/>File processing"]
        PARSERS["Parser Factory<br/>Multi-language support"]
        FLOW["Flow Tracers<br/>Business rule flows"]
        MIGRATION["Graph Migration<br/>Data transformation"]
        SYNC["Graph Sync Service<br/>Real-time updates"]
    end
    
    subgraph "Data Storage Layer"
        POSTGRES[("PostgreSQL + pgvector<br/>Structured data + vectors")]
        NEO4J[("Neo4j Enterprise<br/>Knowledge graph")]
        OPENSEARCH[("OpenSearch<br/>Full-text + semantic search")]
        REDIS[("Redis<br/>Cache + message queue")]
        MINIO[("MinIO<br/>Object storage")]
    end
    
    subgraph "External Services"
        BEDROCK["AWS Bedrock<br/>Claude + Titan models"]
        S3["AWS S3<br/>Scalable storage"]
    end
    
    %% Client connections
    BROWSER --> UI
    UI --> API
    
    %% API Gateway processing
    API --> CORS
    API --> AUTH
    API --> HEALTH
    
    %% Core service orchestration
    API --> PROJECT
    API --> STRANDS
    
    PROJECT --> KNOWLEDGE
    PROJECT --> DISCOVERY
    PROJECT --> BEDROCK_SVC
    PROJECT --> DOMAIN
    
    %% AI service connections
    STRANDS --> BEDROCK
    BEDROCK_SVC --> BEDROCK
    
    %% Processing engine connections
    KNOWLEDGE --> INDEXING
    DISCOVERY --> PARSERS
    DOMAIN --> FLOW
    
    INDEXING --> MIGRATION
    PARSERS --> SYNC
    
    %% Data layer connections
    PROJECT --> POSTGRES
    KNOWLEDGE --> NEO4J
    DISCOVERY --> OPENSEARCH
    STRANDS --> REDIS
    BEDROCK_SVC --> MINIO
    
    %% Cross-service data flows
    SYNC --> NEO4J
    MIGRATION --> POSTGRES
    FLOW --> OPENSEARCH
    
    %% External service connections
    BEDROCK_SVC --> S3
    INDEXING --> S3
    
    %% Styling
    classDef clientLayer fill:#e1f5fe
    classDef apiLayer fill:#f3e5f5
    classDef serviceLayer fill:#e8f5e8
    classDef processingLayer fill:#fff3e0
    classDef dataLayer fill:#fce4ec
    classDef externalLayer fill:#f1f8e9
    
    class UI,BROWSER clientLayer
    class API,CORS,AUTH,HEALTH apiLayer
    class PROJECT,KNOWLEDGE,STRANDS,BEDROCK_SVC,DISCOVERY,DOMAIN serviceLayer
    class INDEXING,PARSERS,FLOW,MIGRATION,SYNC processingLayer
    class POSTGRES,NEO4J,OPENSEARCH,REDIS,MINIO dataLayer
    class BEDROCK,S3 externalLayer
```

## Enterprise Repository Analysis Workflow

```mermaid
sequenceDiagram
    participant Client as Angular Frontend
    participant Gateway as FastAPI Gateway
    participant Coordinator as Project Coordinator
    participant IndexEngine as V1 Indexing Engine
    participant StrandsAgent as Strands Agent Service
    participant BedrokSvc as Bedrock Embedding Service
    participant KnowledgeGraph as Knowledge Graph Service
    participant CrossRepo as Cross-Repo Discovery
    participant FlowTracer as Flow Tracer
    participant PostgreSQL as PostgreSQL + pgvector
    participant Neo4j as Neo4j Enterprise
    participant OpenSearch as OpenSearch Engine
    participant Redis as Redis Queue
    participant Bedrock as AWS Bedrock
    participant MinIO as MinIO Storage

    Client->>+Gateway: POST /api/projects/analyze-repository
    Gateway->>+Coordinator: initiate_project_analysis()
    Coordinator->>+PostgreSQL: Create Project + IndexingJob (pending)
    PostgreSQL-->>-Coordinator: project_id, job_id
    Coordinator->>+Redis: Queue background analysis task
    Redis-->>-Coordinator: task_queued
    Coordinator-->>-Gateway: {project_id, job_id, status: "queued"}
    Gateway-->>-Client: Analysis initiated
    
    Note over Redis, IndexEngine: Background Processing Begins
    Redis->>+IndexEngine: Start repository analysis
    
    par Repository Processing
        IndexEngine->>+PostgreSQL: Update job status (processing)
        IndexEngine->>IndexEngine: Clone & scan repository
        IndexEngine->>+MinIO: Store repository clone
        IndexEngine->>IndexEngine: Extract file metadata
        
        loop For each file batch
            IndexEngine->>+StrandsAgent: analyze_code_batch(files[])
            StrandsAgent->>+Bedrock: Generate embeddings + extract patterns
            Bedrock-->>-StrandsAgent: embeddings + analysis
            StrandsAgent-->>-IndexEngine: enriched_entities[]
            
            IndexEngine->>+BedrokSvc: generate_embeddings(code_chunks)
            BedrokSvc->>+Bedrock: Titan embedding API call
            Bedrock-->>-BedrokSvc: vector_embeddings[]
            BedrokSvc-->>-IndexEngine: embeddings_stored
            
            IndexEngine->>+PostgreSQL: Store entities + embeddings
            IndexEngine->>+OpenSearch: Index code chunks + metadata
        end
    and Knowledge Graph Construction
        IndexEngine->>+KnowledgeGraph: build_graph(entities, relationships)
        KnowledgeGraph->>+Neo4j: Create nodes + relationships
        Neo4j-->>-KnowledgeGraph: graph_created
        KnowledgeGraph-->>-IndexEngine: knowledge_graph_ready
        
        KnowledgeGraph->>+FlowTracer: trace_business_flows()
        FlowTracer->>FlowTracer: Analyze JSP→Struts→Java→DB flows
        FlowTracer->>+Neo4j: Store flow relationships
        FlowTracer->>+PostgreSQL: Store flow metadata
        FlowTracer-->>-KnowledgeGraph: flows_traced
    and Cross-Repository Analysis
        IndexEngine->>+CrossRepo: analyze_dependencies(project_id)
        CrossRepo->>+PostgreSQL: Query related projects
        CrossRepo->>+Neo4j: Find cross-repo relationships
        CrossRepo->>CrossRepo: Identify shared components
        CrossRepo->>+PostgreSQL: Store dependency analysis
        CrossRepo-->>-IndexEngine: cross_analysis_complete
    end
    
    IndexEngine->>+PostgreSQL: Update job status (completed)
    IndexEngine->>+Redis: Publish completion event
    IndexEngine-->>-Redis: Analysis complete
    
    Note over Client: Real-time status updates
    Client->>+Gateway: WebSocket /ws/project/{project_id}/status
    Gateway->>+Redis: Subscribe to project events
    Redis-->>-Gateway: Status updates stream
    Gateway-->>-Client: Real-time progress updates
    
    Note over Client: Query completed analysis
    Client->>+Gateway: GET /api/projects/{project_id}/insights
    Gateway->>+Coordinator: get_project_insights()
    
    par Data Retrieval
        Coordinator->>+PostgreSQL: Get project metadata + entities
        Coordinator->>+Neo4j: Get knowledge graph insights
        Coordinator->>+OpenSearch: Get semantic search results
    end
    
    Coordinator->>Coordinator: Synthesize comprehensive insights
    Coordinator-->>-Gateway: project_insights
    Gateway-->>-Client: Complete analysis results
```

## Enterprise Processing Pipeline Flow

```mermaid
flowchart TD
    Start([Repository Analysis Request]) --> ProjectInit[Initialize Project Context]
    ProjectInit --> ValidateAccess{AWS Bedrock<br/>& Services Available?}
    
    ValidateAccess -->|No| ConfigError["❌ Configuration Error<br/>Check AWS credentials & services"]
    ValidateAccess -->|Yes| CreateProject["📊 Create Project Entry<br/>PostgreSQL"]
    
    CreateProject --> QueueJob["🔄 Queue Analysis Job<br/>Redis"]
    QueueJob --> RepoValidation{Repository<br/>Accessible?}
    
    RepoValidation -->|No| RepoError["❌ Repository Error<br/>Invalid path or permissions"]
    RepoValidation -->|Yes| CloneRepo["📥 Clone Repository<br/>MinIO Storage"]
    
    CloneRepo --> ScanStructure["🔍 Scan Repository Structure<br/>File discovery & classification"]
    
    ScanStructure --> ProcessingChoice{Processing<br/>Strategy}
    
    ProcessingChoice -->|Small Repo| SingleThreaded[Single-threaded Processing]
    ProcessingChoice -->|Large Repo| MultiThreaded["⚡ Multi-threaded Processing<br/>Batch processing"]
    
    SingleThreaded --> FileAnalysis
    MultiThreaded --> FileAnalysis["📝 File Analysis Pipeline"]
    
    FileAnalysis --> ParserSelection{"Select Parser<br/>by File Type"}
    
    ParserSelection -->|Java| JavaParser["☕ Java Parser<br/>Classes, methods, dependencies"]
    ParserSelection -->|Python| PythonParser["🐍 Python Parser<br/>Modules, functions, imports"]
    ParserSelection -->|JSP/Struts| WebParser["🌐 Web Framework Parser<br/>Actions, forms, flows"]
    ParserSelection -->|TypeScript| TSParser["📜 TypeScript Parser<br/>Components, services"]
    ParserSelection -->|Generic| GenericParser["📄 Generic Text Parser<br/>Basic structure"]
    
    JavaParser --> EntityExtraction
    PythonParser --> EntityExtraction
    WebParser --> EntityExtraction
    TSParser --> EntityExtraction
    GenericParser --> EntityExtraction["🎯 Entity Extraction<br/>Code structures & relationships"]
    
    EntityExtraction --> AIEnrichment["🤖 AI-Powered Analysis<br/>Strands Agents + AWS Bedrock"]
    
    AIEnrichment --> AITasks{
"AI Analysis Tasks"}
    
    AITasks -->|Patterns| PatternAnalysis["🔍 Pattern Recognition<br/>Design patterns & anti-patterns"]
    AITasks -->|Rules| BusinessRules["📋 Business Rule Extraction<br/>Logic identification"]
    AITasks -->|Flows| FlowTracing["🔄 Flow Tracing<br/>Cross-technology paths"]
    AITasks -->|Embeddings| VectorGeneration["📊 Vector Generation<br/>Semantic embeddings"]
    
    PatternAnalysis --> StoreResults
    BusinessRules --> StoreResults
    FlowTracing --> StoreResults
    VectorGeneration --> StoreResults["💾 Store Analysis Results"]
    
    StoreResults --> DataStorage{"Multi-store<br/>Data Persistence"}
    
    DataStorage -->|Structured Data| PostgreSQLStore["🗄️ PostgreSQL<br/>Entities, metadata, vectors"]
    DataStorage -->|Graph Data| Neo4jStore["🕸️ Neo4j<br/>Relationships, flows"]
    DataStorage -->|Search Index| OpenSearchStore["🔍 OpenSearch<br/>Full-text, semantic search"]
    DataStorage -->|Cache Data| RedisStore["⚡ Redis<br/>Session cache, job status"]
    
    PostgreSQLStore --> KnowledgeGraph
    Neo4jStore --> KnowledgeGraph
    OpenSearchStore --> KnowledgeGraph
    RedisStore --> KnowledgeGraph["🧠 Knowledge Graph Construction<br/>Unified intelligence layer"]
    
    KnowledgeGraph --> CrossRepoAnalysis{"Multi-repository<br/>Project?"}
    
    CrossRepoAnalysis -->|Yes| DiscoveryService["🔗 Cross-Repo Discovery<br/>Dependency analysis"]
    CrossRepoAnalysis -->|No| FinalValidation
    
    DiscoveryService --> DependencyMapping["📈 Dependency Mapping<br/>Inter-project relationships"]
    DependencyMapping --> FinalValidation["✅ Final Validation<br/>Quality checks"]
    
    FinalValidation --> ValidationPassed{"All Validations<br/>Passed?"}
    
    ValidationPassed -->|Yes| Success["🎉 Analysis Complete<br/>Results available"]
    ValidationPassed -->|No| PartialSuccess["⚠️ Partial Success<br/>Some issues found"]
    
    Success --> NotifyComplete
    PartialSuccess --> NotifyComplete["📢 Notify Completion<br/>Update project status"]
    
    NotifyComplete --> WebSocketUpdate["🔄 Real-time Updates<br/>Frontend notification"]
    WebSocketUpdate --> End(["📊 Analysis Available<br/>Ready for exploration"])
    
    %% Error handling paths
    ConfigError --> End
    RepoError --> End
    
    %% Styling
    classDef startEnd fill:#e8f5e8,stroke:#4caf50,stroke-width:2px
    classDef process fill:#e3f2fd,stroke:#2196f3,stroke-width:2px
    classDef decision fill:#fff3e0,stroke:#ff9800,stroke-width:2px
    classDef error fill:#ffebee,stroke:#f44336,stroke-width:2px
    classDef success fill:#e8f5e8,stroke:#4caf50,stroke-width:2px
    classDef storage fill:#f3e5f5,stroke:#9c27b0,stroke-width:2px
    
    class Start,End startEnd
    class ProjectInit,CreateProject,QueueJob,CloneRepo,ScanStructure,FileAnalysis,EntityExtraction,AIEnrichment,StoreResults,KnowledgeGraph,DiscoveryService,DependencyMapping,FinalValidation,NotifyComplete,WebSocketUpdate process
    class ValidateAccess,RepoValidation,ProcessingChoice,ParserSelection,AITasks,DataStorage,CrossRepoAnalysis,ValidationPassed decision
    class ConfigError,RepoError error
    class Success,PartialSuccess success
    class PostgreSQLStore,Neo4jStore,OpenSearchStore,RedisStore storage
```

## Enterprise Service Dependency Matrix

```mermaid
flowchart TB
    subgraph "Frontend Tier"
        direction TB
        ANGULAR["Angular SPA<br/>📱 User Interface"]
        NGINX["Nginx Proxy<br/>🌐 Load Balancer"]
    end
    
    subgraph "API Gateway Tier"
        direction TB
        FASTAPI["FastAPI Gateway<br/>🚪 Request Router"]
        MIDDLEWARE["Security Middleware<br/>🔒 CORS, Auth, Rate Limiting"]
        HEALTH_API["Health Check API<br/>💓 System Monitoring"]
        SWAGGER["OpenAPI Docs<br/>📚 Interactive Documentation"]
    end
    
    subgraph "Core Service Tier"
        direction TB
        PROJECT_COORD["Project Coordinator<br/>🎯 Multi-repo Orchestration"]
        KNOWLEDGE_SVC["Knowledge Graph Service<br/>🧠 Relationship Intelligence"]
        STRANDS_AGENT["Strands Agent Service<br/>🤖 AI Agent Orchestration"]
        BEDROCK_SVC["Bedrock Embedding Service<br/>📊 Vector Generation"]
        CROSS_DISCOVERY["Cross-Repo Discovery<br/>🔗 Dependency Analysis"]
        DOMAIN_CLASS["Domain Classifier<br/>📋 Business Logic Identification"]
        GRAPH_SYNC["Graph Sync Service<br/>⚡ Real-time Graph Updates"]
    end
    
    subgraph "Processing Engine Tier"
        direction TB
        V1_INDEXING["V1 Indexing Engine<br/>⚙️ File Processing Pipeline"]
        PARSER_FACTORY["Parser Factory<br/>🔧 Multi-language Analysis"]
        FLOW_TRACER["Flow Tracer<br/>🔄 Business Rule Flows"]
        MIGRATION_SVC["Graph Migration Service<br/>🔄 Data Transformation"]
        ARCHITECTURAL["Architectural Insight Service<br/>🏗️ Pattern Analysis"]
    end
    
    subgraph "Parser Ecosystem"
        direction LR
        JAVA_PARSER["Java Parser<br/>☕"]
        PYTHON_PARSER["Python Parser<br/>🐍"]
        JSP_PARSER["JSP/Struts Parser<br/>🌐"]
        TS_PARSER["TypeScript Parser<br/>📜"]
        GENERIC_PARSER["Generic Parser<br/>📄"]
    end
    
    subgraph "Data Storage Tier"
        direction TB
        POSTGRESQL["PostgreSQL + pgvector<br/>🗄️ Structured Data + Vectors"]
        NEO4J["Neo4j Enterprise<br/>🕸️ Knowledge Graph"]
        OPENSEARCH["OpenSearch Engine<br/>🔍 Full-text + Semantic Search"]
        REDIS["Redis<br/>⚡ Cache + Message Queue"]
        MINIO["MinIO<br/>📦 Object Storage"]
    end
    
    subgraph "External Services Tier"
        direction LR
        AWS_BEDROCK["AWS Bedrock<br/>🧠 Claude + Titan Models"]
        AWS_S3["AWS S3<br/>☁️ Scalable Cloud Storage"]
        VECTOR_DB["Vector Database<br/>📊 High-performance Vectors"]
    end
    
    %% Frontend connections
    NGINX --> ANGULAR
    ANGULAR --> FASTAPI
    
    %% API Gateway internal
    FASTAPI --> MIDDLEWARE
    FASTAPI --> HEALTH_API
    FASTAPI --> SWAGGER
    
    %% API to Core Services
    FASTAPI --> PROJECT_COORD
    FASTAPI --> STRANDS_AGENT
    FASTAPI --> HEALTH_API
    
    %% Core Service Orchestration
    PROJECT_COORD --> KNOWLEDGE_SVC
    PROJECT_COORD --> CROSS_DISCOVERY
    PROJECT_COORD --> BEDROCK_SVC
    PROJECT_COORD --> DOMAIN_CLASS
    
    KNOWLEDGE_SVC --> GRAPH_SYNC
    STRANDS_AGENT --> BEDROCK_SVC
    
    %% Core to Processing Engine
    KNOWLEDGE_SVC --> V1_INDEXING
    CROSS_DISCOVERY --> PARSER_FACTORY
    DOMAIN_CLASS --> FLOW_TRACER
    GRAPH_SYNC --> MIGRATION_SVC
    PROJECT_COORD --> ARCHITECTURAL
    
    %% Processing Engine to Parsers
    PARSER_FACTORY --> JAVA_PARSER
    PARSER_FACTORY --> PYTHON_PARSER
    PARSER_FACTORY --> JSP_PARSER
    PARSER_FACTORY --> TS_PARSER
    PARSER_FACTORY --> GENERIC_PARSER
    
    %% Processing to Data Storage
    V1_INDEXING --> POSTGRESQL
    V1_INDEXING --> OPENSEARCH
    V1_INDEXING --> MINIO
    
    KNOWLEDGE_SVC --> NEO4J
    CROSS_DISCOVERY --> OPENSEARCH
    STRANDS_AGENT --> REDIS
    BEDROCK_SVC --> MINIO
    
    GRAPH_SYNC --> NEO4J
    MIGRATION_SVC --> POSTGRESQL
    FLOW_TRACER --> NEO4J
    ARCHITECTURAL --> POSTGRESQL
    
    %% External Service Connections
    STRANDS_AGENT --> AWS_BEDROCK
    BEDROCK_SVC --> AWS_BEDROCK
    BEDROCK_SVC --> AWS_S3
    V1_INDEXING --> AWS_S3
    OPENSEARCH --> VECTOR_DB
    
    %% Cross-tier communication patterns
    REDIS -.-> PROJECT_COORD
    REDIS -.-> KNOWLEDGE_SVC
    REDIS -.-> V1_INDEXING
    
    NEO4J -.-> CROSS_DISCOVERY
    POSTGRESQL -.-> ARCHITECTURAL
    OPENSEARCH -.-> DOMAIN_CLASS
    
    %% Styling
    classDef frontend fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef api fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef core fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef processing fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef parser fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    classDef data fill:#e0f2f1,stroke:#004d40,stroke-width:2px
    classDef external fill:#f1f8e9,stroke:#33691e,stroke-width:2px
    
    class ANGULAR,NGINX frontend
    class FASTAPI,MIDDLEWARE,HEALTH_API,SWAGGER api
    class PROJECT_COORD,KNOWLEDGE_SVC,STRANDS_AGENT,BEDROCK_SVC,CROSS_DISCOVERY,DOMAIN_CLASS,GRAPH_SYNC core
    class V1_INDEXING,PARSER_FACTORY,FLOW_TRACER,MIGRATION_SVC,ARCHITECTURAL processing
    class JAVA_PARSER,PYTHON_PARSER,JSP_PARSER,TS_PARSER,GENERIC_PARSER parser
    class POSTGRESQL,NEO4J,OPENSEARCH,REDIS,MINIO data
    class AWS_BEDROCK,AWS_S3,VECTOR_DB external
```

## Data Flow and State Management

```mermaid
stateDiagram-v2
    [*] --> ProjectInitialization : Repository Analysis Request
    
    ProjectInitialization --> ConfigurationValidation : Validate Environment
    ConfigurationValidation --> ServiceHealthCheck : Check Data Stores
    ServiceHealthCheck --> QueueManagement : Initialize Background Processing
    
    QueueManagement --> RepositoryProcessing : Start Analysis Pipeline
    
    state RepositoryProcessing {
        [*] --> FileDiscovery
        FileDiscovery --> ParsingPipeline : Batch Files
        ParsingPipeline --> EntityExtraction : Parse by Language
        EntityExtraction --> AIEnrichment : Extract Structures
        AIEnrichment --> VectorGeneration : Apply AI Analysis
        VectorGeneration --> StorageDistribution : Generate Embeddings
        StorageDistribution --> [*] : Batch Complete
    }
    
    RepositoryProcessing --> KnowledgeGraphConstruction : All Files Processed
    
    state KnowledgeGraphConstruction {
        [*] --> RelationshipMapping
        RelationshipMapping --> FlowAnalysis : Map Code Relationships
        FlowAnalysis --> PatternRecognition : Trace Business Flows
        PatternRecognition --> GraphOptimization : Identify Patterns
        GraphOptimization --> [*] : Graph Complete
    }
    
    KnowledgeGraphConstruction --> CrossRepositoryAnalysis : Single Repo Complete
    
    state CrossRepositoryAnalysis {
        [*] --> DependencyDiscovery
        DependencyDiscovery --> ImpactAnalysis : Find Shared Components
        ImpactAnalysis --> ArchitecturalInsights : Assess Changes
        ArchitecturalInsights --> [*] : Cross-Analysis Complete
    }
    
    CrossRepositoryAnalysis --> ResultsSynthesis : Analysis Complete
    
    state ResultsSynthesis {
        [*] --> DataAggregation
        DataAggregation --> InsightGeneration : Combine All Sources
        InsightGeneration --> QualityValidation : Generate Comprehensive Insights
        QualityValidation --> ReportGeneration : Validate Results
        ReportGeneration --> [*] : Results Ready
    }
    
    ResultsSynthesis --> ProjectComplete : Analysis Finalized
    
    ProjectComplete --> [*] : Ready for User Interaction
    
    %% Error states
    ConfigurationValidation --> ConfigurationError : Invalid Settings
    ServiceHealthCheck --> ServiceError : Service Unavailable
    RepositoryProcessing --> ProcessingError : Analysis Failure
    KnowledgeGraphConstruction --> GraphError : Graph Construction Failure
    CrossRepositoryAnalysis --> AnalysisError : Cross-Repo Analysis Failure
    
    ConfigurationError --> [*] : Fix Configuration Required
    ServiceError --> [*] : Service Recovery Required  
    ProcessingError --> [*] : Repository Issue Resolution Required
    GraphError --> [*] : Graph Reconstruction Required
    AnalysisError --> [*] : Analysis Retry Required
```